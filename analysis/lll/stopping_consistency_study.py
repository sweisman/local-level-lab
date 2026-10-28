# SPDX-License-Identifier: AGPL-3.0-or-later
"""Four source-bound saved-point diagnostics using the shared study engine."""
import json
import math
from pathlib import Path

PARENT='data/prediction-calibration-20261025'
IDENTITY='prediction-stopping-consistency-20261026'
SCOPE='four exposed saved-point diagnostics; no nonlinear fitting, forecast or protected observations'
POINTS=((281474976810725,False,0),(281474976810726,False,0),
        (281474976810726,False,1),(281474976810726,True,0))
QUALIFICATION='data/ilvis0-source-point-development/stopping-consistency-20261026-request.json'


class Captured(Exception):
    def __init__(self,report):
        self.report=report
        super().__init__('saved-point probe completed before nonlinear fitting')


def no_nonlinear_fit(*args,**kwargs):
    raise RuntimeError('nonlinear fitting is forbidden in the saved-point diagnostic')


def point_identity(seed,profile,start):
    if (seed,profile,start) not in POINTS or type(profile) is not bool or type(start) is not int:
        raise ValueError('only four already exposed development identities are permitted')
    return f'calibration-seed-{seed}-increment-sphere_rotating-{int(profile)}-{start}'


def verify_bindings(root,sources,expected_environment,actual_environment):
    from lll.studies.artifacts import digest,safe_path
    if expected_environment!=actual_environment:raise ValueError('original environment changed')
    for name,sha in sources.items():
        if digest(safe_path(root,name).read_bytes())!=sha:
            raise ValueError('scientific source changed: '+name)


def verify_replay(active,expected,cost,saved_cost):
    if (list(active)!=list(expected) or len(set(active))!=len(active)
            or not math.isfinite(cost) or not math.isfinite(saved_cost)
            or abs(cost-saved_cost)>1e-12*max(1.,abs(saved_cost))):
        raise ValueError('saved column order or fixed-point cost replay differs')


def selection(root,prefix=PARENT):
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import digest,encoded
    s=ClosedStudy(root,prefix)
    try:
        if prefix!=PARENT:raise ValueError('one specified closed calibration source required')
        points=[]
        for seed,profile,start in POINTS:
            identity=point_identity(seed,profile,start);task=s.tasks[identity]
            fit=s.artifact(identity,'fit.json');envelope=s.envelope(identity)
            values={name:s.artifact(identity,name) for name in ('input-binding.json',
                'training-observations.json','training-error-operator.json')}
            points.append(dict(identity=identity,payload=task['payload'],fit=fit,
                saved_converged=fit['converged'],artifacts=values,
                artifact_sha256={name:envelope['artifacts']['artifacts/'+identity+'/'+name]
                    for name in ('fit.json',*values)},
                source_completion=s.completion,
                selection_sha256=digest(encoded(dict(identity=identity,fit=fit,artifacts=values)))))
        return points
    finally:s.close()


def qualification_sources(root):
    from lll.studies.closed import ClosedStudy
    from lll.studies.dependencies import source_closure
    s=ClosedStudy(root,PARENT)
    try:parents=set(s.manifest['sources'])
    finally:s.close()
    own=['analysis/lll/stopping_consistency.py','analysis/lll/stopping_consistency_study.py',
        'analysis/lll/stopping_consistency_report.py','analysis/tests/test_stopping_consistency.py',
        'analysis/tests/test_stopping_consistency_study.py','docs/PREDICTION_STOPPING_PLAN.md',
        'docs/prediction-stopping-consistency/IMPLEMENTATION.md']
    return sorted(parents|set(source_closure(root,own)))


