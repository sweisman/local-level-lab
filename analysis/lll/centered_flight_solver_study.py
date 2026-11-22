# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded full-pipeline flight controls for the centered objective solver."""

from contextlib import closing
from functools import partial
import json
from pathlib import Path
import sys

from . import ilvis0_long_independent_solver_study as longer
from .ilvis0_solver_matrix_core import make_tasks
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'centered-flight-solver-v1'
SCOPE = 'six short full-native generated forecast controls for the centered solver'
FOLDER = 'docs/prediction-group-transfer/'
PLAN = FOLDER + 'CENTERED_FLIGHT_SOLVER_PLAN.md'
RESULT = FOLDER + 'centered-flight-solver-result.json'
SOLVERS = ('trust_v2', 'centered_lbfgsb')
CASES = ('sphere_rotating-header_elapsed', 'sphere_still-nominal_200Hz', 'flat_still-header_elapsed')
QUERIES = 23
TRAINING = 15


def recipes():
    controls = longer.recipes()
    return {key: dict(controls[key], version=ID, duration_s=24., queries=QUERIES,
                     starts=1, workers=1, maximum_wall_s=210.) for key in CASES}


def tasks():
    return [task for task in make_tasks(recipes(), solvers=SOLVERS) if task['payload']['start'] == 0]


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID + '-inputs')
    if (root / 'data' / ID).exists() or directory.exists():
        raise ValueError('existing generated qualification must stay immutable')
    inputs = {}
    for key, value in recipes().items():
        filename = directory / (key + '.json')
        atomic(filename, encoded(value))
        inputs[key] = filename.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, [adapter, PLAN, 'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp', 'analysis/tests/test_centered_flight_solver_study.py'])
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, sources=sources, inputs=inputs,
                      workers=1, threads=1, maximum_wall_s=210., tasks=tasks())
    manifest = Definition.from_dict(definition, root).prepare(root)
    print(encoded(manifest['limits']).decode(), end='')


def evaluate(task, context):
    from .airquantumgrav_prediction import train_and_forecast
    from .ilvis0_independent_scipy_adapter import fit_candidate as scipy
    from .ilvis0_solver_trust_v2 import fit_candidate as trust
    from .structured_noisy_study import run_case

    if (context.manifest['scope'] != SCOPE or
            {key: value for key, value in task.items() if key not in ('index', 'shard')} not in tasks()):
        raise ValueError('exact generated task and scope required')
    key = task['input_key']
    recipe = recipes()[key]
    if json.loads(context.input_path(key).read_bytes()) != recipe:
        raise ValueError('generated training recipe differs from frozen task')
    method = task['payload']['solver']
    solver = trust if method == 'trust_v2' else partial(scipy, method='centered_lbfgsb')
    protocol = partial(train_and_forecast, solver_provider=solver)
    payload = {key: value for key, value in task['payload'].items() if key not in ('solver', 'sensor_case')}
    result = run_case(task, context, r=recipe, payload=payload, training_provider=protocol)
    if (result.get('forecast_saved_before_scoring') is not True or result.get('training_epochs') != TRAINING
            or result.get('prediction_epochs') != QUERIES-TRAINING
            or result.get('original_reads') != 0 or result.get('protected_reads') != 0):
        raise ValueError('complete earlier-only generated forecast required')
    return dict(result, passed=True, technical_completion_only=True,
        physical_accuracy_passed=bool(result['accuracy_all_sections']), solver=method,
        sensor_case=task['payload']['sensor_case'], scientific_decision='abstain')


def _paired_rows(cases):
    import numpy as np
    from .ilvis0_solver_position import physical_metric

    rows = []
    for key in CASES:
        pair = [cases[f'{key}-{method}-0'] for method in SOLVERS]
        spread = cost_gap = None
        if not any(row.get('technical_error') for row in pair):
            left, right = (np.asarray(row['forecast'], dtype=float) for row in pair)
            costs = [row['training_cost'] for row in pair]
            if (left.shape != (QUERIES, 3) or right.shape != left.shape
                    or not np.isfinite([left, right]).all() or not np.isfinite(costs).all()):
                raise ValueError('matched finite forecast arrays and costs required')
            a, b = left[TRAINING:], right[TRAINING:]
            spread = float(np.max(np.linalg.norm((a-b)*physical_metric(a), axis=1)))
            cost_gap = abs(costs[0]-costs[1])
        rows.append(dict(fixture=key, maximum_later_spread_m=spread, absolute_training_cost_gap=cost_gap,
            passed=bool(spread is not None and spread <= .1 and cost_gap <= .01
                        and all(row['converged'] and row['physical_accuracy_passed'] for row in pair))))
    return rows


