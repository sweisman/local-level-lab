# SPDX-License-Identifier: AGPL-3.0-or-later
"""Certify one endpoint-preserving shared displacement at the ESA forecast gap."""
import argparse
from contextlib import ExitStack, closing
from fractions import Fraction as F
import json
import math
from pathlib import Path

from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, WALL_S, _parent
from .esa_integrated_contrast_support import ARTIFACT as PRIOR_ARTIFACT
from .esa_integrated_contrast_support import ID as PRIOR_ID, RESULT as PRIOR, TASK as PRIOR_TASK
from .esa_linked_training_support import LATER, TRAIN
from .esa_rinex_window import FOLDER
from .ilvis0_matched_observed_inputs import _write_equal
from .shared_motion_gap import integrate_path, minimum_acceleration
from .studies.artifacts import encoded
from .studies.closed import ClosedStudy


ID = 'esa-shared-motion-gap-v1'
SCOPE = 'Minimum common coordinate acceleration that spans the certified ESA forecast gap'
PLAN = FOLDER+'ESA_SHARED_MOTION_GAP_PLAN.md'
RESULT = FOLDER+'esa-shared-motion-gap-result.json'
REQUEST = FOLDER+'esa-shared-motion-gap-qualification.json'
XML = FOLDER+'esa-shared-motion-gap-tests.xml'
PRIOR_SHA = '4e3eae50b6e904ba4c521b7c25669ea59f36c715973a5edba855f05ea6b2ed93'
ARTIFACT = 'shared-motion-gap.json'
TESTS = ('test_closed_motion_recovers_exact_midpoint_displacement',
         'test_closed_motion_uses_all_axes_and_keeps_irregular_end_conditions',
         'test_closed_motion_rejects_terminal_only_score')
TASK = dict(identity='closed-common-motion', input_key='score', payload=dict(later=LATER),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=2, bound_steps=2*LATER+1))


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_shared_motion_gap.py')
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
        raise ValueError('retain the original finite shared-motion allowance')
    sources, environment = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with ExitStack() as stack:
        support, row = _parent(root, PRIOR, PRIOR_SHA, PRIOR_ID, PRIOR_TASK, PRIOR_ARTIFACT, stack)
        if support.envelope(PRIOR_TASK['identity'])['charged'] != PRIOR_TASK['limits']:
            raise ValueError('the original completed score is required')
        taps = support.input('direction')['exact_later_taps']
        times = support.input('times')
        if len(times) != TRAIN+LATER or len(taps) != 3*LATER:
            raise ValueError('the original later forecast support is required')
        score = dict(times=times[TRAIN-1:], taps=taps, gap=row['score_gap_lower_exact'])
    values = dict(score=encoded(score), recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, prior=PRIOR, qualification=REQUEST, qualification_tests=XML)
    for key, value in values.items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, value)
        inputs[key] = path
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=WALL_S), root).prepare(root)['limits']


def evaluate(task, context):
    if context.manifest['scope'] != SCOPE or {k: v for k, v in task.items() if k not in ('index', 'shard')} != TASK:
        raise ValueError('the frozen shared-motion comparison is required')
    context.charge(bound_calls=1, bound_steps=LATER+1)
    score = json.loads(context.input_path('score').read_bytes())
    times = list(map(F, score['times']))
    weights = iter(map(F, score['taps']))
    taps = list(zip(weights, weights, weights, strict=True))
    gap = F(score['gap'])
    if len(taps) != LATER or len(times) != LATER+1 or gap <= 0:
        raise ValueError('the original positive gap and forecast grid are required')
    motion = minimum_acceleration(times, taps, gap)
    context.charge(bound_calls=1, bound_steps=LATER)
    accel = motion['acceleration']
    pos, speed = integrate_path(times, accel)
    change = sum(a*b for x, w in zip(pos[1:], taps, strict=True) for a, b in zip(x, w, strict=True))
    if pos[-1] != [0]*3 or speed[-1] != [0]*3 or change != gap:
        raise ValueError('the exact endpoint and score checks must pass')

    def peaks(rows):
        return [float(max(map(abs, axis))) for axis in zip(*rows, strict=True)]

    summary = dict(duration_s=float(times[-1]-times[0]),
                   acceleration_vector_rms_mps2=math.sqrt(motion['acceleration_rms_squared']),
                   acceleration_rms_squared_exact=str(motion['acceleration_rms_squared']),
                   knot_peak_position_m=peaks(pos), knot_peak_velocity_mps=peaks(speed),
                   knot_peak_acceleration_mps2=peaks(accel))
    rows = [dict(elapsed_s=float(t-times[0]), position_m=list(map(float, p)), velocity_mps=list(map(float, v)),
                 acceleration_exact_mps2=list(map(str, a)))
            for t, p, v, a in zip(times, pos, speed, accel, strict=True)]
    verdict = dict(summary=summary, rows=rows, exact_score_shift=str(change), exact_gap_reference=str(gap),
                   new_fits=0, protected_reads=0, scientific_decision='abstain', passed=True)
    context.save(ARTIFACT, verdict)
    return verdict


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
            if TASK['identity'] in study.rows and study.envelope(TASK['identity'])['status'] == 'complete':
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
            raise ValueError('the exact declared shared-motion evidence is required')
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
