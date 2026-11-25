# SPDX-License-Identifier: AGPL-3.0-or-later
"""Diagnose velocity reporting precision on the fixed RF04 receiver windows."""

import argparse
from contextlib import closing
import json
from pathlib import Path

from . import ilvis0_rf04_reference_acceleration as prior
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'ilvis0-rf04-velocity-resolution-v1'
AVERAGE, INTAKE = prior.parent, prior.intake
SCOPE = 'RF04 receiver speed and course reporting resolution and acceleration sensitivity'
PLAN = AVERAGE.motion.FOLDER + 'RF04_VELOCITY_RESOLUTION_PLAN.md'
RESULT = AVERAGE.motion.FOLDER + 'rf04-velocity-resolution-result.json'
PARENT_SHA = '073a07459f2322fec3cde01963c5efee1a4d6531d4c34087484e08a7471cd052'
TEST = 'analysis/tests/test_ilvis0_rf04_velocity_resolution.py'
TESTS = ('test_rf04_course_vectors_follow_north_east_and_wrap',
         'test_rf04_rounding_allowance_covers_component_changes_at_a_southward_heading',
         'test_rf04_grid_check_distinguishes_report_steps_from_five_sample_average_steps')
REQUEST, XML = (f'data/{ID}-inputs/{name}' for name in ('qualification.json', 'tests.xml'))
SPEED_STEP = .001*1852/3600
COURSE_STEP = .1
CASES = len(prior.HALF_WIDTHS)*len(AVERAGE.TRACKS)
TASK = dict(identity='rf04-velocity-resolution', input_key='speed-course', payload={}, limits=dict(
    native_calls=0, packet_visits=0, bound_calls=3+CASES,
    bound_steps=AVERAGE.PREPARATION_STEPS+2*AVERAGE.motion.EPOCHS+2*CASES*AVERAGE.WINDOWS))


def velocity_ne(speed_mps, course_deg):
    import numpy as np

    angle = np.deg2rad(course_deg)
    return np.asarray(speed_mps)[..., None]*np.stack((np.cos(angle), np.sin(angle)), axis=-1)


def grid_match(values, step, tolerance):
    import numpy as np

    values = np.asarray(values)
    residual = abs(values-step*np.rint(values/step))
    return dict(step=step, tolerance=tolerance, matched=int(np.count_nonzero(residual <= tolerance)),
                count=len(values), distance=AVERAGE.motion._stats(residual))


def rounding_allowance(speed_mps, course_deg, *, speed_step, course_step):
    """Bound the velocity component change within the two half-step bins."""
    import numpy as np

    radial = velocity_ne(np.ones(len(speed_mps)), course_deg)
    delta = np.deg2rad(course_step/2)
    direction_change = abs(radial[:, ::-1])*np.sin(delta)+abs(radial)*(1-np.cos(delta))
    return np.asarray(speed_mps)[:, None]*direction_change + speed_step/2*np.minimum(
        1., abs(radial)+direction_change)


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


def prepare(root, source):
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_gps_reconstruction_extension import RECOVERY
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('preserve the fixed RF04 velocity resolution study')
    sources = qualification(root, check=True)
    raw = (root/prior.RESULT).read_bytes()
    if digest(raw) != PARENT_SHA:
        raise ValueError('exact RF04 acceleration receipt required')
    with closing(ClosedStudy(root, 'data/'+prior.ID)) as study:
        if (study.completion != json.loads(raw)['completion'] or not study.summary['passed']
                or study.envelope(prior.TASK['identity'])['charged'] != prior.TASK['limits']):
            raise ValueError('completed acceleration cross-check required')
        original = study.input('velocity')
        material = {key: study.input(key, raw=True) for key in ('velocity', 'freeze', 'recorded', 'recovery_policy')}
    current = INTAKE.inspect_recording(source, include_reference_velocity=True, include_reference_course=True)
    reconstructed = [dict(utc=row['utc'], status=row['GGSTATUS'],
                          velocity_ne_mps=[row.get(key) for key in INTAKE.REFERENCE_VELOCITY])
                     for row in current['rows']]
    if (current['sha256'] != original['source_sha256'] or reconstructed != original['rows']
            or any(row['status'] != 1 for row in reconstructed)):
        raise ValueError('identical RF04 reference measurements and receiver status required')
    speed_course = [[row.get(key) for key in INTAKE.REFERENCE_SPEED_COURSE] for row in current['rows']]
    if len(speed_course) != AVERAGE.motion.EPOCHS or any(None in pair or pair[0] <= 0 for pair in speed_course):
        raise ValueError('complete valid receiver speed and course required')
    material['speed-course'] = encoded(dict(source_sha256=current['sha256'], values=speed_course,
        channels={key: current['variables'][key] for key in INTAKE.REFERENCE_SPEED_COURSE}))
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    files = dict(plan=PLAN, qualification=REQUEST, tests=XML, previous=prior.RESULT)
    for name, value in dict(material, recovery=recovery, recovery_tests=tests).items():
        path = f'data/{ID}-inputs/{name}'
        _write_equal(root/path, value)
        files[name] = path
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                      inputs=files, sources=sources, tasks=[TASK], workers=1, threads=1, maximum_wall_s=120)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def saved_path_windows(root, freeze, receipt):
    """Recover the same rounded UTC centers, original split and GPS polynomials."""
    import numpy as np

    origin, _, windows = AVERAGE.average.windows(root, freeze, receipt, AVERAGE.motion.SEGMENT,
                                                expected_windows=AVERAGE.WINDOWS)
    sides, _, targets, _, _, coefficients, _ = zip(*windows, strict=True)
    seconds, matched = AVERAGE.direction.near_seconds(origin+np.asarray(targets))
    if not matched.all() or np.any(np.diff(seconds) <= 0):
        raise ValueError('exact ordered receiver centers required')
    offsets = AVERAGE.direction.START+seconds-origin-targets
    return seconds, offsets, np.asarray(coefficients), np.asarray(sides) == 'training'


