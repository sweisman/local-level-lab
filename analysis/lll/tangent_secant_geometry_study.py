# SPDX-License-Identifier: AGPL-3.0-or-later
"""Complete the two missing matched geometries without reopening aircraft data."""
import argparse
from contextlib import ExitStack, closing
import json
from pathlib import Path

from . import tangent_secant_flight_study as first
from . import weak_curvature_flight_study as shared
from .esa_calibration_conditioned_margin import RECOVERY
from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_solver_matrix_core import make_tasks
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'tangent-secant-geometry-v1'
SCOPE = 'Matched zero-field globe and stationary disc generated native flights'
PLAN = shared.BASE+'TANGENT_SECANT_GEOMETRY_PLAN.md'
RESULT = shared.BASE+'tangent-secant-geometry-result.json'
REQUEST = shared.BASE+'tangent-secant-geometry-qualification.json'
XML = shared.BASE+'tangent-secant-geometry-tests.xml'
FIRST_SHA = 'bc740b01e49f62dc4a1fa25d5395fe561b883e2e27925dbf9ad67f52eacf2bd2'
KEYS = ('sphere_still-nominal_200Hz', 'flat_still-header_elapsed')
SOLVERS = ('trust_v2', 'tangent_secant')
TESTS = ('test_secant_geometry_keeps_both_frozen_native_pairs',
         'test_secant_geometry_requires_both_gates_and_the_counted_update')


def recipes():
    return {key: shared.ref.recipes()[key] for key in KEYS}


def tasks():
    return [task for task in make_tasks(recipes(), solvers=SOLVERS) if task['payload']['start'] == 0]


def qualification(root, *, verify):
    return qualify(root, verify=verify, adapter=__file__, plan=PLAN,
                   test_files=('analysis/tests/test_tangent_secant_geometry.py',), required_tests=TESTS,
                   request_path=REQUEST, xml=XML)


def qualify(root, *, verify, adapter, plan, test_files, required_tests, request_path, xml):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(adapter).relative_to(root).as_posix(), plan, *test_files,
             'analysis/lll/ilvis0_tangent.cpp', 'analysis/lll/ilvis0_noise_bridge.cpp')
    sources, environment = source_closure(root, seeds), runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=request_path, report=xml)
    checked(root, request_path, sources=sources, environment=environment, required_tests=required_tests,
            minimum_tests=len(required_tests))
    return sources, environment


def frozen_inputs(root):
    raw = (root/first.RESULT).read_bytes()
    if digest(raw) != FIRST_SHA:
        raise ValueError('exact passing first geometry report required')
    report = json.loads(raw)
    with ExitStack() as stack:
        source = stack.enter_context(closing(ClosedStudy(root, 'data/'+first.ID)))
        identity = first.tasks()[0]['identity']
        if (report['completion'] != source.completion or not report['summary']['qualified']
                or not source.envelope(identity)['result']['passed']):
            raise ValueError('unchanged first geometry evidence required')
        original, _ = shared.baseline(root, stack)
        if any(original.input(key) != recipe for key, recipe in recipes().items()):
            raise ValueError('the two sealed generated recipes are required')
        for key in KEYS:
            reference = key+'-trust_v2-0'
            if reference not in original.tasks or reference in original.rows:
                raise ValueError('the two reference starts must have remained unstarted')
        return {key: original.input(key, raw=True) for key in KEYS}


def prepare(root):
    return prepare_geometry(root, study_id=ID, scope=SCOPE, adapter=__file__,
                            declared_tasks=tasks(), workers=4, qualify_study=qualification,
                            freeze_recipes=frozen_inputs,
                            inputs=dict(plan=PLAN, reference=shared.ref.RESULT, first_geometry=first.RESULT,
                                        qualification=REQUEST, qualification_tests=XML))


def prepare_geometry(root, *, study_id, scope, adapter, declared_tasks, workers, qualify_study,
                     freeze_recipes, inputs):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/study_id/'manifest.json').is_file():
        raise ValueError('retain the original finite geometry allowance')
    sources, environment = qualify_study(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    values = freeze_recipes(root)
    values.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(shared.RECOVERY_RULE))
    for key, value in values.items():
        filename = f'data/{study_id}-inputs/{key}'
        _write_equal(root/filename, value)
        inputs[key] = filename
    return Definition.from_dict(dict(id=study_id, scope=scope, adapter=Path(adapter).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=declared_tasks, workers=workers, threads=1,
                                     maximum_wall_s=210), root).prepare(root)['limits']


