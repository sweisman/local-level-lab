# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check full and QR-reduced bounded corrections on saved linear controls."""

import argparse
from contextlib import closing
import json
from pathlib import Path

from . import scaled_solver_replay as prior
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'qr-solver-replay-v1'
SCOPE = 'Direct and QR-reduced BVLS on the seven exact scaled-solver linear controls'
PLAN = prior.FOLDER+'QR_SOLVER_REPLAY_PLAN.md'
RESULT = prior.FOLDER+'qr-solver-replay-result.json'
PARENT_SHA = '9464d315a120ec524faf567cb1cf5453a35c2aee96c5b8cf57e62c36246f76fc'
PARENT_COMPLETION_SHA = '6bd4325f86e18d272d963693736c5d3e49af0c187f0ba541597315918ab3bf2d'
TEST = 'analysis/tests/test_qr_solver_replay.py'
TESTS = ('test_qr_preserves_objective_differences_with_a_large_perpendicular_residual',
         'test_qr_keeps_a_weak_direction_and_the_original_coordinate_bounds')
REQUEST, XML = (f'data/{ID}-inputs/{name}' for name in ('qualification.json', 'tests.xml'))
TASKS = {key: dict(identity=key, input_key=key, payload={},
                  limits=dict(native_calls=0, packet_visits=0, bound_calls=9, bound_steps=0))
         for key in prior.PARENTS}
LINEAR_LIMIT = 1e-4


def reduced_system(tangent, residual):
    """Project onto the QR columns without dropping weak parameter directions."""
    import numpy as np

    design, target = np.asarray(tangent, dtype=float), np.asarray(residual, dtype=float)
    if (design.ndim != 2 or not 0 < design.shape[1] <= len(design)
            or target.shape != (len(design),)
            or not np.isfinite(design).all() or not np.isfinite(target).all()):
        raise ValueError('finite tall tangent and matching residual required')
    q, r = np.linalg.qr(design, mode='reduced')
    return r, q.T@target


def qualification(root, *, check=False):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST))
    environment = runtime_environment()
    if not check:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources, environment


def prepare(root):
    from .esa_calibration_conditioned_margin import RECOVER, RECOVERY
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('retain the frozen linear replay')
    sources, environment = qualification(root, check=True)
    raw = (root/prior.RESULT).read_bytes()
    if digest(raw) != PARENT_SHA:
        raise ValueError('the original scaled solver result is required')
    report = json.loads(raw)
    with closing(ClosedStudy(root, 'data/'+prior.ID)) as study:
        expected = {task['identity'] for task in prior.TASKS}
        if (study.completion['manifest_sha256'] != PARENT_COMPLETION_SHA
                or report['manifest_sha256'] != PARENT_COMPLETION_SHA
                or set(study.rows) != expected or len(report['results']) != len(expected)
                or {row['identity'] for row in report['results']} != expected
                or study.summary['charged']['bound_calls'] != report['charged_calls']):
            raise ValueError('the exact closed prior results, including failures, are required')
        for row in report['results']:
            saved = study.envelope(row['identity'])['result']
            if saved != {key: value for key, value in row.items() if key != 'identity'}:
                raise ValueError('the published prior outcome differs from its envelope')
        material = {key: study.input(key, raw=True) for key in TASKS}
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    files = dict(plan=PLAN, qualification=REQUEST, tests=XML, prior=prior.RESULT)
    for key, value in dict(material, recovery=recovery, recovery_tests=tests,
                           recovery_policy=encoded(RECOVER)).items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, value)
        files[key] = path
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                      inputs=files, sources=sources, tasks=list(TASKS.values()), workers=1, threads=1, maximum_wall_s=90)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np
    from scipy.optimize import lsq_linear

    from .ilvis0_solver_boundary import snap_bounds
    from .ilvis0_solver_position import verify_stability
    from .ilvis0_solver_trust_v2 import POLICY

    identity = task['identity']
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASKS.get(identity):
        raise ValueError('the exact saved linear control is required')
    raw = json.loads(context.input_path(identity).read_bytes())
    problem = prior.LinearControl(raw, context.charge)
    start = np.zeros(len(problem.active))
    if len(start) != 26:
        raise ValueError('all original calibration columns must be retained')

    def evaluate_point(point, fresh=False):
        return problem.residual_tangent(point, 'generated')

    base, tangent, _ = evaluate_point(start)
    results = {}
    for method in ('direct', 'qr_reduced'):
        context.charge(bound_calls=1, bound_steps=0)
        design, residual = reduced_system(tangent, base) if method == 'qr_reduced' else (tangent, base)
        fit = lsq_linear(design, -residual, bounds=(-1., 1.), method='bvls',
                         tol=POLICY['linear_tolerance'], max_iter=POLICY['linear_maximum_iterations'])
        if not fit.success or not np.isfinite(fit.x).all():
            results[method] = dict(passed=False, linear_solve_passed=False)
            continue
        point = snap_bounds(fit.x)
        final, jac, _ = evaluate_point(point)
        context.charge(bound_calls=1, bound_steps=0)
        probe = verify_stability(point, final, jac, evaluate_point, lambda delta: delta.reshape(-1, 3))
        prediction = problem.jacobian@(point-problem.target)
        maximum = float(np.max(abs(prediction)))
        results[method] = dict(passed=bool(probe['passed'] and maximum <= LINEAR_LIMIT),
            linear_solve_passed=True, maximum_whitened_residual=maximum,
            maximum_parameter_error=float(np.max(abs(point-problem.target))),
            excess_squared_error=float(prediction@prediction), fresh_check=probe,
            active_at_bounds=int(np.count_nonzero(abs(point)==1.)), design_rows=len(design))
    return dict(passed=all(row['passed'] for row in results.values()), methods=results,
                source_fit_sha256=raw['fit_sha256'], columns=len(start),
                observed_reads=0, protected_reads=0, native_evaluations=0, scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if set(study.rows) != set(TASKS):
            raise ValueError('complete sealed results or failures required')
        rows = []
        for identity in TASKS:
            envelope = study.envelope(identity)
            charge = envelope['charged']
            if (charge != study.rows[identity]['charged'] or not 0 <= charge['bound_calls'] <= 9
                    or any(charge[key] for key in ('native_calls', 'packet_visits', 'bound_steps'))):
                raise ValueError('unexpected saved linear replay charges')
            rows.append(dict(identity=identity, charged=charge, **envelope['result']))
        result = dict(results=rows, completion=study.completion, charged=study.summary['charged'],
                      observed_reads=0, protected_reads=0, native_evaluations=0, scientific_decision='abstain')
    _write_equal(root/RESULT, encoded(result))
    return dict(tasks=len(rows), passed=sum(row['passed'] for row in rows), charged=result['charged'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = {'request': qualification, 'prepare': prepare, 'report': report}[parser.parse_args().action]
    print(json.dumps(action(Path.cwd()), sort_keys=True))
