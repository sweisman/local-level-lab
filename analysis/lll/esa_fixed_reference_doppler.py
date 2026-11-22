# SPDX-License-Identifier: AGPL-3.0-or-later
"""Direct GPS Doppler motion over the sealed Reykjavík reference stop."""
import argparse
from contextlib import ExitStack, closing
import gzip
import json
import math
from pathlib import Path

from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, WALL_S, _parent
from .esa_fixed_reference_clock import ARTIFACT as PRIOR_ARTIFACT
from .esa_fixed_reference_clock import ID as PRIOR_ID, RESULT as PRIOR, TASK as PRIOR_TASK
from .esa_fixed_reference_pair import SYSTEMS
from .esa_rinex_window import FOLDER, WEEK, read_header
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import encoded
from .studies.closed import ClosedStudy

ID = 'esa-fixed-reference-doppler-v4'
SCOPE = 'Direct Doppler velocity of aircraft and fixed station during the sealed Reykjavík stop'
PLAN = FOLDER+'ESA_FIXED_REFERENCE_DOPPLER_PLAN.md'
EXECUTION = FOLDER+'ESA_FIXED_REFERENCE_DOPPLER_STAGED.md'
RESULT = FOLDER+'esa-fixed-reference-doppler-result.json'
REQUEST = FOLDER+'esa-fixed-reference-doppler-v4-qualification.json'
XML = FOLDER+'esa-fixed-reference-doppler-v4-tests.xml'
PRIOR_SHA = '4fdfda40da89d4877573363358dbba5a17a19d502d8d5f2bfee3b8b4c2f5841d'
ARTIFACT = 'receiver-velocity.json'
TESTS = ('test_doppler_gps_selection_preserves_mixed_epoch_framing',
         'test_implicit_signal_geometry_recovers_velocity_and_clock_drift',
         'test_doppler_adapter_charges_complete_operations_and_preserves_path',
         'test_station_header_and_observations_recover_fixed_velocity')
EPOCHS = {'station': 61, 'air': 3601}
TASKS = tuple(dict(identity=f'reykjavik-{name}-doppler', input_key=name,
                   payload=dict(epochs=count, satellites=10),
                   limits=dict(native_calls=0, packet_visits=0, bound_calls=count+1,
                               bound_steps=count*10+1)) for name, count in EPOCHS.items())


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, EXECUTION,
             'analysis/tests/test_gnss_doppler.py', 'analysis/tests/test_esa_fixed_reference_doppler.py')
    sources, environment = source_closure(root, seeds), runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS,
            minimum_tests=len(TESTS))
    return sources, environment


def prepare(root):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original finite Doppler allowance')
    sources, environment = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with ExitStack() as stack:
        parent, row = _parent(root, PRIOR, PRIOR_SHA, PRIOR_ID, PRIOR_TASK, PRIOR_ARTIFACT, stack)
        if parent.envelope(PRIOR_TASK['identity'])['charged'] != PRIOR_TASK['limits']:
            raise ValueError('the completed clock comparison is required')
        values = {key: parent.input(key, raw=True) for key in ('air', 'station', 'navigation', 'ppp')}
        reference_grid(json.loads(values['ppp'])['rows'], row['rows'])
        station_reference(gzip.decompress(values['station']))
        values['satellites'] = encoded(parent.input('previous')['satellites'])
        values['previous'] = encoded(row)
    values.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, execution=EXECUTION, prior=PRIOR, qualification=REQUEST, qualification_tests=XML)
    for key, value in values.items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, value)
        inputs[key] = path
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=list(TASKS), workers=1, threads=1,
                                     maximum_wall_s=WALL_S), root).prepare(root)['limits']


def reference_grid(positions, changes):
    """Combine the original anchor and the 60 saved relative changes."""
    times = [round(row['time_s']*2)/2 for row in positions]
    if (len(times) != 61 or [row['time_s'] for row in changes] != times[1:]
            or any(b-a != 30 for a, b in zip(times, times[1:]))):
        raise ValueError('exact original anchor and 60 matched changes required')
    zero = [0., 0., 0.]
    return (times, [zero, *(row['original_ppp_neu'] for row in changes)],
            [zero, *(row['arms']['original']['neu'] for row in changes)])


def station_reference(raw):
    from .esa_rinex_code_study import _approximation

    header, _ = read_header(raw, expected_interval=30., expected_systems=SYSTEMS)
    position, _ = _approximation(header)
    if not all(map(math.isfinite, position)):
        raise ValueError('finite fixed-station ECEF coordinates required')
    return position


def _route(raw, *, times, station, anchor, prns, navigation, context):
    from .gnss_doppler import gps_samples, observation_epochs, solve_velocity

    interval, systems = (30., SYSTEMS) if station else (.5, ('G', 'R'))
    header, setup = read_header(raw, expected_interval=interval, expected_systems=systems)
    rows = {}
    for (week, seconds), readings in observation_epochs(raw[len(header):], setup['observation_types'],
                                                       systems=('G',)):
        if seconds < times[0] or seconds > times[-1]:
            continue
        if week != WEEK or seconds in rows or len(rows) >= len(times) or seconds != times[len(rows)]:
            raise ValueError('exact original Doppler epoch sequence required')
        gps = readings['G']
        if any(prn not in gps for prn in prns):
            raise ValueError('missing Doppler for an original satellite')
        context.charge(bound_calls=1, bound_steps=len(prns))
        samples = gps_samples(week, seconds, {prn: gps[prn] for prn in prns}, navigation)
        rows[seconds] = solve_velocity(anchor, samples)
    if list(rows) != times:
        raise ValueError('the Doppler window is incomplete')
    return rows


