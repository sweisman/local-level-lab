# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prospective known-answer tests for the optional curvature retry."""
import argparse
from contextlib import ExitStack, closing
import json
from pathlib import Path

from .curved_bounded_solver_study import Bounds, FOLDER
from .esa_calibration_conditioned_margin import RECOVER, RECOVERY
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import encoded
from .studies.closed import ClosedStudy


ID = 'curvature-retry-controls-v1'
SCOPE = 'Generated curved residuals with known bounded optima and optional fractional retry'
PLAN = FOLDER+'CURVATURE_RETRY_CONTROLS_PLAN.md'
RESULT = FOLDER+'curvature-retry-controls-result.json'
REQUEST = FOLDER+'curvature-retry-controls-qualification.json'
XML = FOLDER+'curvature-retry-controls-tests.xml'
TESTS = ('test_curved_fraction_recovers_quadratic_residual_minimum',
         'test_curvature_retry_uses_one_shorter_step_and_preserves_gate')
RECOVERY_RULE = RECOVER | dict(maximum_wall_s=60)
CAP = 40
# target X, target Y, curve strength, large residual, bend, weak X slope
CASES = dict(interior=(.23, .19, .9, 51., .45, .03),
             upper=(1.17, -.21, .75, 102., -.60, .022),
             lower=(-1.23, .30, .61, 90., .68, .031),
             weak=(.35, -.23, 8e-5, 151., .37, 5e-7))
STARTS = ((-.81, -.64), (.82, .53))
TASKS = [dict(identity=f'{case}-{index}-{arm}', input_key='design',
              payload=dict(case=case, start=index, arm=arm),
              limits=dict(native_calls=0, packet_visits=0, bound_calls=CAP, bound_steps=0))
         for case in CASES for index in range(len(STARTS)) for arm in ('original', 'curvature')]


class Control:
    bounds = Bounds()

    def __init__(self, case, charge):
        self.tx, self.ty, self.q, self.offset, self.bend, self.slope = CASES[case]
        self.x_opt = min(1., max(-1., self.tx))
        self.charge = charge
        self.calls = 0

    def residual_tangent(self, point, model):
        import numpy as np

        if model != 'generated':
            raise ValueError('generated bounded controls required')
        self.charge(bound_calls=1, bound_steps=0)
        self.calls += 1
        x, y = point
        dx, toward_face = x-self.tx, x-self.x_opt
        residual = np.array([self.offset+self.q*dx**2,
                             25.*(y-self.ty-self.bend*toward_face**2), self.slope*dx])
        jac = np.array([[2*self.q*dx, 0.], [-50*self.bend*toward_face, 25.], [self.slope, 0.]])
        return residual, jac, 0

    def exact_optimum(self):
        dx = self.x_opt-self.tx
        return [self.x_opt, self.ty], (self.offset+self.q*dx**2)**2+(self.slope*dx)**2


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_curved_step.py')
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
        raise ValueError('retain the original finite solver allowance')
    sources, environment = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    inputs = dict(design=PLAN, qualification=REQUEST, qualification_tests=XML)
    for key, value in dict(recovery=recovery, recovery_tests=tests,
                           recovery_policy=encoded(RECOVERY_RULE)).items():
        filename = f'data/{ID}-inputs/{key}'
        _write_equal(root/filename, value)
        inputs[key] = filename
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=TASKS, workers=1, threads=1,
                                     maximum_wall_s=60), root).prepare(root)['limits']


def evaluate(task, context):
    from .ilvis0_solver_trust_v2 import fit_candidate

    if (context.manifest['scope'] != SCOPE
            or {k: v for k, v in task.items() if k not in ('index', 'shard')} not in TASKS):
        raise ValueError('frozen generated pair required')
    context.input_path('design')
    case, start, arm = (task['payload'][key] for key in ('case', 'start', 'arm'))
    problem = Control(case, context.charge)
    fit = fit_candidate(problem, 'generated', start=STARTS[start], maximum_evaluations=CAP,
                        physical_step=lambda delta: delta.reshape((1, 3)), curvature_retry=(arm == 'curvature'))
    if problem.calls != fit['evaluations']:
        raise ValueError('charged evaluation count differs')
    point, cost = problem.exact_optimum()
    error = max(abs(a-b) for a, b in zip(point, fit['normalized_parameters'], strict=True))
    gap = abs(cost-fit['residual_sum_squares'])
    accepted = sum(row['accepted'] for row in fit['step_history'] if row.get('method') == 'curvature_retry')
    verdict = dict(case=case, start=start, arm=arm, evaluations=problem.calls,
                   accepted_fractional_steps=accepted, parameter_error=error, cost_gap=gap,
                   fresh_position_passed=fit['converged'], message=fit['message'],
                   passed=bool(fit['converged'] and error <= 1e-4 and gap <= 1e-7), scientific_decision='abstain')
    context.save('fit.json', fit)
    return verdict


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
            study = original
            if origin != prefix:
                study = stack.enter_context(closing(ClosedStudy(root, origin, store=original.store)))
            row = study.envelope(identity)
            outcome = row['result']
            if row['status'] != 'complete' or row['charged']['bound_calls'] != outcome['evaluations']:
                raise ValueError('all declared generated fit charges are required')
            study.artifact(identity, 'fit.json', raw=True)
            rows.append(dict(identity=identity, origin=origin, **outcome))
        curvature = [r for r in rows if r['arm'] == 'curvature']
        passed = all(r['passed'] for r in curvature) and any(r['accepted_fractional_steps'] for r in curvature)
        summary = dict(curvature_passes=sum(r['passed'] for r in curvature),
                       original_passes=sum(r['passed'] for r in rows if r['arm'] == 'original'),
                       cases_with_accepted_retry=sum(r['accepted_fractional_steps'] > 0 for r in curvature),
                       qualification_passed=passed, observed_fits=0, protected_reads=0)
        _write_equal(root/RESULT, encoded(dict(summary=summary, tasks=rows, completion=original.completion)))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
