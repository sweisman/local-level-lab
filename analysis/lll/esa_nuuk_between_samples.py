# SPDX-License-Identifier: AGPL-3.0-or-later
"""Find the exact minimum shared-motion error invisible at the Nuuk sample times."""
import argparse
from contextlib import ExitStack, closing
from fractions import Fraction
import json
import math
from pathlib import Path

from . import esa_nuuk_phase_study as ground
from . import esa_shared_motion_gap as original
from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, _parent
from .ilvis0_matched_observed_inputs import _write_equal
from .shared_motion_gap import integrate_path, minimum_acceleration
from .studies.artifacts import encoded
from .studies.closed import ClosedStudy


ID = 'esa-nuuk-between-samples-v1'
SCOPE = 'Exact minimum shared coordinate acceleration with the four permanent Nuuk position anchors'
PLAN = ground.parent.FOLDER+'ESA_NUUK_BETWEEN_SAMPLES_PLAN.md'
RESULT = ground.parent.FOLDER+'esa-nuuk-between-samples-result.json'
REQUEST = ground.parent.FOLDER+'esa-nuuk-between-samples-qualification.json'
XML = ground.parent.FOLDER+'esa-nuuk-between-samples-tests.xml'
ARTIFACT = 'nuuk-between-samples.json'
ORIGINAL_SHA = 'c23cd7761891f5a239079badc3c0b69f121f61a257267faf4125a997a803536f'
GROUND_SHA = '2feb085e4c7d2895bb3f8a49775e83b8982f9581998b7e23dcb8443218b2f012'
WALL = 90
RECOVERY_RULE = RECOVER | dict(maximum_wall_s=WALL)
KNOTS = 125
TESTS = ('test_closed_motion_recovers_exact_midpoint_displacement',
         'test_closed_motion_anchors_raise_minimum_and_leave_exact_gap',
         'test_closed_motion_rejects_score_supported_only_at_fixed_positions')
TASK = dict(identity='nuuk-between-samples', input_key='score', payload=dict(knots=KNOTS, anchors=4),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=2, bound_steps=2*KNOTS))


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_shared_motion_gap.py')
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
        raise ValueError('retain the original finite anchored motion comparison')
    sources, environment = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with ExitStack() as stack:
        motion, baseline = _parent(root, original.RESULT, ORIGINAL_SHA, original.ID, original.TASK,
                                   original.ARTIFACT, stack)
        station, report = _parent(root, ground.RESULT, GROUND_SHA, ground.ID, ground.TASK, ground.ARTIFACT, stack)
        if (motion.envelope(original.TASK['identity'])['charged'] != original.TASK['limits']
                or station.envelope(ground.TASK['identity'])['charged'] != ground.TASK['limits']):
            raise ValueError('exact completed comparison allowances required')
        if tuple(row['gps_s'] for row in report['epochs']) != ground.TIMES:
            raise ValueError('unchanged four ground receiver times required')
        values = dict(score=motion.input('score', raw=True), anchor=station.input('anchor', raw=True),
                      baseline=encoded(baseline['summary']))
    values.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVERY_RULE))
    inputs = dict(plan=PLAN, ground=ground.RESULT, original=original.RESULT, qualification=REQUEST,
                  qualification_tests=XML)
    for key, value in values.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=WALL), root).prepare(root)['limits']


def evaluate(task, context):
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('the four declared position anchors are required')
    context.charge(bound_calls=1, bound_steps=KNOTS)

    def read(key):
        return json.loads(context.input_path(key).read_bytes())

    score, anchor, ground_report, baseline = (read(key) for key in ('score', 'anchor', 'ground', 'baseline'))
    score_times = list(map(Fraction, score['times']))
    epoch = Fraction(anchor['time_s'])
    gps_times = tuple(row['gps_s'] for row in ground_report['epochs'])
    anchors = [score_times[0]+Fraction(t)-epoch for t in gps_times]
    times = sorted(set(score_times) | set(anchors))
    raw_taps = iter(map(Fraction, score['taps']))
    t_by_time = dict(zip(score_times[1:], zip(raw_taps, raw_taps, raw_taps, strict=True), strict=True))
    taps = [t_by_time.get(t, (0, 0, 0)) for t in times[1:]]
    target = Fraction(score['gap'])
    if (tuple(gps_times) != ground.TIMES or len(score_times) != 121 or len(times) != KNOTS
            or not score_times[0] < min(anchors) < max(anchors) < score_times[-1] or target <= 0):
        raise ValueError('the preserved score grid and four separate ground knots are required')
    motion = minimum_acceleration(times, taps, target, position_anchors=anchors)
    context.charge(bound_calls=1, bound_steps=KNOTS)
    position, speed = integrate_path(times, motion['acceleration'])
    change = sum(x*w for xrow, wrow in zip(position[1:], taps, strict=True) for x, w in zip(xrow, wrow, strict=True))
    zero = [0]*3
    if position[-1] != zero or speed[-1] != zero or change != target or any(position[times.index(t)] != zero for t in anchors):
        raise ValueError('the exact ground anchors, closed endpoint and score shift must hold')
    rms_squared = motion['acceleration_rms_squared']
    original_squared = Fraction(baseline['acceleration_rms_squared_exact'])
    if rms_squared < original_squared:
        raise ValueError('an added exact constraint cannot lower the minimum energy')
    summary = dict(acceleration_vector_rms_mps2=math.sqrt(rms_squared),
                   original_acceleration_vector_rms_mps2=math.sqrt(original_squared),
                   acceleration_rms_ratio=math.sqrt(rms_squared/original_squared),
                   acceleration_rms_squared_exact=str(rms_squared), anchors_gps_s=gps_times,
                   peak_knot_position_by_axis_m=[float(max(map(abs, axis))) for axis in zip(*position, strict=True)],
                   peak_knot_position_norm_m=math.sqrt(max(sum(x*x for x in row) for row in position)))
    knots = [dict(elapsed_s_exact=str(t-times[0]), position_m=list(map(float, p)), speed_mps=list(map(float, v)),
                  acceleration_exact_mps2=list(map(str, a)))
             for t, p, v, a in zip(times, position, speed, motion['acceleration'], strict=True)]
    result = dict(summary=summary, knots=knots, exact_score_shift=str(change), exact_gap_reference=str(target),
                  ground_positions_exactly_zero=True, new_fits=0, protected_reads=0, passed=True,
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
            raise ValueError('exact complete anchored motion result required')
        _write_equal(root/RESULT, encoded(dict(result, ground_sha256=GROUND_SHA, original_sha256=ORIGINAL_SHA,
                                               completion=study.completion)))
    return result['summary']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
