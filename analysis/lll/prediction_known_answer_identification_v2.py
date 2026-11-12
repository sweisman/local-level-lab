# SPDX-License-Identifier: AGPL-3.0-or-later
"""Corrected sealed-result adapter for the unchanged known-answer trial."""
from pathlib import Path

from lll import prediction_known_answer_identification_study as first


IDENTITY = first.IDENTITY+'-v2'
SCOPE = first.SCOPE


def recipe():
    return first.recipe()


def tasks():
    return first.tasks()


def require_first_failure(summary):
    expected = dict(bound_calls=404, bound_steps=1624,
                    native_calls=0, packet_visits=0)
    if (summary.get('state') != 'terminal' or summary.get('completed') != 4 or
            summary.get('passed') != 0 or summary.get('charged') != expected):
        raise ValueError('exact terminal first allowance and charges required')


def evaluate(task, context):
    result = first.evaluate(task, context)
    result['scientific_decision'] = 'abstain'
    return result


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), first.qualification_sources(root)+[
        'analysis/lll/prediction_known_answer_identification_v2.py',
        'analysis/tests/test_prediction_known_answer_identification_v2.py',
        'docs/prediction-known-answer-identification/PLAN_V2.md'])


def required_tests():
    return first.required_tests()+[
        'test_v2_preserves_exact_trial_and_declares_scientific_abstention',
        'test_v2_adapter_loads_directly',
        'test_prior_failure_must_be_exact_and_charged']


def prepare(root, *, qualification, recovery_qualification):
    from lll.ilvis0_control_shards import runtime_environment
    from lll.studies.artifacts import atomic, encoded
    from lll.studies.closed import ClosedStudy
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    from lll.studies.task_resume import (qualification_sources as recovery_sources,
                                         REQUIRED_TESTS as recovery_tests)
    if qualification is None or recovery_qualification is None:
        raise ValueError('source-bound software and recovery qualification required')
    root = Path(root).resolve()
    base = root/'data'/(IDENTITY+'-inputs')
    if base.exists() or (root/'data'/IDENTITY).exists():
        raise ValueError('fresh second allowance required')
    prior = ClosedStudy(root, 'data/'+first.IDENTITY)
    try:
        require_first_failure(prior.summary)
        if any(prior.envelope(name)['result'].get('reason') !=
               'one explicit software result and continued scientific abstention required'
               for name in prior.tasks):
            raise ValueError('first failure was not the exact result-schema failure')
        first_proof = dict(summary_sha256=prior.completion['summary_sha256'],
                           manifest_sha256=prior.completion['manifest_sha256'],
                           completed=4, charged=prior.summary['charged'])
    finally:
        prior.close()
    environment = runtime_environment()
    source_request, source_report = checked(
        root, qualification, sources=qualification_sources(root),
        environment=environment, required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    recovery_request, recovery_report = checked(
        root, recovery_qualification, sources=recovery_sources(root),
        environment=environment, required_tests=recovery_tests,
        minimum_tests=len(recovery_tests))
    material = dict(recipe=encoded(recipe()), first_failure=encoded(first_proof),
                    qualification_request=source_request,
                    qualification_report=source_report,
                    recovery_request=recovery_request,
                    recovery_report=recovery_report,
                    numerical_environment=encoded(environment))
    base.mkdir(parents=True)
    inputs = {}
    for name,blob in material.items():
        path = base/name
        atomic(path, blob)
        inputs[name] = path.relative_to(root).as_posix()
    definition = dict(id=IDENTITY, scope=SCOPE,
                      adapter='analysis/lll/prediction_known_answer_identification_v2.py',
                      sources=qualification_sources(root), inputs=inputs,
                      tasks=tasks(), workers=1, threads=1,
                      maximum_wall_s=recipe()['maximum_wall_s'])
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+IDENTITY, total=4,
                allocation=manifest['allocation'], limits=manifest['limits'])
