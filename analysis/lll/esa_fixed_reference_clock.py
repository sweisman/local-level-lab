# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay the frozen Reykjavík comparison under explicit GPS clock conventions."""

import argparse
from contextlib import ExitStack, closing
import gzip
import json
from pathlib import Path

from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, WALL_S, _parent
from .esa_fixed_reference_phase import ARTIFACT as PRIOR_ARTIFACT
from .esa_fixed_reference_phase import ID as PRIOR_ID, RESULT as PRIOR, TASK as PRIOR_TASK, unpack
from .esa_rinex_window import FOLDER
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import encoded
from .studies.closed import ClosedStudy


ID = 'esa-fixed-reference-clock-v1'
SCOPE = 'Clock convention sensitivity of the frozen Reykjavík relative phase path'
PLAN = FOLDER+'ESA_FIXED_REFERENCE_CLOCK_PLAN.md'
RESULT = FOLDER+'esa-fixed-reference-clock-result.json'
REQUEST = FOLDER+'esa-fixed-reference-clock-qualification.json'
XML = FOLDER+'esa-fixed-reference-clock-tests.xml'
PRIOR_SHA = '07e09f353f856629d186710f4b68658632938f49ee6e0b60ec41595835cee316'
ARTIFACT = 'clock-comparison.json'
TESTS = ('test_clock_correction_preserves_transmit_time_when_epoch_is_retimed',
         'test_two_receivers_cancel_constant_ambiguities_and_ionosphere_in_phase_change')
ARMS = ('original', 'consistent', 'observations_only')
TASK = dict(identity='reykjavik-clock-conventions', input_key='previous', payload=dict(arms=list(ARMS)),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=122, bound_steps=2621))


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_rinex_clock_correction.py',
             'analysis/tests/test_differential_phase.py')
    sources, env = source_closure(root, seeds), runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=env, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=env, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources, env


def prepare(root):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original finite clock allowance')
    sources, env = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=env,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with ExitStack() as stack:
        parent, row = _parent(root, PRIOR, PRIOR_SHA, PRIOR_ID, PRIOR_TASK, PRIOR_ARTIFACT, stack)
        if parent.envelope(PRIOR_TASK['identity'])['charged'] != PRIOR_TASK['limits']:
            raise ValueError('the original completed phase ledger is required')
        values = {key: parent.input(key, raw=True) for key in ('air', 'station', 'navigation', 'ppp')}
        values['previous'] = encoded(row)
    values.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, prior=PRIOR, qualification=REQUEST, qualification_tests=XML)
    for key, value in values.items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, value)
        inputs[key] = path
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=WALL_S), root).prepare(root)['limits']