def prepare(root,qualification=QUALIFICATION):
    from lll.studies.closed import ClosedStudy
    from lll.studies.qualification import checked
    from lll.studies.artifacts import atomic,encoded
    from lll.studies.runtime import Definition
    from lll.airquantumgrav_inventory import environment
    root=Path(root).resolve();env=environment()
    s=ClosedStudy(root,PARENT)
    try:
        parent_sources=s.manifest['sources'];parent_env=s.input('qualification-environment')
        verify_bindings(root,parent_sources,parent_env,env)
    finally:s.close()
    source=qualification_sources(root)
    request,report=checked(root,qualification,sources=source,environment=env,minimum_tests=31,
        required_tests=['test_known_answer_derivatives_at_reference_optima[interior-26]',
            'test_probe_guards[overspend]','test_study_guards[protected_seed]',
            'test_capture_binding_exits_before_any_fit_or_forecast'])
    points=selection(root);directory=root/'data/ilvis0-source-point-development'/f'{IDENTITY}-inputs'
    if directory.exists() or (root/'data'/IDENTITY).exists():raise ValueError('fresh separate study required')
    directory.mkdir(parents=True)
    values={'points':encoded(points),'qualification-request':request,'qualification-report':report,
        'environment':encoded(env),'parent-sources':encoded(parent_sources)}
    inputs={}
    for index,(name,raw) in enumerate(values.items()):
        path=directory/f'input-{index:03d}';atomic(path,raw);inputs[name]=str(path.relative_to(root))
    tasks=[dict(identity=p['identity'],input_key='points',native_kind='tangent',
        payload=dict(point_index=i,selection_sha256=p['selection_sha256']),
        limits=dict(native_calls=59954,packet_visits=376512753,bound_calls=0,bound_steps=0))
        for i,p in enumerate(points)]
    definition=dict(id=IDENTITY,scope=SCOPE,adapter='analysis/lll/stopping_consistency_study.py',
        sources=source,inputs=inputs,tasks=tasks,workers=2,threads=1,maximum_wall_s=7200.)
    atomic(directory/'definition.json',encoded(definition))
    m=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+IDENTITY,allocation=m['allocation'],limits=m['limits'])


def calculate_point(record,r,*,kernel_factory,noise_kernel,reserve,reserve_construction,
                    reserve_evaluation,save,check_continue,protocol_source,protocol_sha256,probe_options=None):
    """Reconstruct the original earlier-only problem, then intercept its fit."""
    import numpy as np
    from lll.airquantumgrav_noisy_inputs import construct,error_law
    from lll.structured_noisy_training import case_recipe
    from lll.ilvis0_native_error_training import ErrorTrainingFactory
    from lll.generated_prediction import calculate
    from lll.studies.protocols import bind_function
    from lll.studies.artifacts import digest,encoded
    from lll.ilvis0_solver_position import verify_stability,physical_residual_step
    from lll.stopping_consistency import probe
    spec=record['payload']['case'];law=spec['law'];base={k:v for k,v in spec.items() if k!='law'}
    material=construct(base,case_recipe(r,law),reserve=reserve_construction)
    anchor=material['training_rows'][0]['height_m']
    factory=ErrorTrainingFactory(noise=error_law(case_recipe(r,law)['noise']),noise_kernel=noise_kernel,
        gravity_anchor_height_m=anchor,maximum_packets=len(material['dt']),maximum_queries=len(material['times']),
        maximum_bytes=64*1024**2,anchor_policy=r['covariance_anchor_policy'])
    old=record['artifacts'];observed={}
    def saving(name,value):
        save('reconstructed/'+name,value);observed[name]=value
        if name in old and encoded(value)!=encoded(old[name]):
            raise ValueError('reconstructed artifact differs: '+name)
    def capture(problem,model,**options):
        if model!=spec['model'] or options.get('stopping')!='near_zero':
            raise ValueError('original candidate and stopping protocol required')
        fit=record['fit'];active=list(problem.bounds.active)
        point=np.asarray(fit['normalized_parameters'],float)
        if len(active)!=26+int(spec['profile']) or active!=fit['active_parameters']:
            raise ValueError('every original nuisance coordinate in its saved order is required')
        first=True
        def evaluating(u,fresh=False):
            nonlocal first
            check_continue();reserve(native_calls=1,packet_visits=len(problem.dt)*len(problem.gps_times))
            result=problem.residual_tangent(u,model)
            if first:
                verify_replay(active,fit['active_parameters'],float(result[0]@result[0]),fit['residual_sum_squares'])
                first=False
            return result
        extra={} if probe_options is None else probe_options(problem)
        result=probe(evaluating,point,bounds=(-np.ones(len(active)),np.ones(len(active))),
            frozen_probe=lambda u,rr,j,e:verify_stability(u,rr,j,e,lambda d:physical_residual_step(problem,d)),
            reserve=reserve_evaluation,check_continue=check_continue,**extra)
        result.update(active_parameters=active,original_saved_converged=fit['converged'],
            original_cost=fit['residual_sum_squares'],input_replay_exact=True,
            source_fit_sha256=record['artifact_sha256']['fit.json'])
        raise Captured(result)
    bound,proof=bind_function(protocol_source,expected_sha256=protocol_sha256,function='train_and_forecast',
        import_module='lll.ilvis0_training_forecast',import_name='fit_training',provider=capture,
        provider_source_sha256=digest(Path(__file__).read_bytes()),namespace={'math':math})
    save('protocol-binding.json',proof)
    try:
        calculate(base,case_recipe(r,law),material=material,train_and_forecast=bound,
            kernel_factory=kernel_factory,reserve=reserve,reserve_construction=reserve_construction,
            save=saving,truth=no_nonlinear_fit,check_continue=check_continue,training_error_factory=factory)
    except Captured as caught:
        save('diagnostic.json',caught.report)
        return dict(passed=True,diagnostic_complete=True,probe_passed=caught.report['stopping_probe']['passed'],
            evaluations=caught.report['evaluations'],nonlinear_fit_starts=0,protected_reads=0,
            original_reads=0,labels_changed=False,scientific_decision='abstain')
    raise RuntimeError('protocol reached fitting or forecasting instead of the saved-point capture')


