# SPDX-License-Identifier: AGPL-3.0-or-later
"""Re-express the sealed development carrier signature on the NKAR time grid."""
import argparse
from contextlib import ExitStack, closing
import json
from pathlib import Path

from . import esa_shared_motion_carrier as parent
from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, _parent
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import encoded
from .studies.closed import ClosedStudy


ID = 'esa-nkar-cadence-v1'
SCOPE = 'Sum the frozen ESA 187 carrier signature on the integer-second GPS grid'
PLAN = parent.FOLDER+'ESA_NKAR_CADENCE_PLAN.md'
RESULT = parent.FOLDER+'esa-nkar-cadence-result.json'
REQUEST = parent.FOLDER+'esa-nkar-cadence-qualification.json'
XML = parent.FOLDER+'esa-nkar-cadence-tests.xml'
PARENT_SHA = '6772d3624b7c5bb8dfc3fb0b8370fd6a8d8a261d2e7760f4f5014762d638a9de'
ARTIFACT = 'nkar-carrier-cadence.json'
WALL_S = 60
RECOVERY_RULE = RECOVER | dict(maximum_wall_s=WALL_S)
PAIR_COUNT = 120
TESTS = ('test_one_second_carrier_sum_uses_shared_satellites_and_removes_each_clock',
         *(f'test_one_second_carrier_sum_rejects_wrong_clock_or_gaps[times{i}]' for i in range(3)))
TASK = dict(identity='nkar-carrier-grid', input_key='carrier', payload=dict(seconds=PAIR_COUNT),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=1, bound_steps=1+PAIR_COUNT))


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_shared_motion_one_second.py')
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
        raise ValueError('retain the original finite cadence study')
    sources, environment = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with ExitStack() as stack:
        original, sealed = _parent(root, parent.RESULT, PARENT_SHA, parent.ID, parent.TASK, parent.ARTIFACT, stack)
        if (original.envelope(parent.TASK['identity'])['charged'] != parent.TASK['limits']
                or len(sealed['rows']) != 2*PAIR_COUNT):
            raise ValueError('the complete half-second study is required')
    values = dict(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVERY_RULE))
    inputs = dict(plan=PLAN, carrier=parent.RESULT, qualification=REQUEST, qualification_tests=XML)
    for key, value in values.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=WALL_S), root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .shared_motion_carrier import compare_signatures
    from .shared_motion_one_second import sum_airborne_pairs
    from .studies.artifacts import digest

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('the declared integer-second carrier task is required')
    context.charge(bound_calls=1, bound_steps=1+PAIR_COUNT)
    raw = context.input_path('carrier').read_bytes()
    if digest(raw) != PARENT_SHA:
        raise ValueError('exact saved signatures required')
    source = json.loads(raw)
    rows = sum_airborne_pairs(source['rows'])
    required, clock = [np.concatenate([row[key] for row in rows]) for key in ('required_m', 'clock_m')]
    summary = compare_signatures(required, clock) | dict(
        seconds=len(rows), first_gps_s=rows[0]['first_gps_s'], last_gps_s=rows[-1]['last_gps_s'],
        comparisons=len(required), minimum_satellites=min(len(row['satellites']) for row in rows),
        maximum_satellites=max(len(row['satellites']) for row in rows),
        aligned_clock_fraction=float(required@clock/(required@required)),
        required_per_second_vs_half_second=float(np.sqrt(np.mean(required**2)) /
                                                 (2*source['summary']['required_rms_m'])))
    result = dict(summary=summary, rows=rows, ground_reads=0, protected_reads=0, new_fits=0,
                  passed=True, scientific_decision='abstain')
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
            raise ValueError('exact complete cadence evidence required')
        _write_equal(root/RESULT, encoded(dict(result, parent_sha256=PARENT_SHA, completion=study.completion)))
    return result['summary']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
