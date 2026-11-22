# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare relative GPS phase motion during the sealed Reykjavík stop."""

import argparse
from contextlib import ExitStack, closing
import gzip
import json
from pathlib import Path

from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, WALL_S
from .esa_fixed_reference_pair import EXCERPT as AIR, REPORT as PAIR, STATION, STATION_SHA, SYSTEMS
from .esa_rinex_code_study import _INPUTS, _NAV
from .esa_rinex_window import FOLDER, WEEK
from .esa_second_ground_interval import SOURCE as PPP
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-fixed-reference-phase-v1'
SCOPE = 'Relative phase motion between the sealed ESA 187 stop and Reykjavík station'
PLAN = FOLDER+'ESA_FIXED_REFERENCE_PHASE_PLAN.md'
REQUEST = FOLDER+'esa-fixed-reference-phase-qualification.json'
XML = FOLDER+'esa-fixed-reference-phase-tests.xml'
RESULT = FOLDER+'esa-fixed-reference-phase-result.json'
PAIR_SHA = '401f7ffd3a080004869941e72d2e3c6e8f8f9fee8f35855e5e609b0a01a534db'
AIR_SHA = '310d9f2e8761de3bf1d9c8c9a4b8ec56949eae06b3c5b29afc370639fd0e021f'
PPP_SHA = '72af2c1e8f2631fb189fbe80e05c7708c351e2afe9234b89f3cc3e1fd9f17024'
ARTIFACT = 'phase-comparison.json'
TESTS = ('test_two_receivers_cancel_constant_ambiguities_and_ionosphere_in_phase_change',
         'test_relative_position_recovers_displacement_with_free_receiver_clock',
         'test_phase_geometry_cancels_common_receiver_terms_without_dropping_measurements')
TASK = dict(identity='reykjavik-relative-phase', input_key='paired', payload=dict(epochs=61, satellites=10),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=122, bound_steps=1881))


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_differential_phase.py')
    sources, env = source_closure(root, seeds), runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=env, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=env, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources, env


def prepare(root):
    from .airquantumgrav_receiver import records
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original finite phase allowance')
    sources, env = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=env,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    for path, expected in ((PAIR, PAIR_SHA), (AIR, AIR_SHA), (STATION, STATION_SHA), (_NAV, _INPUTS[_NAV]), (PPP, PPP_SHA)):
        if digest((root/path).read_bytes()) != expected:
            raise ValueError('sealed phase input differs: '+path)
    paired = json.loads((root/PAIR).read_bytes())
    times = [row['time_s'] for row in paired['rows']]
    if paired['matched'] != 61 or paired['air_records'] != 3601 or paired['week'] != WEEK:
        raise ValueError('all originally paired epochs are required')
    selected = []
    with (root/PPP).open() as handle:
        for row in records(handle):
            nominal = round(row['time_s']*2)/2
            if nominal in times and row['gps_week'] == WEEK:
                if (not 45253 <= row['sequence'] < 48943 or abs(row['time_s']-nominal) > .001):
                    raise ValueError('same sealed ground selection and one-millisecond GPS match required')
                selected.append({key: row[key] for key in ('time_s', 'sequence', 'latitude_deg', 'longitude_deg', 'height_m')})
    if [round(row['time_s']*2)/2 for row in selected] != times:
        raise ValueError('one original PPP position per matched epoch required')
    inputs = dict(plan=PLAN, paired=PAIR, air=AIR, station=STATION, navigation=_NAV,
                  qualification=REQUEST, qualification_tests=XML)
    for key, value in dict(ppp=encoded(dict(source_sha256=PPP_SHA, rows=selected)), recovery=recovery,
                           recovery_tests=tests, recovery_policy=encoded(RECOVER)).items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, value)
        inputs[key] = path
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=WALL_S), root).prepare(root)['limits']


def unpack(raw, times, prns, *, station, station_version='3.04', station_systems=SYSTEMS):
    """Reuse the original RINEX framing and field readers for both receivers."""
    from .esa_carrier_phase_support import _fields
    from .esa_rinex_code import observation_epochs
    from .esa_rinex_code_study import _approximation
    from .esa_rinex_window import epoch_offsets, read_header

    header, setup = (read_header(raw, expected_interval=30., expected_systems=station_systems,
                                  expected_version=station_version)
                     if station else read_header(raw))
    body = raw[len(header):]
    offsets = epoch_offsets(body, offset=0)
    starts_and_ends = zip(offsets, [row[0] for row in offsets[1:]]+[len(body)], strict=True)
    records, phases = [], []
    for (start, week, time, flag, _), end in starts_and_ends:
        if time not in times:
            continue
        if week != WEEK or flag:
            raise ValueError('normal observation on the sealed GPS week is required')
        block = body[start:end].decode('ascii')
        record, = observation_epochs(block, setup['observation_types'])
        record['satellites'] = [row for row in record['satellites'] if row['sv_id'] in prns]
        found = {int(line[1:3]): _fields(line, setup['observation_types']['G'])
                 for line in block.splitlines()[1:] if line.startswith('G') and int(line[1:3]) in prns}
        values = []
        for prn in prns:
            l1, l2 = found[prn]['l1'], found[prn]['l2']['2W']
            if l1 is None or l1[1] or l2[1]:
                raise ValueError('the complete unflagged dual-frequency arc is required')
            values.append([l1[0], l2[0]])
        records.append(record)
        phases.append(values)
    if [record['gps_week_seconds'] for record in records] != times:
        raise ValueError('unchanged exact time match required')
    return records, phases, _approximation(header)


