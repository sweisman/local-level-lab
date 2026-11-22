# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare safeguarded trial tangents with three sealed flight references."""
import argparse
from contextlib import ExitStack, closing
from functools import partial
import json
from pathlib import Path

from . import tangent_secant_geometry_study as geometry
from . import weak_curvature_flight_study as shared
from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_solver_matrix_core import make_tasks
from .ilvis0_solver_matrix_report_core import case_from_study
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'tangent-secant-fallback-v1'
SCOPE = 'Three matched generated flights with a bounded Gauss–Newton safeguard'
PLAN = shared.BASE+'TANGENT_SECANT_FALLBACK_PLAN.md'
RESULT = shared.BASE+'tangent-secant-fallback-result.json'
REQUEST = shared.BASE+'tangent-secant-fallback-qualification.json'
XML = shared.BASE+'tangent-secant-fallback-tests.xml'
GEOMETRY_SHA = '9d25bbd530c95abbae9dbedc54e08b3bf84b21a6594d301982d0440dba44b177'
KEYS = (shared.KEY, *geometry.KEYS)
FALLBACK_REQUIRED = 'sphere_still-nominal_200Hz'
SOLVER = 'tangent_secant_fallback'
TESTS = ('test_secant_fallback_changes_direction_and_preserves_fresh_gate',
         'test_fallback_study_changes_only_the_solver_on_three_recipes')


def tasks():
    recipes = {key: shared.ref.recipes()[key] for key in KEYS}
    return [task for task in make_tasks(recipes, solvers=(SOLVER,)) if task['payload']['start'] == 0]


def qualification(root, *, verify):
    return geometry.qualify(root, verify=verify, adapter=__file__, plan=PLAN, required_tests=TESTS,
                            test_files=('analysis/tests/test_residual_curvature_solver.py',
                                        'analysis/tests/test_tangent_secant_geometry.py'),
                            request_path=REQUEST, xml=XML)


def references(root, stack):
    raw = (root/geometry.RESULT).read_bytes()
    if digest(raw) != GEOMETRY_SHA:
        raise ValueError('exact prior completed geometry report required')
    receipt = json.loads(raw)
    rotated, _ = shared.baseline(root, stack)
    remaining = stack.enter_context(closing(ClosedStudy(root, 'data/'+geometry.ID)))
    if remaining.completion != receipt['completion']:
        raise ValueError('mismatched earlier geometry completion')
    result = dict.fromkeys(KEYS, remaining)
    result[shared.KEY] = rotated
    for key, source in result.items():
        reference = f'{key}-trust_v2-0'
        if (source.input(key) != shared.ref.recipes()[key]
                or source.envelope(reference)['result']['passed'] is not True):
            raise ValueError('unchanged generated recipe and passing reference required')
    return result


def freeze_recipes(root):
    with ExitStack() as stack:
        return {key: source.input(key, raw=True) for key, source in references(root, stack).items()}


def prepare(root):
    return geometry.prepare_geometry(
        root, study_id=ID, scope=SCOPE, adapter=__file__, declared_tasks=tasks(), workers=3,
        qualify_study=qualification, freeze_recipes=freeze_recipes,
        inputs=dict(plan=PLAN, reference=shared.ref.RESULT, geometry=geometry.RESULT,
                    qualification=REQUEST, qualification_tests=XML))


def evaluate(task, context):
    solver = partial(geometry.first.solve_native, gauss_newton_fallback=True)
    return shared.evaluate_flight(task, context, scope=SCOPE, declared_tasks=tasks(), solver_provider=solver)


def report(root):
    prefix = 'data/'+ID
    continuation = root/(prefix+'-recovery')
    with ExitStack() as stack:
        baseline = references(root, stack)
        original = stack.enter_context(closing(ClosedStudy(root, prefix)))
        selected = {}
        if continuation.is_dir():
            from .studies.combined_task_evidence import inspect

            selected = inspect(root, continuation)['selected']
        pairs = []
        for task in tasks():
            key, identity = task['input_key'], task['identity']
            origin = selected.get(identity, {}).get('origin', prefix)
            source = original if origin == prefix else stack.enter_context(
                closing(ClosedStudy(root, origin, store=original.store)))
            reference = baseline[key]
            reference_id = f'{key}-trust_v2-0'
            shape = dict(total_epochs=shared.ref.QUERIES, training_epochs=shared.ref.TRAINING)
            ref = case_from_study(reference, reference_id, reference.tasks[reference_id], **shape)
            fit = case_from_study(source, identity, task, **shape) if identity in source.rows else {
                'identity': identity, 'technical_error': 'no sealed candidate'}
            updates, probes, attempts, accepted, matched = 0, None, 0, 0, False
            if 'forecast' in fit:
                details = source.artifact(identity, 'fit.json')
                fallback = [step for step in details['step_history'] if step.get('direction') == 'gauss_newton']
                attempts, accepted = len(fallback), sum(step['accepted'] for step in fallback)
                updates, probes = details['secant_curvature_updates'], details['separate_derivative_probes']
                matched = reference.artifact(reference_id, 'input-binding.json') == source.artifact(
                    identity, 'input-binding.json')
            comparison = geometry.compare(ref, fit, matched_inputs=matched, updates=updates, probes=probes)
            passed = comparison['passed'] and (key != FALLBACK_REQUIRED or accepted > 0)
            ref.pop('forecast', None)
            fit.pop('forecast', None)
            pairs.append(dict(comparison, passed=passed, fixture=key, reference=ref, candidate=fit, origin=origin,
                              fallback_trials=attempts, accepted_fallback_trials=accepted))
        summary = dict(qualified=all(row['passed'] for row in pairs), passing_pairs=sum(row['passed'] for row in pairs),
                       original_reads=0, protected_reads=0, scientific_decision='abstain')
        _write_equal(root/RESULT, encoded(dict(summary=summary, pairs=pairs, completion=original.completion,
                                               charged=original.summary['charged'], geometry_sha256=GEOMETRY_SHA)))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {
        'prepare': prepare, 'recover': partial(geometry.recover_geometry, study_id=ID), 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
