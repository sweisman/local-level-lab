# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare a reset and a carried motion weight on the saved ESA forecasts."""

import argparse
from contextlib import closing
import io
import json
import math
from pathlib import Path

from .esa_innovation_persistence import PersistenceScore
from .esa_motion_error_transfer import THRESHOLD_DEG_S
from .esa_motion_innovation_scale import BASE, LAWS, InnovationScore, response, scorer
from .esa_persistence_analytic import ID as PARENT, RESULT as PRIOR
from .esa_repeat_turn_inputs import TRAIN
from .esa_repeat_turn_scoring import DECAY_S
from .esa_scored_path_shape import checked_receipts
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-persistence-history-v1'
SCOPE = 'Training-to-forecast carry of the fixed ESA 187 native innovation motion weight'
PLAN = BASE+'ESA_PERSISTENCE_HISTORY_PLAN.md'
RESULT = BASE+'esa-persistence-history-result.json'
REQUEST = BASE+'esa-persistence-history-qualification.json'
REPORT = BASE+'esa-persistence-history-tests.xml'
TEST = 'analysis/tests/test_esa_persistence_history.py'
TESTS = ('test_carried_motion_matches_single_stream_across_cut',
         'test_no_history_preserves_score_and_history_changes_only_weights')
PRIOR_SHA = '1d07f836e7ac81dc97cabd2ee3f3bd8739222ad1bac9bcdb23f85af46e07125b'
LIMITS = dict(native_calls=0, packet_visits=0, bound_calls=10, bound_steps=2*(TRAIN+8))


def carry(reset, times, previous_time, start):
    import numpy as np

    reset, times = np.asarray(reset, float), np.asarray(times, float)
    if (reset.shape != times.shape or times.ndim != 1 or not len(times) or not 0. <= start <= 1.
            or not np.isfinite(times).all() or not math.isfinite(previous_time)
            or np.any(np.diff(times, prepend=previous_time) <= 0.)
            or not np.isfinite(reset).all() or np.any((reset < 0.) | (reset > 1.))):
        raise ValueError('aligned causal motion response and finite history required')
    return np.minimum(1., reset+start*np.exp(-(times-previous_time)/DECAY_S))


def scores(baseline, times, *, previous_time, start, point):
    import numpy as np

    weight = baseline.weight.reshape(-1, 3)[:, 0]
    updated = carry(weight, times, previous_time, start)
    source_normalization = baseline.normalization-.5*len(baseline.y)*math.log(2.*math.pi)
    warm = InnovationScore(baseline.y, baseline.root, np.repeat(updated, 3), source_normalization)
    quiet, moving = map(math.exp, point[4:])
    return tuple(PersistenceScore(case, times, point[:4]).score(quiet, moving) for case in (baseline, warm))


def task_for(pair):
    return dict(identity=f'pair-{pair[0]}', input_key='design', payload=pair, limits=LIMITS)


def qualification(root, *, check):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST))
    environment = runtime_environment()
    if not check:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=REPORT)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources


