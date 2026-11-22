# SPDX-License-Identifier: AGPL-3.0-or-later
"""Rescore fixed ESA 187 forecast windows against matched GPS exports."""

import argparse
from contextlib import ExitStack, closing
import json
import math
from pathlib import Path

from .esa_innovation_persistence import PersistenceScore
from .esa_motion_innovation_scale import InnovationScore, scorer
from .esa_persistence_analytic import ID as COVARIANCE_STUDY
from .esa_repeat_turn_inputs import RESULT as TURN_CLOCK, query_indices
from .esa_straight_control_windows import CLOCK_RESULT as STEADY_CLOCK
from .esa_window_scale_mixture import BASE, DIMENSION, ID as MIXTURE_STUDY, LAWS, window_score
from .esa_window_scale_mixture import RESULT as PRIOR
from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-forecast-receiver-transfer-v1'
SCOPE = 'Same-time substitution of two alternate GPS position exports on fixed ESA 187 forecasts'
PLAN = BASE+'ESA_FORECAST_RECEIVER_TRANSFER_PLAN.md'
RESULT = BASE+'esa-forecast-receiver-transfer-result.json'
REQUEST = BASE+'esa-forecast-receiver-transfer-qualification-v2.json'
REPORT = BASE+'esa-forecast-receiver-transfer-tests-v2.xml'
PPP_AUDIT = BASE+'full-parallel-gnss-v2-result.json'
PPP_SHA = 'f0cf2f2f1db5855c74c8c39962acc537c0867516cf61ae72b6145ca41ecfb74b'
PRIOR_SHA = '9ac0620280b9e0c2edfcec4aa636ccc1c879868b33efbbd56f245c65d6bd7782'
CLOCK_HASHES = {
    TURN_CLOCK: '78e4d5bcd0ee1a27776afaff06ec1eeaf0692cbd4a1b1eee0f649ab19fe740df',
    STEADY_CLOCK: '78271d62699d9e58904f4726bd772e9661f1429ca9c777e174f88312d91a9c30',
}
TEST = 'analysis/tests/test_esa_forecast_receiver_transfer.py'
TESTS = (
    'test_receiver_clock_and_local_metric_are_carried_to_the_anchor',
    'test_shift_changes_only_residual_and_matches_direct_score',
    'test_unmatched_window_is_not_interpolated',
    'test_relative_times_require_the_original_absolute_clock_tags',
)
REPORTS = DIMENSION//3
WALL_S = 180
RECOVER = dict(RECOVERY_POLICY, maximum_wall_s=WALL_S)
LIMITS = dict(native_calls=0, packet_visits=0, bound_calls=8, bound_steps=10)


def geodetic(row):
    return [math.radians(row['latitude_deg']), math.radians(row['longitude_deg']), row['height_m']]


def receiver_shifts(reference, alternate, *, anchor):
    import numpy as np

    from .esa_parallel_gnss_time import corrected_neu
    from .ilvis0_solver_position import physical_metric

    pairs = list(zip(reference, alternate, strict=True))
    if not pairs or any(row is None for _, row in pairs):
        return None
    local_metric = physical_metric([geodetic(row) for row in reference])
    adjusted = np.asarray([corrected_neu(ref, row)[1] for ref, row in pairs])
    return adjusted*physical_metric([anchor])[0]/local_metric


