# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bound score changes using all signed carrier ranges on the open ESA flight."""
import argparse
from contextlib import ExitStack, closing
from fractions import Fraction
import gzip
import json
from pathlib import Path

from . import esa_nuuk_between_samples as motion
from . import esa_nuuk_orbit_clock as products
from . import esa_shared_motion_carrier as carrier
from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, _parent
from .esa_final_orbit_replay import interpolate_orbit
from .esa_precise_gps_support import read_orbit_positions
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import encoded


ID = 'esa-carrier-score-bound-v1'
SCOPE = 'Carrier-range sensitivity to any smooth position displacement with exact anchors on ESA 187'
PLAN = carrier.FOLDER+'ESA_CARRIER_SCORE_BOUND_PLAN.md'
RESULT = carrier.FOLDER+'esa-carrier-score-bound-result.json'
REQUEST = carrier.FOLDER+'esa-carrier-score-bound-qualification.json'
XML = carrier.FOLDER+'esa-carrier-score-bound-tests.xml'
ARTIFACT = 'carrier-score-bound.json'
PRODUCT_SHA = '40b586d4e848468e41482df75353efc8d93256cf0593e8eca8a3635d7cd7261d'
TESTS = ('test_off_grid_score_interpolation_matches_quadratic_error',
         'test_carrier_certificate_is_sharp_for_simple_centered_geometry',
         'test_unobserved_direction_remains_in_acceleration_bound',
         'test_range_gradient_agrees_with_signed_exact_range_change',
         'test_clock_correction_keeps_common_satellites_and_cancellation_signs')
TASK = dict(identity='carrier-score-bound', input_key='score', payload=dict(pairs=products.N),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=products.N+2,
                        bound_steps=1+66*products.N+4*3*(products.N-1)))


def qualification(root, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN,
                                    'analysis/tests/test_carrier_score_bound.py',
                                    'analysis/tests/test_shared_motion_carrier.py'))
    environment = runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment,
            required_tests=TESTS, minimum_tests=len(TESTS))
    return sources, environment


def prepare(root):
    from .esa_nuuk_between_carrier import MOTION_SHA
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original finite carrier score bound')
    sources, environment = qualification(root, True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with ExitStack() as stack:
        anchored, point = _parent(root, motion.RESULT, MOTION_SHA, motion.ID, motion.TASK, motion.ARTIFACT, stack)
        replay, history = _parent(root, products.RESULT, PRODUCT_SHA, products.ID, products.TASK, products.ARTIFACT, stack)
        if (not point['ground_positions_exactly_zero'] or len(history['rows']) != products.N
                or replay.envelope(products.TASK['identity'])['charged'] != products.TASK['limits']):
            raise ValueError('the exact anchored geometry and complete carrier evidence are required')
        values = {key: replay.input(key, raw=True) for key in
                  ('rinex', 'navigation', 'orbit', 'anchor', 'path', 'continuity', 'metric')}
        values['score'] = anchored.input('score', raw=True)
    values.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, original=products.RESULT, anchored=motion.RESULT, qualification=REQUEST,
                  qualification_tests=XML)
    for key, value in values.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=carrier.WALL_S), root).prepare(root)['limits']


def range_gradients(coordinates, satellites, metric):
    """Map fixed-transmit geometric range gradients to the frozen score coordinates."""
    import math

    import numpy as np

    from .gnss_carrier_phase import _geometry
    from .gnss_position import ecef, local_rotation

    lat, lon, height = coordinates
    flattening = 1/298.257223563
    eccentricity_squared = flattening*(2-flattening)
    root = math.sqrt(1-eccentricity_squared*math.sin(lat)**2)
    equatorial_radius = 6378137
    north = equatorial_radius*(1-eccentricity_squared)/root**3 + height
    east = (equatorial_radius/root + height)*math.cos(lat)
    jacobian = local_rotation(lat, lon).T * (np.array([north, east, 1.])/metric)
    _, derivative = _geometry(ecef(*coordinates), np.asarray(satellites))
    return derivative[:, :3]@jacobian


def pair_range_gradients(first, second, satellites, expected, positions, navigation, orbits, metric):
    _, states = carrier.paired_satellite_states(first, second, expected, satellites, navigation)
    return tuple(range_gradients(position, [interpolate_orbit(orbits[prn], state[2])
                 for prn, state in zip(satellites, endpoint, strict=True)], metric)
                 for position, endpoint in zip(positions, states, strict=True))


