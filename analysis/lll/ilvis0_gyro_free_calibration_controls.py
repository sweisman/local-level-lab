# SPDX-License-Identifier: AGPL-3.0-or-later
"""Charge generated gyro-free training and held-back force prediction checks."""

import argparse
from contextlib import closing
import gzip
import json
from pathlib import Path

from .ilvis0_matched_generated import DOCS, RECOVERY
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'ilvis0-gyro-free-packet-calibration-controls-v1'
PLAN = DOCS+'GYRO_FREE_CALIBRATION_CONTROLS_PLAN.md'
REQUEST = DOCS+'gyro-free-calibration-controls-qualification.json'
TEST_REPORT = DOCS+'gyro-free-calibration-controls-tests.xml'
RESULT = DOCS+'gyro-free-calibration-controls-result.json'
TEST = 'analysis/tests/test_ilvis0_gyro_free_packet_fit.py'
SCOPE = 'eight generated training-only gyro-free force magnitude calibration controls'
CLOCKS = ('nominal_200Hz', 'header_elapsed')
SEEDS = (31, 75, 135, 201)
EARLIER, LATER = 600, 240
EVALUATIONS = 80
LIMITS = dict(native_calls=0, packet_visits=0, bound_calls=2*EVALUATIONS+4, bound_steps=2*EVALUATIONS+4)
RECOVERY_POLICY = dict(max_attempts_per_task=2, max_technical_interruptions=2,
    maximum_wall_s=180, minimum_free_bytes=1024**3, smoke_task_count=0)
TESTS = ('test_quadrature_fit_jacobian_includes_gravity_and_retains_off_diagonal_covariance',
         'test_continuous_gap_bound_encloses_a_rotating_force_with_exact_packet_average',
         'test_overlapping_packet_windows_match_direct_sums_and_finite_differences')


def tasks():
    return [dict(identity=f'{clock}-{seed}', input_key=f'{clock}-{seed}-earlier',
        later_key=f'{clock}-{seed}-later', clock=clock, seed=seed, limits=LIMITS)
        for clock in CLOCKS for seed in SEEDS]


def generated(clock, seed):
    import numpy as np

    rng = np.random.default_rng(seed)
    count = EARLIER+LATER
    dt = np.full(count, .005) if clock == CLOCKS[0] else rng.uniform(.003, .007, count)
    edges = np.r_[0., np.cumsum(dt)]
    normalized_centers = (edges[1:]+edges[:-1])/(2.*edges[-1])
    gains = rng.uniform(-.018, .018, 3)
    offsets = rng.uniform(-.06, .06, 3)
    gravity = float(rng.uniform(-.02, .02))
    a, b, c = 8.6, 2.1, .27
    norms = a + b*normalized_centers + c*(normalized_centers**2+(dt/edges[-1])**2/12.) + gravity
    # The sensor changes direction between packets. Each packet has a known exact mean.
    anchors = np.vstack((np.eye(3), -np.eye(3)))
    modes = rng.permutation(len(anchors))[(np.arange(count)//20) % len(anchors)]
    directions = anchors[modes]+rng.normal(0., .30, (count, 3))
    directions /= np.linalg.norm(directions, axis=1)[:, None]
    increments = dt[:, None]*(directions*norms[:, None]*(1.+gains)+offsets)
    # Two-point Gauss quadrature integrates the independent polynomial target exactly.
    nodes = np.array([-1., 1.])/np.sqrt(3.)
    materials = []
    for start, stop, role in ((0, EARLIER, 'earlier'), (EARLIER, count, 'later')):
        first = np.arange(start, stop-19, 10)
        last = first+20
        t0, t1 = edges[first], edges[last]
        q = ((t0+t1)[:, None]+(t1-t0)[:, None]*nodes)/(2.*edges[-1])
        required = np.zeros(q.shape+(3,))
        required[..., 2] = -(a+b*q+c*q*q)
        lag = abs(np.subtract.outer(np.arange(len(first)), np.arange(len(first))))
        covariance = 4e-5*(np.eye(len(first))+.55**lag)
        materials.append(dict(role=role, clock=clock, seed=seed, input_start=start, input_stop=stop,
            durations_s=dt[start:stop].tolist(), increments_mps=increments[start:stop].tolist(),
            windows=np.column_stack((first-start,last-start)).tolist(),
            required_force=required.tolist(), covariance=covariance.tolist(),
            weights=[.5, .5], known_physical_point=[*gains.tolist(), *offsets.tolist(), gravity]))
    return materials


def sources(root):
    from .studies.dependencies import source_closure

    return source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST,
        'analysis/tests/test_ilvis0_packet_force_calibration.py'))