def evaluate(task, context):
    from .ilvis0_solver_trust_v2 import fit_candidate

    solver = fit_candidate if task['payload']['solver'] == 'trust_v2' else first.solve_native
    return shared.evaluate_flight(task, context, scope=SCOPE, declared_tasks=tasks(), solver_provider=solver)


def compare(reference, candidate, *, matched_inputs, updates, probes):
    import numpy as np

    from .ilvis0_solver_position import physical_metric

    spread, cost = None, None
    if 'forecast' in reference and 'forecast' in candidate:
        paths = [np.asarray(row['forecast'], float) for row in (reference, candidate)]
        if (any(p.shape != (shared.ref.QUERIES, 3) or not np.isfinite(p).all() for p in paths)
                or not matched_inputs):
            raise ValueError('two finite matched forecasts required')
        a, b = [p[shared.ref.TRAINING:] for p in paths]
        spread = float(np.max(np.linalg.norm((a-b)*physical_metric(a), axis=1)))
        cost = abs(reference['training_cost']-candidate['training_cost'])
    passed = bool(spread is not None and spread <= .1 and cost <= .01 and updates > 0 and probes == 0
                  and all(row['converged'] and row['physical_accuracy_passed'] for row in (reference, candidate)))
    return dict(passed=passed, maximum_later_spread_m=spread, absolute_training_cost_gap=cost,
                secant_curvature_updates=updates, separate_derivative_probes=probes)


def recover(root):
    return recover_geometry(root, ID)


def recover_geometry(root, study_id):
    from .studies.task_resume import close_original, prepare_campaign, resume_campaign

    prefix = 'data/'+study_id
    continuation = root/(prefix+'-recovery')
    if not continuation.is_dir():
        if not (root/prefix/'completion.json').is_file():
            close_original(root, prefix, qualification_request=RECOVERY)
        with closing(ClosedStudy(root, prefix)) as study:
            if study.input('recovery_policy') != shared.RECOVERY_RULE:
                raise ValueError('unchanged recovery policy required')
            if all(key in study.rows and study.envelope(key)['status'] == 'complete' for key in study.tasks):
                return dict(state='original_tasks_finished', pending=0)
        prepare_campaign(root, prefix, continuation, qualification_request=RECOVERY, **shared.RECOVERY_RULE)
    return resume_campaign(root, continuation)


def report(root):
    from .ilvis0_solver_matrix_report_core import case_from_study

    prefix = 'data/'+ID
    continuation = root/(prefix+'-recovery')
    frozen_inputs(root)
    with ExitStack() as stack:
        original = stack.enter_context(closing(ClosedStudy(root, prefix)))
        selected = {}
        if continuation.is_dir():
            from .studies.combined_task_evidence import inspect

            selected = inspect(root, continuation)['selected']
        cases, bindings = {}, {}
        for task in tasks():
            identity = task['identity']
            origin = selected.get(identity, {}).get('origin', prefix)
            source = original
            if origin != prefix:
                source = stack.enter_context(closing(ClosedStudy(root, origin, store=original.store)))
            row = dict(identity=identity, **task['payload'], technical_error='no sealed result')
            if identity in source.rows:
                row = case_from_study(source, identity, task, total_epochs=shared.ref.QUERIES,
                                      training_epochs=shared.ref.TRAINING)
                if 'forecast' in row:
                    bindings[identity] = source.artifact(identity, 'input-binding.json')
                    fit = source.artifact(identity, 'fit.json')
                    row.update(updates=fit.get('secant_curvature_updates', 0),
                               separate_derivative_probes=fit.get('separate_derivative_probes'))
                else:
                    names = {name.rsplit('/', 1)[-1] for name in source.envelope(identity)['artifacts']}
                    row['attempted_training_tangents'] = shared.ref._interrupted_training_attempts(
                        source, identity, names)
            cases[identity] = dict(row, origin=origin)
        pairs = []
        for key in KEYS:
            baseline, trial = [cases[f'{key}-{solver}-0'] for solver in SOLVERS]
            pairs.append(dict(fixture=key, **compare(baseline, trial,
                matched_inputs=bindings.get(baseline['identity']) == bindings.get(trial['identity']),
                updates=trial.get('updates', 0), probes=trial.get('separate_derivative_probes'))))
        summary = dict(qualified=all(row['passed'] for row in pairs), passing_pairs=sum(row['passed'] for row in pairs),
                       observed_reads=0, protected_reads=0, scientific_decision='abstain')
        compact = [{key: value for key, value in row.items() if key != 'forecast'} for row in cases.values()]
        _write_equal(root/RESULT, encoded(dict(summary=summary, pairs=pairs, cases=compact,
                                               completion=original.completion, charged=original.summary['charged'],
                                               first_geometry_sha256=FIRST_SHA)))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
