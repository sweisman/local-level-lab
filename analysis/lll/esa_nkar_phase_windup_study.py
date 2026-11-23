# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay ideal antenna phase variation on the fixed ESA and Nuuk ranges."""

import argparse
from contextlib import ExitStack, closing
import gzip
import io
import json
from math import degrees, fsum, asin
from pathlib import Path

from . import esa_nkar_score_study as nkar
from . import esa_nkar_antenna_study as antenna
from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, _parent
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded


ID = 'esa-nkar-phase-windup-v1'
SCOPE = 'Ideal GPS phase wind-up replay on the sealed aircraft and Nuuk range score'
FOLDER = nkar.carrier.FOLDER
PLAN = FOLDER+'ESA_NKAR_PHASE_WINDUP_PLAN.md'
REQUEST = FOLDER+'esa-nkar-phase-windup-qualification.json'
XML = FOLDER+'esa-nkar-phase-windup-tests.xml'
RESULT = FOLDER+'esa-nkar-phase-windup-result.json'
ARTIFACT = 'phase-windup.json'
ANTENNA_SHA = 'cf7774271aaf6f3907383f0eadcb5b989a5e9359fa6ae3bde4ceaa32d2c724c4'
TASK = dict(identity='phase-windup', input_key='attitude', payload=dict(seconds=120),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=361, bound_steps=1+132*360))
TESTS = ('test_gnss_phase_windup.py', 'test_esa_phase_windup_budget.py', 'test_gnss_antenna.py',
         'test_esa_nkar_score.py', 'test_carrier_score_cadence.py')
REQUIRED = ('test_fractional_phase_rotates_with_upright_receiver_for_any_ray',
            'test_boresight_phase_and_branch_crossing_use_signed_conventions',
            'test_phase_fails_on_null_dipole_or_invalid_ray',
            'test_ideal_phase_gradient_matches_independent_finite_rotations',
            'test_final_station_range_includes_clock_and_delay_with_expected_sign')


def qualification(root, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN,
                                    *(f'analysis/tests/{test}' for test in TESTS)))
    environment = runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=REQUIRED, minimum_tests=13)
    return sources, environment


