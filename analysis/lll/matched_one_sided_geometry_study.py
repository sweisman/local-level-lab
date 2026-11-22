# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite shared-input, three-candidate geometry control for one-sided stopping."""

import json
import shutil
from pathlib import Path

ID='generated-matched-one-sided-v2-20261117'
PREFLIGHT_ID=ID+'-preflight'
SCOPE='two generated shared-input route cases with one-sided three-candidate fits'
PREFLIGHT_SCOPE='short generated shared-input one-sided three-candidate preflight'
PLAN='docs/prediction-observed-development/MATCHED_ONE_SIDED_GEOMETRY_V2_PLAN.md'
QUALIFICATION_DIR='docs/prediction-observed-development/qualification/'
QUALIFICATION_NAME='matched-one-sided-geometry-v2'


def recipe():
    from .matched_candidate_generated_study import recipe as base
    from .one_sided_stopping import VERSION,FRACTIONS
    return dict(base(),version='matched-one-sided-geometry-v2',
        input_laws=['increment'],noise_by_law={'increment':base()['noise_by_law']['increment']},
        rule_version=VERSION,rule_fractions=list(FRACTIONS),
        verification_evaluations=9,maximum_wall_s=3600.,workers=2,threads=1,
        original_reads=0,protected_reads=0)


def preflight_recipe():
    return dict(recipe(),version='matched-one-sided-geometry-preflight-v2',
        duration_s=10.,queries=9,maximum_evaluations=18,
        maximum_wall_s=900.,workers=1,threads=1)


def tasks(r=None):
    from .structured_noisy_training import limits
    from .structured_noisy_study import extra_forecast_work
    r=recipe() if r is None else r
    if r not in (recipe(),preflight_recipe()):
        raise ValueError('exact matched one-sided recipe required')
    preflight=r==preflight_recipe()
    routes=('straight',) if preflight else ('straight','turning')
    rows=[]
    for route in routes:
        extra=extra_forecast_work(r,3)
        allowance=limits(r,'increment')[0]
        for key,value in extra.items():allowance[key]+=value
        for key in allowance:allowance[key]*=3
        identity=('preflight-' if preflight else '')+route+'-level'
        rows.append(dict(identity=identity,input_key='recipe',native_kind='tangent',
            payload=dict(truth_model='sphere_rotating',latitude_deg=55.,law='increment',
                seed=770101,route=route,height_profile='level',profile=False,start=0,
                policy_id='reported-short-v1',rule_version=r['rule_version']),
            limits=allowance))
    return rows


def validate_task(task,*,preflight):
    expected={row['identity']:row for row in tasks(preflight_recipe() if preflight else recipe())}
    declared={key:value for key,value in task.items() if key not in ('index','shard')}
    if declared!=expected.get(task.get('identity')):
        raise ValueError('unchanged matched geometry task required')
    return declared


def solver_provider():
    from .ilvis0_solver_position import physical_residual_step
    from .ilvis0_solver_trust_v2 import fit_candidate
    from .one_sided_stopping import verify
    def solve(problem,model,*,start,maximum_evaluations):
        return fit_candidate(problem,model,start=start,
            maximum_evaluations=maximum_evaluations,
            physical_step=lambda delta:physical_residual_step(problem,delta),
            stability_verifier=verify,verification_evaluations=9)
    return solve


def evaluate(task,context):
    from .airquantumgrav_inventory import environment
    from .matched_candidate_generated_study import _run_case
    preflight=context.manifest.get('scope')==PREFLIGHT_SCOPE
    r=preflight_recipe() if preflight else recipe()
    validate_task(task,preflight=preflight)
    if (context.manifest.get('scope') not in (SCOPE,PREFLIGHT_SCOPE)
            or json.loads(context.input_path('recipe').read_bytes())!=r
            or json.loads(context.input_path('environment').read_bytes())!=environment()):
        raise ValueError('changed generated input or numerical environment')
    result=_run_case(task,context,r,solver_provider=solver_provider())
    return dict(result,matched_rule=r['rule_version'],route=task['payload']['route'],
        original_reads=0,protected_reads=0,scientific_decision='abstain')


def qualification_sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(),[
        'analysis/lll/matched_one_sided_geometry_study.py',
        'analysis/lll/matched_candidate_generated_study.py',
        'analysis/lll/matched_candidate_case.py',
        'analysis/lll/airquantumgrav_prediction.py',
        'analysis/lll/one_sided_stopping.py',
        'analysis/lll/ilvis0_solver_trust_v2.py',
        'analysis/tests/test_matched_one_sided_geometry_study.py',
        'analysis/tests/test_airquantumgrav_prediction.py',
        'analysis/tests/test_matched_candidate_case.py',
        'analysis/tests/test_one_sided_stopping.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',PLAN])


