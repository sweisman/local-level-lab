# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare conservative score bounds at the verified and ideal ground cadences."""
import argparse
from contextlib import ExitStack, closing
from fractions import Fraction
import json
import math
from pathlib import Path

from . import esa_nkar_cadence_study as cadence
from . import esa_nuuk_between_samples as motion
from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, _parent
from .ground_grid_score import score_sensitivity
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import encoded
from .studies.closed import ClosedStudy


ID = 'esa-ground-grid-score-v1'
SCOPE = 'Fixed-score sensitivity to verified Nuuk times and an ideal one-second grid'
PLAN = cadence.parent.FOLDER+'ESA_GROUND_GRID_SCORE_PLAN.md'
RESULT = cadence.parent.FOLDER+'esa-ground-grid-score-result.json'
REQUEST = cadence.parent.FOLDER+'esa-ground-grid-score-qualification.json'
XML = cadence.parent.FOLDER+'esa-ground-grid-score-tests.xml'
ARTIFACT = 'ground-grid-score.json'
MOVEMENT_SHA = '2baf051f00af95e8ec9021bcdd84bda30fef442c61158b8e2d8b015518e64f75'
CADENCE_SHA = '461e5385024e7925ffb276a41898ac66743d9c1891a9e9049e6440569c544eee'
WALL = 90
RECOVERY_RULE = RECOVER | dict(maximum_wall_s=WALL)
SCHEDULES = ('verified_30s_times', 'ideal_1s_times')
TESTS = ('test_grid_bound_integrates_the_linear_midpoint_kernel',
         'test_grid_bound_accumulates_signed_interpolation_weights_before_norm')
TASK = dict(identity='ground-grid-score', input_key='score', payload=dict(schedules=list(SCHEDULES)),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=2, bound_steps=484))


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_ground_grid_score.py')
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
        raise ValueError('retain the original finite ground-grid check')
    sources, environment = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with ExitStack() as stack:
        previous, movement = _parent(root, motion.RESULT, MOVEMENT_SHA, motion.ID, motion.TASK, motion.ARTIFACT, stack)
        _, replay = _parent(root, cadence.RESULT, CADENCE_SHA, cadence.ID, cadence.TASK, cadence.ARTIFACT, stack)
        if (not movement['ground_positions_exactly_zero'] or replay['ground_reads'] != 0
                or tuple(movement['summary']['anchors_gps_s']) != motion.ground.TIMES
                or replay['summary']['seconds'] != 120):
            raise ValueError('the original verified and hypothetical sampling schedules are required')
        values = dict(score=previous.input('score', raw=True), anchor=previous.input('anchor', raw=True),
                      movement=encoded(movement['summary']), cadence=encoded(replay['summary']))
    values.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVERY_RULE))
    inputs = dict(plan=PLAN, prior_motion=motion.RESULT, prior_cadence=cadence.RESULT, qualification=REQUEST,
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
        raise ValueError('the declared two-schedule sensitivity task is required')

    def read(key):
        return json.loads(context.input_path(key).read_bytes())

    rows = []
    for schedule in SCHEDULES:
        context.charge(bound_calls=1, bound_steps=242)
        score, anchor, movement, replay = (read(k) for k in ('score', 'anchor', 'movement', 'cadence'))
        t = list(map(Fraction, score['times']))
        gps_start = Fraction(anchor['time_s'])
        taps = iter(map(Fraction, score['taps']))
        taps = list(zip(taps, taps, taps, strict=True))
        gap = Fraction(score['gap'])
        all_ideal = range(int(replay['first_gps_s']), int(replay['last_gps_s'])+1)
        gps_end = gps_start+t[-1]-t[0]
        grid = (movement['anchors_gps_s'] if schedule == SCHEDULES[0]
                else [s for s in all_ideal if gps_start < s < gps_end])
        knots = [t[0]+Fraction(s)-gps_start for s in grid]
        if len(t) != 121 or len(grid) != (4 if schedule == SCHEDULES[0] else 120) or gap <= 0:
            raise ValueError('the original score grid, gap and sampling schedules are required')
        position, acceleration_squared = score_sensitivity(t, taps, knots)
        minimum_squared = gap**2/acceleration_squared
        if schedule == SCHEDULES[0] and minimum_squared > Fraction(movement['acceleration_rms_squared_exact']):
            raise ValueError('the relaxed lower bound must be below the exact earlier minimum')
        rows.append(dict(schedule=schedule, interior_anchors=len(grid), first_gps_s=grid[0], last_gps_s=grid[-1],
                         minimum_acceleration_rms_mps2=math.sqrt(minimum_squared),
                         position_only_gap_m=float(gap/position),
                         position_score_per_m=float(position),
                         acceleration_score_per_mps2=math.sqrt(acceleration_squared),
                         score_gap=float(gap), position_score_per_m_exact=str(position),
                         acceleration_score_per_mps2_squared_exact=str(acceleration_squared)))
    result = dict(schedules=rows, ground_reads=0, new_fits=0, protected_reads=0, passed=True,
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
            raise ValueError('exact completed schedule sensitivity evidence required')
        _write_equal(root/RESULT, encoded(dict(result, completion=study.completion)))
    return [{key: value for key, value in row.items() if not key.endswith('_exact')} for row in result['schedules']]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
