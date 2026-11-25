# SPDX-License-Identifier: AGPL-3.0-or-later
"""Translate an installed antenna's angular response into the fixed ESA range score."""

import argparse
from contextlib import ExitStack, closing
import gzip
import io
import json
import math
from pathlib import Path

from . import esa_carrier_lever_sensitivity as lever
from . import esa_nkar_phase_windup_study as phase
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-installed-pattern-v1'
SCOPE = 'Conditional static installed antenna slope sensitivity on ESA development recording 187'
PLAN = phase.FOLDER+'ESA_INSTALLED_PATTERN_PLAN.md'
RESULT = phase.FOLDER+'esa-installed-pattern-result.json'
TEST = 'analysis/tests/test_esa_installed_pattern.py'
TESTS = ('test_installed_pattern_sensitivity_centers_the_interval_weights',
         'test_installed_pattern_ray_change_is_stable_for_tiny_and_opposed_rays')
REQUEST, XML = (f'data/{ID}-inputs/{name}' for name in ('qualification-v2.json', 'tests-v2.xml'))
LEVER_SHA = '0a449aac45cffef41ac3fcbc9b52ab5ebc79b8ebb5ce170fcd2688e88c9bff84'
WINDUP_SHA = '103daedec51b2bfd5c82a94bd531572b5ec93195322a437ad69952d43f363244'
WINDUP = phase.FOLDER+'esa-phase-windup-budget.json'
INTERVALS, RANGES = 240, 2496
TASK = dict(identity='installed-pattern', input_key='score', payload={}, limits=dict(
    native_calls=0, packet_visits=0, bound_calls=2+INTERVALS,
    bound_steps=lever.MAX_PACKETS+132*INTERVALS+6*RANGES))


def angular_change(first, last):
    import numpy as np

    return np.arctan2(np.linalg.norm(np.cross(first, last), axis=-1), np.sum(first*last, axis=-1))


def slope_coefficient(angular_steps, weights):
    """Apply the transpose of satellite-mean removal before the triangle bound."""
    count = 0
    terms = []
    for angles in angular_steps:
        support = len(angles)
        subset = weights[count:count+support]
        if support < 2 or len(subset) != support:
            raise ValueError('exact centered satellite support required')
        center = math.fsum(subset)/support
        terms.extend(abs(weight-center)*angle for weight, angle in zip(subset, angles, strict=True))
        count += support
    if count != len(weights):
        raise ValueError('unexpected weight support')
    return math.fsum(terms)


def qualification(root, *, check=False):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST))
    environment = runtime_environment()
    if not check:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources, environment