def required_tests():
    return ('test_two_routes_each_fit_all_three_candidates_with_one_rule',
        'test_short_preflight_is_separate_and_finite',
        'test_route_changes_generation_recipe_but_not_identity_spec',
        'test_changed_task_fails_before_input_or_native_work',
        'test_provider_uses_same_research_rule_for_every_candidate',
        'test_explicit_solver_provider_reaches_shared_training_fit',
        'test_three_candidates_use_one_saved_input_before_later_truth',
        'test_detectable_descent_is_rejected',
        'test_physical_instability_is_rejected')


def request_qualification(root,*,recovery=False):
    from .airquantumgrav_inventory import environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    from .studies.task_resume import qualification_sources as recovery_sources
    root=Path(root).resolve();stem='recovery' if recovery else 'source'
    return request(root,sources=recovery_sources(root) if recovery else qualification_sources(root),
        environment=runtime_environment() if recovery else environment(),
        output=QUALIFICATION_DIR+stem+'-'+QUALIFICATION_NAME+'-request.json',
        report=QUALIFICATION_DIR+stem+'-'+QUALIFICATION_NAME+'-tests.xml')


def definition(root,*,preflight,inputs):
    r=preflight_recipe() if preflight else recipe()
    return dict(id=PREFLIGHT_ID if preflight else ID,
        scope=PREFLIGHT_SCOPE if preflight else SCOPE,
        adapter='analysis/lll/matched_one_sided_geometry_study.py',
        sources=qualification_sources(root),inputs=dict(inputs),tasks=tasks(r),
        workers=r['workers'],threads=r['threads'],maximum_wall_s=r['maximum_wall_s'])


def prepare(root,*,preflight,qualification,recovery_qualification):
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as thread_environment
    from .ilvis0_control_shards import runtime_environment,verify_completion
    from .studies.artifacts import atomic,encoded
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import qualification_sources as recovery_sources,REQUIRED_TESTS as recovery_tests
    root=Path(root).resolve();r=preflight_recipe() if preflight else recipe();env=environment()
    if env['numerical_environment']!=thread_environment(workers=r['workers'],threads=r['threads']):
        raise ValueError('guarded declared numerical allocation required')
    if shutil.disk_usage(root).free<2*1024**3:
        raise ValueError('2 GiB free space required')
    source_request,source_report=checked(root,qualification,
        sources=qualification_sources(root),environment=env,
        required_tests=required_tests(),minimum_tests=len(required_tests()))
    recovery_request,recovery_report=checked(root,recovery_qualification,
        sources=recovery_sources(root),environment=runtime_environment(),
        required_tests=recovery_tests,minimum_tests=len(recovery_tests))
    if not preflight:
        prior=verify_completion(root/'data'/PREFLIGHT_ID)
        if prior['state']!='complete' or prior['completed']!=1 or prior['passed'] is not True:
            raise ValueError('sealed matched one-sided preflight required')
    name=PREFLIGHT_ID if preflight else ID
    base=root/'data'/(name+'-inputs')
    if base.exists() or (root/'data'/name).exists():
        raise ValueError('fresh finite matched one-sided study required')
    base.mkdir(parents=True)
    values=dict(recipe=encoded(r),environment=encoded(env),
        qualification_request=source_request,qualification_report=source_report,
        recovery_request=recovery_request,recovery_report=recovery_report)
    inputs={}
    for key,raw in values.items():
        path=base/key;atomic(path,raw);inputs[key]=path.relative_to(root).as_posix()
    frozen=definition(root,preflight=preflight,inputs=inputs)
    atomic(base/'definition.json',encoded(frozen))
    manifest=Definition.from_dict(frozen,root).prepare(root)
    return dict(path='data/'+name,tasks=len(frozen['tasks']),
        allocation=manifest['allocation'],limits=manifest['limits'])


def launch(root,*,preflight=False):
    from .ilvis0_control_shards import launch as run_study
    return run_study(Path(root).resolve()/'data'/(PREFLIGHT_ID if preflight else ID),
                     reserved_threads=0)


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request-source','request-recovery',
                                          'prepare-preflight','run-preflight','prepare','run'))
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv)
    if args.action=='request-source':answer=request_qualification(args.root)
    elif args.action=='request-recovery':answer=request_qualification(args.root,recovery=True)
    elif args.action in ('prepare-preflight','prepare'):
        answer=prepare(args.root,preflight=args.action=='prepare-preflight',
            qualification=QUALIFICATION_DIR+'source-'+QUALIFICATION_NAME+'-request.json',
            recovery_qualification=QUALIFICATION_DIR+'recovery-'+QUALIFICATION_NAME+'-request.json')
    else:answer=launch(args.root,preflight=args.action=='run-preflight')
    print(answer)


if __name__=='__main__':main()
