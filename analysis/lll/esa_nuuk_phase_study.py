# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run the finite permanent Nuuk fixed-path carrier comparison."""
import argparse
from contextlib import ExitStack, closing
import gzip
import json
from pathlib import Path

from . import esa_nuuk_ground_intake as intake
from . import esa_shared_motion_carrier as parent
from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, _parent
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-nuuk-phase-v2'
PREVIOUS = 'esa-nuuk-phase-v1'
SCOPE = 'Four fixed permanent-Nuuk and aircraft times against the constructed motion'
ORIGINAL_PLAN = parent.FOLDER+'ESA_NUUK_GROUND_PHASE_PLAN.md'
PLAN = parent.FOLDER+'ESA_NUUK_GROUND_PHASE_PLAN_V2.md'
RESULT = parent.FOLDER+'esa-nuuk-ground-phase-result.json'
REQUEST = parent.FOLDER+'esa-nuuk-ground-phase-v2-qualification.json'
XML = parent.FOLDER+'esa-nuuk-ground-phase-v2-tests.xml'
ARTIFACT = 'nuuk-ground-phase.json'
INTAKE_SHA = 'bb9ee437d5031e72fdb57908d8f535400c1899317a6b2c00c3f8ec6f1fb2ce6b'
TIMES = (388620., 388650., 388680., 388710.)
PRNS = (1, 2, 8, 10, 14, 17, 19, 21, 24, 30, 32)
WALL = 90
RECOVERY_RULE = RECOVER | dict(maximum_wall_s=WALL)
TESTS = ('test_carrier_comparison_uses_signed_station_error_and_removes_receiver_clock',
         'test_carrier_comparison_retains_simple_band_differences',
         'test_nuuk_worker_charges_each_declared_operation_once')
TASK = dict(identity='nuuk-phase', input_key='ground', payload=dict(times=4, prns=11, pairs=3),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=8, bound_steps=169))


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, ORIGINAL_PLAN, 'analysis/tests/test_esa_nuuk_phase.py')
    sources, environment = source_closure(root, seeds), runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources, environment


def prepare(root):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original finite Nuuk comparison')
    sources, environment = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    raw = (root/intake.REPORT).read_bytes()
    if digest(raw) != INTAKE_SHA:
        raise ValueError('the exact Nuuk ground intake receipt is required')
    receipt = json.loads(raw)
    if digest((root/intake.EXCERPT).read_bytes()) != receipt['excerpt_sha256']:
        raise ValueError('the exact Nuuk station excerpt is required')
    with ExitStack() as stack:
        previous = stack.enter_context(closing(ClosedStudy(root, 'data/'+PREVIOUS)))
        failure = previous.envelope(TASK['identity'])
        if (previous.completion['state'] != 'terminal' or failure['artifacts'] or any(failure['charged'].values())
                or failure['result'].get('reason') != 'charge exactly one operation or a declared native block'):
            raise ValueError('the original failed zero-work accounting receipt is required')
        source, _ = _parent(root, parent.RESULT, intake.cadence.PARENT_SHA,
                            parent.ID, parent.TASK, parent.ARTIFACT, stack)
        inputs = {key: source.input(key, raw=True) for key in ('rinex', 'navigation', 'gap', 'anchor', 'path', 'metric')}
        if digest(inputs['rinex']) != receipt['aircraft_source_sha256']:
            raise ValueError('the original matching AIR1 excerpt is required')
        unchanged = inputs | {'intake': raw, 'ground': (root/intake.EXCERPT).read_bytes()}
        if any(previous.input(key, raw=True) != value for key, value in unchanged.items()):
            raise ValueError('keep the original frozen scientific input bytes')
        previous_receipt = encoded(dict(completion=previous.completion, failure=failure))
    inputs.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVERY_RULE),
                  previous_receipt=previous_receipt)
    paths = dict(plan=PLAN, original_plan=ORIGINAL_PLAN, intake=intake.REPORT, ground=intake.EXCERPT,
                 qualification=REQUEST, qualification_tests=XML)
    for key, value in inputs.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        paths[key] = name
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=paths, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=WALL), root).prepare(root)['limits']