def prepare(root):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original finite phase wind-up study')
    sources, environment = qualification(root, True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with ExitStack() as stack:
        parent, row = _parent(root, antenna.RESULT, ANTENNA_SHA, antenna.ID, antenna.TASK, antenna.ARTIFACT, stack)
        if (parent.envelope(antenna.TASK['identity'])['charged'] != TASK['limits']
                or row['pairs'] != 240 or row['matched_intervals'] != 120):
            raise ValueError('the complete sealed antenna replay is required')
        values = {key: parent.input(key, raw=True) for key in (
            'attitude', 'rinex', 'navigation', 'orbit', 'clock', 'path',
            'anchor', 'continuity', 'ground', 'score', 'ranges', 'station')}
    if digest(values['attitude']) != antenna.ATTITUDE_SHA:
        raise ValueError('the verified flight-day satellite attitudes are required')
    values.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, qualification=REQUEST, qualification_tests=XML, antenna_reference=antenna.RESULT)
    for key, value in values.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
        inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1, maximum_wall_s=nkar.carrier.WALL_S),
        root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .esa_carrier_phase_support import phase_epochs
    from .esa_nkar_score import final_range_model, reference_pair
    from .esa_relative_clock_replay import _clock_records
    from .esa_rinex_code import read_navigation
    from .esa_rinex_code_comparison import coordinates
    from .gnss_orbex import attitude_series
    from .gnss_phase_windup import fractional_phase, range_change
    from .gnss_position import ecef, geodetic, local_rotation
    from .shared_motion_carrier import centre

    if context.manifest['scope'] != SCOPE or {k: v for k, v in task.items() if k not in ('index', 'shard')} != TASK:
        raise ValueError('the fixed phase replay is required')
    context.charge(bound_calls=1, bound_steps=1)

    def raw(name):
        return context.input_path(name).read_bytes()

    def product(name):
        return gzip.decompress(raw(name)).decode('ascii')

    saved, score, original, ground, path, anchor, continuity = [json.loads(raw(key)) for key in
        ('ranges', 'score', 'station', 'ground', 'path', 'anchor', 'continuity')]
    prns = {prn for row in saved['rows'] for prn in row['common_satellites']}
    start, stop = score['endpoint_gps_s']
    attitudes = attitude_series(io.StringIO(product('attitude')), prns, week=nkar.intake.WEEK,
                                first=start-1, last=stop)
    navigation, atmosphere = read_navigation(product('navigation'))
    orbits = nkar.orbit.read_orbit_positions(product('orbit'))
    clocks = _clock_records(product('clock'))
    epochs = list(phase_epochs(gzip.decompress(raw('rinex'))))
    flags = continuity['result']['per_pair']

    def sample(receiver, axes, satellite, transmit, prn):
        satellite = np.asarray(satellite)
        ray = satellite-receiver
        ray /= np.linalg.norm(ray)
        north, east, up = axes
        attitude = attitudes[prn](transmit)
        if attitude.apply(-satellite)[2]/np.linalg.norm(satellite) < .999:
            raise ValueError('the satellite must point toward Earth')
        tx = attitude.inv().apply(np.eye(3)[:2])
        elevation = degrees(asin(float(np.clip(up@ray, -1., 1.))))
        return fractional_phase(ray, tx, [east, north]), elevation

    def intervals(samples, satellites):
        return centre([range_change(samples[0][prn][0], samples[1][prn][0]) for prn in satellites])

    air, minima, earlier = [], [], coordinates([anchor])[0]
    for index, (row, fixed) in enumerate(zip(saved['rows'], path, strict=True), nkar.carrier.START):
        context.charge(bound_calls=1, bound_steps=132)
        first, last = epochs[index:index+2]
        if (last['seconds'] != fixed['seconds'] or last['seconds'] != row['seconds']
                or last['seconds']-first['seconds'] != .5 or fixed['satellites'] != row['satellites']):
            raise ValueError('the fixed aircraft path does not match the original carrier grid')
        _, states = nkar.carrier.paired_satellite_states(first, last, flags[index]['accepted_prns'],
                                                         row['satellites'], navigation)
        endpoints = []
        for position, side in zip((earlier, fixed['position']), states, strict=True):
            receiver, axes = ecef(*position), local_rotation(*position[:2])
            times = dict(zip(row['satellites'], (state[2] for state in side), strict=True))
            endpoints.append({prn: sample(receiver, axes, nkar.orbit.interpolate_orbit(orbits[prn], times[prn]),
                                          times[prn], prn) for prn in row['common_satellites']})
        minima.append(min(value[1] for side in endpoints for value in side.values()))
        air.append(dict(zip(row['common_satellites'], intervals(endpoints, row['common_satellites']), strict=True)))
        earlier = fixed['position']

    receiver = np.asarray(ground['antenna_ecef_m'])
    axes = local_rotation(*geodetic(receiver)[:2])
    station = {row['seconds']: row for row in ground['epochs']}
    endpoints = []

    def collect(candidates, transmit, satellite):
        endpoints.append({prn: sample(receiver, axes, pos, time, prn)
                          for prn, time, pos in zip(candidates, transmit, satellite, strict=True) if prn in prns})

    model = final_range_model(navigation, atmosphere, orbits, clocks, receiver, on_endpoint=collect)
    matched = []
    for row in original['intervals']:
        context.charge(bound_calls=1, bound_steps=132)
        satellites, i = row['satellites'], row['first']
        endpoints.clear()
        candidates = sorted(air[i].keys() & air[i+1].keys())
        baseline = reference_pair(station[row['start_gps_s']], station[row['stop_gps_s']], candidates, model)
        if (list(baseline) != satellites or not np.allclose(centre(list(baseline.values())), row['ground_range_m'],
                                                         atol=1e-12, rtol=0.)):
            raise ValueError('the original Nuuk range replay differs')
        matched.append(dict(start_gps_s=row['start_gps_s'], satellites=satellites,
            air=centre([air[i][prn]+air[i+1][prn] for prn in satellites]).tolist(),
            ground=intervals(endpoints, satellites).tolist()))

    def join(rows, key):
        return np.concatenate([r[key] for r in rows])

    weights = join(original['intervals'], 'aggregate_weights')
    difference = join(original['intervals'], 'air_range_m')-join(original['intervals'], 'ground_range_m')
    phase_air, phase_ground = join(matched, 'air'), join(matched, 'ground')
    corrected = difference-phase_air+phase_ground
    shifts = dict(air=float(-weights@phase_air), ground=float(weights@phase_ground))
    full_air = [value for row in air for value in row.values()]
    full_shift = -fsum(w*x for w, x in zip(score['bound']['dual_weights'], full_air, strict=True))
    result = dict(passed=True, pairs=len(air), matched_intervals=len(matched), matched_values=len(weights),
        score_gap=score['score_gap'], signed_shifts=shifts, signed_total_shift=fsum(shifts.values()),
        signed_full_air_shift=full_shift, minimum_air_elevation_deg=min(minima), per_pair_minima_deg=minima,
        rms_m={k: float(np.sqrt(np.mean(v**2))) for k, v in dict(
            uncorrected=difference, corrected=corrected, air=phase_air, ground=phase_ground).items()},
        air=[list(row.values()) for row in air], matched=matched, new_fits=0, protected_reads=0,
        aircraft_error_cap_established=False, scientific_decision='abstain')
    context.save(ARTIFACT, result)
    return result


def report(root):
    from .studies.closed import ClosedStudy

    prefix, identity = 'data/'+ID, TASK['identity']
    with ExitStack() as stack:
        study = stack.enter_context(closing(ClosedStudy(root, prefix)))
        continuation = root/(prefix+'-recovery')
        if continuation.is_dir():
            from .studies.combined_task_evidence import inspect

            origin = inspect(root, continuation)['selected'][identity]['origin']
            if origin != prefix:
                study = stack.enter_context(closing(ClosedStudy(root, origin, store=study.store)))
        envelope, result = study.envelope(identity), study.artifact(identity, ARTIFACT)
        if envelope['charged'] != TASK['limits'] or envelope['result'] != result or not result['passed']:
            raise ValueError('the complete charged phase replay is required')
        _write_equal(root/RESULT, encoded(dict(result, completion=study.completion, antenna_sha256=ANTENNA_SHA)))
    return {k: v for k, v in result.items() if k not in ('air', 'matched', 'per_pair_minima_deg')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report', 'recover'))
    args = parser.parse_args()
    root = Path.cwd()
    if args.action == 'request':
        result = qualification(root, False)
    elif args.action == 'prepare':
        result = prepare(root)
    elif args.action == 'recover':
        result = nkar.carrier.recover_signature(root, study_id=ID, task=TASK)
    else:
        result = report(root)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
