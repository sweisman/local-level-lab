# SPDX-License-Identifier: AGPL-3.0-or-later
"""Decompose the already verified Reykjavík carrier path by signal band."""

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


ID = 'esa-fixed-reference-band-v1'
SCOPE = 'Band contributions to the unchanged ten-satellite Reykjavík ground path'
PLAN = FOLDER+'ESA_FIXED_REFERENCE_BAND_PLAN.md'
RESULT = FOLDER+'esa-fixed-reference-band-result.json'
REQUEST = FOLDER+'esa-fixed-reference-band-qualification.json'
XML = FOLDER+'esa-fixed-reference-band-tests.xml'
PRIOR_SHA = '07e09f353f856629d186710f4b68658632938f49ee6e0b60ec41595835cee316'
ARTIFACT = 'carrier-bands.json'
TESTS = ('test_band_decomposition_recovers_both_paths_despite_distinct_clock_terms',)
TASK = dict(identity='reykjavik-carrier-bands', input_key='previous', payload=dict(epochs=60, satellites=10),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=61, bound_steps=661))


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_phase_band_contribution.py')
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
        raise ValueError('retain the original finite band allowance')
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

    from .differential_phase import receiver_geometry
    from .esa_rinex_code import read_navigation
    from .gnss_position import ecef, geodetic, local_rotation
    from .phase_band_contribution import bands

    if context.manifest['scope'] != SCOPE or {k: v for k, v in task.items() if k not in ('index', 'shard')} != TASK:
        raise ValueError('the ten-satellite band audit is required')

    def read(key):
        return context.input_path(key).read_bytes()

    context.charge(bound_calls=1, bound_steps=1)
    prior, ppp = json.loads(read('previous')), json.loads(read('ppp'))
    times, prns = [row['time_s'] for row in prior['rows']], prior['satellites']
    if len(prns) != 10 or len(times) != 61 or [round(row['time_s']*2)/2 for row in ppp['rows']] != times:
        raise ValueError('the exact original times and satellite geometry are required')
    air, air_phase, _ = unpack(gzip.decompress(read('air')), times, prns, station=False)
    _, base_phase, _ = unpack(gzip.decompress(read('station')), times, prns, station=True)
    nav, ion = read_navigation(gzip.decompress(read('navigation')).decode('ascii'))
    origin = ppp['rows'][0]
    origin = ecef(math.radians(origin['latitude_deg']), math.radians(origin['longitude_deg']), origin['height_m'])
    rotation = local_rotation(*geodetic(origin)[:2])
    rows = []
    for index, previous in enumerate(prior['rows'][1:], start=1):
        context.charge(bound_calls=1, bound_steps=len(prns)+1)
        _, derivative, geometry = receiver_geometry(air[index], nav, ion, origin, prns)
        if geometry != previous['air_geometry']:
            raise ValueError('the exact original satellite geometry must reproduce')
        result = bands(air_phase[index], base_phase[index], air_phase[0], base_phase[0],
                       rotation.T @ previous['phase_change_neu_m'], derivative)
        rows.append(dict(time_s=times[index], ppp_neu_m=previous['ppp_change_neu_m'],
                         combined_neu_m=previous['phase_change_neu_m'],
                         l1_neu_m=(rotation @ result['l1_position']).tolist(),
                         l2_neu_m=(rotation @ result['l2_position']).tolist(),
                         aircraft_band_change_m=result['aircraft_band_change'].tolist(),
                         station_band_change_m=result['station_band_change'].tolist(),
                         band_residual_m=result['residual'].tolist()))
    target = np.asarray([row['ppp_neu_m'] for row in rows])
    errors = {band: np.sqrt(np.mean((np.asarray([row[band+'_neu_m'] for row in rows])-target)**2, axis=0)).tolist()
              for band in ('combined', 'l1', 'l2')}
    outcome = dict(rows=rows, satellites=prns, relative_difference_rms_neu_m=errors, passed=True,
                   scientific_decision='abstain', reserved_reads=0, new_aircraft_imu_fits=0)
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
        source = original
        if continuation.is_dir():
            from .studies.combined_task_evidence import inspect

            origin = inspect(root, continuation)['selected'][identity]['origin']
            if origin != prefix:
                source = stack.enter_context(closing(ClosedStudy(root, origin, store=original.store)))
        row, verdict = source.envelope(identity), source.artifact(identity, ARTIFACT)
        if row['status'] != 'complete' or row['charged'] != TASK['limits'] or verdict != row['result']:
            raise ValueError('the declared band decomposition work must be complete')
        _write_equal(root/RESULT, encoded(dict(verdict, completion=source.completion)))
    return verdict['relative_difference_rms_neu_m']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