def evaluate(task, context):
    from fractions import Fraction

    import numpy as np

    from .differential_phase import receiver_geometry
    from .esa_carrier_phase_support import L1_WAVELENGTH, L2_WAVELENGTH
    from .esa_fixed_reference_phase import unpack
    from .esa_nuuk_phase import carrier_comparison
    from .esa_rinex_code import read_navigation
    from .gnss_position import ecef
    from .shared_motion_carrier import displacement_at

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('the single frozen Nuuk phase comparison is required')
    context.charge(bound_calls=1, bound_steps=1)

    def read(key):
        return context.input_path(key).read_bytes()

    receipt = json.loads(read('intake'))
    times, prns = list(TIMES), list(PRNS)
    if (receipt['later_targets'] != times or receipt['later_continuous_satellites'] != [f'G{p:02}' for p in prns]):
        raise ValueError('the complete declared contact times and lock arcs are required')
    air, air_phase, (_, air_clock) = unpack(gzip.decompress(read('rinex')), times, prns, station=False)
    ground, ground_phase, (station_xyz, ground_clock) = unpack(
        gzip.decompress(read('ground')), times, prns, station=True, station_version='3.05',
        station_systems=intake.SYSTEMS)
    navigation, ionosphere = read_navigation(gzip.decompress(read('navigation')).decode('ascii'))
    gap, anchor, path, metric = [json.loads(read(k)) for k in ('gap', 'anchor', 'path', 'metric')]
    acceleration = np.array([[float(Fraction(x)) for x in row['acceleration_exact_mps2']] for row in gap])
    positions = {row['seconds']: np.asarray(row['position']) for row in path}

    air_model, ground_model, shifted_model, metadata = [], [], [], []
    for t, air_epoch, ground_epoch in zip(times, air, ground, strict=True):
        context.charge(bound_calls=1, bound_steps=3*len(prns))
        original = positions[t]
        new = original + displacement_at(gap, t-anchor['time_s'], acceleration)/metric
        aircraft, _, air_info = receiver_geometry(air_epoch, navigation, ionosphere, ecef(*original), prns)
        station, _, site_info = receiver_geometry(ground_epoch, navigation, ionosphere, station_xyz, prns)
        shifted, _, _ = receiver_geometry(air_epoch, navigation, ionosphere, ecef(*new), prns)
        air_model.append(aircraft)
        ground_model.append(station)
        shifted_model.append(shifted)
        metadata.append(dict(gps_s=t, aircraft=air_info, ground=site_info, air_xyz_m=ecef(*original).tolist(),
                             constructed_displacement_ecef_m=(ecef(*new)-ecef(*original)).tolist()))
    wavelengths = np.array([L1_WAVELENGTH, L2_WAVELENGTH])
    for _ in range(len(times)-1):
        context.charge(bound_calls=1, bound_steps=1+len(prns))
    comparison = carrier_comparison(np.asarray(air_phase)*wavelengths, np.asarray(ground_phase)*wavelengths,
                                    air_model, ground_model, shifted_model)
    for first, last, row in zip(times[:-1], times[1:], comparison['pairs'], strict=True):
        row.update(first_gps_s=first, last_gps_s=last)
    for row in comparison['omissions']:
        row['omitted_prn'] = prns[row.pop('omitted_index')]
    changes = sorted({row['sv_id'] for side in ('aircraft', 'ground') for first, second in zip(metadata, metadata[1:])
                      for row, then in zip(first[side], second[side], strict=True)
                      if row['ephemeris_payload_sha256'] != then['ephemeris_payload_sha256']})
    comparison['summary'].update(times=len(times), satellites=len(prns), ephemeris_change_prns=changes)
    result = dict(comparison, prns=prns, epochs=metadata, station_xyz_m=station_xyz, aircraft_clock_applied=air_clock,
                  ground_clock_applied=ground_clock, new_fits=0, protected_reads=0, passed=True,
                  scientific_decision='abstain')
    context.save(ARTIFACT, result)
    return result


def recover(root):
    from .studies.task_resume import close_original, prepare_campaign, resume_campaign

    prefix = 'data/'+ID
    continuation = root/(prefix+'-recovery')
    if not continuation.is_dir():
        if not (root/prefix/'completion.json').is_file():
            close_original(root, prefix, qualification_request=RECOVERY)
        with closing(ClosedStudy(root, prefix)) as study:
            if study.input('recovery_policy') != RECOVERY_RULE:
                raise ValueError('unchanged recovery policy required')
            if any(study.envelope(key)['status'] == 'complete' for key in study.rows):
                return dict(state='original_task_finished', pending=0)
        prepare_campaign(root, prefix, continuation, qualification_request=RECOVERY, **RECOVERY_RULE)
    return resume_campaign(root, continuation)


def report(root):
    prefix, identity = 'data/'+ID, TASK['identity']
    continuation = root/(prefix+'-recovery')
    with ExitStack() as stack:
        study = stack.enter_context(closing(ClosedStudy(root, prefix)))
        if continuation.is_dir():
            from .studies.combined_task_evidence import inspect

            origin = inspect(root, continuation)['selected'][identity]['origin']
            if origin != prefix:
                study = stack.enter_context(closing(ClosedStudy(root, origin, store=study.store)))
        envelope, result = study.envelope(identity), study.artifact(identity, ARTIFACT)
        if envelope['charged'] != TASK['limits'] or envelope['result'] != result or not result['passed']:
            raise ValueError('the complete sealed Nuuk phase outcome is required')
        _write_equal(root/RESULT, encoded(dict(result, intake_sha256=INTAKE_SHA, completion=study.completion)))
    return result['summary']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