def request(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request as qualify

    return qualify(root, sources=sources(root), environment=runtime_environment(),
                   output=REQUEST, report=TEST_REPORT)


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID).exists():
        raise ValueError('retain the existing generated calibration allowance')
    environment, deps = runtime_environment(), sources(root)
    qualification, tests = checked(root, REQUEST, sources=deps, environment=environment,
                                   required_tests=TESTS, minimum_tests=len(TESTS))
    recovery, recovery_tests = checked(root, RECOVERY, sources=qualification_sources(root),
        environment=environment, required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    staged = dict(qualification=qualification, qualification_tests=tests, recovery=recovery,
                  recovery_tests=recovery_tests, recovery_policy=encoded(RECOVERY_POLICY))
    rows = tasks()
    for task in rows:
        earlier, later = generated(task['clock'], task['seed'])
        staged[task['input_key']] = gzip.compress(encoded(earlier), mtime=0)
        staged[task['later_key']] = gzip.compress(encoded(later), mtime=0)
    inputs = dict(plan=PLAN)
    for key, raw in staged.items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, raw)
        inputs[key] = path
    definition = dict(id=ID, scope=SCOPE, tasks=rows, inputs=inputs, sources=deps,
        adapter=Path(__file__).relative_to(root).as_posix(), workers=2, threads=1, maximum_wall_s=180.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def _load(task, context, role):
    key, limits = ('input_key', (0, EARLIER)) if role == 'earlier' else ('later_key', (EARLIER, EARLIER+LATER))
    data = json.loads(gzip.decompress(context.input_path(task[key]).read_bytes()))
    if (data['role'] != role or data['clock'] != task['clock'] or data['seed'] != task['seed']
            or (data['input_start'], data['input_stop']) != limits
            or len(data['durations_s']) != limits[1]-limits[0]):
        raise ValueError('preserve the disjoint earlier and later packet inputs')
    return data


def _problem(data, limits, *, altered=False):
    import numpy as np

    from .ilvis0_gyro_free_packet_fit import PacketForceProblem
    from .ilvis0_packet_force_calibration import PacketMeans

    packets = PacketMeans(data['increments_mps'], data['durations_s'], data['windows'])
    target = np.asarray(data['required_force'], float)
    if altered:
        target[..., 2] -= .025
    return PacketForceProblem(packets, target, data['weights'], limits, data['covariance'])


def evaluate(task, context):
    import numpy as np

    from .ilvis0_matched_training import matched_limits
    from .ilvis0_scalar_nonlinear import fit

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in tasks():
        raise ValueError('exact generated training and check allowance required')
    config = matched_limits(1.)
    limits = [config[f'accel_{kind}_{axis}'] for kind in ('gain', 'bias') for axis in 'xyz']+[config['gravity_delta']]
    earlier = _load(task, context, 'earlier')

    def charge():
        context.charge(bound_calls=1, bound_steps=1)

    outcome = fit(_problem(earlier, limits), np.zeros(7), max_evaluations=EVALUATIONS, reserve=charge)
    context.save('training-fit.json', outcome)
    result = dict(passed=False, clock=task['clock'], seed=task['seed'], training_calls=outcome['calls'],
        training_passed=outcome['passed'], training_stop=outcome['stationarity'], scored_calls=0,
        recorded_aircraft_fits=0, scientific_decision='abstain')
    if outcome['passed']:
        later = _load(task, context, 'later')
        scores = []
        for altered in (False, True):
            charge()
            error = _problem(later, limits, altered=altered).raw_residual(outcome['point'])
            scores.append(float(np.sqrt(np.mean(error**2))))
        result.update(passed=scores[0] <= 1e-6 and scores[1] >= .024, scored_calls=2,
            forecast_rms_mps2=scores[0], altered_force_rms_mps2=scores[1], calibration_saved_before_later=True,
            maximum_physical_parameter_difference=float(np.max(np.abs(
                np.asarray(outcome['physical_point'])-np.asarray(earlier['known_physical_point'])))))
    context.save('result.json', result)
    return result


def report(root):
    from .ilvis0_matched_observed_inputs import _write_equal

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if study.manifest['scope'] != SCOPE or len(study.tasks) != len(tasks()):
            raise ValueError('the exact generated control freeze is required')
        rows = []
        for identity in study.rows:
            envelope = study.envelope(identity)
            outcome = envelope['result']
            if f'artifacts/{identity}/result.json' in envelope['artifacts']:
                if (outcome != study.artifact(identity, 'result.json') or envelope['charged']['bound_calls'] !=
                        outcome['training_calls']+outcome['scored_calls']):
                    raise ValueError('the fresh stop, scoring and charge accounting must agree')
            rows.append(dict(identity=identity, **outcome))
        value = dict(study.completion, cases=rows, qualified=study.summary['passed'],
            charged=study.summary['charged'], recorded_aircraft_fits=0, scientific_decision='abstain')
    raw = encoded(value)
    _write_equal(root/RESULT, raw)
    return dict(result_sha256=digest(raw), qualified=value['qualified'], completed=len(rows), charged=value['charged'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    print(json.dumps({'request': request, 'prepare': prepare, 'report': report}[action](Path.cwd()), sort_keys=True))


if __name__ == '__main__':
    main()