def shift_score(baseline, native, changes):
    import numpy as np
    from scipy.linalg import solve_triangular

    change = np.asarray(changes, float)
    if change.shape != (len(baseline.y)//3, 3) or not np.isfinite(change).all():
        raise ValueError('finite aligned receiver offsets required')
    shift = solve_triangular(native, change.ravel(), lower=True, check_finite=False)
    normalization = baseline.normalization-.5*len(shift)*math.log(2*math.pi)
    return InnovationScore(baseline.y+shift, baseline.root, baseline.weight, normalization)


def verify_clock(rows, relative_times, *, anchor_s, expected):
    tags = [(row['sequence'], row['time_s'], row['gps_week']) for row in rows]
    if (digest(encoded(tags)) != expected
            or relative_times != [row[1]-anchor_s for row in tags]):
        raise ValueError('original absolute and forecast-relative receiver times are required')


def match_exports(root, audit, observations, clocks):
    import numpy as np

    from .airquantumgrav_receiver import records
    from .esa_full_parallel_gnss import AIR1, BASE as SOURCE_DIRECTORY, _sha
    from .esa_full_parallel_gnss_v2 import EXPECTED_ROLLOVERS
    from .esa_parallel_gnss import match_times
    from .esa_ppp_acquisition import TARGETS, verify_complete
    from .esa_receiver_sequence_wrap import records_with_sequence_wrap

    base = root/SOURCE_DIRECTORY
    air1 = base/AIR1
    if (audit['reference_file'] != AIR1 or audit['protected_group_reads'] != 0
            or _sha(air1) != audit['reference_sha256']):
        raise ValueError('the verified opened air1 source is required')
    scoring = {index: query_indices(clock['window'])[1] for index, clock in clocks.items()}
    needed = {item for values in scoring.values() for item in values}
    if set(scoring) != set(observations) or len(needed) != 8*REPORTS:
        raise ValueError('eight disjoint original receiver supports required')
    with air1.open() as stream:
        by_index = {index: row for index, row in enumerate(records(stream)) if index in needed}
    if set(by_index) != needed:
        raise ValueError('all selected rows must occur in air1')
    targets = list(by_index.values())
    windows = {index: [by_index[item] for item in indices] for index, indices in scoring.items()}
    for index, (relative_times, positions) in observations.items():
        rows, clock = windows[index], clocks[index]
        anchor_s = clock['raw_first_s'] if 'raw_first_s' in clock else clock['inertial_support']['first_time_s']
        verify_clock(rows, relative_times, anchor_s=anchor_s, expected=clock['scoring_clock_sha256'])
        if not np.allclose([geodetic(row) for row in rows], positions, rtol=0., atol=2e-13):
            raise ValueError('sealed scoring coordinates differ from the original air1 rows')
    matches = {}
    for name, size in TARGETS.items():
        source = base/name
        receipt_raw = (base/(name+'.receipt.json')).read_bytes()
        previous = next(row for row in audit['sources'] if row['filename'] == name)
        if (digest(receipt_raw) != previous['receipt_sha256']
                or verify_complete(source, size, json.loads(receipt_raw)) != previous['source_sha256']):
            raise ValueError('the verified alternate receiver file is required')
        sequence = {}
        with source.open() as stream:
            parsed = records_with_sequence_wrap(stream, expected_rollovers=EXPECTED_ROLLOVERS[name], audit=sequence)
            matched = match_times(targets, parsed, tolerance_s=audit['match_tolerance_s'])
            for _ in parsed:
                pass
        if sequence != previous['sequence_audit']:
            raise ValueError('the alternate sequence audit differs')
        matches[name] = {targets[index]['time_s']: row for index, row in matched}
    return windows, matches


def task_for(pair, law):
    return dict(identity=f'{pair[0]}-{law}', input_key='design',
                payload=dict(pair=pair, law=law), limits=LIMITS)


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


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('reuse the existing frozen comparison')
    prior_raw, ppp_raw = ((root/name).read_bytes() for name in (PRIOR, PPP_AUDIT))
    if digest(prior_raw) != PRIOR_SHA or digest(ppp_raw) != PPP_SHA:
        raise ValueError('the original score and receiver audit reports are required')
    prior, ppp = json.loads(prior_raw), json.loads(ppp_raw)
    sources = qualification(root, check=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with (closing(ClosedStudy(root, 'data/'+MIXTURE_STUDY)) as mixture,
          closing(ClosedStudy(root, 'data/'+COVARIANCE_STUDY)) as covariance):
        if (mixture.completion != prior['closures'][mixture.prefix] or not mixture.summary['passed']
                or not covariance.summary['passed'] or len(mixture.rows) != 8 or len(covariance.rows) != 8):
            raise ValueError('eight verified donor selections and covariance fits required')
        design = mixture.input('design')
        indices = [index for pair in design['pairs'] for index in pair]
        tasks = [task_for(pair, law) for pair in design['pairs'] for law in LAWS]
        if len(indices) != 8 or len(set(indices)) != 8 or len(tasks) != 8:
            raise ValueError('four disjoint original pairs required')
        keys = ['design', *(f'observed-{index}' for index in indices)]
        keys.extend(f'forecast-{index}-{law}' for index in indices for law in LAWS)
        staged = {key: mixture.input(key, raw=True) for key in keys}
        for task in tasks:
            identity = task['identity']
            selected = mixture.artifact(identity, 'comparison.json')
            fitted = covariance.artifact(identity, 'analytic-result.json')
            if (selected != prior['folds'][identity] or selected != mixture.envelope(identity)['result']
                    or fitted != covariance.envelope(identity)['result'] or not fitted['verified']
                    or not fitted['fit']['converged'] or fitted['pair'] != selected['pair']
                    or fitted['donor_ids'] != selected['donors'] or fitted['law'] != selected['law']):
                raise ValueError('the original fit, selection and scores are required')
            staged[identity] = encoded(dict(dof=selected['dof'], fit=fitted['fit'], heldout=selected['heldout']))
    clocks = {}
    for path, expected in CLOCK_HASHES.items():
        raw = (root/path).read_bytes()
        clock_report = json.loads(raw)
        if digest(raw) != expected or clock_report['protected_reads'] != 0:
            raise ValueError('original clock receipts required')
        for entry in clock_report['windows']:
            index = entry['window']['first_index']
            if index in clocks:
                raise ValueError('clock receipts overlap')
            clocks[index] = entry
    observations = {index: json.loads(staged[f'observed-{index}']) for index in indices}
    reference, matches = match_exports(root, ppp, observations, clocks)
    for index, (times, _) in observations.items():
        rows = reference[index]
        absolute_times = [row['time_s'] for row in rows]
        by_source = {name: [by_time.get(time) for time in absolute_times] for name, by_time in matches.items()}
        for law in LAWS:
            forecast = json.loads(staged[f'forecast-{index}-{law}'])
            if times != forecast['times_s'] or len(times) != REPORTS:
                raise ValueError('the original 120 forecast epochs are required')
            shifts = {}
            for name, alternate in by_source.items():
                values = receiver_shifts(rows, alternate, anchor=forecast['anchor_geodetic'])
                shifts[name] = dict(matched=sum(row is not None for row in alternate),
                                    offsets_m=values.tolist() if values is not None else None)
            staged[f'substitutions-{index}-{law}'] = encoded(dict(times_s=times,
                absolute_times_s=absolute_times, sources=shifts))
    staged.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, prior=PRIOR, ppp=PPP_AUDIT, qualification=REQUEST, qualification_tests=REPORT)
    inputs.update(turn_clock=TURN_CLOCK, steady_clock=STEADY_CLOCK)
    for key, raw in staged.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, raw)
        inputs[key] = name
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                      inputs=inputs, sources=sources, tasks=tasks, workers=2, threads=1,
                      maximum_wall_s=WALL_S)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .esa_ppp_acquisition import TARGETS
    from .esa_repeat_turn_scoring import NATIVE_VARIANCE, _lower

    pair, law = (task['payload'][key] for key in ('pair', 'law'))

    def read(key):
        return json.loads(context.input_path(key).read_bytes())

    design = read('design')
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE or pair not in design['pairs'] or law not in LAWS
            or declared != task_for(pair, law)):
        raise ValueError('exact frozen two-window comparison required')
    saved = read(task['identity'])
    point = saved['fit']['parameters']
    windows = []
    for index, original in zip(pair, saved['heldout'], strict=True):
        key = f'{index}-{law}'
        baseline = scorer(context, index, law, design['scores'][key])
        forecast, alternate = read('forecast-'+key), read('substitutions-'+key)
        times = forecast['times_s']
        if (index != original['index'] or len(times) != REPORTS or times != alternate['times_s']
                or set(alternate['sources']) != set(TARGETS)):
            raise ValueError('the original aligned comparisons are required')
        native = _lower(forecast['native_root_neu_m'], DIMENSION)*math.sqrt(NATIVE_VARIANCE[law])

        def score(item):
            context.charge(bound_calls=1, bound_steps=1)
            gaussian = PersistenceScore(item, times, point[:4]).score(*map(math.exp, point[4:]))
            return dict(gaussian=gaussian, mixture=window_score(gaussian, DIMENSION, saved['dof']))

        air1 = score(baseline)
        if air1['mixture']['within_reference'] != original['mixture']['within_reference'] or any(
                not math.isclose(air1[method][metric], original[method][metric], rel_tol=1e-10, abs_tol=1e-8)
                for method in ('gaussian', 'mixture') for metric in ('quadratic', 'negative_log_score')):
            raise ValueError('unchanged air1 scores must reproduce')
        outcomes = {}
        for name, row in alternate['sources'].items():
            if row['matched'] != REPORTS:
                if row['offsets_m'] is not None:
                    raise ValueError('partial comparisons may not be filled')
                outcomes[name] = dict(matched=row['matched'], available=False)
                continue
            offsets = np.asarray(row['offsets_m'], float)
            changed = score(shift_score(baseline, native, offsets))
            outcomes[name] = dict(matched=row['matched'], available=True, **changed,
                quadratic_change=changed['mixture']['quadratic']-air1['mixture']['quadratic'],
                reference_changed=changed['mixture']['within_reference'] != air1['mixture']['within_reference'],
                rms_m=np.sqrt(np.mean(offsets**2, axis=0)).tolist())
        windows.append(dict(index=index, air1=air1, alternate=outcomes))
    result = dict(pair=pair, law=law, windows=windows, passed=True,
                  scientific_decision='abstain', protected_reads=0, new_fits=0)
    context.save('receiver-transfer.json', result)
    return result


