# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay published GPS antenna terms on the frozen two-minute ESA 187 score."""
import argparse
from contextlib import ExitStack, closing
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path

from . import esa_nkar_score_study as nkar
from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, _parent
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import encoded


ID = 'esa-nkar-antenna-v2'
SCOPE = 'GPS transmitter and Nuuk Museum antenna effects on the saved ESA 187 carrier score'
PLAN = nkar.carrier.FOLDER+'ESA_NKAR_ANTENNA_PLAN_V2.md'
REQUEST = nkar.carrier.FOLDER+'esa-nkar-antenna-qualification-v2.json'
XML = nkar.carrier.FOLDER+'esa-nkar-antenna-tests-v2.xml'
RESULT = nkar.carrier.FOLDER+'esa-nkar-antenna-result-v2.json'
ARTIFACT = 'nkar-antenna.json'
NKAR_SHA = 'ab8fcb08bbf97d43538e0020649fce3f810bd4d488b1c52dadbc93ae5690aa75'
STATION = 'SEPPOLANT_X_MF  NONE'
ATX = {
    'igs20_2247.atx': '1fb7464228e0dcdb6bc129796f55c70e08cf68c7cacd01fb48335d41930690f6',
    'igs20_2270.atx': '11331130a9d5ed7dfc19e185eee2bf5545bad26fa86932a5e15367cbb4b6c7ef',
}
ATTITUDE_SHA = 'fdad4fb04be1f9706643132db6d7e2d458486cf9a27eb994a3acb1d33a8c77dd'
TASK = dict(identity='nkar-antenna', input_key='calibration', payload=dict(seconds=120),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=361, bound_steps=1+132*360))


def qualification(root, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    tests = ('test_gnss_antenna.py', 'test_esa_nkar_score.py', 'test_carrier_score_cadence.py')
    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN,
                                   *(f'analysis/tests/{test}' for test in tests)))
    environment = runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=(
        'test_offset_and_pcv_signs_use_transmitter_and_receiver_axes',
        'test_azimuth_wraps_and_interpolates_both_axes',
        'test_range_correction_validates_boresight_on_orbit_position_tuples',
        'test_attitude_is_scalar_first_ecef_to_body_and_sign_invariant',
        'test_attitude_refuses_to_bridge_missing_samples',
        'test_final_station_range_includes_clock_and_delay_with_expected_sign'), minimum_tests=10)
    return sources, environment


def prepare(root, earlier_antex, later_antex, attitude):
    from .gnss_antenna import read_patterns
    from .studies.artifacts import digest
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original finite antenna study')
    sources, environment = qualification(root, True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    attitude_bytes = attitude.read_bytes()
    if digest(attitude_bytes) != ATTITUDE_SHA:
        raise ValueError('the pinned July 6 CODE attitude product is required')
    orbit, bound = nkar.orbit, nkar.bound
    with ExitStack() as stack:
        flight, ranges = _parent(root, orbit.RESULT, bound.PRODUCT_SHA, orbit.ID, orbit.TASK, orbit.ARTIFACT, stack)
        scoring, score = _parent(root, bound.RESULT, nkar.BOUND_SHA, bound.ID, bound.TASK, bound.ARTIFACT, stack)
        station, ground = _parent(root, nkar.RESULT, NKAR_SHA, nkar.ID, nkar.TASK, nkar.ARTIFACT, stack)
        for study, module in ((flight, orbit), (scoring, bound), (station, nkar)):
            if study.envelope(module.TASK['identity'])['charged'] != module.TASK['limits']:
                raise ValueError('complete sealed parent accounting required')
        values = {key: flight.input(key, raw=True) for key in ('rinex', 'navigation', 'orbit', 'clock', 'path',
                                                               'anchor', 'continuity')}
        if (any(station.input(key, raw=True) != values[key] for key in ('navigation', 'orbit', 'clock'))
                or len(ranges['rows']) != 240 or ground['matched_intervals'] != 120
                or score['endpoint_gps_s'] != list(nkar.intake.SCORE_WINDOW)):
            raise ValueError('the same frozen carrier grid and satellite products are required')
        values['ground'] = station.input('ground', raw=True)

    prns = {prn for row in ranges['rows'] for prn in row['common_satellites']}
    calibrations = []
    for source, sha in zip((earlier_antex, later_antex), ATX.values(), strict=True):
        with source.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != sha:
                raise ValueError('the pinned IGS20 calibration releases are required')
        with source.open(encoding='ascii') as stream:
            calibrations.append(read_patterns(stream, prns=prns, receiver=STATION,
                                              start=(2023, 7, 6, 11, 56, 53), stop=(2023, 7, 6, 11, 58, 55)))
    if calibrations[0] != calibrations[1]:
        raise ValueError('flight-day antenna patterns differ between the adjacent releases')
    patterns = {str(key): [vehicle, asdict(l1), asdict(l2)] for key, (vehicle, l1, l2) in calibrations[0].items()}
    values.update(calibration=encoded(dict(patterns=patterns, antex_sha256=ATX, attitude_sha256=ATTITUDE_SHA)),
                  attitude=attitude_bytes, recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, qualification=REQUEST, qualification_tests=XML, ranges=orbit.RESULT,
                  score=bound.RESULT, station=nkar.RESULT)
    for key, value in values.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=nkar.carrier.WALL_S), root).prepare(root)['limits']


