# SPDX-License-Identifier: AGPL-3.0-or-later
"""RF04 antenna displacement sensitivity using independently reported attitudes."""

import argparse
from contextlib import closing
import json
from pathlib import Path

from . import ilvis0_rf04_velocity_resolution as parent
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'ilvis0-rf04-antenna-motion-v1'
AVERAGE, PRIOR = parent.AVERAGE, parent.prior
SCOPE = 'Sampled RF04 antenna displacement sensitivity on the original receiver windows'
PLAN = AVERAGE.motion.FOLDER + 'RF04_ANTENNA_MOTION_PLAN.md'
RESULT = AVERAGE.motion.FOLDER + 'rf04-antenna-motion-result.json'
PARENT_SHA = 'f7d3b25dee6935d195a09d827ff3cabc3bf76fa9179660e3b969d2852337af26'
RADIUS_M, LONGITUDINAL_EXAMPLE_M = 42., 4.3
TEST = 'analysis/tests/test_ilvis0_rf04_antenna_motion.py'
TESTS = ('test_sampled_antenna_acceleration_vanishes_at_constant_attitude',
         'test_sampled_antenna_acceleration_matches_endpoint_differences_for_yaw',
         'test_antenna_displacement_respects_radius_and_keeps_rank')
REQUEST, XML = (f'data/{ID}-inputs/{name}' for name in ('qualification-v2.json', 'tests-v2.xml'))
TASK = dict(identity='rf04-antenna-motion', input_key='rf04', payload={}, limits=dict(
    native_calls=0, packet_visits=0, bound_calls=1+parent.CASES,
    bound_steps=AVERAGE.PREPARATION_STEPS+4*parent.CASES*AVERAGE.WINDOWS))


def sampled_acceleration_design(rotations, centers, half_width):
    """Map displacement to mean component acceleration via centered endpoint velocities."""
    import numpy as np

    lo, hi = centers-half_width, centers+half_width
    if np.any(lo < 1) or np.any(hi >= len(rotations)-1):
        raise ValueError('each endpoint must have both neighboring attitude reports')
    r = rotations[:, :2, :]
    return (r[hi+1]-r[hi-1]-r[lo+1]+r[lo-1])/(4*half_width)


