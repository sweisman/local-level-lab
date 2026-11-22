# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test counted trial-tangent curvature in the full generated native forecast."""
import argparse
from functools import partial
import json
from pathlib import Path

from . import tangent_secant_curvature_study as controls
from . import weak_curvature_flight_study as shared


ID = 'tangent-secant-flight-v1'
SCOPE = 'One earlier-only native generated flight with curvature from counted trial tangents'
PLAN = shared.BASE+'TANGENT_SECANT_FLIGHT_PLAN.md'
RESULT = shared.BASE+'tangent-secant-flight-result.json'
REQUEST = shared.BASE+'tangent-secant-flight-qualification.json'
XML = shared.BASE+'tangent-secant-flight-tests.xml'
CONTROL_SHA = 'be014e2bb3e5ef01ba47c5d390faf2fe91c4e0262b47e6bb14dc8e7a7230da1f'
TESTS = ('test_native_secant_uses_counted_tangents_without_a_residual_oracle',
         'test_native_secant_preserves_the_frozen_matched_flight_allowance')


def tasks():
    return shared.tasks('tangent_secant')


def solve_native(problem, model, *, start, maximum_evaluations, gauss_newton_fallback=False):
    from .ilvis0_solver_position import physical_residual_step
    from .residual_curvature_solver import fit_candidate

    safeguard = {'gauss_newton_fallback': True} if gauss_newton_fallback else {}
    fit = fit_candidate(problem, model, start=start, maximum_evaluations=maximum_evaluations,
                        physical_step=partial(physical_residual_step, problem), strong_restoration=True,
                        secant_curvature=True, **safeguard)
    fresh = 1+int('actual_cost_change' in fit['stability_probe'])
    if fit['evaluations'] != 1+len(fit['step_history'])+fresh:
        raise ValueError('native secant study requires only initial, trial and fresh calls')
    return dict(fit, active_parameters=list(problem.bounds.active),
                maximum_evaluations=maximum_evaluations, separate_derivative_probes=0)


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_tangent_secant_flight.py',
             'analysis/lll/ilvis0_tangent.cpp', 'analysis/lll/ilvis0_noise_bridge.cpp')
    sources, environment = source_closure(root, seeds), runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS,
            minimum_tests=len(TESTS))
    return sources, environment


def prepare(root):
    sources, environment = qualification(root, verify=True)
    return shared.prepare_flight(root, identity=ID, scope=SCOPE, plan=PLAN,
                                 adapter=Path(__file__).relative_to(root).as_posix(), declared_tasks=tasks(),
                                 sources=sources, environment=environment, request=REQUEST, xml=XML,
                                 control_path=controls.RESULT, control_id=controls.ID, control_sha=CONTROL_SHA,
                                 control_tasks=controls.TASKS)


def evaluate(task, context):
    return shared.evaluate_flight(task, context, scope=SCOPE, declared_tasks=tasks(), solver_provider=solve_native)


def recover(root):
    return shared.recover_flight(root, study_id=ID, task=tasks()[0])


def report(root):
    return shared.report_flight(root, study_id=ID, task=tasks()[0], destination=RESULT,
                                fit_statistic='secant_curvature_updates', result_statistic='secant_curvature_updates',
                                require_statistic=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
