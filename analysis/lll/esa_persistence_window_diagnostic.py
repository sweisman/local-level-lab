# SPDX-License-Identifier: AGPL-3.0-or-later
"""Locate when and where the fixed ESA forecast scores accumulate."""

import argparse
from contextlib import closing
import json
import math
from pathlib import Path

from .esa_innovation_persistence import PersistenceScore, transitions
from .esa_motion_innovation_scale import BASE, LAWS, scorer
from .esa_persistence_analytic import ID as PARENT, RESULT as PRIOR
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-persistence-window-diagnostic-v1'
SCOPE = 'Sequential error on the fixed ESA 187 leave-pair-out forecasts'
PLAN = BASE+'ESA_PERSISTENCE_WINDOW_DIAGNOSTIC_PLAN.md'
RESULT = BASE+'esa-persistence-window-diagnostic-result.json'
REQUEST = BASE+'esa-persistence-window-diagnostic-qualification.json'
REPORT = BASE+'esa-persistence-window-diagnostic-tests.xml'
TEST = 'analysis/tests/test_esa_persistence_window_diagnostic.py'
TESTS = ('test_window_innovations_match_dense_unwhitened_cholesky[0]',
         'test_window_innovations_match_dense_unwhitened_cholesky[6]',
         'test_window_summary_keeps_fixed_blocks_and_axes')
PRIOR_SHA = '1d07f836e7ac81dc97cabd2ee3f3bd8739222ad1bac9bcdb23f85af46e07125b'
LIMITS = dict(native_calls=0, packet_visits=0, bound_calls=4, bound_steps=6)
REPORTS = 120


def conditional_innovations(baseline, times, point):
    """Apply the frozen time filter, then whiten the extra covariance in order."""
    import numpy as np
    from scipy.linalg import cholesky, solve_triangular

    if len(point) != 6 or not 2 <= len(times) <= REPORTS:
        raise ValueError('six settings and a short forecast window required')
    score = PersistenceScore(baseline, times, point[:4])
    phi = transitions(times, score.response, *map(math.exp, point[4:]))
    sigma = np.sqrt((1.-phi)*(1.+phi))
    if np.any(sigma <= 0.):
        raise ValueError('positive temporal innovation variances required')
    white = score.data.copy()
    white[1:] = (score.data[1:]-phi[:, None, None]*score.data[:-1])/sigma[:, None, None]
    flat = white.reshape(-1, white.shape[-1])
    roots = flat[:, 1:]
    covariance = roots@roots.T
    covariance.flat[::len(flat)+1] += 1.
    factor = cholesky(covariance, lower=True, check_finite=False)
    innovation = solve_triangular(factor, flat[:, 0], lower=True, check_finite=False)
    loss = (score.log_normalization+3.*np.log(sigma).sum()+np.log(factor.diagonal()).sum()
            +.5*(innovation@innovation+len(flat)*math.log(2.*math.pi)))
    return innovation.reshape(-1, 3), float(loss)


def summarize(innovations, weight, exposure):
    import numpy as np

    squares = np.square(innovations)
    epochs = squares.sum(axis=1)
    if len(epochs) % 3 or len(epochs) != len(weight) or len(epochs) != len(exposure):
        raise ValueError('complete aligned consecutive thirds required')
    thirds = np.split(squares, 3)
    total = float(epochs.sum())
    return dict(quadratic=total, quadratic_by_axis=squares.sum(axis=0).tolist(),
                quadratic_by_third=[float(values.sum()) for values in thirds],
                quadratic_by_third_and_axis=[values.sum(axis=0).tolist() for values in thirds],
                peak_epoch=int(epochs.argmax()), peak_quadratic=float(epochs.max()),
                top_five_fraction=float(np.sort(epochs)[-5:].sum()/total) if total else 0.,
                exposure_by_third=[float(values.sum()) for values in np.split(np.asarray(exposure), 3)],
                mean_weight_by_third=[float(values.mean()) for values in np.split(np.asarray(weight), 3)])