def evaluate(task, context):
    import numpy as np

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('the fixed RF04 velocity resolution comparison is required')

    def read(key):
        return json.loads(context.input_path(key).read_bytes())

    context.charge(bound_calls=1, bound_steps=AVERAGE.PREPARATION_STEPS)
    raw, course_source = read('velocity'), read('speed-course')
    if raw['source_sha256'] != course_source['source_sha256']:
        raise ValueError('same RF04 receiver source required')
    speed, course = np.asarray(course_source['values'], dtype=float).T
    velocity = np.asarray([row['velocity_ne_mps'] for row in raw['rows']], dtype=float)
    seconds, center_offsets, coefficients, earlier = saved_path_windows(
        context.root.parents[1], read('freeze'), read('recorded'))
    previous = read('previous')

    context.charge(bound_calls=1, bound_steps=AVERAGE.motion.EPOCHS)
    projected = velocity_ne(speed, course)
    projection_error = projected-velocity
    component_reconstruction = dict(
        horizontal_mps=AVERAGE.motion._stats(np.linalg.norm(projection_error, axis=1)),
        mean_ne_mps=projection_error.mean(axis=0).tolist(),
        rms_ne_mps=np.sqrt(np.mean(projection_error**2, axis=0)).tolist())

    context.charge(bound_calls=1, bound_steps=AVERAGE.motion.EPOCHS)
    course_grid = [grid_match(course, value/divisor, 2.5e-5)
                   for value in (1., .1, .01, .001) for divisor in (1, 5)]
    speed_grid = [grid_match(speed, SPEED_STEP*value/divisor, 4e-5)
                  for value in (100, 10, 1) for divisor in (1, 5)]
    endpoint_allowance = rounding_allowance(speed, course, speed_step=SPEED_STEP, course_step=COURSE_STEP)
    results = []
    for half_width, support in zip(prior.HALF_WIDTHS, previous['selection'], strict=True):
        width = 2*half_width
        ids = np.asarray(support['seconds_after_start'])
        selected = np.searchsorted(seconds, ids)
        if width != support['width_s'] or not np.array_equal(ids, seconds[selected]):
            raise ValueError('identical acceleration support required')
        is_later = ~earlier[selected]
        if is_later.sum() != len(ids)-support['earlier']:
            raise ValueError('original earlier/later split required')
        lo, hi = ids-half_width, ids+half_width
        measured = (velocity[hi]-velocity[lo])/width
        component_difference = (projected[hi]-projected[lo])/width-measured
        allowance = (endpoint_allowance[hi]+endpoint_allowance[lo])/width
        for index, track in enumerate(AVERAGE.TRACKS):
            context.charge(bound_calls=1, bound_steps=2*AVERAGE.WINDOWS)
            predicted = prior.acceleration_components(coefficients[selected, index],
                                                      center_offsets[selected], half_width)
            residual = (predicted-measured)[is_later]
            base = next(x['later'] for x in previous['results']
                        if (x['width_s'], x['track'], x['shift_s']) == (width, track, 0.))
            if not np.allclose(prior.discrepancy(residual)['rms_ne_mps2'], base['rms_ne_mps2'], rtol=0., atol=1e-12):
                raise ValueError('original acceleration baseline must replay')
            results.append(dict(width_s=width, track=track, later=int(is_later.sum()),
                beyond_allowance_ne=np.sum(abs(residual)>allowance[is_later], axis=0).tolist(),
                conditional_allowance_median_ne_mps2=np.median(allowance[is_later], axis=0).tolist(),
                projection_acceleration_difference=prior.discrepancy(component_difference[is_later])))
    return dict(passed=True, scientific_decision='abstain', calibrated_error_bound_established=False,
                component_reconstruction=component_reconstruction, course_grid_deg=course_grid,
                speed_grid_mps=speed_grid, hypothetical_course_step_deg=COURSE_STEP, results=results,
                new_fits=0, original_imu_reads=0, reserved_reads=0)


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        env = study.envelope(TASK['identity'])
        if env['charged'] != TASK['limits'] or not env['result']['passed']:
            raise ValueError('complete finite RF04 velocity resolution study required')
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