def evaluate(task, context):
    import math
    import numpy as np

    from .differential_phase import phase_difference, receiver_geometry, relative_position
    from .esa_rinex_code import read_navigation
    from .gnss_position import C, ecef, geodetic, local_rotation
    from .rinex_clock_correction import correct_clock

    if context.manifest['scope'] != SCOPE or {k: v for k, v in task.items() if k not in ('index', 'shard')} != TASK:
        raise ValueError('the frozen three-convention study is required')

    def read(key):
        return context.input_path(key).read_bytes()

    def l1_transmit(record):
        return [record['gps_week_seconds']-signal['pseudorange_m']/C for satellite in record['satellites']
                for signal in satellite['signals'] if signal['band'] == 0 and signal['track_type'] == 0]

    context.charge(bound_calls=1, bound_steps=1)
    previous, ppp = json.loads(read('previous')), json.loads(read('ppp'))
    times, prns = [row['time_s'] for row in previous['rows']], previous['satellites']
    if len(times) != 61 or len(prns) != 10 or [round(row['time_s']*2)/2 for row in ppp['rows']] != times:
        raise ValueError('the exact original epochs and satellites are required')
    air, air_phase, (_, air_clock_flag) = unpack(gzip.decompress(read('air')), times, prns, station=False)
    base, base_phase, (station_xyz, station_flag) = unpack(gzip.decompress(read('station')), times, prns, station=True)
    if air_clock_flag or station_flag or any(row['receiver_clock_offset_s'] is not None for row in base):
        raise ValueError('unexpected receiver clock interpretation')
    nav, ion = read_navigation(gzip.decompress(read('navigation')).decode('ascii'))
    origin = ppp['rows'][0]
    anchor = ecef(math.radians(origin['latitude_deg']), math.radians(origin['longitude_deg']), origin['height_m'])
    rotation = local_rotation(*geodetic(anchor)[:2])
    samples = []
    max_transmit = 0.
    for index, (air_epoch, base_epoch, phase) in enumerate(zip(air, base, air_phase, strict=True)):
        context.charge(bound_calls=1, bound_steps=4*len(prns))
        consistent = correct_clock(air_epoch, phase, retime=True)
        altered = correct_clock(air_epoch, phase, retime=False)
        quick = [abs(a-b) for a, b in zip(l1_transmit(air_epoch), l1_transmit(consistent[0]), strict=True)]
        if len(quick) != len(prns) or max(quick) > 2e-10:
            raise ValueError('the consistent clock change must preserve raw satellite transmission time')
        max_transmit = max(max_transmit, max(quick))
        station, _, station_items = receiver_geometry(base_epoch, nav, ion, station_xyz, prns)
        if station_items != previous['rows'][index]['station_geometry']:
            raise ValueError('the original fixed station geometry changed')
        arms = {}
        for name, (record, cycles) in zip(ARMS, ((air_epoch, phase), consistent, altered), strict=True):
            geometric, gradient, items = receiver_geometry(record, nav, ion, anchor, prns)
            if name == 'original' and items != previous['rows'][index]['air_geometry']:
                raise ValueError('the original aircraft geometry changed')
            arms[name] = (geometric-station, gradient, items, cycles)
        samples.append(arms)
    rows = []
    for index, saved in enumerate(previous['rows'][1:], start=1):
        context.charge(bound_calls=1, bound_steps=len(ARMS))
        results = {}
        for name in ARMS:
            geometry, gradient, items, phase = samples[index][name]
            early_geometry, _, _, early_phase = samples[0][name]
            measured = phase_difference(phase, base_phase[index], early_phase, base_phase[0])
            fit = relative_position(measured, geometry-early_geometry, gradient)
            delta = rotation @ fit['position_change_m']
            if name == 'original' and not np.allclose(delta, saved['phase_change_neu_m'], rtol=0., atol=1e-10):
                raise ValueError('the original phase path did not reproduce')
            results[name] = dict(neu=delta.tolist(), residual=fit['residual_m'].tolist(),
                                 transmit_gps_s=[item['transmit_gps_seconds'] for item in items],
                                 ephemeris_hashes=[item['ephemeris_payload_sha256'] for item in items])
        rows.append(dict(time_s=times[index], original_ppp_neu=saved['ppp_change_neu_m'], arms=results))
    reference = np.asarray([row['arms']['original']['neu'] for row in rows])
    ppp_path = np.asarray([row['original_ppp_neu'] for row in rows])
    by_arm = {}
    for name in ARMS:
        path = np.asarray([row['arms'][name]['neu'] for row in rows])
        by_arm[name] = dict(rms_to_ppp_neu_m=np.sqrt(np.mean((path-ppp_path)**2, axis=0)).tolist(),
                            max_change_from_original_neu_m=np.max(np.abs(path-reference), axis=0).tolist())
    output = dict(rows=rows, summary=by_arm, maximum_raw_transmit_time_change_s=max_transmit,
                  passed=True, scientific_decision='abstain', new_aircraft_imu_fits=0, reserved_reads=0)
    context.save(ARTIFACT, output)
    return output


def recover(root):
    from .studies.task_resume import close_original, prepare_campaign, resume_campaign

    prefix = 'data/'+ID
    continuation = root/(prefix+'-recovery')
    if not continuation.is_dir():
        if not (root/prefix/'completion.json').is_file():
            close_original(root, prefix, qualification_request=RECOVERY)
        with closing(ClosedStudy(root, prefix)) as study:
            if study.input('recovery_policy') != RECOVER:
                raise ValueError('unchanged recovery policy required')
            identity = TASK['identity']
            if identity in study.rows and study.envelope(identity)['status'] == 'complete':
                return dict(state='original_tasks_finished', pending=0)
        prepare_campaign(root, prefix, continuation, qualification_request=RECOVERY, **RECOVER)
    return resume_campaign(root, continuation)


def report(root):
    prefix, identity = 'data/'+ID, TASK['identity']
    continuation = root/(prefix+'-recovery')
    with ExitStack() as stack:
        original = stack.enter_context(closing(ClosedStudy(root, prefix)))
        source = original
        if continuation.is_dir():
            from .studies.combined_task_evidence import inspect

            origin = inspect(root, continuation)['selected'][identity]['origin']
            if origin != prefix:
                source = stack.enter_context(closing(ClosedStudy(root, origin, store=original.store)))
        row, verdict = source.envelope(identity), source.artifact(identity, ARTIFACT)
        if row['status'] != 'complete' or row['charged'] != TASK['limits'] or verdict != row['result']:
            raise ValueError('the exact declared clock work is required')
        _write_equal(root/RESULT, encoded(dict(verdict, completion=source.completion)))
    return verdict['summary']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
