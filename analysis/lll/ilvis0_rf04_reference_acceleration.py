# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cross-check saved trajectory accelerations with independent GPS velocity."""

import argparse
from contextlib import closing
import json
from pathlib import Path

from . import ilvis0_ncar_rf04 as intake
from . import ilvis0_rf04_force_average as parent
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'ilvis0-rf04-reference-acceleration-v1'
SCOPE = 'RF04 horizontal receiver acceleration consistency at shared whole-second endpoints'
PLAN = parent.motion.FOLDER + 'RF04_REFERENCE_ACCELERATION_PLAN.md'
RESULT = parent.motion.FOLDER + 'rf04-reference-acceleration-result.json'
PARENT_SHA = 'a687d34bdf03de7909985aa32704d12aeb1a4c63ea7d9356cadc0d705bb6d587'
TEST = 'analysis/tests/test_ilvis0_rf04_reference_acceleration.py'
INTAKE_TEST = 'analysis/tests/test_ilvis0_ncar_rf04.py'
TESTS = ('test_rf04_mean_acceleration_recovers_quadratic_route_in_receiver_axes',
         'test_rf04_acceleration_window_requires_both_endpoints_and_all_shifted_support',
         'test_rf04_reference_velocity_intake_preserves_old_output_and_signed_valid_samples')
REQUEST, XML = (f'data/{ID}-inputs/{name}' for name in ('qualification.json', 'tests.xml'))
OFFSET_SHA = '6a6f5bd0ff028568305350ce6bd1a972c11e834f39a5023fdeb105fe0394d861'
HALF_WIDTHS = (1, 3, 5)
SHIFTS_S = (0., -.4, .4)
SCALE_MPS2 = .02
CASES = len(HALF_WIDTHS)*len(parent.TRACKS)*len(SHIFTS_S)
TASK = dict(identity='rf04-reference-acceleration', input_key='velocity', payload={}, limits=dict(
    native_calls=0, packet_visits=0, bound_calls=1+CASES,
    bound_steps=parent.PREPARATION_STEPS+2*CASES*parent.WINDOWS))


def shared_windows(seconds, offsets, path_support, *, half_width, epoch_count, shift):
    """Check complete GPS endpoints and predicted support for the entire shift range."""
    return ((seconds-half_width >= 0) & (seconds+half_width < epoch_count)
            & (offsets-half_width-shift >= path_support[:, 0]-1e-10)
            & (offsets+half_width+shift <= path_support[:, 1]+1e-10))


def acceleration_components(coefficients, centers, half_width_s):
    """Mean derivative of the local velocity components on the receiver's scale."""
    import numpy as np

    from .models import radii

    times = centers[:, None]+np.asarray([-half_width_s, half_width_s])
    positions, derivatives, _ = parent.evaluate_polynomial_jets(coefficients, times)
    latitude, height = positions[..., 0], positions[..., 2]
    north, prime = radii(latitude)
    metric = np.stack((north+height, (prime+height)*np.cos(latitude)), axis=-1)
    velocity = metric*derivatives[..., :2]
    return (velocity[:, 1]-velocity[:, 0])/(2*half_width_s)


def qualification(root, *, check=False):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST, INTAKE_TEST))
    environment = runtime_environment()
    if not check:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources


def prepare(root, source):
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_gps_reconstruction_extension import RECOVERY
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('preserve the fixed RF04 reference acceleration study')
    sources = qualification(root, check=True)
    raw = (root/parent.RESULT).read_bytes()
    if digest(raw) != PARENT_SHA:
        raise ValueError('exact RF04 force-average receipt required')
    with closing(ClosedStudy(root, 'data/'+parent.ID)) as study:
        if (study.completion != json.loads(raw)['completion'] or not study.summary['passed']
                or study.envelope(parent.TASK['identity'])['charged'] != parent.TASK['limits']):
            raise ValueError('completed RF04 force-average study required')
        old_source = study.input('rf04')
        material = {key: study.input(key, raw=True) for key in ('freeze', 'recorded', 'recovery_policy')}
    offset = parent.direction.offset.RESULT
    if digest((root/offset).read_bytes()) != OFFSET_SHA:
        raise ValueError('exact RF04 receiver offset receipt required')
    current = intake.inspect_recording(source, include_reference_velocity=True)
    if current['sha256'] != old_source['sha256'] or current['rows'] != [
        original | {key: row.get(key) for key in intake.REFERENCE_VELOCITY}
        for original, row in zip(old_source['rows'], current['rows'], strict=True)
    ]:
        raise ValueError('unaltered verified RF04 source and time axis required')
    rows = [dict(utc=row['utc'], status=row['GGSTATUS'],
                 velocity_ne_mps=[row.get(key) for key in intake.REFERENCE_VELOCITY]) for row in current['rows']]
    if (len(rows) != parent.motion.EPOCHS
            or any(row['status'] != 1 or None in row['velocity_ne_mps'] for row in rows)):
        raise ValueError('complete one-second reference velocity and valid receiver status required')
    material['velocity'] = encoded(dict(source_sha256=current['sha256'], source_bytes=current['bytes'],
        channels={key: current['variables'][key] for key in intake.REFERENCE_VELOCITY}, rows=rows))
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    files = dict(plan=PLAN, qualification=REQUEST, tests=XML, averaged=parent.RESULT, offset=offset)
    for name, value in dict(material, recovery=recovery, recovery_tests=tests).items():
        path = f'data/{ID}-inputs/{name}'
        _write_equal(root/path, value)
        files[name] = path
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                      inputs=files, sources=sources, tasks=[TASK], workers=1, threads=1, maximum_wall_s=120)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def discrepancy(difference):
    import numpy as np

    horizontal = np.linalg.norm(difference, axis=1)
    return dict(epochs=len(horizontal), mean_ne_mps2=difference.mean(axis=0).tolist(),
                rms_ne_mps2=np.sqrt(np.mean(difference**2, axis=0)).tolist(),
                horizontal_mps2=parent.motion._stats(horizontal),
                above_descriptive_scale=int(np.count_nonzero(horizontal>SCALE_MPS2)))


