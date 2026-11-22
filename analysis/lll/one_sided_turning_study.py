# SPDX-License-Identifier: AGPL-3.0-or-later
"""Two native generated turning fits with a separately versioned stop rule."""

import json
import math
from pathlib import Path

ID='generated-turning-one-sided-v2-20261117'
SCOPE='two generated turning fits with research-only one-sided numerical stability'
PLAN='docs/prediction-observed-development/ONE_SIDED_TURNING_V2_PLAN.md'
QUALIFICATION_DIR='docs/prediction-observed-development/qualification/'
QUALIFICATION_NAME='guarded-one-sided-turning-v2'


def recipe():
    from .geometry_calibration_study import recipe as parent_recipe
    from .one_sided_stopping import VERSION as rule_version,FRACTIONS
    return dict(version='generated-one-sided-turning-v2',
        generated_recipe=parent_recipe(),
        parent_id='data/generated-geometry-calibration-v1-20261117',
        identities=['turning-level','turning-climb'],
        model='sphere_rotating',start=0,rule_version=rule_version,
        fractions=list(FRACTIONS),maximum_evaluations=200,
        verification_evaluations=9,workers=2,threads=1,
        maximum_wall_s=1200.,original_reads=0,protected_reads=0)


def _limits(r):
    base=r['generated_recipe']
    n=round(base['duration_s']*base['rate_hz'])
    cut=2*base['queries']//3
    last=base['query_start_s']+(cut-1)*base['query_step_s']
    prefix=math.ceil((last+base['limits']['time_offset'])*base['rate_hz'])+2
    bridge=prefix+cut+n+base['queries']
    return dict(native_calls=bridge+r['maximum_evaluations'],
        packet_visits=bridge+r['maximum_evaluations']*prefix*cut,
        bound_calls=0,bound_steps=0)


def tasks(r=None):
    r=recipe() if r is None else r
    if r!=recipe():raise ValueError('exact one-sided turning recipe required')
    return [dict(identity=name,input_key='recipe',native_kind='tangent',
        payload=dict(parent_identity=name,model=r['model'],start=r['start'],
                     rule_version=r['rule_version']),limits=_limits(r))
        for name in r['identities']]


def validate_task(task):
    declared={key:value for key,value in task.items() if key not in ('index','shard')}
    if declared!={row['identity']:row for row in tasks()}.get(task.get('identity')):
        raise ValueError('unchanged one-sided task required')
    return declared


def qualification_sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(),[
        'analysis/lll/one_sided_turning_study.py',
        'analysis/lll/one_sided_stopping.py',
        'analysis/lll/generated_turning_problem.py',
        'analysis/lll/geometry_calibration_study.py',
        'analysis/lll/turning_fixed_point_study.py',
        'analysis/tests/test_one_sided_turning_study.py',
        'analysis/tests/test_one_sided_stopping.py',
        'analysis/tests/test_one_sided_solver_integration.py',
        'analysis/tests/test_generated_turning_problem.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',PLAN])


def required_tests():
    return ('test_two_unchanged_turning_inputs_get_one_finite_start_each',
        'test_changed_turning_study_task_is_rejected',
        'test_study_id_is_accepted_by_shared_generated_reconstruction',
        'test_known_exact_minimum_passes',
        'test_exact_boundary_minimum_passes',
        'test_redundant_weak_coordinate_does_not_require_unique_parameters',
        'test_small_linear_prediction_but_actual_cost_increase_can_pass',
        'test_detectable_descent_is_rejected',
        'test_physical_instability_is_rejected',
        'test_changed_baseline_repeat_is_rejected',
        'test_nonstationary_point_is_rejected')


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


def prepare(root,*,qualification,recovery_qualification):
    import shutil
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as thread_environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.artifacts import atomic,encoded
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import qualification_sources as recovery_sources,REQUIRED_TESTS as recovery_tests
    from .turning_fixed_point_study import parent_binding
    root=Path(root).resolve();r=recipe();env=environment()
    if env['numerical_environment']!=thread_environment(workers=2,threads=1):
        raise ValueError('guarded two-thread numerical allocation required')
    if shutil.disk_usage(root).free<2*1024**3:
        raise ValueError('2 GiB free space required')
    source_request,source_report=checked(root,qualification,
        sources=qualification_sources(root),environment=env,
        required_tests=required_tests(),minimum_tests=len(required_tests()))
    recovery_request,recovery_report=checked(root,recovery_qualification,
        sources=recovery_sources(root),environment=runtime_environment(),
        required_tests=recovery_tests,minimum_tests=len(recovery_tests))
    binding=parent_binding(root)
    base=root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('fresh finite one-sided study required')
    base.mkdir(parents=True)
    values=dict(recipe=encoded(r),environment=encoded(env),parent_binding=encoded(binding),
        qualification_request=source_request,qualification_report=source_report,
        recovery_request=recovery_request,recovery_report=recovery_report)
    inputs={}
    for key,raw in values.items():
        path=base/key;atomic(path,raw);inputs[key]=path.relative_to(root).as_posix()
    definition=dict(id=ID,scope=SCOPE,
        adapter='analysis/lll/one_sided_turning_study.py',
        sources=qualification_sources(root),inputs=inputs,tasks=tasks(r),
        workers=2,threads=1,maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json',encoded(definition))
    manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+ID,tasks=2,allocation=manifest['allocation'],
                limits=manifest['limits'])