def score_grid(score, anchor):
    import numpy as np

    taps = np.asarray([float(Fraction(t)) for t in score['taps']]).reshape(-1, 3)
    scoring = list(map(Fraction, score['times']))
    scoring = [float(Fraction(anchor['time_s'])+t-scoring[0]) for t in scoring[1:]]
    return scoring, taps


def evaluate(task, context):
    import numpy as np

    from .carrier_score_bound import carrier_score_bound
    from .esa_carrier_phase_support import phase_epochs
    from .esa_rinex_code import read_navigation
    from .esa_rinex_code_comparison import coordinates

    if context.manifest['scope'] != SCOPE or {k: v for k, v in task.items() if k not in ('index', 'shard')} != TASK:
        raise ValueError('the frozen carrier geometry task is required')
    context.charge(bound_calls=1, bound_steps=1)

    def read(key):
        return context.input_path(key).read_bytes()

    phase = list(phase_epochs(gzip.decompress(read('rinex'))))
    navigation, _ = read_navigation(gzip.decompress(read('navigation')).decode('ascii'))
    orbits = read_orbit_positions(gzip.decompress(read('orbit')).decode('ascii'))
    anchor, path, score, metric, continuity, before, fixed = [json.loads(read(key)) for key in
        ('anchor', 'path', 'score', 'metric', 'continuity', 'original', 'anchored')]
    previous = coordinates([anchor])[0]
    previous_time = phase[carrier.START]['seconds']
    times = [previous_time]
    pairs = []
    for index, (row, original) in enumerate(zip(path, before['rows'], strict=True), carrier.START):
        context.charge(bound_calls=1, bound_steps=66)
        first, second = phase[index:index+2]
        prns = original['common_satellites']
        if (row['seconds'] != original['seconds'] or second['seconds'] != original['seconds']
                or first['seconds'] != times[-1] or second['seconds']-first['seconds'] != .5
                or first['week'] != second['week'] or second['week'] != anchor['gps_week']):
            raise ValueError('the exact matched carrier grid is required')
        pairs.append(pair_range_gradients(first, second, prns,
                     continuity['result']['per_pair'][index]['accepted_prns'], (previous, row['position']),
                     navigation, orbits, metric))
        times.append(second['seconds'])
        previous = row['position']
    ground = fixed['summary']['anchors_gps_s']
    indices = [0, *(times.index(t) for t in ground), len(times)-1]
    scoring, taps = score_grid(score, anchor)
    context.charge(bound_calls=1, bound_steps=4*3*(products.N-1))
    bound = carrier_score_bound(times, pairs, indices, scoring, taps)
    if len(pairs) != products.N or bound['range_values'] != before['product_summary']['values']:
        raise ValueError('all frozen observations must enter the certificate')
    gap = float(Fraction(score['gap']))
    accel = fixed['summary']['acceleration_vector_rms_mps2']
    minimum = max(0., gap-bound['acceleration_rms_to_score']*accel)/bound['range_rms_to_score']
    result = dict(bound=bound, score_gap=gap, test_acceleration_rms_mps2=accel, minimum_range_rms_m=minimum,
                  ground_anchors_gps_s=ground, endpoint_gps_s=[times[0], times[-1]], pairs=len(pairs),
                  new_fits=0, protected_reads=0, passed=True, scientific_decision='abstain')
    context.save(ARTIFACT, result)
    return result


def report(root):
    from .studies.closed import ClosedStudy

    prefix, identity = 'data/'+ID, TASK['identity']
    with ExitStack() as stack:
        study = stack.enter_context(closing(ClosedStudy(root, prefix)))
        if (root/(prefix+'-recovery')).is_dir():
            from .studies.combined_task_evidence import inspect

            origin = inspect(root, root/(prefix+'-recovery'))['selected'][identity]['origin']
            if origin != prefix:
                study = stack.enter_context(closing(ClosedStudy(root, origin, store=study.store)))
        envelope, result = study.envelope(identity), study.artifact(identity, ARTIFACT)
        if envelope['charged'] != TASK['limits'] or envelope['result'] != result or not result['passed']:
            raise ValueError('sealed and complete carrier certificate required')
        _write_equal(root/RESULT, encoded(dict(result, parent_sha256=PRODUCT_SHA, completion=study.completion)))
    return result | dict(bound={k: v for k, v in result['bound'].items() if k != 'dual_weights'})


if __name__ == '__main__':
    from functools import partial

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    result = {'request': partial(qualification, verify=False), 'prepare': prepare, 'report': report,
              'recover': partial(carrier.recover_signature, study_id=ID, task=TASK)}[action](Path.cwd())
    print(json.dumps(result, sort_keys=True))
