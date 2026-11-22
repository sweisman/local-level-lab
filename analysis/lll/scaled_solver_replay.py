# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test the scaled bounded solver against exact saved-derivative controls."""

from contextlib import closing
import json
from pathlib import Path
import sys

from .curved_bounded_solver_study import MAXIMUM_CALLS
from .ilvis0_long_independent_solver_study import case_key, CLOCKS, MODELS
from .independent_bounded_solver import column_scale, solve
from .studies.artifacts import ArchiveStore, atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'scaled-solver-replay-v1'
SCOPE = 'seven saved generated flight derivatives and two bounded solvers'
FOLDER = 'docs/prediction-group-transfer/'
PLAN = FOLDER + 'SCALED_SOLVER_REPLAY_PLAN.md'
RESULT = FOLDER + 'scaled-solver-replay-result.json'
LONG = ('data/ilvis0-long-independent-solver-v1-20261118',
        'e0a97a251ce0c1c74fdd45466960eabe3c6fb92c560e1d3323e96586b6a0d8b6')
SHORT = ('data/centered-flight-solver-v1',
         '0e314e0c404cad027ebc88a33ac3d74e7d1bbb1d0eb5a195d5d689dd60a950f3')
PARENTS = {f'long-{case_key(model, clock)}': (LONG, case_key(model, clock) + '-trust_v2-0')
           for model in MODELS for clock in CLOCKS}
PARENTS['short-sphere_rotating-header_elapsed'] = (SHORT, 'sphere_rotating-header_elapsed-trust_v2-0')
METHODS = ('centered_lbfgsb', 'centered_scaled_lbfgsb')
TASKS = [dict(identity=f'{key}-{method}', input_key=key, payload=dict(source=key, method=method),
              limits=dict(native_calls=0, packet_visits=0, bound_calls=MAXIMUM_CALLS, bound_steps=0))
         for key in PARENTS for method in METHODS]


class LinearControl:
    def __init__(self, material, charge):
        import numpy as np

        self.active = tuple(material['active_parameters'])
        self.jacobian = np.asarray(material['jacobian'], float)
        original = np.asarray(material['normalized_parameters'], float)
        self.decode(original)
        if (self.jacobian.ndim != 2 or self.jacobian.shape[1] != len(self.active)
                or len(self.jacobian) % 3 or not np.isfinite(self.jacobian).all()):
            raise ValueError('finite three-axis linear problem and complete columns required')
        self.target = np.where(abs(original) >= .99, np.sign(original), original)
        self.full_jacobian = np.vstack((self.jacobian, np.zeros((3, len(self.active)))))
        self.bounds = self
        self.charge = charge

    def decode(self, point):
        import numpy as np

        values = np.asarray(point, float)
        if (values.shape != (len(self.active),) or not np.isfinite(values).all()
                or np.any(abs(values) > 1)):
            raise ValueError('finite normalized feasible point required')
        return dict(zip(self.active, values.tolist(), strict=True))

    def residual_tangent(self, point, model):
        import numpy as np

        self.charge(bound_calls=1, bound_steps=0)
        return np.r_[self.jacobian @ (point-self.target), 102., 0., 0.], self.full_jacobian, 0


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID + '-inputs')
    if (root / 'data' / ID).exists() or directory.exists():
        raise ValueError('frozen saved-derivative study must be preserved')
    inputs = {}
    with closing(ArchiveStore(root)) as store:
        for path, expected in (LONG, SHORT):
            with closing(ClosedStudy(root, path, store=store)) as parent:
                if parent.completion['manifest_sha256'] != expected:
                    raise ValueError('exact generated training parent required')
                for key, (parent_key, identity) in PARENTS.items():
                    if parent_key[0] != path:
                        continue
                    fit = parent.artifact(identity, 'fit.json')
                    linear = fit['local_linearization']
                    if (not parent.rows[identity]['passed'] or not fit['converged']
                            or len(set(linear['active_parameters'])) != 26
                            or linear['normalized_parameters'] != fit['normalized_parameters']):
                        raise ValueError('complete passing fit with all calibration columns required')
                    material = {key: linear[key] for key in ('jacobian', 'active_parameters', 'normalized_parameters')}
                    material.update(parent_manifest_sha256=expected, fit_sha256=parent.envelope(identity)['artifacts'][
                        f'artifacts/{identity}/fit.json'])
                    target = directory / (key + '.json')
                    atomic(target, encoded(material))
                    inputs[key] = target.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, sources=source_closure(root, [adapter, PLAN,
        'analysis/tests/test_scaled_solver_replay.py']), inputs=inputs, tasks=TASKS, workers=1, threads=1,
        maximum_wall_s=90.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def evaluate(task, context):
    import numpy as np

    if (context.manifest['scope'] != SCOPE or
            {key: value for key, value in task.items() if key not in ('index', 'shard')} not in TASKS):
        raise ValueError('exact generated replay task required')
    material = json.loads(context.input_path(task['input_key']).read_bytes())
    problem = LinearControl(material, context.charge)
    if len(problem.active) != 26:
        raise ValueError('all 26 original calibration columns required')
    method = task['payload']['method']
    fit = solve(problem, 'generated', start=np.zeros(len(problem.active)), method=method,
                maximum_calls=MAXIMUM_CALLS, reserve=lambda **_: None,
                physical_step=lambda d: d.reshape(-1, 3))
    context.save_bytes('fit.json', encoded(fit))
    error = np.asarray(fit['point']) - problem.target
    prediction = problem.jacobian @ error
    scale = column_scale(problem.jacobian)
    raw = np.linalg.svd(problem.jacobian, compute_uv=False)
    scaled = np.linalg.svd(problem.jacobian/scale, compute_uv=False)
    maximum = float(np.max(abs(prediction)))
    return dict(method=method, source=task['input_key'], source_fit_sha256=material['fit_sha256'],
        passed=bool(fit['original_gate_passed'] and maximum <= .0001),
        evaluations=fit['native_calls_actual'], scipy_success=fit['scipy_success'],
        stopping_passed=fit['original_gate_passed'], maximum_whitened_residual=maximum,
        excess_squared_error=float(prediction @ prediction), maximum_parameter_error=float(np.max(abs(error))),
        column_norm_ratio=float(max(scale)/min(scale)), condition=float(raw[0]/raw[-1]) if raw[-1] else None,
        scaled_condition=float(scaled[0]/scaled[-1]) if scaled[-1] else None, scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/' + ID)) as study:
        if set(study.rows) != {task['identity'] for task in TASKS}:
            raise ValueError('all saved derivative qualification tasks required')
        rows = []
        for task in TASKS:
            identity = task['identity']
            row = study.envelope(identity)['result']
            if 'evaluations' in row:
                study.artifact(identity, 'fit.json', raw=True)
                if row['evaluations'] != study.rows[identity]['charged']['bound_calls']:
                    raise ValueError('sealed linear call charges differ')
            rows.append(dict(identity=identity, **row))
        result = dict(manifest_sha256=study.completion['manifest_sha256'], results=rows, native_evaluations=0,
            observed_reads=0, protected_reads=0, charged_calls=study.summary['charged']['bound_calls'],
            scientific_decision='abstain')
    raw = encoded(result)
    output = root / RESULT
    if not output.exists():
        atomic(output, raw)
    if output.read_bytes() != raw:
        raise ValueError('saved scaling report differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.scaled_solver_replay {prepare,report}')