def evaluate(task, context):
    from .esa_rinex_code import read_navigation
    from .gnss_position import ecef

    if (context.manifest['scope'] != SCOPE
            or {k: v for k, v in task.items() if k not in ('index', 'shard')} not in TASKS):
        raise ValueError('the frozen Doppler comparison is required')

    def read(key):
        return context.input_path(key).read_bytes()

    context.charge(bound_calls=1, bound_steps=1)
    clock = json.loads(read('previous'))['rows']
    prns = json.loads(read('satellites'))
    if len(prns) != 10 or len(set(prns)) != 10:
        raise ValueError('exact sealed clock result required')
    positions = json.loads(read('ppp'))['rows']
    station_times, _, _ = reference_grid(positions, clock)
    receiver = task['input_key']
    station = receiver == 'station'
    raw = gzip.decompress(read(receiver))
    if station:
        anchor, times = station_reference(raw), station_times
    else:
        origin = positions[0]
        anchor = ecef(math.radians(origin['latitude_deg']), math.radians(origin['longitude_deg']), origin['height_m'])
        times = [station_times[0]+step/2 for step in range(EPOCHS['air'])]
    navigation, _ = read_navigation(gzip.decompress(read('navigation')).decode('ascii'))
    series = _route(raw, times=times, station=station, anchor=anchor, prns=prns, navigation=navigation,
                    context=context)
    failed = [t for t, row in series.items() if row['status'] != 'converged']
    context.save(ARTIFACT, list(series.items()))
    return dict(receiver=receiver, epochs=len(series), failed=failed, passed=not failed,
                scientific_decision='abstain', new_aircraft_imu_fits=0, reserved_reads=0)


def compare(positions, changes, air, fixed):
    import numpy as np

    from .esa_doppler_comparison import integrate_half_second

    station_times, ppp, relative = reference_grid(positions, changes)
    air_times = [station_times[0]+step/2 for step in range(EPOCHS['air'])]
    if [t for t, _ in air] != air_times or [t for t, _ in fixed] != station_times:
        raise ValueError('complete sealed receiver velocity grids required')

    def rms(values):
        return np.sqrt(np.mean(np.asarray(values)**2, axis=0)).tolist()

    displacement = integrate_half_second(np.zeros(3), [row['velocity_neu_mps'] for _, row in air])[::60]
    ppp_path, phase_path = np.asarray(ppp), np.asarray(relative)
    comparisons = {'ppp': displacement-ppp_path, 'relative_phase': displacement-phase_path}
    summary = dict(path_rms_m={name: rms(values) for name, values in comparisons.items()},
                   displacement_30s_rms_m={name: rms(np.diff(values, axis=0))
                                           for name, values in comparisons.items()},
                   fixed_velocity_rms_mps=rms([row['velocity_neu_mps'] for _, row in fixed]))
    rows = [dict(time_s=t, doppler_neu_m=d.tolist(), ppp_neu_m=p.tolist(), phase_neu_m=r.tolist())
            for t, d, p, r in zip(station_times, displacement, ppp_path, phase_path, strict=True)]
    return dict(summary=summary, rows=rows)


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
            if all(key in study.rows and study.envelope(key)['status'] == 'complete' for key in study.tasks):
                return dict(state='original_tasks_finished', pending=0)
        prepare_campaign(root, prefix, continuation, qualification_request=RECOVERY, **RECOVER)
    return resume_campaign(root, continuation)


def report(root):
    prefix = 'data/'+ID
    continuation = root/(prefix+'-recovery')
    with ExitStack() as stack:
        original = stack.enter_context(closing(ClosedStudy(root, prefix)))
        selected = {}
        if continuation.is_dir():
            from .studies.combined_task_evidence import inspect

            selected = inspect(root, continuation)['selected']
        series, hashes = {}, {}
        for task in TASKS:
            identity, receiver = task['identity'], task['input_key']
            origin = selected.get(identity, {}).get('origin', prefix)
            source = original
            if origin != prefix:
                source = stack.enter_context(closing(ClosedStudy(root, origin, store=original.store)))
            row = source.envelope(identity)
            if row['status'] != 'complete' or row['charged'] != task['limits'] or not row['result']['passed']:
                raise ValueError('the two declared Doppler tasks must complete and pass')
            series[receiver] = source.artifact(identity, ARTIFACT)
            hashes[receiver] = dict(origin=origin, completion=source.completion, artifacts=row['artifacts'])
        verdict = compare(original.input('ppp')['rows'], original.input('previous')['rows'],
                          series['air'], series['station'])
        _write_equal(root/RESULT, encoded(dict(verdict, sources=hashes, scientific_decision='abstain',
                                               new_aircraft_imu_fits=0, reserved_reads=0)))
    return verdict['summary']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
