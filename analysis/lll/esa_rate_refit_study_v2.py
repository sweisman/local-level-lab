# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fresh ESA rate-refit study with a reference-matched generated smoke gate."""
import json
from pathlib import Path

from . import esa_rate_refit_study as first


ID = 'esa-rate-refit-development-v2-20261114'
SMOKE_ID = ID + '-generated-smoke'


def smoke_gate(reference_converged, actual_converged, baseline_reproduced,
               method):
    """Qualify plumbing against the deliberately unfinished generated control."""
    return (reference_converged is False and actual_converged is False and
            baseline_reproduced is True)


def observed_gate(actual_converged, baseline_reproduced, method):
    return (actual_converged is True and
            (method != 'linear_points' or baseline_reproduced is True))


def sources(root):
    from .studies.dependencies import source_closure
    root = Path(root).resolve()
    return source_closure(root, first.sources(root) + [
        'analysis/lll/esa_rate_refit_study_v2.py',
        'analysis/tests/test_esa_rate_refit_study_v2.py',
        'docs/prediction-observed-development/RATE_REFIT_V2_PLAN.md'])


def required_tests():
    return first.required_tests() + (
        'test_v2_smoke_accepts_matched_reference_status_only',
        'test_v2_observed_gate_still_requires_convergence',
        'test_v2_preparation_requires_source_qualification')


def request_qualification(root):
    from .airquantumgrav_inventory import environment
    from .studies.qualification import request
    root = Path(root).resolve()
    return request(root, sources=sources(root), environment=environment(),
                   output='docs/prediction-observed-development/qualification/rate-refit-v2-request.json',
                   report='docs/prediction-observed-development/qualification/rate-refit-v2-tests.xml')


def prepare(root, *, smoke, qualification=None):
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    from .esa_fixed_rate_protocol import stage_parent
    from .ilvis0_control_shards import verify_completion
    from .studies.artifacts import atomic, encoded, safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition

    if not smoke and qualification is None:
        raise ValueError('source-bound qualification required before observed preparation')
    root = Path(root).resolve()
    identity = SMOKE_ID if smoke else ID
    base = safe_path(root, 'data/' + identity + '-inputs')
    if base.exists() or safe_path(root, 'data/' + identity).exists():
        raise ValueError('fresh finite rate-refit identity required')
    workers = 1 if smoke else 3
    env = environment()
    if env['numerical_environment'] != numerical_environment(workers=workers, threads=1):
        raise ValueError('guarded declared numerical allocation required')
    qualification_files = {}
    if not smoke:
        request, report = checked(
            root, qualification, sources=sources(root), environment=env,
            required_tests=required_tests(), minimum_tests=len(required_tests()))
        check = verify_completion(root/'data'/SMOKE_ID)
        if (check['state'] != 'complete' or check['completed'] != 6 or
                check['passed'] is not True):
            raise ValueError('verified six-task technical smoke required')
        failed = ClosedStudy(root, 'data/'+first.SMOKE_ID)
        try:
            if (failed.completion['state'] != 'terminal' or
                    failed.completion['manifest_sha256'] !=
                    'db96faa2de0502679ddc6d349c956cf8047c6bad96a7617977fce6fd907ae9af' or
                    failed.completion['summary_sha256'] !=
                    'fa6ce84a4fb46569d5e22060fb9bd19c3757e16c985a241a9f5b0378705b2eb6'):
                raise ValueError('preserved terminal first smoke required')
        finally:
            failed.close()
        qualification_files = dict(qualification_request=request,
                                   qualification_report=report)
    staged = stage_parent(root, smoke=smoke)
    parent = ClosedStudy(root, 'data/prediction-observed-development-continuation-v1-20261113'+
                        ('-smoke-v3' if smoke else ''))
    try:
        staged['saved-point-fit'] = parent.input('saved-point-fit', raw=True)
        staged['saved-point-forecast'] = parent.input('saved-point-forecast', raw=True)
    finally:
        parent.close()
    materials = dict(staged, qualification_environment=encoded(env),
                     **qualification_files)
    base.mkdir(parents=True)
    inputs = {}
    for number, (key, raw) in enumerate(materials.items()):
        path = base/f'input-{number:03d}'
        atomic(path, raw)
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=identity,
                      scope=first.SMOKE_SCOPE if smoke else first.SCOPE,
                      adapter='analysis/lll/esa_rate_refit_study_v2.py',
                      sources=sources(root), inputs=inputs,
                      tasks=first.tasks(smoke=smoke), workers=workers, threads=1,
                      maximum_wall_s=600. if smoke else 14400.)
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+identity, total=6,
                allocation=manifest['allocation'])


def evaluate(task, context):
    smoke = context.manifest.get('scope') == first.SMOKE_SCOPE
    result = first.evaluate(task, context)
    method = task['payload']['method']
    if smoke:
        import numpy as np
        reference = json.loads(context.input_path(
            'saved-'+task['payload']['law']+'-fit').read_bytes())
        original_forecast = json.loads(context.input_path(
            'saved-'+task['payload']['law']+'-forecast').read_bytes())
        actual_fit = json.loads((context.directory/'fit.json').read_bytes())
        actual_forecast = json.loads((context.directory/'forecast.json').read_bytes())
        parameter_difference = float(np.max(np.abs(
            np.asarray(actual_fit['normalized_parameters'])-
            np.asarray(reference['normalized_parameters']))))
        coordinate_difference = float(np.max(np.abs(
            np.asarray(actual_forecast['coordinates'])-
            np.asarray(original_forecast['coordinates']))))
        matched = parameter_difference <= 1e-10 and coordinate_difference <= 1e-12
        passed = smoke_gate(reference['converged'],
                            result['numerical_converged'],
                            matched, method)
        context.save('qualification-summary.json', dict(
            technical_pipeline_passed=passed,
            reference_numerical_converged=reference['converged'],
            observed_numerical_converged=result['numerical_converged'],
            original_baseline_reproduced=matched,
            parameter_max_difference=parameter_difference,
            coordinate_max_difference=coordinate_difference,
            scientific_decision='abstain'))
    else:
        passed = observed_gate(result['numerical_converged'],
                               result['baseline_reproduced'], method)
    return dict(result, passed=passed)


def launch(root, *, smoke):
    from .ilvis0_control_shards import launch as run
    root = Path(root).resolve()
    return run(root/'data'/(SMOKE_ID if smoke else ID), reserved_threads=0)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare-smoke', 'run-smoke',
                                           'prepare', 'run'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if args.action == 'request': result = request_qualification(root)
    elif args.action == 'prepare-smoke': result = prepare(root, smoke=True)
    elif args.action == 'run-smoke': result = launch(root, smoke=True)
    elif args.action == 'prepare':
        result = prepare(root, smoke=False,
                         qualification='docs/prediction-observed-development/qualification/rate-refit-v2-request.json')
    else: result = launch(root, smoke=False)
    print(result)
    return result


if __name__ == '__main__':
    main()