def earlier_inputs(root, indices, *, store):
    import numpy as np

    staged = {}
    for regime, (receipt, _, prefix) in checked_receipts(root).items():
        with closing(ClosedStudy(root, prefix+'runtime', store=store)) as source:
            if (source.completion['manifest_sha256'] != receipt['manifest_sha256']
                    or source.completion['state'] != 'complete' or source.summary['completed'] != 16):
                raise ValueError('original archived training inputs required')
            meta_key = 'input-preflight' if regime == 'turn' else 'bundle'
            for record in source.input(meta_key)['windows']:
                index = record['window']['first_index']
                if index not in indices or f'earlier-{index}' in staged:
                    raise ValueError('each checked window must occur once')
                prefix_count = record['training_packets']
                raw = source.input(f'{index}-interval', raw=True)
                with np.load(io.BytesIO(raw), allow_pickle=False) as archive:
                    if len(archive['dt']) != record['forecast_packets']:
                        raise ValueError('archived support differs from original preflight')
                    arrays = {key: np.asarray(archive[key][:prefix_count], dtype='<f8') for key in ('dt', 'theta')}
                if any(digest(v.tobytes()) != record['training_prefix_hashes'][key] for key, v in arrays.items()):
                    raise ValueError('training prefix hashes differ')
                buffer = io.BytesIO()
                np.savez_compressed(buffer, **arrays)
                staged[f'earlier-{index}'] = buffer.getvalue()
                staged[f'earlier-meta-{index}'] = encoded(dict(query_times_s=record['query_times_s'][:TRAIN],
                    count=record['angular_exposure_counts']['training'], packet_count=prefix_count,
                    source_manifest=source.completion['manifest_sha256'],
                    prefix_sha256={key: record['training_prefix_hashes'][key] for key in arrays}))
    if len(staged) != 2*len(indices):
        raise ValueError('complete earlier-only input freeze required')
    return staged


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('reuse the existing history comparison')
    raw = (root/PRIOR).read_bytes()
    if digest(raw) != PRIOR_SHA:
        raise ValueError('exact completed donor refinement required')
    prior = json.loads(raw)
    sources = qualification(root, check=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if parent.completion != prior['completion'] or len(parent.rows) != 8 or not parent.summary['passed']:
            raise ValueError('eight closed donor refits required')
        design = parent.input('design')
        indices = {i for pair in design['pairs'] for i in pair}
        if len(indices) != 8 or len(design['pairs']) != 4 or any(len(pair) != 2 for pair in design['pairs']):
            raise ValueError('four disjoint pairs required')
        keys = ['design', *(f'observed-{i}' for i in sorted(indices))]
        keys.extend(f'forecast-{i}-{law}' for i in sorted(indices) for law in LAWS)
        staged = {key: parent.input(key, raw=True) for key in keys}
        staged.update(earlier_inputs(root, indices, store=parent.store))
        for identity in parent.rows:
            refit = parent.artifact(identity, 'analytic-result.json')
            if (refit != prior['folds'][identity] or refit != parent.envelope(identity)['result']
                    or not refit['verified'] or not refit['fit']['converged']):
                raise ValueError('verified frozen parameter vector required')
            staged[identity] = encoded(refit)
    staged.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVERY_POLICY))
    inputs = dict(plan=PLAN, prior=PRIOR, qualification=REQUEST, qualification_tests=REPORT)
    for key, data in staged.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, data)
        inputs[key] = name
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(), inputs=inputs,
                      sources=sources, tasks=[task_for(pair) for pair in design['pairs']], workers=2, threads=1,
                      maximum_wall_s=180.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np
    from .maneuver_error_roots import turn_exposure

    def read(key):
        return json.loads(context.input_path(key).read_bytes())

    pair = task['payload']
    design = read('design')
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or pair not in design['pairs'] or declared != task_for(pair):
        raise ValueError('exact motion history pair and allowance required')
    refits = {law: read(f'{pair[0]}-{law}') for law in LAWS}
    windows = []
    for offset, index in enumerate(pair):
        meta = read(f'earlier-meta-{index}')
        earlier = meta['query_times_s']
        with np.load(context.input_path(f'earlier-{index}'), allow_pickle=False) as archive:
            if set(archive.files) != {'dt', 'theta'}:
                raise ValueError('earlier time steps and angles only')
            arrays = {key: archive[key] for key in archive.files}
        if (len(earlier) != TRAIN or len(arrays['dt']) != meta['packet_count']
                or any(digest(v.tobytes()) != meta['prefix_sha256'][k] for k, v in arrays.items())):
            raise ValueError('exact sealed earlier motion support required')
        context.charge(bound_calls=1, bound_steps=TRAIN)
        exposure = turn_exposure(arrays['dt'], arrays['theta'], earlier, previous_time=0.,
                                 threshold_deg_s=THRESHOLD_DEG_S)
        active = np.flatnonzero(exposure)
        if len(active) != meta['count']:
            raise ValueError('training threshold count differs from the original preflight')
        initial = float(response(earlier, previous_time=0., exposure=exposure)[-1])
        row = dict(index=index, earlier_active=len(active), initial_weight=initial,
                   time_since_last_active_s=earlier[-1]-earlier[active[-1]] if len(active) else None, laws={})
        for law, fit in refits.items():
            archived = fit['heldout'][offset]
            key = f'{index}-{law}'
            forecast = read(f'forecast-{key}')
            previous_time, times = forecast['previous_time'], forecast['times_s']
            if (fit['pair'] != pair or fit['law'] != law or archived['index'] != index or previous_time != earlier[-1]
                    or not fit['verified'] or not fit['fit']['converged']):
                raise ValueError('forecast must start at the final training report of the same fixed fit')
            baseline = scorer(context, index, law, design['scores'][key])
            context.charge(bound_calls=1, bound_steps=2)
            reset, updated = scores(baseline, times, previous_time=previous_time, start=initial,
                                    point=fit['fit']['parameters'])
            if any(abs(reset[k]-archived['updated'][k]) > .000001 for k in ('quadratic', 'negative_log_score')):
                raise ValueError('zero-state score differs from the original covariance')
            weight = baseline.weight.reshape(-1, 3)[:, 0]
            updated_weight = carry(weight, times, previous_time, initial)
            row['laws'][law] = dict(reset=reset, carried=updated, maximum_weight_change=float((updated_weight-weight).max()))
        windows.append(row)
    result = dict(pair=pair, windows=windows, passed=True, new_fits=0, scientific_decision='abstain')
    context.save('history.json', result)
    return result


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if len(study.rows) != 4 or not study.summary['passed']:
            raise ValueError('all four history diagnostics must replay the archived scores')
        rows = {}
        for identity in study.rows:
            record = study.envelope(identity)
            if (record['status'] != 'complete' or record['charged'] != LIMITS
                    or record['result'] != study.artifact(identity, 'history.json')):
                raise ValueError('exact sealed and charged motion-history result required')
            for row in record['result']['windows']:
                if str(row['index']) in rows:
                    raise ValueError('each fixed window must appear once')
                rows[str(row['index'])] = row
        result = dict(windows=rows, completion=study.completion, new_fits=0)
    _write_equal(root/RESULT, encoded(result))
    return dict(windows=len(rows), passing=len(study.rows), new_fits=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    value = qualification(root, check=False) if action == 'request' else {'prepare': prepare, 'report': report}[action](root)
    print(json.dumps(value, sort_keys=True))
