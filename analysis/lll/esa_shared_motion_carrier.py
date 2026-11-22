# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare the shared-motion carrier signature with archived satellite clocks."""
import argparse
from contextlib import ExitStack, closing
from fractions import Fraction as F
import gzip
import json
from pathlib import Path

from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, WALL_S, _parent
from .esa_carrier_phase_later import END, START, ID as CARRIER_ID, RESULT as CARRIER, TASK as CARRIER_TASK
from .esa_integrated_contrast_support import ID as SCORE_ID
from .esa_relative_clock_replay import CLOCK, CLOCK_SHA, EXCLUDED_PRN, ID as CLOCK_ID
from .esa_rinex_window import FOLDER
from .esa_shared_motion_gap import ARTIFACT as GAP_ARTIFACT
from .esa_shared_motion_gap import ID as GAP_ID, RESULT as GAP, TASK as GAP_TASK
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-shared-motion-carrier-v1'
SCOPE = 'Carrier signature and archived satellite clock changes for the ESA shared-motion example'
PLAN = FOLDER+'ESA_SHARED_MOTION_CARRIER_PLAN.md'
RESULT = FOLDER+'esa-shared-motion-carrier-result.json'
REQUEST = FOLDER+'esa-shared-motion-carrier-qualification.json'
XML = FOLDER+'esa-shared-motion-carrier-tests.xml'
ARTIFACT = 'shared-motion-carrier.json'
GAP_SHA = 'c23cd7761891f5a239079badc3c0b69f121f61a257267faf4125a997a803536f'
CARRIER_SHA = 'b92a9aa1f45947e7fc437d526563851effe07b7e956cf77c33851260103e4e5d'
TESTS = ('test_shared_motion_range_signature_matches_full_geometry',
         'test_shared_motion_interpolation_is_cubic_and_closes',
         'test_carrier_signature_compares_signed_clock_free_values',
         'test_clock_correction_keeps_common_satellites_and_cancellation_signs')
TASK = dict(identity='shared-motion-range-signature', input_key='gap', payload=dict(pairs=END-START),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=1+END-START,
                        bound_steps=1+33*(END-START)))


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_shared_motion_carrier.py')
    sources, environment = source_closure(root, seeds), runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS,
            minimum_tests=len(TESTS))
    return sources, environment


def load_carrier(root, stack):
    raw = (root/CARRIER).read_bytes()
    if digest(raw) != CARRIER_SHA:
        raise ValueError('the original checked carrier path report is required')
    prior = stack.enter_context(closing(ClosedStudy(root, 'data/'+CARRIER_ID)))
    report = json.loads(raw)
    if (prior.completion['manifest_sha256'] != report['study_manifest_sha256']
            or not prior.summary['passed'] or prior.envelope(CARRIER_TASK['identity'])['charged'] != CARRIER_TASK['limits']):
        raise ValueError('unchanged complete carrier pair work is required')
    return prior, prior.artifact(CARRIER_TASK['identity'], 'carrier-path.json')['positions']


def prepare(root):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original carrier-signature allowance')
    sources, environment = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with ExitStack() as stack:
        shared, row = _parent(root, GAP, GAP_SHA, GAP_ID, GAP_TASK, GAP_ARTIFACT, stack)
        carrier, path = load_carrier(root, stack)
        score = stack.enter_context(closing(ClosedStudy(root, 'data/'+SCORE_ID)))
        clocks = stack.enter_context(closing(ClosedStudy(root, 'data/'+CLOCK_ID)))
        clock_raw = clocks.input('clock', raw=True)
        if (not score.summary['passed'] or not clocks.summary['passed'] or digest(clock_raw) != CLOCK_SHA
                or shared.envelope(GAP_TASK['identity'])['charged'] != GAP_TASK['limits']
                or len(row['rows']) != (END-START)//2+1):
            raise ValueError('complete clock, score and shared-motion evidence required')
        values = {key: carrier.input(key, raw=True) for key in ('rinex', 'navigation', 'anchor', 'continuity')}
        values.update(gap=encoded(row['rows']), path=encoded(path), clock=clock_raw,
                      metric=encoded(score.input('shape')['metric']))
    values.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, prior=GAP, carrier=CARRIER, qualification=REQUEST, qualification_tests=XML)
    for key, value in values.items():
        filename = f'data/{ID}-inputs/{key}'
        _write_equal(root/filename, value)
        inputs[key] = filename
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=WALL_S), root).prepare(root)['limits']


