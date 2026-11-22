# SPDX-License-Identifier: AGPL-3.0-or-later
"""Validate the geometric domain for the frozen ESA carrier remainder bound."""
import argparse
from contextlib import ExitStack, closing
import gzip
import json
import math
from pathlib import Path

from . import esa_carrier_anchor_error as anchors
from . import esa_carrier_score_bound as prior
from . import esa_shared_motion_carrier as carrier
from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, _parent
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import encoded


ID = 'esa-carrier-range-remainder-v1'
SCOPE = 'Exact geometric range remainder on the saved ESA 187 carrier domain'
PLAN = carrier.FOLDER+'ESA_CARRIER_RANGE_REMAINDER_PLAN.md'
REQUEST = carrier.FOLDER+'esa-carrier-range-remainder-qualification.json'
XML = carrier.FOLDER+'esa-carrier-range-remainder-tests.xml'
RESULT = carrier.FOLDER+'esa-carrier-range-remainder-result.json'
ARTIFACT = 'carrier-range-remainder.json'
N = prior.products.N
TASK = dict(identity='carrier-range-remainder', input_key='score', payload=dict(pairs=N),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=N+2, bound_steps=1+66*N+N))


def qualification(root, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN,
                                    'analysis/tests/test_carrier_range_remainder.py',
                                    'analysis/tests/test_carrier_score_bound.py'))
    environment = runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=(
        'test_reference_error_acceleration_bounds_interior_displacement',
        'test_second_order_bound_covers_exact_signed_range_changes',
        'test_second_order_bound_rejects_displacements_outside_validated_altitude'), minimum_tests=7)
    return sources, environment


def prepare(root):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original finite carrier remainder study')
    sources, environment = qualification(root, True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with ExitStack() as stack:
        study, result = _parent(root, prior.RESULT, anchors.PARENT_SHA, prior.ID, prior.TASK, prior.ARTIFACT, stack)
        if study.envelope(prior.TASK['identity'])['charged'] != prior.TASK['limits'] or result['pairs'] != N:
            raise ValueError('the complete original range score is required')
        values = {key: study.input(key, raw=True) for key in
                  ('rinex', 'navigation', 'orbit', 'anchor', 'path', 'continuity', 'metric', 'original')}
    values.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, score=prior.RESULT, qualification=REQUEST, qualification_tests=XML)
    for key, value in values.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=carrier.WALL_S), root).prepare(root)['limits']


def evaluate(task, context):
    from .carrier_range_remainder import bound_score_remainder, position_cap
    from .esa_carrier_phase_support import phase_epochs
    from .esa_final_orbit_replay import interpolate_orbit
    from .esa_precise_gps_support import read_orbit_positions
    from .esa_rinex_code import read_navigation

    if context.manifest['scope'] != SCOPE or {k: v for k, v in task.items() if k not in ('index', 'shard')} != TASK:
        raise ValueError('the frozen carrier geometry domain task is required')
    context.charge(bound_calls=1, bound_steps=1)

    def read(key):
        return context.input_path(key).read_bytes()

    def product(key):
        return gzip.decompress(read(key)).decode('ascii')

    epochs = list(phase_epochs(gzip.decompress(read('rinex'))))
    navigation, _ = read_navigation(product('navigation'))
    orbit = read_orbit_positions(product('orbit'))
    anchor, path, continuity, saved, score, metric = [json.loads(read(key)) for key in
        ('anchor', 'path', 'continuity', 'original', 'score', 'metric')]
    rows = saved['rows']
    if (len(rows) != N or len(path) != N or not all(a['seconds'] == b['seconds'] for a, b in zip(path, rows, strict=True))
            or abs(epochs[carrier.START]['seconds']-anchor['time_s']) > .001
            or [epochs[carrier.START]['seconds'], epochs[carrier.END]['seconds']] != score['endpoint_gps_s']):
        raise ValueError('the original position and score grid are required')
    max_altitude = math.ceil(max(abs(anchor['height_m']), *(abs(row['position'][2]) for row in path)))
    radii = []
    counts = []
    for index, row in enumerate(rows, carrier.START):
        context.charge(bound_calls=1, bound_steps=66)
        a, b = epochs[index:index+2]
        if b['seconds'] != row['seconds'] or a['week'] != b['week'] or b['week'] != anchor['gps_week']:
            raise ValueError('unaltered recorded endpoint times are required')
        prns = row['common_satellites']
        _, endpoints = carrier.paired_satellite_states(a, b, continuity['result']['per_pair'][index]['accepted_prns'],
                                                       prns, navigation)
        counts.append(len(prns))
        radii.extend(math.hypot(*interpolate_orbit(orbit[prn], state[2])) for side in endpoints
                     for prn, state in zip(prns, side, strict=True))
    context.charge(bound_calls=1, bound_steps=N)
    if not all(20e6 < radius < 40e6 for radius in radii) or len(radii) != 2*score['bound']['range_values']:
        raise ValueError('the validated final satellite radii must contain every score range')
    weights = score['bound']['dual_weights']
    time_bounds = [score['endpoint_gps_s'][0], *score['ground_anchors_gps_s'], score['endpoint_gps_s'][1]]
    unit = bound_score_remainder(weights, counts, metric, max_altitude, 1)
    cap = position_cap(time_bounds, 1., .002)
    example = bound_score_remainder(weights, counts, metric, max_altitude, cap)
    result = dict(pairs=N, range_endpoints=len(radii), max_absolute_path_height_m=max_altitude,
                  measured_final_satellite_radius_m=[min(radii), max(radii)], metric=metric,
                  exact_score_bound_per_square_m=str(unit['max_score_remainder']),
                  score_bound_per_square_m=float(unit['max_score_remainder']),
                  anchor_times_gps_s=time_bounds, representative_axis_cap_m=float(cap),
                  representative_score_remainder=float(example['max_score_remainder']), score_gap=score['score_gap'],
                  scope='Fixed satellite, atmosphere and clock terms; geodetic-to-range geometry only',
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
            raise ValueError('sealed complete remainder evidence required')
        _write_equal(root/RESULT, encoded(dict(result, parent_sha256=anchors.PARENT_SHA, completion=study.completion)))
    return {k: v for k, v in result.items() if k != 'exact_score_bound_per_square_m'}


if __name__ == '__main__':
    from functools import partial

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    result = {'request': partial(qualification, verify=False), 'prepare': prepare, 'report': report,
              'recover': partial(carrier.recover_signature, study_id=ID, task=TASK)}[action](Path.cwd())
    print(json.dumps(result, sort_keys=True))