def evaluate(task, context):
    import math
    import numpy as np

    from .differential_phase import phase_difference, relative_position, receiver_geometry
    from .esa_rinex_code import read_navigation
    from .gnss_position import ecef, geodetic, local_rotation

    if context.manifest['scope'] != SCOPE or {k: v for k, v in task.items() if k not in ('index', 'shard')} != TASK:
        raise ValueError('the frozen 61-epoch receiver comparison is required')

    def read(key):
        return context.input_path(key).read_bytes()

    context.charge(bound_calls=1, bound_steps=1)
    report = json.loads(read('paired'))
    times = [row['time_s'] for row in report['rows']]
    prns = sorted(int(name[1:]) for name in set.intersection(*(set(row['continued']) for row in report['rows'][1:])))
    if len(times) != 61 or len(prns) != 10 or report['matched'] != 61:
        raise ValueError('the ten continuously tracked satellites are required')
    air, air_phase, (_, air_clk) = unpack(gzip.decompress(read('air')), times, prns, station=False)
    base, base_phase, (station_xyz, base_clk) = unpack(gzip.decompress(read('station')), times, prns, station=True)
    nav, ion = read_navigation(gzip.decompress(read('navigation')).decode('ascii'))
    ppp = json.loads(read('ppp'))
    if ppp['source_sha256'] != PPP_SHA or [round(row['time_s']*2)/2 for row in ppp['rows']] != times:
        raise ValueError('the original receiver position series must match both physical inputs')
    origin = [math.radians(ppp['rows'][0][key]) for key in ('latitude_deg', 'longitude_deg')]
    air_xyz = ecef(*origin, ppp['rows'][0]['height_m'])
    coordinates = local_rotation(*geodetic(air_xyz)[:2])
    geometries = []
    for air_epoch, base_epoch in zip(air, base, strict=True):
        context.charge(bound_calls=1, bound_steps=2*len(prns))
        air_geom, gradient, air_items = receiver_geometry(air_epoch, nav, ion, air_xyz, prns)
        base_geom, _, base_items = receiver_geometry(base_epoch, nav, ion, station_xyz, prns)
        geometries.append((air_geom-base_geom, gradient, air_items, base_items))
    minimum_elevations = [min(source[index]['elevation_deg'] for _, _, air_info, base_info in geometries
                              for source in (air_info, base_info)) for index in range(len(prns))]
    ref = max(range(len(prns)), key=lambda index: (minimum_elevations[index], -prns[index]))
    rows = []
    for index, (time, (geometry, gradient, air_items, base_items)) in enumerate(zip(times, geometries, strict=True)):
        point = ppp['rows'][index]
        original = coordinates @ (ecef(math.radians(point['latitude_deg']), math.radians(point['longitude_deg']),
                                       point['height_m'])-air_xyz)
        if index:
            context.charge(bound_calls=1, bound_steps=1+len(prns))
            measured = phase_difference(air_phase[index], base_phase[index], air_phase[0], base_phase[0])
            predicted = geometry-geometries[0][0]
            fit = relative_position(measured, predicted, gradient)
            position = coordinates @ fit['position_change_m']
            residual = fit['residual_m']
            omissions = []
            for excluded in range(len(prns)):
                keep = np.arange(len(prns)) != excluded
                reduced = relative_position(measured[keep], predicted[keep], gradient[keep])
                omissions.append((coordinates @ reduced['position_change_m']-position).tolist())
            record = dict(phase_change_neu_m=position.tolist(), residual_m=residual.tolist(),
                          double_difference_residual_m=(residual-residual[ref]).tolist(),
                          clock_change_m=fit['clock_change_m'], singular_values=fit['singular_values'].tolist(),
                          omit_minus_all_neu_m=omissions)
        else:
            record = dict(phase_change_neu_m=[0., 0., 0.])
        rows.append(dict(time_s=time, ppp_change_neu_m=original.tolist(), air_timeshift_s=air[index]['receiver_clock_offset_s'],
                         station_timeshift_s=base[index]['receiver_clock_offset_s'], air_geometry=air_items,
                         station_geometry=base_items, **record))
    difference = np.asarray([row['phase_change_neu_m'] for row in rows[1:]])-np.asarray([row['ppp_change_neu_m'] for row in rows[1:]])
    outcome = dict(rows=rows, satellites=prns, reference_prn=prns[ref], minimum_elevations_deg=minimum_elevations,
                   aircraft_clock_applied=air_clk, station_clock_applied=base_clk,
                   relative_difference_rms_neu_m=np.sqrt(np.mean(difference**2, axis=0)).tolist(),
                   maximum_absolute_difference_neu_m=np.max(np.abs(difference), axis=0).tolist(),
                   max_omission_shift_neu_m=np.max(np.abs([row['omit_minus_all_neu_m'] for row in rows[1:]]), axis=(0, 1)).tolist(),
                   passed=True, scientific_decision='abstain', new_aircraft_imu_fits=0, reserved_reads=0)
    context.save(ARTIFACT, outcome)
    return outcome


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
        study = original
        if continuation.is_dir():
            from .studies.combined_task_evidence import inspect

            origin = inspect(root, continuation)['selected'][identity]['origin']
            if origin != prefix:
                study = stack.enter_context(closing(ClosedStudy(root, origin, store=original.store)))
        row, verdict = study.envelope(identity), study.artifact(identity, ARTIFACT)
        if row['status'] != 'complete' or row['charged'] != TASK['limits'] or verdict != row['result']:
            raise ValueError('the declared geometry and fit work must be complete')
        _write_equal(root/RESULT, encoded(dict(verdict, completion=study.completion)))
    return {key: verdict[key] for key in ('reference_prn', 'relative_difference_rms_neu_m',
                                           'maximum_absolute_difference_neu_m', 'max_omission_shift_neu_m')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
