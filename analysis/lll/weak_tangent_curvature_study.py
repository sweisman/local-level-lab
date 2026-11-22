# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded weak-direction Hessian probes on the frozen generated controls."""
import argparse
from contextlib import ExitStack, closing
import json
from pathlib import Path

from .direct_residual_change_study import fit_control, matched_outcomes
from .ilvis0_matched_observed_inputs import _write_equal
from .residual_curvature_study import FOLDER, RECOVERY, RECOVERY_RULE, TASKS as PRIOR_TASKS
from .strong_residual_restore_study import ID as PRIOR_ID, RESULT as PRIOR
from .studies.artifacts import encoded
from .studies.closed import ClosedStudy


ID = 'weak-tangent-curvature-v1'
SCOPE = 'Generated box controls with curvature probes in the weak tangent space'
PLAN = FOLDER+'WEAK_TANGENT_CURVATURE_PLAN.md'
RESULT = FOLDER+'weak-tangent-curvature-result.json'
REQUEST = FOLDER+'weak-tangent-curvature-qualification.json'
XML = FOLDER+'weak-tangent-curvature-tests.xml'
PRIOR_SHA = '3d3db24fd160b1d1146d5f082359e0ac18f401764ccd21fe35cfd40bb6a562b1'
TASKS = [task for task in PRIOR_TASKS if task['payload']['method'] == 'differences']
TESTS = ('test_directional_tangent_curvature_keeps_the_weak_and_cross_terms',
         'test_directional_tangent_curvature_uses_feasible_one_sided_probes',
         'test_directional_tangent_curvature_falls_back_before_infeasible_work')


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_weak_tangent_curvature.py')
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
        raise ValueError('retain the original weak-curvature allowance')
    sources, environment = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    matched_outcomes(root, PRIOR, PRIOR_SHA, PRIOR_ID)
    inputs = dict(design=PLAN, prior=PRIOR, qualification=REQUEST, qualification_tests=XML)
    for key, value in dict(recovery=recovery, recovery_tests=tests,
                           recovery_policy=encoded(RECOVERY_RULE)).items():
        filename = f'data/{ID}-inputs/{key}'
        _write_equal(root/filename, value)
        inputs[key] = filename
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=TASKS, workers=1, threads=1,
                                     maximum_wall_s=60), root).prepare(root)['limits']


def evaluate(task, context):
    if (context.manifest['scope'] != SCOPE
            or {k: v for k, v in task.items() if k not in ('index', 'shard')} not in TASKS):
        raise ValueError('frozen weak-curvature control required')
    return fit_control(task, context, strong_restoration=True, weak_curvature=True)


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
            if all(key in study.rows and study.envelope(key)['status'] == 'complete' for key in study.tasks):
                return dict(state='original_tasks_finished', pending=0)
        prepare_campaign(root, prefix, continuation, qualification_request=RECOVERY, **RECOVERY_RULE)
    return resume_campaign(root, continuation)


def report(root):
    prefix = 'data/'+ID
    continuation = root/(prefix+'-recovery')
    prior = matched_outcomes(root, PRIOR, PRIOR_SHA, PRIOR_ID)
    with ExitStack() as stack:
        original = stack.enter_context(closing(ClosedStudy(root, prefix)))
        selected = {}
        if continuation.is_dir():
            from .studies.combined_task_evidence import inspect

            selected = inspect(root, continuation)['selected']
        rows = []
        for task in TASKS:
            identity = task['identity']
            origin = selected.get(identity, {}).get('origin', prefix)
            source = original
            if origin != prefix:
                source = stack.enter_context(closing(ClosedStudy(root, origin, store=original.store)))
            envelope = source.envelope(identity)
            outcome = envelope['result']
            if envelope['status'] != 'complete' or outcome['evaluations'] != envelope['charged']['bound_calls']:
                raise ValueError('all weak-curvature charges are required')
            source.artifact(identity, 'fit.json', raw=True)
            reference = prior[identity]
            rows.append(dict(identity=identity, origin=origin, prior_passed=reference['passed'],
                             prior_evaluations=reference['evaluations'], **outcome))
        count = sum(row['passed'] for row in rows)
        probes = sum(row['weak_curvature_estimates'] for row in rows)
        summary = dict(passed=count, qualified=count == len(TASKS) and probes > 0,
                       weak_curvature_estimates=probes, observed_fits=0, protected_reads=0)
        _write_equal(root/RESULT, encoded(dict(summary=summary, tasks=rows, completion=original.completion,
                                               original_outcome_sha256=PRIOR_SHA)))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