def task_for(pair, law):
    return dict(identity=f'{pair[0]}-{law}', input_key='design', payload=dict(pair=pair, law=law), limits=LIMITS)


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
    from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('retain the existing window diagnostic and allowance')
    prior_raw = (root/PRIOR).read_bytes()
    if digest(prior_raw) != PRIOR_SHA:
        raise ValueError('exact archived analytic result required')
    prior = json.loads(prior_raw)
    sources = qualification(root, check=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if (parent.completion != prior['completion'] or not parent.summary['passed'] or len(parent.rows) != 8):
            raise ValueError('eight closed donor refinements required')
        design = parent.input('design')
        indices = [i for pair in design['pairs'] for i in pair]
        tasks = [task_for(pair, law) for pair in design['pairs'] for law in LAWS]
        if len(indices) != 8 or len(set(indices)) != 8 or len(tasks) != 8:
            raise ValueError('the original four disjoint forecast pairs are required')
        keys = ['design', *(f'observed-{i}' for i in indices)]
        keys.extend(f'forecast-{i}-{law}' for i in indices for law in LAWS)
        staged = {key: parent.input(key, raw=True) for key in keys}
        for task in tasks:
            identity = task['identity']
            row = parent.artifact(identity, 'analytic-result.json')
            if (row != prior['folds'][identity] or row != parent.envelope(identity)['result']
                    or not row['verified'] or not row['fit']['converged']):
                raise ValueError('the fixed verified donor settings are required')
            staged[identity] = encoded(row)
    staged.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVERY_POLICY))
    inputs = dict(plan=PLAN, prior=PRIOR, qualification=REQUEST, qualification_tests=REPORT)
    for key, raw in staged.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, raw)
        inputs[key] = name
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(), inputs=inputs,
                      sources=sources, tasks=tasks, workers=2, threads=1, maximum_wall_s=180.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    pair, law = (task['payload'][key] for key in ('pair', 'law'))
    design = json.loads(context.input_path('design').read_bytes())
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE or pair not in design['pairs'] or law not in LAWS
            or declared != task_for(pair, law)):
        raise ValueError('exact frozen diagnostic pair and allowance required')
    saved = json.loads(context.input_path(task['identity']).read_bytes())
    if (saved['pair'] != pair or saved['law'] != law or not saved['verified'] or not saved['fit']['converged']
            or [row['index'] for row in saved['heldout']] != pair):
        raise ValueError('that pair must have two verified fixed scores')
    windows = []
    for row in saved['heldout']:
        index = row['index']
        key = f'{index}-{law}'
        baseline = scorer(context, index, law, design['scores'][key])
        forecast = json.loads(context.input_path(f'forecast-{key}').read_bytes())
        times, exposure = forecast['times_s'], forecast['angular_exposure']
        if len(times) != REPORTS:
            raise ValueError('exact original 120-report horizon required')
        context.charge(bound_calls=1, bound_steps=1)
        innovations, loss = conditional_innovations(baseline, times, saved['fit']['parameters'])
        weights = baseline.weight.reshape(-1, 3)[:, 0]
        summary = summarize(innovations, weights, exposure)
        summary.update(index=index, negative_log_score=loss, within_reference=row['updated']['within_reference'],
                       score_error=loss-row['updated']['negative_log_score'],
                       quadratic_error=summary['quadratic']-row['updated']['quadratic'])
        if max(abs(summary[key]) for key in ('score_error', 'quadratic_error')) > .000001:
            raise ValueError('ordered error components did not reproduce the frozen scores')
        context.save(f'innovations-{index}.json', dict(summary=summary, times_s=times, exposure=exposure,
                     weight=weights.tolist(), standardized_innovations=innovations.tolist()))
        windows.append(summary)
    result = dict(pair=pair, law=law, windows=windows, passed=True, new_fits=0, scientific_decision='abstain')
    context.save('window-diagnostic.json', result)
    return result


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if len(study.rows) != 8 or not study.summary['passed']:
            raise ValueError('all eight diagnostic tasks must pass score replay')
        rows = {}
        for identity in study.rows:
            record = study.envelope(identity)
            row = record['result']
            if (record['status'] != 'complete' or record['charged'] != LIMITS
                    or row != study.artifact(identity, 'window-diagnostic.json')
                    or any(w != study.artifact(identity, f"innovations-{w['index']}.json")['summary']
                           for w in row['windows'])):
                raise ValueError('result does not match the complete charges and saved sequence')
            rows[identity] = row
        result = dict(folds=rows, completion=study.completion, new_fits=0)
    _write_equal(root/RESULT, encoded(result))
    return dict(passing=len(rows), windows=sum(len(row['windows']) for row in rows.values()), new_fits=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    output = qualification(root, check=False) if action == 'request' else {'prepare': prepare, 'report': report}[action](root)
    print(json.dumps(output, sort_keys=True))
