# SPDX-License-Identifier: AGPL-3.0-or-later
"""Project the withheld ground-transfer residuals through their fixed GPS geometry."""
import argparse
from contextlib import ExitStack, closing
import gzip
import json
from pathlib import Path

from . import esa_nuuk_phase_transfer as prior
from .esa_calibration_conditioned_margin import RECOVERY, _parent
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import encoded
from .studies.closed import ClosedStudy


ID = 'esa-nuuk-phase-position-v1'
SCOPE = 'Position projection of the three withheld permanent Nuuk range intervals'
PLAN = prior.path.FOLDER+'ESA_NUUK_PHASE_POSITION_PLAN.md'
RESULT = prior.path.FOLDER+'esa-nuuk-phase-position-result.json'
REQUEST = prior.path.FOLDER+'esa-nuuk-phase-position-qualification.json'
XML = prior.path.FOLDER+'esa-nuuk-phase-position-tests.xml'
ARTIFACT = 'nuuk-phase-position.json'
PRIOR_SHA = '0779e5d7362e17176ade66268f45276b2158db7989ff4a1c1dacd01b48a4d58e'
TESTS = ('test_phase_projection_separates_motion_and_bounds_range_amplification',
         'test_phase_projection_can_leave_nonposition_range_residuals')
TASK = dict(identity='nuuk-phase-position', input_key='transfer', payload=dict(pairs=3, satellites=11),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=4, bound_steps=133))


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_differential_phase_projection.py')
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
        raise ValueError('retain the original finite position projection')
    sources, environment = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with ExitStack() as stack:
        study, result = _parent(root, prior.RESULT, PRIOR_SHA, prior.ID, prior.TASK, prior.ARTIFACT, stack)
        if (result['withheld_indices'] != [13, 14, 15] or len(result['training_indices']) != 11
                or study.envelope(prior.TASK['identity'])['charged'] != prior.TASK['limits']):
            raise ValueError('the exact earlier-to-later correction is required')
        values = {key: study.input(key, raw=True) for key in ('rinex', 'navigation', 'path')}
    values.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(prior.RECOVERY_RULE))
    inputs = dict(plan=PLAN, transfer=prior.RESULT, qualification=REQUEST, qualification_tests=XML)
    for key, value in values.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=prior.WALL), root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .differential_phase import position_projection, receiver_geometry
    from .esa_fixed_reference_phase import unpack
    from .esa_rinex_code import read_navigation
    from .gnss_position import GAMMA, ecef, local_rotation

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('the three frozen position projection intervals are required')
    context.charge(bound_calls=1, bound_steps=1)

    def read(key):
        return context.input_path(key).read_bytes()

    transfer = json.loads(read('transfer'))
    positions = json.loads(read('path'))
    indices, times, prns = transfer['withheld_indices'], transfer['times'], transfer['satellites']
    if indices != [13, 14, 15] or [row['seconds'] for row in positions] != times or prns != list(prior.ground.PRNS):
        raise ValueError('unaltered path and matched satellites required')
    end_times = [times[i+1] for i in indices]
    air, _, _ = unpack(gzip.decompress(read('rinex')), end_times, prns, station=False)
    nav, neutral = read_navigation(gzip.decompress(read('navigation')).decode('ascii'))
    scale = np.array([GAMMA, -1.])/(GAMMA-1.)
    aircraft = np.asarray(transfer['aircraft_band_residual_m'])@scale
    station = np.asarray(transfer['ground_band_residual_m'])@scale
    gain = transfer['summary']['ionosphere_free']['trained_gain']
    methods = dict(no_ground=0., full_ground=1., earlier_gain=gain)
    start_local = local_rotation(*positions[indices[0]]['position'][:2])
    rows = []
    for i, record in zip(indices, air, strict=True):
        context.charge(bound_calls=1, bound_steps=44)
        aircraft_position = positions[i+1]['position']
        local = local_rotation(*aircraft_position[:2])
        _, gradient, meta = receiver_geometry(record, nav, neutral, ecef(*aircraft_position), prns)
        if meta != transfer['geometry'][i+1]['air']:
            raise ValueError('original saved satellite geometry must reproduce')
        modes = {label: position_projection(aircraft[i]-g*station[i], gradient, local)
                 for label, g in methods.items()}
        rows.append(dict(first_gps_s=times[i], last_gps_s=times[i+1], projections=modes))

    summary = {}
    for label in methods:
        projected = [row['projections'][label] for row in rows]
        local = np.array([r['equivalent_neu_m'] for r in projected])
        accumulated = np.cumsum([r['equivalent_ecef_m'] for r in projected], axis=0)@start_local.T
        summary[label] = dict(rms_equivalent_increment_neu_m=np.sqrt(np.mean(local**2, axis=0)).tolist(),
                              peak_accumulated_neu_m=np.max(abs(accumulated), axis=0).tolist(),
                              accumulated_neu_m=accumulated.tolist(),
                              remaining_range_rms_m=float(np.sqrt(np.mean([
                                  r['remaining_range_rms_m']**2 for r in projected]))))
    geometry = [r['projections']['no_ground'] for r in rows]
    result = dict(summary=summary, intervals=rows, earlier_gain=gain, prns=prns,
                  maximum_component_gain_m_per_m=np.max([r['component_gain_m_per_m'] for r in geometry], axis=0).tolist(),
                  maximum_geometry_condition=max(r['geometry_condition'] for r in geometry),
                  new_trajectory_fits=0, protected_reads=0, passed=True, scientific_decision='abstain')
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
            if study.input('recovery_policy') != prior.RECOVERY_RULE:
                raise ValueError('unchanged recovery policy required')
            if any(study.envelope(key)['status'] == 'complete' for key in study.rows):
                return dict(state='original_task_finished', pending=0)
        prepare_campaign(root, prefix, continuation, qualification_request=RECOVERY, **prior.RECOVERY_RULE)
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
            raise ValueError('exact sealed position projection evidence required')
        _write_equal(root/RESULT, encoded(dict(result, completion=study.completion)))
    return {key: result[key] for key in ('summary', 'maximum_component_gain_m_per_m', 'maximum_geometry_condition')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