def fit_displacement(design, values, *, radius):
    """Solve the three-coordinate least squares problem inside a Euclidean ball."""
    import numpy as np
    from scipy.optimize import brentq

    u, s, vt = np.linalg.svd(design, full_matrices=False)
    keep = s > np.finfo(float).eps*max(design.shape)*s[0]
    rhs = (u.T@values)[keep]
    retained, directions = s[keep], vt[keep]
    norm_unconstrained = float(np.linalg.norm(rhs/retained))
    if norm_unconstrained <= radius:
        weights = rhs/retained
    else:
        numerator = retained*rhs

        def radius_error(damping):
            return np.linalg.norm(numerator/(retained**2+damping))-radius

        upper = 2*np.linalg.norm(numerator)/radius
        damping = brentq(radius_error, 0., upper, xtol=np.finfo(float).tiny)
        weights = numerator/(retained**2+damping)
    return weights@directions, dict(rank=int(keep.sum()), singular_values=s.tolist(),
        unconstrained_norm_m=norm_unconstrained, at_radius=norm_unconstrained>radius)


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
        raise ValueError('preserve the fixed RF04 antenna comparison')
    sources = qualification(root, check=True)
    raw = (root/parent.RESULT).read_bytes()
    if digest(raw) != PARENT_SHA:
        raise ValueError('exact RF04 velocity reporting receipt required')
    with closing(ClosedStudy(root, 'data/'+parent.ID)) as study:
        if (study.completion != json.loads(raw)['completion'] or not study.summary['passed']
                or study.envelope(parent.TASK['identity'])['charged'] != parent.TASK['limits']):
            raise ValueError('completed velocity reporting comparison required')
        inputs = ('velocity', 'speed-course', 'freeze', 'recorded', 'recovery_policy', 'previous')
        material = {key: study.input(key, raw=True) for key in inputs}
    with closing(ClosedStudy(root, 'data/'+AVERAGE.ID)) as study:
        material['rf04'] = study.input('rf04', raw=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    files = dict(plan=PLAN, qualification=REQUEST, tests=XML, resolution=parent.RESULT)
    for name, value in dict(material, recovery=recovery, recovery_tests=tests).items():
        path = f'data/{ID}-inputs/{name}'
        _write_equal(root/path, value)
        files[name] = path
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                      inputs=files, sources=sources, tasks=[TASK], workers=1, threads=1, maximum_wall_s=120)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np
    from scipy.spatial.transform import Rotation

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('the fixed RF04 antenna-motion comparison is required')

    def read(key):
        return json.loads(context.input_path(key).read_bytes())

    context.charge(bound_calls=1, bound_steps=AVERAGE.PREPARATION_STEPS)
    rf04, velocity, speed_course = (read(key) for key in ('rf04', 'velocity', 'speed-course'))
    if (rf04['sha256'] != velocity['source_sha256'] or rf04['sha256'] != speed_course['source_sha256']
            or [row['utc'] for row in rf04['rows']] != [row['utc'] for row in velocity['rows']]):
        raise ValueError('matched RF04 attitude and velocity epochs required')
    attitudes = Rotation.from_euler('ZYX', [[r[k] for k in reversed(AVERAGE.motion.ATTITUDE)]
                                           for r in rf04['rows']], degrees=True).as_matrix()
    speed, course = np.asarray(speed_course['values'], dtype=float).T
    observed = np.asarray([row['velocity_ne_mps'] for row in velocity['rows']], dtype=float)
    endpoint_allowance = parent.rounding_allowance(speed, course, speed_step=parent.SPEED_STEP,
                                                    course_step=parent.COURSE_STEP)
    seconds, offsets, coefficients, training = parent.saved_path_windows(
        context.root.parents[1], read('freeze'), read('recorded'))
    previous, resolution = read('previous'), read('resolution')
    results = []
    for half_width, support in zip(PRIOR.HALF_WIDTHS, previous['selection'], strict=True):
        ids = np.asarray(support['seconds_after_start'])
        selected = np.searchsorted(seconds, ids)
        width = 2*half_width
        earlier = training[selected]
        if not np.array_equal(ids, seconds[selected]) or width != support['width_s'] or earlier.sum() != support['earlier']:
            raise ValueError('the original acceleration support and split are required')
        lo, hi = ids-half_width, ids+half_width
        measured = (observed[hi]-observed[lo])/width
        rounding = (endpoint_allowance[hi]+endpoint_allowance[lo])/width
        design = sampled_acceleration_design(attitudes, ids, half_width)
        envelope = RADIUS_M*np.linalg.norm(design, axis=2)
        later = ~earlier
        for index, track in enumerate(AVERAGE.TRACKS):
            context.charge(bound_calls=1, bound_steps=4*AVERAGE.WINDOWS)
            predicted = PRIOR.acceleration_components(coefficients[selected, index], offsets[selected], half_width)
            residual = predicted-measured
            absolute = abs(residual[later])
            baseline_counts = np.sum(absolute>rounding[later], axis=0).tolist()
            saved = next(row for row in resolution['results'] if (row['width_s'], row['track']) == (width, track))
            if saved['beyond_allowance_ne'] != baseline_counts:
                raise ValueError('the previous reporting check must replay')
            displacement, fit = fit_displacement(design[earlier, 0], residual[earlier, 0], radius=RADIUS_M)
            corrected = residual[later]-design[later]@displacement
            results.append(dict(width_s=width, track=track, earlier=int(earlier.sum()), later=int(later.sum()),
                fit=fit | dict(displacement_body_frd_m=displacement.tolist(), norm_m=float(np.linalg.norm(displacement))),
                baseline_later=PRIOR.discrepancy(residual[later]), corrected_later=PRIOR.discrepancy(corrected),
                beyond_rounding_ne=baseline_counts,
                beyond_motion_ne=np.sum(absolute>envelope[later], axis=0).tolist(),
                beyond_both_ne=np.sum(absolute>rounding[later]+envelope[later], axis=0).tolist(),
                aircraft_envelope_median_ne_mps2=np.median(envelope[later], axis=0).tolist(),
                longitudinal_example=PRIOR.discrepancy(design[later, :, 0]*LONGITUDINAL_EXAMPLE_M)))
    return dict(passed=True, scientific_decision='abstain', aircraft_radius_m=RADIUS_M,
                longitudinal_example_m=LONGITUDINAL_EXAMPLE_M, results=results,
                independently_calibrated_error_bound=False, actual_antenna_separation_known=False,
                new_fits=0, original_imu_reads=0, reserved_reads=0)


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        env = study.envelope(TASK['identity'])
        if env['charged'] != TASK['limits'] or not env['result']['passed']:
            raise ValueError('complete RF04 antenna sensitivity required')
        value = dict(env['result'], completion=study.completion, charged=env['charged'])
    _write_equal(root/RESULT, encoded(value))
    return dict(cases=len(value['results']), charged=value['charged'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = {'request': qualification, 'prepare': prepare, 'report': report}[parser.parse_args().action]
    print(json.dumps(action(Path.cwd()), sort_keys=True))
