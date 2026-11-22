# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fresh whole-period cohort with a measured-runtime allowance."""
import json
from pathlib import Path

from . import prediction_simultaneous_study as base


IDENTITY = 'prediction-simultaneous-law-family-v3-runtime-20261112'
PREFLIGHT_ID = IDENTITY + '-preflight'
SCOPE = ('96 fresh independent generated whole-period two-law forecasts; '
         'no observed/protected inputs or calibrated Earth-model decision')
PREFLIGHT_SCOPE = 'one short generated frozen-worker runtime-cohort wiring check'


def recipe():
    return dict(base.recipe(), cohort_version='v3-runtime',
                mixture_draw_seed=31415927,
                noise_seed_start=31415927000,
                maximum_wall_s=43200.)


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
                {item['identity']:item for item in tasks(r)})
    if (context.manifest.get('scope') not in (SCOPE, PREFLIGHT_SCOPE) or
            {key:value for key,value in task.items()
             if key not in ('index', 'shard')} != expected.get(task['identity'])):
        raise ValueError('changed or unqualified runtime cohort')
    if (json.loads(context.input_path('recipe').read_bytes()) != r or
            json.loads(context.input_path('numerical_environment').read_bytes())
            != environment()):
        raise ValueError('changed or unqualified runtime cohort')
    result = base.run_case(task, context, r=base.case_recipe(r, task))
    if preflight and result.get('technical_pair_complete') is not True:
        raise ValueError('short frozen-worker preflight did not save paired result')
    return result


def qualification_sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/prediction_simultaneous_study_v3.py',
        'analysis/tests/test_prediction_simultaneous_study_v3.py',
        'analysis/tests/test_prediction_simultaneous_study.py',
        'analysis/tests/test_prediction_paired_simultaneous_native.py',
        'analysis/tests/test_prediction_paired_simultaneous_family.py',
        'analysis/tests/test_ilvis0_frozen_adapter_package.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',
        'docs/prediction-simultaneous-law-family-v3/PLAN.md'])


def required_tests():
    return base.required_tests() + [
        'test_fresh_runtime_cohort_has_disjoint_seeds_and_finite_allowance',
        'test_changed_case_is_rejected_before_any_charge',
        'test_source_freeze_includes_new_adapter_test_and_plan',
        'test_release_tests_bind_fresh_cohort_checks',
        'test_new_study_requires_both_qualifications_before_mutation',
        'test_short_preflight_rejects_unguarded_allocation',
        'test_frozen_definitions_use_short_and_twelve_hour_caps',
        'test_preflight_writes_a_separate_frozen_input_snapshot',
        'test_full_study_refuses_an_unverified_preflight',
        'test_software_and_recovery_qualification_requests_are_separate',
        'test_cli_routes_new_qualification_without_creating_a_study',
        'test_recovery_qualification_includes_the_versioned_source_list_fix',
        'test_full_study_freezes_96_new_tasks_after_checked_preflight',
        'test_short_frozen_worker_uses_preflight_scope_and_recipe',
        'test_full_frozen_worker_uses_the_twelve_hour_recipe',
        'test_launch_refuses_less_than_35_gib_free_before_worker_start']


def recovery_sources(root):
    from .studies import task_resume
    from .studies.task_resume_sourcefix import SOURCE, TEST
    return list(dict.fromkeys((*task_resume.qualification_sources(root),
                               SOURCE, TEST)))


def recovery_required_tests():
    from .studies import task_resume
    from .studies.task_resume_sourcefix import TEST_NAME
    return tuple(dict.fromkeys((*task_resume.REQUIRED_TESTS, TEST_NAME)))


def request_qualification(root, *, recovery=False):
    from .airquantumgrav_inventory import environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    root = Path(root).resolve()
    directory = 'docs/prediction-simultaneous-law-family-v3/qualification/'
    return request(root,
                   sources=recovery_sources(root) if recovery
                           else qualification_sources(root),
                   environment=runtime_environment() if recovery
                               else environment(),
                   output=directory+('recovery-request.json' if recovery
                                     else 'request.json'),
                   report=directory+('recovery-tests.xml' if recovery
                                     else 'tests.xml'))


