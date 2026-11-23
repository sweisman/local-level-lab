# SPDX-License-Identifier: AGPL-3.0-or-later
"""Decompose the original anchored ESA position-score ambiguity by axis."""
import argparse
from contextlib import ExitStack, closing
from fractions import Fraction as F
from itertools import islice
import json
from math import sqrt
from pathlib import Path

from . import esa_girafe as girafe
from . import esa_nuuk_between_samples as prior
from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, _parent
from .ilvis0_matched_observed_inputs import _write_equal
from .shared_motion_gap import _inner_product, integrate_path
from .studies.artifacts import encoded


ID = 'esa-motion-axis-support-v1'
SCOPE = 'Axis constraints on the anchored ESA 187 score and independent force coverage'
FOLDER = prior.ground.parent.FOLDER
PLAN = FOLDER+'ESA_MOTION_AXIS_SUPPORT_PLAN.md'
REQUEST = FOLDER+'esa-motion-axis-support-qualification.json'
XML = FOLDER+'esa-motion-axis-support-tests.xml'
RESULT = FOLDER+'esa-motion-axis-support-result.json'
ARTIFACT = 'motion-axis-support.json'
PARENT_SHA = '2baf051f00af95e8ec9021bcdd84bda30fef442c61158b8e2d8b015518e64f75'
SOURCE = 'GIRAFE_raw_acc_187a-Nuuk-Rey.txt'
START, STOP = 388614, 388734
MAX_ROWS = 50_000
KNOTS = 125
TASK = dict(identity='motion-axis-support', input_key='score', payload=dict(knots=KNOTS, maximum_rows=MAX_ROWS),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=2, bound_steps=6*KNOTS+MAX_ROWS))


def axis_replay(times, taps, gap, anchors, acceleration):
    """Replay subsets of the original minimum-energy path in the saved score metric."""
    position, speed = integrate_path(times, acceleration)
    durations = [b-a for a, b in zip(times[:-1], times[1:], strict=True)]
    axes = ('north', 'east', 'up')
    original_score = tuple(sum(p*w for p, w in zip(axis, weight, strict=True))
                           for axis, weight in zip(zip(*position[1:], strict=True), zip(*taps, strict=True), strict=True))
    energy = tuple(_inner_product(axis, axis, durations) for axis in zip(*acceleration, strict=True))
    total_energy = sum(energy)
    if gap <= 0 or sum(original_score) != gap or not total_energy:
        raise ValueError('the fixed score gap does not reproduce')
    if any(a*total_energy != gap*b for a, b in zip(original_score, energy, strict=True)):
        raise ValueError('orthogonal acceleration and score contributions must agree')
    anchor_indices = [times.index(t) for t in anchors]
    if any(position[-1]) or any(speed[-1]) or any(any(position[i]) for i in anchor_indices):
        raise ValueError('the original path must close at all anchors')

    cases = {}
    for name, allowed in dict(unrestricted=range(3), horizontal=(0, 1), north_only=(0,), east_only=(1,), up_only=(2,)).items():
        permitted_score = sum(original_score[i] for i in allowed)
        if not permitted_score:
            cases[name] = dict(possible=False)
            continue
        scale = gap/permitted_score
        selected = [[scale*v if i in allowed else F(0) for i, v in enumerate(row)] for row in acceleration]
        path, velocities = integrate_path(times, selected)
        change = sum(p*w for row, weights in zip(path[1:], taps, strict=True)
                     for p, w in zip(row, weights, strict=True))
        if (change != gap or any(path[-1]) or any(velocities[-1])
                or any(any(path[i]) for i in anchor_indices)):
            raise ValueError('restricted path must match every anchor and the exact score gap')
        peak = [float(max(map(abs, axis))) for axis in zip(*path, strict=True)]
        rms = sqrt(scale**2*sum(energy[i] for i in allowed)/sum(durations))
        cases[name] = dict(possible=True, score_shift_exact=str(gap), acceleration_rms_mps2=rms, peak_position_m=peak)
    return dict(energy_fraction={axis: float(e/total_energy) for axis, e in zip(axes, energy, strict=True)},
                cases=cases, anchor_count=len(anchor_indices), knots=len(times))


def coverage(path):
    samples = []
    with path.open('rb') as stream:
        for count, row in enumerate(islice(girafe.read_rows(stream), MAX_ROWS), 1):
            time = girafe.utc_seconds_to_gps(row.utc_seconds)
            if time > STOP:
                break
            if time >= START:
                samples.append((time, row.half_interrogation_s))
        else:
            raise ValueError('the bounded GIRAFE scan did not reach the end of the score interval')
    if len(samples) < 2:
        raise ValueError('the score interval must overlap the GIRAFE clock')
    times, half = zip(*samples, strict=True)
    interval = [b-a for a, b in zip(times[:-1], times[1:], strict=True)]
    if times[0]-START > .101 or STOP-times[-1] > .101 or max(interval) > .101:
        raise ValueError('uninterrupted 10 Hz GIRAFE coverage required')
    return dict(rows=len(samples), rows_checked=count, first_gps_s=times[0], last_gps_s=times[-1],
                min_spacing_s=min(interval), max_spacing_s=max(interval), half_interrogation_s=[min(half), max(half)],
                raw_channels=['atom vertical force', 'quartz horizontal x', 'quartz horizontal y'],
                forces_compared=False, source_sha256=girafe.TARGETS[SOURCE][1])


