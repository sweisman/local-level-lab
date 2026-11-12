# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fresh seeded whole-period cohort with a frozen-worker preflight."""
import json
from pathlib import Path

from . import prediction_simultaneous_study as base


IDENTITY = 'prediction-simultaneous-law-family-v2-20261113'
PREFLIGHT_ID = IDENTITY + '-preflight-v4'
SCOPE = ('96 fresh independent generated whole-period two-law forecasts; '
         'no observed/protected inputs or calibrated Earth-model decision')
PREFLIGHT_SCOPE = 'one short generated frozen-worker import and wiring check'


def recipe():
    return dict(base.recipe(), cohort_version='v2-fresh-seeds',
                mixture_draw_seed=20261113,
                noise_seed_start=20261113000)


def tasks(r=None):
    return base.tasks(recipe() if r is None else r)


def preflight_recipe():
    return dict(recipe(), duration_s=2., rate_hz=200, queries=9,
                query_start_s=.1, query_step_s=.2, maximum_evaluations=8)


def preflight_task():
    return dict(tasks()[0], identity='preflight-000')


def evaluate(task, context):
    from .airquantumgrav_inventory import environment
    preflight = context.manifest.get('scope') == PREFLIGHT_SCOPE
    r = preflight_recipe() if preflight else recipe()
    expected = ({'preflight-000':preflight_task()} if preflight else
                {item['identity']:item for item in tasks()})
    if (context.manifest.get('scope') not in (SCOPE, PREFLIGHT_SCOPE) or
            {key:value for key,value in task.items()
             if key not in ('index', 'shard')} != expected.get(task['identity']) or
            json.loads(context.input_path('recipe').read_bytes()) != r or
            json.loads(context.input_path('numerical_environment').read_bytes())
            != environment()):
        raise ValueError('changed or unqualified fresh cohort')
    result = base.run_case(task, context, r=base.case_recipe(r, task))
    if preflight and not result.get('technical_pair_complete'):
        raise ValueError('short frozen-worker preflight did not save paired result')
    return result


def qualification_sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/prediction_simultaneous_study_v2.py',
        'analysis/tests/test_prediction_simultaneous_study_v2.py',
        'analysis/tests/test_ilvis0_frozen_adapter_package.py',
        'analysis/tests/test_prediction_simultaneous_study.py',
        'analysis/tests/test_prediction_paired_simultaneous_native.py',
        'analysis/tests/test_prediction_paired_simultaneous_family.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',
        'docs/prediction-simultaneous-law-family-v2/PLAN.md'])


def required_tests():
    return base.required_tests() + [
        'test_fresh_seeds_and_preflight_recipe',
        'test_fresh_adapter_rejects_changed_task_before_charging',
        'test_preflight_requires_guarded_one_thread',
        'test_frozen_worker_loads_relative_import_adapter']


def request_qualification(root, *, recovery=False):
    from .airquantumgrav_inventory import environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    from .studies import task_resume as recovery_module
    from .studies.task_resume_sourcefix import install as install_sourcefix
    install_sourcefix()
    root = Path(root).resolve()
    directory = 'docs/prediction-simultaneous-law-family-v2/qualification/'
    return request(root,
                   sources=(recovery_module.qualification_sources(root)
                            if recovery else qualification_sources(root)),
                   environment=(runtime_environment() if recovery else
                                environment()),
                   output=directory+('recovery-request.json' if recovery else
                                    'request.json'),
                   report=directory+('recovery-tests.xml' if recovery else
                                    'tests.xml'))


def _prepare(root, *, preflight, qualification=None, recovery_qualification=None):
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as thread_environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.artifacts import atomic, encoded
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies import task_resume as recovery_module
    from .studies.task_resume_sourcefix import install as install_sourcefix
    install_sourcefix()
    root = Path(root).resolve()
    name = PREFLIGHT_ID if preflight else IDENTITY
    if (root/'data'/name).exists() or (root/'data'/(name+'-inputs')).exists():
        raise ValueError('fresh frozen allowance required')
    env = environment()
    if preflight:
        if env['numerical_environment'] != thread_environment(workers=1, threads=1):
            raise ValueError('guarded one-thread preflight allocation required')
        selected, r, scope, workers, maximum_wall_s = (
            [preflight_task()], preflight_recipe(), PREFLIGHT_SCOPE, 1, 600.)
    else:
        if qualification is None or recovery_qualification is None:
            raise ValueError('source-bound software and recovery qualification required')
        if env['numerical_environment'] != thread_environment(workers=4, threads=1):
            raise ValueError('guarded four-thread allocation required')
        source_request, source_report = checked(
            root, qualification, sources=qualification_sources(root),
            environment=env, required_tests=required_tests(),
            minimum_tests=len(required_tests()))
        recovery_request, recovery_report = checked(
            root, recovery_qualification,
            sources=recovery_module.qualification_sources(root),
            environment=runtime_environment(),
            required_tests=recovery_module.REQUIRED_TESTS,
            minimum_tests=len(recovery_module.REQUIRED_TESTS))
        preflight_root = root/'data'/PREFLIGHT_ID
        from .ilvis0_control_shards import verify_completion
        preflight_summary = verify_completion(preflight_root)
        if (preflight_summary['passed'] is not True or
                preflight_summary['completed'] != 1):
            raise ValueError('actual frozen-worker preflight did not pass')
        selected, r, scope, workers, maximum_wall_s = (
            tasks(), recipe(), SCOPE, 4, 28800.)
    base_dir = root/'data'/(name+'-inputs')
    base_dir.mkdir(parents=True)
    material = dict(recipe=encoded(r), numerical_environment=encoded(env))
    if not preflight:
        material.update(qualification_request=source_request,
                        qualification_report=source_report,
                        recovery_request=recovery_request,
                        recovery_report=recovery_report)
    inputs = {}
    for key, raw in material.items():
        path = base_dir/key
        atomic(path, raw)
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=name, scope=scope,
                      adapter='analysis/lll/prediction_simultaneous_study_v2.py',
                      sources=qualification_sources(root), inputs=inputs,
                      tasks=selected, workers=workers, threads=1,
                      maximum_wall_s=maximum_wall_s)
    atomic(base_dir/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+name, total=len(selected),
                allocation=manifest['allocation'])


def prepare_preflight(root):
    return _prepare(root, preflight=True)


def prepare(root, *, qualification, recovery_qualification):
    return _prepare(root, preflight=False, qualification=qualification,
                    recovery_qualification=recovery_qualification)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'recovery-request',
                                           'prepare-preflight', 'prepare'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    if args.action == 'request':
        result = request_qualification(args.root)
    elif args.action == 'recovery-request':
        result = request_qualification(args.root, recovery=True)
    elif args.action == 'prepare-preflight':
        result = prepare_preflight(args.root)
    else:
        base_dir = Path(args.root)/'docs/prediction-simultaneous-law-family-v2/qualification'
        result = prepare(args.root,
            qualification=base_dir/'request.json',
            recovery_qualification=base_dir/'recovery-request.json')
    print(result)


if __name__ == '__main__':
    main()