def paired_satellite_states(first, second, expected, saved_prns, navigation):
    from .esa_carrier_phase_support import pair_satellites
    from .gnss_carrier_phase import shared_ephemerides
    from .gnss_position import satellite_state

    paired, _ = pair_satellites(first, second)
    if list(paired) != expected or len(saved_prns) < 5 or not set(saved_prns) <= paired.keys():
        raise ValueError('the frozen satellite support must reproduce')
    model = shared_ephemerides(navigation, *[
        dict(gps_week=epoch['week'], gps_week_seconds=epoch['seconds']) for epoch in (first, second)])
    states = [[satellite_state(model[prn], epoch['week'], epoch['seconds'],
              paired[prn]['broadcast_input_code_m'][side]) for prn in saved_prns]
              for side, epoch in enumerate((first, second))]
    return paired, states


def pair_signature(first, second, expected, saved_prns, coordinates, offsets, navigation, clocks, *,
                   ionosphere=None, final_orbit_position=None):
    import numpy as np

    from .esa_relative_clock_replay import interpolate_clock
    from .gnss_carrier_phase import _atmosphere, _geometry
    from .gnss_position import C, ecef
    from .shared_motion_carrier import centre, fixed_path_range_residual, range_shift

    paired, states = paired_satellite_states(first, second, expected, saved_prns, navigation)
    geometry, clock_correction, orbit_correction, modeled = [], [], [], []
    common = [i for i, prn in enumerate(saved_prns) if prn != EXCLUDED_PRN]
    if len(common) < 5:
        raise ValueError('too few satellites share a complete final clock product')
    for side, (epoch, endpoint_states) in enumerate(zip((first, second), states, strict=True)):
        positions, broadcast, transmit = zip(*endpoint_states, strict=True)
        start = np.asarray(coordinates[side])
        receiver = ecef(*start)
        geometry.append(range_shift(receiver, ecef(*(start+offsets[side])), positions))
        if ionosphere is not None:
            satellites = np.asarray(positions)
            ranges, _ = _geometry(receiver, satellites)
            mask, _, delay = _atmosphere(receiver, satellites, epoch['seconds'], ionosphere)
            if not np.all(mask):
                raise ValueError('an original satellite falls outside the fixed-path atmosphere model')
            modeled.append((ranges, broadcast, delay))
        clock_correction.append(np.asarray([
            -C*(interpolate_clock(clocks[saved_prns[i]], transmit[i])-broadcast[i]) for i in common]))
        if final_orbit_position is not None:
            final = np.asarray([final_orbit_position(saved_prns[i], transmit[i]) for i in common])
            final_ranges, _ = _geometry(receiver, final)
            broadcast_ranges, _ = _geometry(receiver, np.asarray(positions)[common])
            orbit_correction.append(final_ranges-broadcast_ranges)
    required = geometry[0]-geometry[1]
    signature = centre(required), common, centre(required[common]), centre(clock_correction[1]-clock_correction[0])
    if orbit_correction:
        signature += (centre(orbit_correction[1]-orbit_correction[0]),)
    if ionosphere is None:
        return signature
    measured = [paired[prn]['ionosphere_free_displacement_m'] for prn in saved_prns]
    return (*signature, fixed_path_range_residual(measured, *zip(*modeled, strict=True)))


def evaluate(task, context):
    if context.manifest['scope'] != SCOPE or {k: v for k, v in task.items() if k not in ('index', 'shard')} != TASK:
        raise ValueError('the frozen satellite signature task is required')
    verdict = replay_signature(context)
    context.save(ARTIFACT, verdict)
    return verdict