def definition(root, *, preflight, inputs):
    return dict(id=PREFLIGHT_ID if preflight else IDENTITY,
                scope=PREFLIGHT_SCOPE if preflight else SCOPE,
                adapter='analysis/lll/prediction_simultaneous_study_v3.py',
                sources=qualification_sources(root), inputs=dict(inputs),
                tasks=[preflight_task()] if preflight else tasks(),
                workers=1 if preflight else 4, threads=1,
                maximum_wall_s=600. if preflight else 43200.)


def prepare(root, *, qualification, recovery_qualification):
    if qualification is None or recovery_qualification is None:
        raise ValueError('source-bound software and recovery qualification required')
    return _prepare(root, preflight=False, qualification=qualification,
                    recovery_qualification=recovery_qualification)


def prepare_preflight(root):
    return _prepare(root, preflight=True)


def _prepare(root, *, preflight, qualification=None, recovery_qualification=None):
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as thread_environment
    from .ilvis0_control_shards import runtime_environment, verify_completion
    from .studies.artifacts import atomic, encoded
    from .studies.qualification import checked
    from .studies.runtime import Definition
    root = Path(root).resolve()
    env = environment()
    if preflight and env['numerical_environment'] != thread_environment(
            workers=1, threads=1):
        raise ValueError('guarded one-thread preflight allocation required')
    approvals = {}
    if not preflight:
        if env['numerical_environment'] != thread_environment(workers=4, threads=1):
            raise ValueError('guarded four-thread study allocation required')
        source_request, source_report = checked(
            root, qualification, sources=qualification_sources(root),
            environment=env, required_tests=required_tests(),
            minimum_tests=len(required_tests()))
        recovery_tests = recovery_required_tests()
        recovery_request, recovery_report = checked(
            root, recovery_qualification, sources=recovery_sources(root),
            environment=runtime_environment(),
            required_tests=recovery_tests,
            minimum_tests=len(recovery_tests))
        preflight_summary = verify_completion(root/'data'/PREFLIGHT_ID)
        if (preflight_summary['passed'] is not True or
                preflight_summary['completed'] != 1):
            raise ValueError('verified frozen-worker preflight required')
        approvals = dict(qualification_request=source_request,
                         qualification_report=source_report,
                         recovery_request=recovery_request,
                         recovery_report=recovery_report)
    name = PREFLIGHT_ID if preflight else IDENTITY
    if ((root/'data'/name).exists() or
            (root/'data'/(name+'-inputs')).exists()):
        raise ValueError('fresh frozen allowance required')
    base_dir = root/'data'/(name+'-inputs')
    base_dir.mkdir(parents=True)
    material = dict(recipe=encoded(preflight_recipe() if preflight else recipe()),
                    numerical_environment=encoded(env), **approvals)
    inputs = {}
    for key, raw in material.items():
        path = base_dir/key
        atomic(path, raw)
        inputs[key] = path.relative_to(root).as_posix()
    frozen = definition(root, preflight=preflight, inputs=inputs)
    atomic(base_dir/'definition.json', encoded(frozen))
    manifest = Definition.from_dict(frozen, root).prepare(root)
    return dict(path='data/'+name, total=1 if preflight else 96,
                allocation=manifest['allocation'])


def launch(root, *, preflight=False):
    import shutil
    from .ilvis0_control_shards import launch as run_study
    root = Path(root).resolve()
    if shutil.disk_usage(root).free < 35*1024**3:
        raise ValueError('35 GiB free space required before worker launch')
    name = PREFLIGHT_ID if preflight else IDENTITY
    return run_study(root/'data'/name, reserved_threads=0)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'recovery-request',
                                           'prepare-preflight', 'prepare',
                                           'run-preflight', 'run'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    if args.action == 'request':
        result = request_qualification(args.root)
    elif args.action == 'recovery-request':
        result = request_qualification(args.root, recovery=True)
    elif args.action == 'prepare-preflight':
        result = prepare_preflight(args.root)
    elif args.action == 'run-preflight':
        result = launch(args.root, preflight=True)
    elif args.action == 'run':
        result = launch(args.root)
    else:
        directory = (Path(args.root)/
                     'docs/prediction-simultaneous-law-family-v3/qualification')
        result = prepare(args.root,
                         qualification=directory/'request.json',
                         recovery_qualification=directory/'recovery-request.json')
    print(result)
    return result


if __name__ == '__main__':
    main()