def evaluate(task,context):
    from lll.airquantumgrav_inventory import environment
    from lll.prediction_calibration_study import case_recipe
    from lll.structured_noisy_study import _kernels
    from lll.structured_noisy_training import limits
    from lll.studies.journal import Journal
    from lll.studies.artifacts import digest
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.source_binding import verify
    env=json.loads(context.input_path('environment').read_bytes())
    verify_bindings(context.root/'source-freeze',context.manifest['sources'],env,environment())
    if context.manifest['scope']!=SCOPE:raise ValueError('exact diagnostic scope required')
    parent=json.loads(context.input_path('parent-sources').read_bytes())
    if any(context.manifest['sources'].get(k)!=v for k,v in parent.items()):
        raise ValueError('original scientific freeze must remain unchanged')
    points=json.loads(context.input_path('points').read_bytes());record=points[task['payload']['point_index']]
    seed=record['payload']['draw_seed'];case=record['payload']['case']
    if (task['identity']!=point_identity(seed,case['profile'],case['start'])
            or task['payload']['selection_sha256']!=record['selection_sha256']
            or task['limits']!=dict(native_calls=59954,packet_visits=376512753,bound_calls=0,bound_steps=0)):
        raise ValueError('exact four identities and original finite allowances required')
    r=case_recipe(seed);construction=limits(r,'increment')[1]
    freeze=digest((context.root/'manifest.json').read_bytes());identity=task['identity']
    cj=Journal(context.directory/'construction.sqlite',freeze=freeze,limits={identity:construction});cj.start(identity)
    ej=Journal(context.directory/'evaluations.sqlite',freeze=freeze,limits={identity:dict(evaluations=170)});ej.start(identity)
    check=lambda:_check_continue(context.root,context.manifest)
    def charge_construction(**work):
        check()
        for key,value in work.items():cj.reserve(identity,key,value)
    def charge_evaluation(**work):
        check()
        if work!={'evaluations':1}:raise ValueError('one residual/tangent evaluation required')
        ej.reserve(identity,'evaluations')
    budget=None
    try:
        noise,kernels=_kernels(context,env)
        with context.prepay_native(native_calls=59954,packet_visits=376512753) as budget:
            protocol='analysis/lll/airquantumgrav_prediction.py'
            result=calculate_point(record,r,kernel_factory=kernels,noise_kernel=noise,reserve=budget.reserve,
                reserve_construction=charge_construction,reserve_evaluation=charge_evaluation,
                save=context.save,check_continue=check,
                protocol_source=(context.root/'source-freeze'/protocol).read_bytes(),
                protocol_sha256=context.manifest['sources'][protocol])
        cj.verify();ej.verify()
        if ej.count(identity,'evaluations')!=result['evaluations']:raise ValueError('evaluation charges differ')
        return result
    finally:
        if budget is not None:context.save('native-prepayment.json',budget.snapshot())
        context.note_file(cj.path);context.note_file(ej.path)