def qualification(root, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    tests = ('test_esa_motion_axis_support.py', 'test_esa_girafe.py', 'test_shared_motion_gap.py')
    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN,
                                   *(f'analysis/tests/{test}' for test in tests)))
    environment = runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=(
        'test_closed_axis_replay_preserves_gap_and_exact_anchors', 'test_axis_replay_rejects_a_different_score_gap',
        'test_closed_motion_recovers_exact_midpoint_displacement'), minimum_tests=6)
    return sources, environment


def prepare(root):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original finite axis-support comparison')
    sources, environment = qualification(root, True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    observation = girafe.BASE/SOURCE
    girafe.verify_file(root/observation, SOURCE)
    with ExitStack() as stack:
        parent, result = _parent(root, prior.RESULT, PARENT_SHA, prior.ID, prior.TASK, prior.ARTIFACT, stack)
        if parent.envelope(prior.TASK['identity'])['charged'] != prior.TASK['limits'] or len(result['knots']) != KNOTS:
            raise ValueError('the complete exact original path is required')
        values = {key: parent.input(key, raw=True) for key in ('score', 'anchor')}
    values.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, prior=prior.RESULT, qualification=REQUEST, qualification_tests=XML,
                  girafe=observation.as_posix())
    for key, value in values.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=RECOVER['maximum_wall_s']), root).prepare(root)['limits']


def evaluate(task, context):
    if context.manifest['scope'] != SCOPE or {k: v for k, v in task.items() if k not in ('index', 'shard')} != TASK:
        raise ValueError('the frozen motion-axis task is required')
    context.charge(bound_calls=1, bound_steps=6*KNOTS)
    score, anchor, original = [json.loads(context.input_path(key).read_bytes()) for key in ('score', 'anchor', 'prior')]
    measured = list(map(F, score['times']))
    nominal_anchors = original['summary']['anchors_gps_s']
    anchors = [measured[0]+F(t)-F(anchor['time_s']) for t in nominal_anchors]
    times = sorted(set(measured) | set(anchors))
    if (len(times) != KNOTS or len(nominal_anchors) != 4
            or [t-measured[0] for t in times] != [F(row['elapsed_s_exact']) for row in original['knots']]):
        raise ValueError('the original four anchors and exact score knots must align')
    linear = iter(map(F, score['taps']))
    taps = dict(zip(measured[1:], zip(linear, linear, linear, strict=True), strict=True))
    acceleration = [list(map(F, row['acceleration_exact_mps2'])) for row in original['knots']]
    result = axis_replay(times, [taps.get(t, (0, 0, 0)) for t in times[1:]], F(score['gap']), anchors, acceleration)
    if result['cases']['unrestricted']['acceleration_rms_mps2'] != original['summary']['acceleration_vector_rms_mps2']:
        raise ValueError('the original acceleration scale must reproduce')
    context.charge(bound_calls=1, bound_steps=MAX_ROWS)
    result.update(coverage=coverage(context.input_path('girafe')), new_fits=0, protected_reads=0,
                  scientific_decision='abstain', passed=True)
    context.save(ARTIFACT, result)
    return result


def report(root):
    from .studies.closed import ClosedStudy

    prefix, identity = 'data/'+ID, TASK['identity']
    with ExitStack() as stack:
        study = stack.enter_context(closing(ClosedStudy(root, prefix)))
        if (root/(prefix+'-recovery')).is_dir():
            from .studies.combined_task_evidence import inspect

            origin = inspect(root, root/(prefix+'-recovery'))['selected'][identity]['origin']
            if origin != prefix:
                study = stack.enter_context(closing(ClosedStudy(root, origin, store=study.store)))
        envelope, result = study.envelope(identity), study.artifact(identity, ARTIFACT)
        if envelope['charged'] != TASK['limits'] or envelope['result'] != result or not result['passed']:
            raise ValueError('complete motion-axis and coverage evidence required')
        _write_equal(root/RESULT, encoded(dict(result, completion=study.completion, parent_sha256=PARENT_SHA)))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report', 'recover'))
    args = parser.parse_args()
    root = Path.cwd()
    if args.action == 'request':
        result = qualification(root, False)
    elif args.action == 'prepare':
        result = prepare(root)
    elif args.action == 'recover':
        from .esa_shared_motion_carrier import recover_signature

        result = recover_signature(root, study_id=ID, task=TASK)
    else:
        result = report(root)
    print(json.dumps(result, sort_keys=True))
