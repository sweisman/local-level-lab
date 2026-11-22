# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare bounded solvers on curved residuals with exact global optima."""

from contextlib import closing
from pathlib import Path
import sys

from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'curved-bounded-solver-v2'
SCOPE = '24 generated bounded solver controls with known optima'
FOLDER = 'docs/prediction-group-transfer/'
PLAN = FOLDER + 'CURVED_BOUNDED_SOLVER_PLAN.md'
RESULT = FOLDER + 'curved-bounded-solver-result.json'
MAXIMUM_CALLS = 200
CASES = {'linear': (0., .20, 0., .50), 'interior': (.05, .20, .08, .002),
         'upper': (.05, 1.06, .08, .002), 'lower': (.05, -1.06, -.08, .002)}
STARTS = ((-.65, -.55), (.75, .60))
METHODS = ('trust_v2', 'trf', 'centered_lbfgsb')
TASKS = [dict(identity=f'{case}-{start}-{method}', input_key='design',
              payload=dict(case=case, start=start, method=method),
              limits=dict(native_calls=0, packet_visits=0, bound_calls=MAXIMUM_CALLS, bound_steps=0))
         for case in CASES for start in range(len(STARTS)) for method in METHODS]


class Bounds:
    active = ('x', 'y')

    def decode(self, point):
        import numpy as np
        point = np.asarray(point)
        if point.shape != (2,) or not np.isfinite(point).all() or np.any(abs(point) > 1.):
            raise ValueError('finite normalized box point required')
        return dict(zip(self.active, point.tolist(), strict=True))


class Control:
    bounds = Bounds()

    def __init__(self, case, charge):
        self.q, self.target, self.bend, self.slope = CASES[case]
        self.charge = charge
        self.calls = 0

    def residual_tangent(self, point, model):
        import numpy as np
        if model != 'generated':
            raise ValueError('generated optimization control required')
        self.charge(bound_calls=1, bound_steps=0)
        self.calls += 1
        x, y = point
        d = x - .25
        residual = np.array([102. + self.q*d*d, 20.*(y - self.target - self.bend*d*d), self.slope*d])
        jacobian = np.array([[2.*self.q*d, 0.], [-40.*self.bend*d, 20.], [self.slope, 0.]])
        return residual, jacobian, 0

    def exact_optimum(self):
        y = max(-1., min(1., self.target))
        return (.25, y), 102.**2 + (20.*(y-self.target))**2


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root / 'data' / ID).exists():
        raise ValueError('completed and interrupted runs remain frozen')
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, workers=1, threads=1,
        maximum_wall_s=60., tasks=TASKS, inputs=dict(design=PLAN),
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_curved_bounded_solver_study.py']))
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def evaluate(task, context):
    import numpy as np
    from .ilvis0_solver_trust_v2 import fit_candidate
    from .independent_bounded_solver import solve

    if context.manifest['scope'] != SCOPE or (task['identity'], task['payload']) not in [
            (row['identity'], row['payload']) for row in TASKS]:
        raise ValueError('frozen generated control required')
    context.input_path('design')
    case, start, method = (task['payload'][key] for key in ('case', 'start', 'method'))
    problem = Control(case, context.charge)

    def physical_step(change):
        return change.reshape(1, 3)

    if method == 'trust_v2':
        fit = fit_candidate(problem, 'generated', start=STARTS[start],
                            maximum_evaluations=MAXIMUM_CALLS, physical_step=physical_step)
        point, cost, stop, calls = (fit[key] for key in ('normalized_parameters', 'residual_sum_squares',
                                                      'converged', 'evaluations'))
    else:
        fit = solve(problem, 'generated', start=STARTS[start], method=method,
                    maximum_calls=MAXIMUM_CALLS, reserve=lambda **_: None, physical_step=physical_step)
        point, cost, stop, calls = (fit[key] for key in ('point', 'cost', 'original_gate_passed', 'native_calls_actual'))
    if problem.calls != calls:
        raise ValueError('bounded solver and task evaluation count differ')
    exact_point, exact_cost = problem.exact_optimum()
    gap = abs(cost-exact_cost) if cost is not None else None
    error = float(np.max(np.abs(np.asarray(point)-exact_point))) if point is not None else None
    result = dict(case=case, start=start, method=method, evaluations=calls,
        point=point, exact_point=list(exact_point), maximum_parameter_error=error, absolute_cost_gap=gap,
        stopping_passed=stop, scipy_success=fit.get('scipy_success'),
        passed=bool(stop and gap is not None and gap <= 1e-7 and error is not None and error <= 1e-4),
        scientific_decision='abstain')
    context.save_bytes('fit.json', encoded(fit))
    return result


def report(root):
    with closing(ClosedStudy(root, 'data/' + ID)) as study:
        if set(study.rows) != {task['identity'] for task in TASKS}:
            raise ValueError('all 24 generated tasks must be accounted for')
        rows = []
        for task in TASKS:
            identity = task['identity']
            result = study.envelope(identity)['result']
            if 'evaluations' in result:
                study.artifact(identity, 'fit.json', raw=True)
                if result['evaluations'] != study.rows[identity]['charged']['bound_calls']:
                    raise ValueError('saved evaluation charges differ')
            rows.append(dict(identity=identity, **result))
        result = dict(study_manifest_sha256=study.completion['manifest_sha256'],
            charged_calls=study.summary['charged']['bound_calls'], tasks=rows,
            observed_fits=0, protected_reads=0, scientific_decision='abstain')
    raw = encoded(result)
    destination = root / RESULT
    if not destination.exists():
        atomic(destination, raw)
    if destination.read_bytes() != raw:
        raise ValueError('generated optimizer report differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.curved_bounded_solver_study {prepare,report}')