def _interrupted_training_attempts(run, identity, bindings):
    if not {'native-prepayment.json', 'input-binding.json'} <= bindings:
        return None
    prepayment = run.artifact(identity, 'native-prepayment.json')
    binding = run.artifact(identity, 'input-binding.json')
    if 'fit.json' in bindings or prepayment['state'] != 'failed_or_interrupted':
        return None
    # Before the fit is saved, bridge operations visit one item each and
    # each native training tangent visits the complete prefix-by-report grid.
    work = prepayment['attempted']
    tangent_visits = binding['training_prefix_packets'] * binding['training_epochs']
    if tangent_visits <= 1:
        raise ValueError('exact pre-forecast tangent accounting required')
    calls, leftover = divmod(work['packet_visits'] - work['native_calls'], tangent_visits - 1)
    if leftover or not 0 <= calls <= work['native_calls']:
        raise ValueError('pre-forecast attempted operations do not reconcile')
    return calls


def report(root):
    import numpy as np
    from .ilvis0_solver_matrix_report_core import case_from_study

    with closing(ClosedStudy(root, 'data/' + ID)) as run:
        if (set(run.tasks) != {task['identity'] for task in tasks()}
                or any(run.input(key) != value for key, value in recipes().items())):
            raise ValueError('exact generated forecast study required')
        cases = {}
        norms = {}
        for task in tasks():
            identity = task['identity']
            if identity not in run.rows:
                cases[identity] = dict(identity=identity, **task['payload'],
                    disposition='unstarted_at_close', technical_error='no sealed result')
                continue
            envelope = run.envelope(identity)
            if not envelope['result'].get('technical_completion_only'):
                bound_files = {name.rsplit('/', 1)[-1] for name in envelope['artifacts']}
                cases[identity] = dict(identity=identity, **task['payload'], disposition='started_without_result',
                    technical_error=envelope['result'].get('reason', 'missing completed forecast'),
                    attempted_training_tangents=_interrupted_training_attempts(run, identity, bound_files))
                continue
            cases[identity] = case_from_study(run, identity, task, total_epochs=QUERIES, training_epochs=TRAINING)
            cases[identity]['disposition'] = 'completed_forecast'
            if task['payload']['solver'] == 'trust_v2':
                fit = run.artifact(identity, 'fit.json')
                jac = np.asarray(fit['local_linearization']['jacobian'], dtype=float)
                column_norms = np.linalg.norm(jac, axis=0)
                lower, upper = int(np.argmin(column_norms)), int(np.argmax(column_norms))
                norms[identity] = dict(smallest_column=fit['active_parameters'][lower],
                    smallest_norm=float(column_norms[lower]), largest_column=fit['active_parameters'][upper],
                    largest_norm=float(column_norms[upper]),
                    norm_ratio=float(column_norms[upper] / column_norms[lower]) if column_norms[lower] > 0 else None)
        for key in CASES:
            pair = [f'{key}-{method}-0' for method in SOLVERS]
            if all('forecast' in cases[identity] for identity in pair):
                a, b = [run.artifact(identity, 'input-binding.json') for identity in pair]
                if a != b:
                    raise ValueError('only the solver may change in a matched pair')
        rows = _paired_rows(cases)
        result = dict(manifest_sha256=run.completion['manifest_sha256'], charged=run.summary['charged'],
            fit_results=[{key: value for key, value in row.items() if key != 'forecast'} for row in cases.values()],
            pair_results=rows, qualifying_pairs=sum(row['passed'] for row in rows), training_column_norms=norms,
            observed_reads=0, protected_reads=0, scientific_decision='abstain')
    raw = encoded(result)
    path = root / RESULT
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('saved generated flight result differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.centered_flight_solver_study {prepare,report}')