def evaluate(task,context):
    import numpy as np
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_noisy_inputs import construction_limits
    from .generated_turning_problem import reconstruct
    from .geometry_calibration_study import recipe as parent_recipe
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_solver_position import physical_residual_step
    from .ilvis0_solver_trust_v2 import fit_candidate
    from .one_sided_stopping import verify
    from .studies.artifacts import digest,encoded
    from .studies.journal import Journal

    validate_task(task);r=recipe()
    if (context.manifest['scope']!=SCOPE
            or json.loads(context.input_path('recipe').read_bytes())!=r
            or json.loads(context.input_path('environment').read_bytes())!=environment()):
        raise ValueError('changed one-sided input or numerical environment')
    identity=task['payload']['parent_identity']
    route,height=identity.split('-');base=parent_recipe()
    configured=dict(base,route=route,height_profile=height,
                    noise=base['noise_by_law']['increment'])
    construction=construction_limits(configured)
    journal=Journal(context.directory/'construction.sqlite',
        freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={identity:construction})
    journal.start(identity);budget=None
    def check():_check_continue(context.root,context.manifest)
    def reserve_construction(**work):
        check()
        for key,value in work.items():journal.reserve(identity,key,value)
    try:
        with context.prepay_native(native_calls=task['limits']['native_calls'],
                packet_visits=task['limits']['packet_visits']) as budget:
            native_calls=0
            def reserve_native(**work):
                nonlocal native_calls
                check();budget.reserve(**work);native_calls+=work['native_calls']
            problem,parent_fit,prefix,cut=reconstruct(context,study_id=ID,
                identity=identity,reserve_construction=reserve_construction,
                reserve_native=reserve_native,save=context.save)
            if parent_fit['model']!=r['model']:
                raise ValueError('unchanged generating candidate required')
            class Counted:
                calls=0
                def __getattr__(self,name):return getattr(problem,name)
                def residual_tangent(self,point,model):
                    reserve_native(native_calls=1,packet_visits=prefix*cut)
                    self.calls+=1
                    return problem.residual_tangent(point,model)
            counted=Counted()
            fit=fit_candidate(counted,r['model'],
                start=np.zeros(len(problem.bounds.active)),
                maximum_evaluations=r['maximum_evaluations'],
                physical_step=lambda delta:physical_residual_step(problem,delta),
                stability_verifier=verify,
                verification_evaluations=r['verification_evaluations'])
            if counted.calls!=fit['evaluations']:
                raise ValueError('complete native tangent charge required')
            context.save('fit.json',fit)
            context.save('comparison.json',dict(original_fit_sha256=digest(encoded(parent_fit)),
                original_converged=False,original_cost=parent_fit['residual_sum_squares'],
                new_converged=fit['converged'],new_cost=fit['residual_sum_squares'],
                old_full_probe_passed=fit['stability_probe']['original_probe']['passed'],
                labels_changed=False,native_calls_actual=native_calls,
                original_reads=0,protected_reads=0,scientific_decision='abstain'))
        journal.verify()
        if any(journal.count(identity,key)!=value for key,value in construction.items()):
            raise ValueError('generated construction charge differs')
        return dict(passed=True,technical_passed=True,candidate_converged=fit['converged'],
            original_full_probe_passed=fit['stability_probe']['original_probe']['passed'],
            original_parent_converged=False,fit_evaluations=fit['evaluations'],
            native_calls_actual=native_calls,original_reads=0,protected_reads=0,
            scientific_decision='abstain')
    finally:
        if budget is not None:context.save('native-prepayment.json',budget.snapshot())
        context.note_file(journal.path)


def launch(root):
    from .ilvis0_control_shards import launch as run_study
    return run_study(Path(root).resolve()/'data'/ID,reserved_threads=0)


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request-source','request-recovery','prepare','run'))
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv)
    if args.action=='request-source':result=request_qualification(args.root)
    elif args.action=='request-recovery':result=request_qualification(args.root,recovery=True)
    elif args.action=='prepare':
        result=prepare(args.root,qualification=QUALIFICATION_DIR+
            'source-'+QUALIFICATION_NAME+'-request.json',
            recovery_qualification=QUALIFICATION_DIR+
            'recovery-'+QUALIFICATION_NAME+'-request.json')
    else:result=launch(args.root)
    print(result)


if __name__=='__main__':main()
