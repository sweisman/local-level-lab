# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare RF04 force directions at shared centers under both packet clocks."""

import argparse
from contextlib import closing
from itertools import combinations
import json
from pathlib import Path

from . import ilvis0_paired_gyro_average as average
from . import ilvis0_rf04_force_direction as direction
from . import ilvis0_rf04_motion_match as motion
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'ilvis0-rf04-force-average-v1'
SCOPE = 'RF04 attitude-conditioned averaged force directions on matched clock support'
PLAN = motion.FOLDER + 'RF04_FORCE_AVERAGE_PLAN.md'
RESULT = motion.FOLDER + 'rf04-force-average-result.json'
PARENT_SHA = '3c8c83c60d324969f065b453eb56dce5c97065f00a9d82b52490b5d04ba3f60f'
TEST = 'analysis/tests/test_ilvis0_rf04_force_average.py'
TESTS = ('test_rf04_force_average_uses_polynomial_derivatives_at_each_quadrature_node',
         'test_rf04_force_average_requires_both_clocks_and_original_path_support',
         'test_rf04_force_average_preserves_stationary_force_in_center_local_axes')
REQUEST, XML = (f'data/{ID}-inputs/{name}' for name in ('qualification.json', 'tests.xml'))
PATHS = direction.prior.paths
TRACKS, CLOCKS, MODELS = PATHS.TRACKS, PATHS.SUPPORT.CLOCKS, PATHS.average.MATCHED_MODELS
WIDTHS = (.25, 1.)
WINDOWS = 383
PREPARATION_STEPS = PATHS.SUPPORT.MAX_PACKETS
SCORE_STEPS = WINDOWS * PATHS.QUADRATURE
SCORES, PAIRS = 32, 48
TASK = dict(identity='rf04-force-average', input_key='rf04', payload={}, limits=dict(
    native_calls=0, packet_visits=0, bound_calls=1+SCORES+PAIRS,
    bound_steps=PREPARATION_STEPS+SCORES*SCORE_STEPS+PAIRS*WINDOWS))


def common_support(ends_by_clock, center, target, width, start, stop, limits):
    """Use whole increments only. Retain a center only when both clocks qualify."""
    if len(ends_by_clock) != 2:
        raise ValueError('both declared clocks required')
    intervals = []
    for ends in ends_by_clock:
        support = average._support(ends, center, width, start, stop)
        if support is None:
            return None
        _, _, lo, hi = support
        if hi-lo < .95*width-1e-9 or not limits[0] <= lo-target < hi-target <= limits[1]:
            return None
        intervals.append(support)
    return intervals


def evaluate_polynomial_jets(coefficients, times):
    """Evaluate position and its two derivatives at each window's node times."""
    import numpy as np

    times = np.asarray(times, dtype=float)
    polynomial = np.polynomial.polynomial
    result = []
    for order in range(3):
        terms = polynomial.polyder(coefficients, m=order, axis=1)
        powers = times[..., None]**np.arange(terms.shape[1])
        result.append(np.einsum('nqk,nkc->nqc', powers, terms))
    return result


def local_mean_force(coefficients, centers, points, weights, model):
    """Average in fixed axes, then express the result in NED at the window center."""
    import numpy as np

    from .ilvis0_force_motion_triplets import force_in_fixed_frame
    from .ilvis0_receiver_force import evaluate_batch

    position, velocity, acceleration = evaluate_polynomial_jets(coefficients, points)
    coordinates = position.reshape(-1, 3)
    settings = PATHS._settings(model)
    settings['gravity_mps2'] = np.full(len(coordinates), settings['gravity_mps2'])
    force = evaluate_batch(coordinates, velocity.reshape(-1, 3),
                           acceleration.reshape(-1, 3), **settings)['specific_force_ned_mps2']
    fixed = force_in_fixed_frame(force, coordinates, model=model).reshape(position.shape)
    fixed_mean = np.einsum('q,nqc->nc', weights, fixed)

    center_position = evaluate_polynomial_jets(coefficients, centers[:, None])[0][:, 0]
    local_axes = force_in_fixed_frame(np.tile(np.eye(3), (len(centers), 1)),
        np.repeat(center_position, 3, axis=0), model=model).reshape(-1, 3, 3)
    return np.einsum('nij,nj->ni', local_axes, fixed_mean)


def qualification(root, *, check=False):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST))
    environment = runtime_environment()
    if not check:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_gps_reconstruction_extension import RECOVERY
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('preserve the fixed RF04 force average comparison')
    sources = qualification(root, check=True)
    raw = (root/direction.RESULT).read_bytes()
    receipt = json.loads(raw)
    if digest(raw) != PARENT_SHA:
        raise ValueError('exact RF04 force direction receipt required')
    with closing(ClosedStudy(root, 'data/'+direction.ID)) as study:
        if (study.completion != receipt['completion'] or not study.summary['passed']
                or study.envelope(direction.TASK['identity'])['charged'] != direction.TASK['limits']):
            raise ValueError('completed RF04 single-packet comparison required')
        material = {key: study.input(key, raw=True) for key in ('rf04', 'freeze', 'recorded', 'recovery_policy')}
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    inputs = dict(plan=PLAN, qualification=REQUEST, tests=XML, direction=direction.RESULT)
    for name, value in dict(material, recovery=recovery, recovery_tests=tests).items():
        path = f'data/{ID}-inputs/{name}'
        _write_equal(root/path, value)
        inputs[name] = path
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                      inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1, maximum_wall_s=120)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def matched_support(origin, clock_ends, windows, width):
    import numpy as np

    retained = []
    for side, _, target, start, stop, coefficients, limits in windows:
        seconds, valid = direction.near_seconds([origin+target])
        if not valid[0]:
            continue
        second = int(seconds[0])
        center = direction.START+second-origin
        intervals = common_support(clock_ends, center, target, width, start, stop, limits)
        if intervals is not None:
            retained.append((side, second, center-target, target, intervals, coefficients))
    sides, seconds, centers, targets, intervals, coefficients = zip(*retained, strict=True)
    training = sides.count('training')
    if (training < 2 or len(sides)-training < 2 or np.any(np.diff(seconds) <= 0)
            or sides != ('training',)*training+('later',)*(len(sides)-training)):
        raise ValueError('ordered and disjoint earlier/later RF04 windows required')
    return training, list(seconds), np.asarray(centers), np.asarray(targets), np.asarray(intervals), np.asarray(coefficients)