def evaluate(task, context):
    import io
    from math import fsum

    import numpy as np

    from .esa_carrier_phase_support import phase_epochs
    from .esa_nkar_score import final_range_model, reference_pair
    from .esa_relative_clock_replay import _clock_records
    from .esa_rinex_code import read_navigation
    from .esa_rinex_code_comparison import coordinates
    from .gnss_antenna import Pattern, phase_corrections
    from .gnss_orbex import attitude_series
    from .gnss_position import ecef
    from .shared_motion_carrier import centre

    if context.manifest['scope'] != SCOPE or {k: v for k, v in task.items() if k not in ('index', 'shard')} != TASK:
        raise ValueError('the frozen antenna replay is required')
    context.charge(bound_calls=1, bound_steps=1)

    def raw(name):
        return context.input_path(name).read_bytes()

    def product(name):
        return gzip.decompress(raw(name)).decode('ascii')

    calibration, saved, score, original, ground, path, anchor, continuity = [json.loads(raw(key)) for key in
        ('calibration', 'ranges', 'score', 'station', 'ground', 'path', 'anchor', 'continuity')]
    patterns = {k: tuple(Pattern(**p) for p in v[1:]) for k, v in calibration['patterns'].items()}
    prns = {int(prn) for prn in patterns if prn != STATION}
    start, stop = score['endpoint_gps_s']
    attitudes = attitude_series(io.StringIO(product('attitude')), prns, week=nkar.intake.WEEK,
                                first=start-1, last=stop)
    navigation, atmosphere = read_navigation(product('navigation'))
    orbits = nkar.orbit.read_orbit_positions(product('orbit'))
    clocks = _clock_records(product('clock'))
    epochs = list(phase_epochs(gzip.decompress(raw('rinex'))))
    flags = continuity['result']['per_pair']

    def correction(receiver, satellite, transmit, prn, receiver_pattern=None):
        attitude = attitudes[prn](transmit)
        return phase_corrections(receiver, satellite, attitude, patterns[str(prn)], receiver_pattern)

    air, earlier = [], coordinates([anchor])[0]
    for index, (row, fixed) in enumerate(zip(saved['rows'], path, strict=True), nkar.carrier.START):
        context.charge(bound_calls=1, bound_steps=132)
        first, last = epochs[index:index+2]
        if (last['seconds'] != fixed['seconds'] or last['seconds'] != row['seconds']
                or last['seconds']-first['seconds'] != .5 or fixed['satellites'] != row['satellites']):
            raise ValueError('the sealed aircraft range path does not align')
        _, states = nkar.carrier.paired_satellite_states(first, last, flags[index]['accepted_prns'],
                                                         row['satellites'], navigation)
        endpoint = []
        for position, side in zip((earlier, fixed['position']), states, strict=True):
            receiver = ecef(*position)
            times = dict(zip(row['satellites'], (state[2] for state in side), strict=True))
            endpoint.append(np.asarray([correction(receiver, nkar.orbit.interpolate_orbit(orbits[prn], times[prn]),
                                                    times[prn], prn)[0] for prn in row['common_satellites']]))
        air.append(dict(zip(row['common_satellites'], centre(endpoint[1]-endpoint[0]), strict=True)))
        earlier = fixed['position']

    antenna = np.asarray(ground['antenna_ecef_m'])
    station = {row['seconds']: row for row in ground['epochs']}
    endpoints = []

    def collect(candidates, transmit, satellite):
        endpoints.append({prn: correction(antenna, pos, time, prn, patterns[STATION])
                          for prn, time, pos in zip(candidates, transmit, satellite, strict=True) if prn in prns})

    model = final_range_model(navigation, atmosphere, orbits, clocks, antenna, on_endpoint=collect)
    matched = []
    for row in original['intervals']:
        context.charge(bound_calls=1, bound_steps=132)
        prns = row['satellites']
        first, last = row['start_gps_s'], row['stop_gps_s']
        endpoints.clear()
        i = row['first']
        candidates = sorted(air[i].keys() & air[i+1].keys())
        baseline = reference_pair(station[first], station[last], candidates, model)
        if (list(baseline) != prns or not np.allclose(centre(list(baseline.values())), row['ground_range_m'],
                                                    atol=1e-12, rtol=0.)):
            raise ValueError('the sealed station ranges must reproduce')
        delta = np.asarray([endpoints[1][prn]-endpoints[0][prn] for prn in prns])
        air_delta = centre([air[i][prn]+air[i+1][prn] for prn in prns])
        ground_tx, ground_rx = map(centre, delta.T)
        matched.append(dict(start_gps_s=first, satellites=prns, weights=row['aggregate_weights'],
                            air_range_m=row['air_range_m'], ground_range_m=row['ground_range_m'],
                            air_transmitter_m=air_delta.tolist(), ground_transmitter_m=ground_tx.tolist(),
                            ground_receiver_m=ground_rx.tolist()))

    def join(name):
        return np.concatenate([r[name] for r in matched])

    def rms(values):
        return float(np.sqrt(np.mean(values**2)))

    joined_air, joined_ground, tx_air, tx_ground, rx_ground, weights = map(
        join, ('air_range_m', 'ground_range_m', 'air_transmitter_m', 'ground_transmitter_m', 'ground_receiver_m', 'weights'))
    raw_difference = joined_air-joined_ground
    shift = dict(air_transmitter=float(-weights@tx_air), ground_transmitter=float(weights@tx_ground),
                 ground_receiver=float(weights@rx_ground))
    total = fsum(shift.values())
    full_air = [value for row in air for value in row.values()]
    full_shift = -fsum(w*x for w, x in zip(score['bound']['dual_weights'], full_air, strict=True))
    result = dict(pairs=240, matched_intervals=len(matched), matched_values=len(weights), score_gap=score['score_gap'],
                  signed_air_minus_ground_score_shifts=shift, signed_total_shift=total,
                  signed_shift_per_gap=total/score['score_gap'], signed_full_air_transmitter_score_shift=full_shift,
                  rms_m=dict(uncorrected=rms(raw_difference), satellite_only=rms(raw_difference-tx_air+tx_ground),
                             satellite_and_ground=rms(raw_difference-tx_air+tx_ground+rx_ground),
                             air_transmitter=rms(tx_air), ground_transmitter=rms(tx_ground), ground_receiver=rms(rx_ground)),
                  calibration=calibration['antex_sha256'], attitude_sha256=calibration['attitude_sha256'],
                  matched=matched, new_fits=0, protected_reads=0, aircraft_error_cap_established=False,
                  scientific_decision='abstain', passed=True)
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
            raise ValueError('complete antenna replay evidence required')
        _write_equal(root/RESULT, encoded(dict(result, completion=study.completion, nkar_sha256=NKAR_SHA)))
    return {k: v for k, v in result.items() if k != 'matched'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report', 'recover'))
    parser.add_argument('--antex', type=Path, nargs=2)
    parser.add_argument('--attitude', type=Path)
    args = parser.parse_args()
    root = Path.cwd()
    if args.action == 'prepare':
        if args.antex is None or args.attitude is None:
            parser.error('prepare requires two ANTEX releases and the flight-day attitude product')
        result = prepare(root, *args.antex, args.attitude)
    elif args.action == 'request':
        result = qualification(root, False)
    elif args.action == 'recover':
        result = nkar.carrier.recover_signature(root, study_id=ID, task=TASK)
    else:
        result = report(root)
    print(json.dumps(result, sort_keys=True))