def evaluate(task, context):
    import numpy as np

    declared = {key: val for key, val in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('the fixed receiver acceleration check is required')

    def read(key):
        return json.loads(context.input_path(key).read_bytes())

    context.charge(bound_calls=1, bound_steps=parent.PREPARATION_STEPS)
    velocity = np.asarray([r['velocity_ne_mps'] for r in read('velocity')['rows']], dtype=float)
    if velocity.shape != (parent.motion.EPOCHS, 2) or not np.isfinite(velocity).all():
        raise ValueError('all reference velocity components are required')
    origin, _, windows = parent.average.windows(context.root.parents[1], read('freeze'), read('recorded'),
                                              parent.motion.SEGMENT, expected_windows=parent.WINDOWS)
    sides, _, targets, _, _, coefficients, supports = zip(*windows, strict=True)
    seconds, near = parent.direction.near_seconds(origin+np.asarray(targets))
    expected = read('averaged')['support']
    if (not near.all() or any(row['seconds_after_start'] != seconds.tolist() for row in expected)
            or any(sides != ('training',)*row['earlier']+('later',)*row['later'] for row in expected)):
        raise ValueError('require the exact earlier and later centers from the force-average study')
    center_offsets = parent.direction.START+seconds-origin-targets
    supports, coefficients = (np.asarray(x, dtype=float) for x in (supports, coefficients))
    training = np.asarray(sides) == 'training'
    results, selection = [], []
    for half_width in HALF_WIDTHS:
        valid = shared_windows(seconds, center_offsets, supports, half_width=half_width,
                               epoch_count=len(velocity), shift=max(abs(x) for x in SHIFTS_S))
        ids = seconds[valid]
        earlier = training[valid]
        if min(earlier.sum(), (~earlier).sum()) < 2:
            raise ValueError('both time partitions require common receiver and shifted support')
        actual = (velocity[ids+half_width]-velocity[ids-half_width])/(2*half_width)
        selection.append(dict(width_s=2*half_width, seconds_after_start=ids.tolist(), earlier=int(earlier.sum())))
        for track_index, track in enumerate(parent.TRACKS):
            for shift in SHIFTS_S:
                context.charge(bound_calls=1, bound_steps=2*parent.WINDOWS)
                predicted = acceleration_components(coefficients[valid, track_index],
                                                     center_offsets[valid]+shift, half_width)
                difference = predicted-actual
                results.append(dict(width_s=2*half_width, track=track, shift_s=shift,
                                    earlier=discrepancy(difference[earlier]), later=discrepancy(difference[~earlier])))
    return dict(passed=True, scientific_decision='abstain', calibrated_error_bound_established=False,
                descriptive_scale_mps2=SCALE_MPS2, results=results, selection=selection,
                new_fits=0, original_imu_reads=0, reserved_reads=0)


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        env = study.envelope(TASK['identity'])
        if env['charged'] != TASK['limits'] or not env['result']['passed']:
            raise ValueError('complete finite RF04 acceleration study required')
        value = dict(env['result'], completion=study.completion, charged=env['charged'])
    _write_equal(root/RESULT, encoded(value))
    return dict(cases=len(value['results']), charged=value['charged'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    parser.add_argument('--source', type=Path)
    args = parser.parse_args()
    if (args.action == 'prepare') != (args.source is not None):
        parser.error('prepare requires --source and other actions omit it')
    root = Path.cwd()
    action = {'request': qualification, 'prepare': prepare, 'report': report}[args.action]
    print(json.dumps(action(root, args.source) if args.source is not None else action(root), sort_keys=True))