def replay_signature(context, *, record_residuals=False, final_orbit_position=None):
    import numpy as np

    from .esa_carrier_phase_support import phase_epochs
    from .esa_relative_clock_replay import _clock_records
    from .esa_rinex_code import read_navigation
    from .esa_rinex_code_comparison import coordinates
    from .shared_motion_carrier import compare_signatures, displacement_at, signed_product_comparison

    if final_orbit_position is not None and not record_residuals:
        raise ValueError('product replay requires the fixed-path residuals')

    def read(name):
        return context.input_path(name).read_bytes()

    context.charge(bound_calls=1, bound_steps=1)
    epochs = list(phase_epochs(gzip.decompress(read('rinex'))))
    navigation, ionosphere = read_navigation(gzip.decompress(read('navigation')).decode('ascii'))
    clocks = _clock_records(gzip.decompress(read('clock')).decode('ascii'))
    gap, anchor, geometry, support, metric = [
        json.loads(read(k)) for k in ('gap', 'anchor', 'path', 'continuity', 'metric')]
    flags = support['result']['per_pair']
    if ([row['index'] for row in geometry] != list(range(START+1, END+1))
            or abs(epochs[START]['seconds']-anchor['time_s']) > .001 or epochs[START]['week'] != anchor['gps_week']
            or abs(epochs[END]['seconds']-anchor['time_s']-gap[-1]['elapsed_s']) > .001
            or len(metric) != 3 or any(not scale > 0 for scale in metric)):
        raise ValueError('the original path, clock anchor and coordinate metric are required')
    acceleration = np.array([[float(F(x)) for x in row['acceleration_exact_mps2']] for row in gap])
    rows = []
    earlier = coordinates([anchor])[0]
    for index, original in enumerate(geometry, START):
        context.charge(bound_calls=1, bound_steps=99 if final_orbit_position is not None else
                       66 if record_residuals else 33)
        first, second = epochs[index:index+2]
        if (first['week'] != second['week'] or second['seconds'] != original['seconds']
                or second['seconds']-first['seconds'] != .5):
            raise ValueError('the original half-second later carrier grid is required')
        times = [row['seconds']-anchor['time_s'] for row in (first, second)]
        offsets = [displacement_at(gap, x, acceleration)/metric for x in times]
        prns = original['satellites']
        required, common, matched, replacement, *observed = pair_signature(
            first, second, flags[index]['accepted_prns'], prns, (earlier, original['position']),
            offsets, navigation, clocks, ionosphere=ionosphere if record_residuals else None,
            final_orbit_position=final_orbit_position)
        row = dict(seconds=second['seconds'], satellites=prns, required_m=required.tolist(),
                   common_satellites=[prns[i] for i in common], common_required_m=matched.tolist(),
                   clock_m=replacement.tolist(), original_residual_rms_m=original['range_difference_rms_m'])
        if record_residuals:
            base = observed[-1]
            row.update(fixed_path_residual_m=base.tolist(), shifted_residual_m=(base+required).tolist())
        if final_orbit_position is not None:
            orbit = observed[0]
            comparison = signed_product_comparison(matched, base[common], orbit, replacement)
            row.update(orbit_m=orbit.tolist(), **{k: v.tolist() for k, v in comparison.items()})
        rows.append(row)
        earlier = original['position']
    combined = [np.concatenate([r[name] for r in rows]) for name in ('common_required_m', 'clock_m', 'required_m')]
    residual_energy = sum(len(r['satellites'])*r['original_residual_rms_m']**2 for r in rows)
    summary = compare_signatures(*combined[:2]) | dict(
        full_required_rms_m=float(np.sqrt(np.mean(combined[2]**2))),
        original_residual_rms_m=float(np.sqrt(residual_energy/len(combined[2]))),
        common_values=len(combined[0]), full_values=len(combined[2]), pairs=len(rows))
    if record_residuals:
        base = np.concatenate([r['fixed_path_residual_m'] for r in rows])
        shifted = np.concatenate([r['shifted_residual_m'] for r in rows])
        def rms(a):
            return float(np.sqrt(np.mean(a*a)))

        required, clock = combined[:2]
        summary.update(fixed_path_rms_m=rms(base), shifted_path_rms_m=rms(shifted),
                       aligned_clock_fraction=float(required@clock/(required@required)),
                       pairs_with_larger_rms=sum(rms(np.asarray(r['shifted_residual_m'])) >
                                                 rms(np.asarray(r['fixed_path_residual_m'])) for r in rows))
    return dict(summary=summary, rows=rows, new_fits=0, protected_reads=0, passed=True, scientific_decision='abstain')


def recover(root):
    return recover_signature(root, study_id=ID, task=TASK)


def recover_signature(root, *, study_id, task):
    from .studies.task_resume import close_original, prepare_campaign, resume_campaign

    prefix = 'data/'+study_id
    continuation = root/(prefix+'-recovery')
    if not continuation.is_dir():
        if not (root/prefix/'completion.json').is_file():
            close_original(root, prefix, qualification_request=RECOVERY)
        with closing(ClosedStudy(root, prefix)) as study:
            if study.input('recovery_policy') != RECOVER:
                raise ValueError('unchanged recovery policy required')
            identity = task['identity']
            if identity in study.rows and study.envelope(identity)['status'] == 'complete':
                return dict(state='original_tasks_finished', pending=0)
        prepare_campaign(root, prefix, continuation, qualification_request=RECOVERY, **RECOVER)
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
        envelope, verdict = study.envelope(identity), study.artifact(identity, ARTIFACT)
        if envelope['status'] != 'complete' or envelope['charged'] != TASK['limits'] or verdict != envelope['result']:
            raise ValueError('the exact declared signature evidence is required')
        _write_equal(root/RESULT, encoded(dict(verdict, completion=study.completion)))
    return verdict['summary']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