def evaluate(task, context):
    import numpy as np
    from scipy.spatial.transform import Rotation

    from .esa_gyro_force_direction import angles
    from .force_direction_alignment import aligned_direction_scores, unit_vectors

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('the fixed RF04 force average comparison is required')

    def read(key):
        return json.loads(context.input_path(key).read_bytes())

    context.charge(bound_calls=1, bound_steps=PREPARATION_STEPS)
    rf04, receipt = read('rf04'), read('direction')
    if rf04['attitude_epochs'] != motion.EPOCHS or len(rf04['rows']) != motion.EPOCHS:
        raise ValueError('complete RF04 attitude required')
    attitude = Rotation.from_euler('ZYX', [[row[key] for key in reversed(motion.ATTITUDE)]
                                          for row in rf04['rows']], degrees=True)
    origin, record, windows = average.windows(context.root.parents[1], read('freeze'), read('recorded'),
                                               motion.SEGMENT, expected_windows=WINDOWS)
    clock_ends = [np.cumsum(periods) for periods in record['periods']]
    integrated = np.vstack((np.zeros(3, dtype=np.int64), np.cumsum(record['counts'], axis=0)))
    nodes, weights = np.polynomial.legendre.leggauss(PATHS.QUADRATURE)
    expected = next(r for r in receipt['scores'] if r['clock'] == CLOCKS[0])
    scores, pairs, support = [], [], []
    for width in WIDTHS:
        training, seconds, centers, targets, intervals, coeffs = matched_support(origin, clock_ends, windows, width)
        if training > expected['earlier'] or len(seconds)-training > expected['later']:
            raise ValueError('only previously matched RF04 seconds can qualify')
        edges_ms = 1000*abs(intervals[:, 0, 2:]-intervals[:, 1, 2:])
        support.append(dict(width_s=width, earlier=training, later=len(seconds)-training,
                            seconds_after_start=seconds, left_edge_difference_ms=motion._stats(edges_ms[:, 0]),
                            right_edge_difference_ms=motion._stats(edges_ms[:, 1])))
        for clock_index, clock in enumerate(CLOCKS):
            first, last, lo, hi = intervals[:, clock_index, :].T
            measured = integrated[last.astype(int)]-integrated[first.astype(int)]
            points = ((lo+hi)/2-targets)[:, None] + (hi-lo)[:, None]/2*nodes
            for track_index, track in enumerate(TRACKS):
                predictions = {}
                for model in MODELS:
                    context.charge(bound_calls=1, bound_steps=SCORE_STEPS)
                    local = local_mean_force(coeffs[:, track_index], centers, points, weights/2, model)
                    predicted = unit_vectors(direction.body_prediction(attitude[seconds], local))
                    fitted = aligned_direction_scores(predicted, measured, training=training)
                    later = predicted[training:]
                    rotation = fitted.get('rotation_reference_to_measured')
                    predictions[model] = later, None if rotation is None else later @ np.asarray(rotation).T
                    scores.append(dict(width_s=width, track=track, clock=clock, model=model,
                        earlier=training, later=len(later),
                        **{key: value for key, value in fitted.items() if key != 'angular_errors_deg'}))
                for m0, m1 in combinations(MODELS, 2):
                    context.charge(bound_calls=1, bound_steps=WINDOWS)
                    first, aligned_first = predictions[m0]
                    second, aligned_second = predictions[m1]
                    pairs.append(dict(width_s=width, track=track, clock=clock, models=[m0, m1],
                        nominal_deg=motion._stats(np.rad2deg(angles(first, second))),
                        aligned_deg=None if aligned_first is None or aligned_second is None else
                        motion._stats(np.rad2deg(angles(aligned_first, aligned_second)))))
    if len(scores) != SCORES or len(pairs) != PAIRS:
        raise ValueError('all matched settings required')
    return dict(passed=True, scientific_decision='abstain', attitude_source='RF04 fused navigation at window center',
                support=support, scores=scores, comparisons=pairs, new_fits=0, original_imu_reads=0, reserved_reads=0,
                absolute_model_error_bound_established=False)


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        env = study.envelope(TASK['identity'])
        if env['charged'] != TASK['limits'] or not env['result']['passed']:
            raise ValueError('complete finite RF04 force average comparison required')
        value = dict(env['result'], completion=study.completion, charged=env['charged'])
    _write_equal(root/RESULT, encoded(value))
    return dict(comparisons=len(value['comparisons']), scores=len(value['scores']), charged=value['charged'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = {'request': qualification, 'prepare': prepare, 'report': report}[parser.parse_args().action]
    print(json.dumps(action(Path.cwd()), sort_keys=True))
