# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare the grounded motion witness with the archived half-second phases."""
import argparse
from contextlib import ExitStack
from fractions import Fraction
import json
from pathlib import Path

from . import esa_nuuk_between_samples as motion
from . import esa_nkar_cadence_study as cadence
from . import esa_shared_motion_carrier as carrier
from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, _parent
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import encoded


ID = 'esa-nuuk-between-carrier-v1'
SCOPE = 'Saved half-second carrier phases against the exact Nuuk-anchored displacement'
PLAN = carrier.FOLDER+'ESA_NUUK_BETWEEN_CARRIER_PLAN.md'
RESULT = carrier.FOLDER+'esa-nuuk-between-carrier-result.json'
REQUEST = carrier.FOLDER+'esa-nuuk-between-carrier-qualification.json'
XML = carrier.FOLDER+'esa-nuuk-between-carrier-tests.xml'
ARTIFACT = 'nuuk-between-carrier.json'
MOTION_SHA = '2baf051f00af95e8ec9021bcdd84bda30fef442c61158b8e2d8b015518e64f75'
RECOVERY_RULE = RECOVER
PAIR_COUNT = carrier.END-carrier.START
TESTS = ('test_fixed_carrier_residual_differences_clock_and_troposphere_with_expected_signs',
         'test_clock_correction_keeps_common_satellites_and_cancellation_signs',
         'test_shared_motion_interpolation_is_cubic_and_closes')
TASK = dict(identity='nuuk-between-carrier', input_key='gap', payload=dict(pairs=PAIR_COUNT),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=1+PAIR_COUNT, bound_steps=1+66*PAIR_COUNT))


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_shared_motion_carrier.py')
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
        raise ValueError('retain the original finite between-sample carrier comparison')
    sources, environment = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with ExitStack() as stack:
        station, constructed = _parent(root, motion.RESULT, MOTION_SHA, motion.ID, motion.TASK, motion.ARTIFACT, stack)
        original, prior = _parent(root, carrier.RESULT, cadence.PARENT_SHA, carrier.ID, carrier.TASK,
                                  carrier.ARTIFACT, stack)
        if (station.envelope(motion.TASK['identity'])['charged'] != motion.TASK['limits']
                or original.envelope(carrier.TASK['identity'])['charged'] != carrier.TASK['limits']
                or not constructed['ground_positions_exactly_zero'] or len(prior['rows']) != PAIR_COUNT):
            raise ValueError('the complete exact motion and original phase evidence are required')
        values = {key: original.input(key, raw=True) for key in
                  ('rinex', 'navigation', 'clock', 'anchor', 'path', 'continuity', 'metric')}
        knots = [dict(row, elapsed_s=float(Fraction(row['elapsed_s_exact'])), velocity_mps=row['speed_mps'])
                 for row in constructed['knots']]
        values.update(gap=encoded(knots), recovery=recovery, recovery_tests=tests,
                      recovery_policy=encoded(RECOVERY_RULE))
    inputs = dict(plan=PLAN, motion=motion.RESULT, original=carrier.RESULT, qualification=REQUEST,
                  qualification_tests=XML)
    for key, value in values.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=carrier.WALL_S), root).prepare(root)['limits']


def evaluate(task, context):
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('the frozen between-sample range signature task is required')
    result = carrier.replay_signature(context, record_residuals=True)
    context.save(ARTIFACT, result)
    return result


def report(root):
    from contextlib import closing

    from .studies.closed import ClosedStudy

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
            raise ValueError('exact complete aircraft-carrier evidence required')
        _write_equal(root/RESULT, encoded(dict(result, motion_sha256=MOTION_SHA, completion=study.completion)))
    return result['summary']


if __name__ == '__main__':
    from functools import partial

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {
        'prepare': prepare, 'recover': partial(carrier.recover_signature, study_id=ID, task=TASK),
        'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