def prepare(root):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('preserve the installed antenna sensitivity freeze')
    sources, environment = qualification(root, check=True)
    records = {'lever_reference': lever.RESULT, 'phase_budget': WINDUP, 'antenna_reference': phase.antenna.RESULT}
    for path, sha in zip(records.values(), (LEVER_SHA, WINDUP_SHA, phase.ANTENNA_SHA), strict=True):
        if digest((root/path).read_bytes()) != sha:
            raise ValueError(f'exact archived report required: {path}')
    with ExitStack() as stack:
        antenna, row = phase._parent(root, phase.antenna.RESULT, phase.ANTENNA_SHA,
                                     phase.antenna.ID, phase.antenna.TASK, phase.antenna.ARTIFACT, stack)
        if row['pairs'] != INTERVALS or row['matched_intervals'] != 120:
            raise ValueError('original full and ground-covered range supports required')
        inputs = ('rinex', 'navigation', 'orbit', 'path', 'anchor', 'continuity', 'score', 'ranges', 'station')
        frozen = {key: antenna.input(key, raw=True) for key in inputs}
        study = stack.enter_context(closing(ClosedStudy(root, 'data/'+lever.ID)))
        receipt = json.loads((root/lever.RESULT).read_bytes())
        envelope = study.envelope(lever.TASK['identity'])
        if (study.completion != receipt['completion'] or envelope['charged'] != lever.TASK['limits']
                or not envelope['result']['passed']):
            raise ValueError('completed gyro motion sensitivity required')
        frozen.update(gyro=study.input('gyro', raw=True), timing=study.input('fixed', raw=True))
    recovery, tests = checked(root, phase.RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    files = dict(records, plan=PLAN, qualification=REQUEST, tests=XML)
    for key, value in dict(frozen, recovery=recovery, recovery_tests=tests,
                           recovery_policy=encoded(phase.RECOVER)).items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, value)
        files[key] = path
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=files, sources=sources,
                      tasks=[TASK], workers=1, threads=1, maximum_wall_s=180)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np
    from scipy.spatial.transform import Rotation

    from .esa_carrier_phase_support import phase_epochs
    from .esa_rinex_code import read_navigation
    from .esa_rinex_code_comparison import coordinates
    from .gnss_position import ecef

    declared = {key: val for key, val in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('the fixed installed antenna sensitivity is required')

    def raw(key):
        return context.input_path(key).read_bytes()

    def read(key):
        return json.loads(raw(key))

    def product(key):
        return gzip.decompress(raw(key)).decode('ascii')

    context.charge(bound_calls=1, bound_steps=lever.MAX_PACKETS)
    score, ranges, path, anchor, timing = (read(key) for key in ('score', 'ranges', 'path', 'anchor', 'timing'))
    original, windup = read('station'), read('phase_budget')
    start, stop = score['endpoint_gps_s']
    times = start+np.arange(INTERVALS+1)/2
    if (len(ranges['rows']) != INTERVALS or times[-1] != stop
            or abs(start-timing['start_gps_s']) > .001 or timing['source_id'] != 'esa-99f1530c3eda4318'
            or original['matched_intervals'] != 120 or score['score_gap'] != windup['score_gap']):
        raise ValueError('original anchored gyro and complete range score required')
    with np.load(io.BytesIO(raw('gyro')), allow_pickle=False) as gyro:
        if len(gyro['increments']) > lever.MAX_PACKETS:
            raise ValueError('saved gyro packet limit exceeded')
        relative = Rotation.from_matrix(lever.relative_rotations(gyro['edges'], gyro['increments'], start, times[1:]))
    rotations = Rotation.concatenate((Rotation.identity(1), relative))
    turn = (rotations[:-1].inv()*rotations[1:]).magnitude()

    navigation, _ = read_navigation(product('navigation'))
    orbit = phase.nkar.orbit
    orbits = orbit.read_orbit_positions(product('orbit'))
    epochs = list(phase_epochs(gzip.decompress(raw('rinex'))))
    flags = read('continuity')['result']['per_pair']
    earlier = coordinates([anchor])[0]
    ray_steps = []
    for index, (row, fixed) in enumerate(zip(ranges['rows'], path, strict=True), phase.nkar.carrier.START):
        context.charge(bound_calls=1, bound_steps=132)
        first, last = epochs[index:index+2]
        offset = index-phase.nkar.carrier.START
        if (first['seconds'] != times[offset] or last['seconds'] != times[offset+1]
                or last['seconds'] != fixed['seconds'] or last['seconds'] != row['seconds']
                or fixed['satellites'] != row['satellites']):
            raise ValueError('the original aircraft range and orbit support are required')
        _, states = phase.nkar.carrier.paired_satellite_states(first, last, flags[index]['accepted_prns'],
                                                               row['satellites'], navigation)
        rays = []
        for position, side in zip((earlier, fixed['position']), states, strict=True):
            receiver = np.asarray(ecef(*position))
            transmit = dict(zip(row['satellites'], (state[2] for state in side), strict=True))
            rays.append(np.array([orbit.interpolate_orbit(orbits[prn], transmit[prn])-receiver
                                  for prn in row['common_satellites']]))
        ray_steps.append(angular_change(*rays))
        earlier = fixed['position']

    context.charge(bound_calls=1, bound_steps=6*RANGES)
    full = score['bound']['dual_weights']
    covered = original['projected_weights']
    if len(full) != RANGES or len(covered) != RANGES or sum(map(len, ray_steps)) != RANGES:
        raise ValueError('original full and projected weights required')
    missed = [x-y for x, y in zip(full, covered, strict=True)]
    gap, example = score['score_gap'], windup['covered_example_score_allowance']
    cases = []
    for frame in (0., lever.ANGULAR_ALLOWANCE_RADS):
        angular_cap = [min(np.pi, step+frame/2) for step in turn]
        steps = [np.minimum(np.pi, ray+limit) for ray, limit in zip(ray_steps, angular_cap, strict=True)]
        factors = {key: slope_coefficient(steps, weights)
                   for key, weights in (('full', full), ('covered', covered), ('uncovered', missed))}
        cases.append(dict(extra_frame_rate_rads=frame, score_per_metre_per_radian=factors,
                          full_gap_minimum_mm_per_deg=1000*math.radians(1)*gap/factors['full'],
                          covered_example_minimum_mm_per_deg=1000*math.radians(1)*example/factors['covered']))
    def angular_summary(values):
        degrees = np.degrees(values)
        return dict(median=float(np.median(degrees)), maximum=float(np.max(degrees)),
                    rms=float(np.sqrt(np.mean(degrees**2))))

    return dict(passed=True, scientific_decision='abstain', recording=187, intervals=len(ray_steps), ranges=RANGES,
                score_gap=gap, covered_example_allowance=example, gyro_step_deg=angular_summary(turn),
                sightline_step_deg=angular_summary(np.concatenate(ray_steps)), cases=cases,
                new_fits=0, protected_reads=0, original_reads=0, installed_response_measured=False)


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        envelope = study.envelope(TASK['identity'])
        if envelope['charged'] != TASK['limits'] or not envelope['result']['passed']:
            raise ValueError('completed installed antenna sensitivity required')
        result = dict(envelope['result'], completion=study.completion, charged=envelope['charged'])
    _write_equal(root/RESULT, encoded(result))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = {'request': qualification, 'prepare': prepare, 'report': report}[parser.parse_args().action]
    print(json.dumps(action(Path.cwd()), sort_keys=True))