def recover(root):
    from .studies.task_resume import close_original, prepare_campaign, resume_campaign

    prefix = 'data/'+ID
    continuation = root/(prefix+'-recovery')
    if not continuation.is_dir():
        if not (root/prefix/'completion.json').is_file():
            close_original(root, prefix, qualification_request=RECOVERY)
        with closing(ClosedStudy(root, prefix)) as original:
            if original.input('recovery_policy') != RECOVER:
                raise ValueError('unchanged recovery allowance required')
            if all(identity in original.rows and original.envelope(identity)['status'] == 'complete'
                   for identity in original.tasks):
                return dict(state='original_tasks_finished', pending=0)
        prepare_campaign(root, prefix, continuation, qualification_request=RECOVERY, **RECOVER)
    return resume_campaign(root, continuation)


def report(root):
    prefix = 'data/'+ID
    continuation = root/(prefix+'-recovery')
    with ExitStack() as stack:
        original = stack.enter_context(closing(ClosedStudy(root, prefix)))
        sources = {prefix: original}
        if continuation.is_dir():
            from .studies.combined_task_evidence import inspect

            selected = {identity: row['origin'] for identity, row in inspect(root, continuation)['selected'].items()}
        else:
            selected = {identity: prefix for identity in original.rows
                        if original.envelope(identity)['status'] == 'complete'}
        results = {}
        for identity, origin in selected.items():
            if origin not in sources:
                sources[origin] = stack.enter_context(closing(ClosedStudy(root, origin, store=original.store)))
            source = sources[origin]
            envelope = source.envelope(identity)
            row = source.artifact(identity, 'receiver-transfer.json')
            count = sum(value['available'] for window in row['windows'] for value in window['alternate'].values())
            expected = dict(LIMITS, bound_calls=4+count, bound_steps=6+count)
            if envelope['result'] != row or envelope['charged'] != expected or envelope['status'] != 'complete':
                raise ValueError('verified results and allowance required')
            results[identity] = row
        alternatives = [row for result in results.values() for window in result['windows']
                        for row in window['alternate'].values() if row['available']]
        result = dict(results=results, complete=len(results), available=len(alternatives),
                      reference_changes=sum(row['reference_changed'] for row in alternatives),
                      maximum_absolute_change=max((abs(row['quadratic_change']) for row in alternatives), default=None),
                      closures={key: study.completion for key, study in sources.items()})
    _write_equal(root/RESULT, encoded(result))
    return {key: result[key] for key in ('complete', 'available', 'reference_changes', 'maximum_absolute_change')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    output = qualification(root, check=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(output, sort_keys=True))
