# SPDX-License-Identifier: AGPL-3.0-or-later
"""Measure chronological transfer of the permanent Nuuk phase correction."""
import argparse
from contextlib import ExitStack, closing
import gzip
import json
from pathlib import Path

from . import esa_carrier_phase_continuous as path
from . import esa_nuuk_phase_study as ground
from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, _parent
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-nuuk-phase-transfer-v1'
SCOPE = 'Earlier-only ground phase correction on the continuous ESA 187 path'
PLAN = path.FOLDER+'ESA_NUUK_PHASE_TRANSFER_PLAN.md'
RESULT = path.FOLDER+'esa-nuuk-phase-transfer-result.json'
REQUEST = path.FOLDER+'esa-nuuk-phase-transfer-qualification.json'
XML = path.FOLDER+'esa-nuuk-phase-transfer-tests.xml'
ARTIFACT = 'nuuk-phase-transfer.json'
PATH_SHA = '68f6cfad45e74571296d2029ef72a9d0bd32f163db57b61727f835f307f4d090'
GROUND_SHA = '2feb085e4c7d2895bb3f8a49775e83b8982f9581998b7e23dcb8443218b2f012'
WALL = 90
RECOVERY_RULE = RECOVER | dict(maximum_wall_s=WALL)
TIMES = tuple(range(388230, 388711, 30))
TESTS = ('test_ground_phase_transfer_uses_only_earlier_pairs_to_estimate_gain',
         'test_ground_phase_transfer_rejects_overlapping_or_unordered_groups')
TASK = dict(identity='nuuk-phase-transfer', input_key='ground', payload=dict(times=17, prns=11, withheld=3),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=19, bound_steps=423))


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_ground_phase_transfer.py')
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
        raise ValueError('retain the original finite phase transfer study')
    sources, environment = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    raw = (root/path.RESULT).read_bytes()
    if digest(raw) != PATH_SHA:
        raise ValueError('the exact earlier continuous phase report is required')
    with ExitStack() as stack:
        station, _ = _parent(root, ground.RESULT, GROUND_SHA, ground.ID, ground.TASK, ground.ARTIFACT, stack)
        previous = stack.enter_context(closing(ClosedStudy(root, 'data/'+path.ID)))
        if (not previous.summary['passed'] or previous.envelope(path.TASK['identity'])['charged'] != path.TASK['limits']
                or previous.completion['manifest_sha256'] != json.loads(raw)['study_manifest_sha256']):
            raise ValueError('the unchanged complete continuous path is required')
        positions = previous.artifact(path.TASK['identity'], 'carrier-path.json')['positions']
        selected = [row for row in positions if row['seconds'] in TIMES]
        if [row['seconds'] for row in selected] != list(TIMES):
            raise ValueError('the declared path must contain all ground times')
        values = {key: station.input(key, raw=True) for key in ('rinex', 'navigation', 'ground', 'intake')}
        if any(values[key] != previous.input(key, raw=True) for key in ('rinex', 'navigation')):
            raise ValueError('ground and continuous phase studies must share observations and navigation')
        values.update(path=encoded(selected), clock=previous.input('clock', raw=True))
    values.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVERY_RULE))
    inputs = dict(plan=PLAN, earlier_path=path.RESULT, late_ground=ground.RESULT, qualification=REQUEST,
                  qualification_tests=XML)
    for key, value in values.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=WALL), root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .differential_phase import receiver_geometry
    from .esa_carrier_phase_support import L1_WAVELENGTH, L2_WAVELENGTH
    from .esa_fixed_reference_phase import unpack
    from .esa_nuuk_phase import centred_band_residuals
    from .esa_rinex_code import read_navigation
    from .gnss_position import GAMMA, ecef
    from .ground_phase_transfer import compare_transfer

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('the declared phase transfer task is required')
    context.charge(bound_calls=1, bound_steps=1)

    def read(key):
        return context.input_path(key).read_bytes()

    times, prns = list(TIMES), list(ground.PRNS)
    candidates = json.loads(read('intake'))['rows']
    continuous = set.intersection(*(set(row['continued']) for row in candidates[1:]))
    if ([row['time_s'] for row in candidates] != times or any(row['status'] != 'matched' for row in candidates)
            or continuous != {f'G{p:02}' for p in prns}):
        raise ValueError('the exact 17 times and 11 continuous satellites are required')
    clock = json.loads(read('clock'))['result']['second_gps_seconds']
    if clock != 388556. or times[-4:] != list(ground.TIMES):
        raise ValueError('the exact aircraft clock-step and held-out group are required')
    air, air_phase, _ = unpack(gzip.decompress(read('rinex')), times, prns, station=False)
    station, phase, (site, _) = unpack(gzip.decompress(read('ground')), times, prns, station=True,
                                      station_version='3.05', station_systems=ground.intake.SYSTEMS)
    navigation, atmosphere = read_navigation(gzip.decompress(read('navigation')).decode('ascii'))
    positions = json.loads(read('path'))
    air_range, ground_range, info = [], [], []
    for t, a, b, row in zip(times, air, station, positions, strict=True):
        context.charge(bound_calls=1, bound_steps=22)
        if row['seconds'] != t:
            raise ValueError('saved aircraft positions must match receiver times')
        ar, _, air_meta = receiver_geometry(a, navigation, atmosphere, ecef(*row['position']), prns)
        gr, _, ground_meta = receiver_geometry(b, navigation, atmosphere, site, prns)
        air_range.append(ar)
        ground_range.append(gr)
        info.append(dict(time_s=t, air=air_meta, ground=ground_meta))
    context.charge(bound_calls=1, bound_steps=48)
    units = np.array([L1_WAVELENGTH, L2_WAVELENGTH])
    a = centred_band_residuals(np.asarray(air_phase)*units, air_range)
    b = centred_band_residuals(np.asarray(phase)*units, ground_range)
    training = [i for i in range(len(times)-5) if not times[i] < clock <= times[i+1]]
    withheld = list(range(len(times)-4, len(times)-1))
    if (len(training), len(withheld)) != (11, 3):
        raise ValueError('the frozen chronological split must reproduce')
    coefficients = np.asarray([GAMMA, -1.])/(GAMMA-1.)
    result = {band: compare_transfer(x, y, training=training, withheld=withheld)
              for band, x, y in (('ionosphere_free', a@coefficients, b@coefficients),
                                 ('L1', a[:, :, 0], b[:, :, 0]), ('L2', a[:, :, 1], b[:, :, 1]))}
    changes = [dict(first=left['time_s'], last=right['time_s'], path=key, prn=satellite['sv_id'])
               for left, right in zip(info, info[1:]) for key in ('air', 'ground')
               for satellite, following in zip(left[key], right[key], strict=True)
               if satellite['ephemeris_payload_sha256'] != following['ephemeris_payload_sha256']]
    outcome = dict(summary=result, times=times, satellites=prns, training_indices=training,
                   withheld_indices=withheld, geometry=info, navigation_changes=changes,
                   ground_band_residual_m=b.tolist(), aircraft_band_residual_m=a.tolist(),
                   new_receiver_fits=0, new_inertial_fits=0, protected_reads=0, passed=True,
                   scientific_decision='abstain')
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
            raise ValueError('exact sealed phase transfer evidence required')
        _write_equal(root/RESULT, encoded(dict(result, completion=study.completion)))
    return {band: {key: value for key, value in row.items() if key != 'per_interval'}
            for band, row in result['summary'].items()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
