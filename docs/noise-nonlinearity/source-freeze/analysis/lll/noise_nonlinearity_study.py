# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite matched nonlinear check of the known-calibration noise benchmark."""
import json
from pathlib import Path
from lll.noise_benchmark_study import kernel as bridge_kernel

SCOPE='generated matched nonlinear noise diagnostic; known calibration; no fitting or original/protected reads'


def recipe():
    return dict(version='known-calibration-noise-nonlinearity-v1',durations_s=[120.,1200.],
        laws=['increment','point'],seeds=list(range(26102500,26102516)),amplitudes=[1.,-1.,.5,-.5],
        absolute_limit_m=.001,relative_limit=.01,workers=2,threads=1,maximum_wall_s=7200.,
        maximum_operator_bytes=64*1024**2,optimizer_starts=0,original_reads=0,protected_reads=0)


def limits(payload):
    from lll.noise_benchmark_study import limits as parent_limits
    bridge,construction=parent_limits(payload);n=round(payload['duration_s']*300)
    m=119 if payload['duration_s']==120 else 1200;cut=2*m//3
    calls=1+len(recipe()['seeds'])*len(recipe()['amplitudes'])
    noise=18*n+6 if payload['law']=='increment' else 12*(n+1)
    work=dict(bridge,native_calls=bridge['native_calls']+calls,packet_visits=bridge['packet_visits']+calls*n*m)
    return work,dict(generated_samples=construction['generated_samples'],constructed_intervals=n,
        realizations=len(recipe()['seeds']),noise_normal_variates=len(recipe()['seeds'])*(noise+6*cut+6))


def tasks():
    return [dict(identity=f'{law}-{int(duration)}',input_key='recipe',native_kind='mixed',
        payload=dict(law=law,duration_s=duration),limits=limits(dict(law=law,duration_s=duration))[0])
        for duration in recipe()['durations_s'] for law in recipe()['laws']]


def scalar_kernel(context,*,anchor):
    from lll.ilvis0_precision_value import load,derive
    from lll.studies.journal import Journal
    from lll.studies.artifacts import digest
    from lll.airquantumgrav_inventory import environment
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels'
    journal=Journal(directory/'scalar-builds.sqlite',freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={'worker':dict(builds=1)})
    already_started=bool(journal.verify()['starts'])
    if not already_started:
        journal.start('worker');journal.reserve('worker','builds')
    else:
        raw=(context.root/'source-freeze/analysis/lll/ilvis0_tangent.cpp').read_bytes()
        sha=digest(derive(raw,expected_sha256=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp'],precision='long_double'))
        if any(not (directory/('precision-value-'+sha+suffix)).is_file() for suffix in ('.cpp','.so')):
            raise ValueError('charged scalar build missing; no uncharged rebuild')
    native,metadata=load(directory,precision='long_double',gravity_anchor_height_m=anchor,
        expected_source_sha256=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp'])
    if metadata['compiler']!=environment()['compilers']['c++']:raise ValueError('frozen compiler differs')
    journal.verify();context.save('scalar-compilation.json',metadata)
    context.save_bytes('scalar-build-journal.sqlite',journal.path.read_bytes())
    return native


def evaluate(task,context):
    import io
    import numpy as np
    from lll.generated_noise_benchmark import material,build_operator
    from lll.noise_benchmark_study import limits as parent_limits
    from lll.noise_nonlinearity import draw,propagate,conditional_error,summarize_pair
    from lll.airquantumgrav_inventory import environment
    from lll.studies.journal import Journal
    from lll.studies.artifacts import digest
    from lll.ilvis0_control_shards import _check_continue
    expected={v['identity']:v for v in tasks()}
    if ({k:v for k,v in task.items() if k not in ('index','shard')}!=expected.get(task['identity'])
            or context.manifest['scope']!=SCOPE
            or json.loads(context.input_path('recipe').read_bytes())!=recipe()
            or json.loads(context.input_path('qualification-environment').read_bytes())!=environment()):
        raise ValueError('unchanged nonlinear diagnostic identity, recipe, scope and environment required')
    r=recipe();payload=task['payload'];work,construction=limits(payload);identity=task['identity']
    journal=Journal(context.directory/'construction.sqlite',freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={identity:construction});journal.start(identity)
    def reserve_construction(**counts):
        _check_continue(context.root,context.manifest)
        for key,value in counts.items():journal.reserve(identity,key,value)
    native=bridge_kernel(context);budget=None
    bridge,_=parent_limits(payload)
    try:
        with context.prepay_native(native_calls=bridge['native_calls'],packet_visits=bridge['packet_visits'],
                native_kind='tangent') as budget:
            queries=119 if payload['duration_s']==120 else 1200
            data=material(duration_s=payload['duration_s'],queries=queries,query_start_s=.5,query_step_s=1.,
                reserve=reserve_construction)
            def reserve_bridge(**counts):
                if counts!=dict(native_calls=1,packet_steps=1):raise ValueError('one charged bridge step required')
                budget.reserve(native_calls=1,packet_visits=1)
            op,bridge_mean,descriptor=build_operator(data,law=payload['law'],kernel=native,
                reserve=reserve_bridge,maximum_bytes=r['maximum_operator_bytes'])
        scalar=scalar_kernel(context,anchor=data['anchor_height_m'])
        def reserve_value(**counts):
            if counts!=dict(native_calls=1,packet_steps=len(data['dt']),packet_query_visits=len(data['dt'])*queries):
                raise ValueError('one full known-calibration propagation required')
            _check_continue(context.root,context.manifest)
            context.charge(native_calls=1,packet_visits=counts['packet_query_visits'],native_kind='value')
        nominal=propagate(data,theta=data['raw_theta'],dv=data['raw_dv'],operator=op,kernel=scalar,reserve=reserve_value)
        discrepancy=float(np.max(abs((nominal-bridge_mean)*data['nominal_metric'])))
        if discrepancy>1e-5:raise ValueError('unchanged nominal scalar/bridge agreement failed')
        cut=data['training_epochs'];metric=data['nominal_metric'][cut:]
        _,state=op.apply_block(np.zeros(3*cut),first_epoch=0)
        sigma=np.sqrt(np.diagonal(op.conditional_marginals(state=state)['covariance'],axis1=1,axis2=2))*metric
        context.save('error-operator.json',descriptor)
        context.save('nominal-context.json',dict(times_s=data['times'].tolist(),coordinates=nominal.tolist(),
            nominal_metric=data['nominal_metric'].tolist(),conditional_standard_deviation_neu_m=sigma.tolist(),
            scalar_bridge_maximum_difference_m=discrepancy))
        rows=[]
        for seed in r['seeds']:
            reserve_construction(realizations=1)
            noise=draw(data,law=payload['law'],seed=seed,reserve=reserve_construction);errors=[]
            for amplitude in r['amplitudes']:
                coords=propagate(data,theta=data['raw_theta']+amplitude*noise['theta_error'],
                    dv=data['raw_dv']+amplitude*noise['dv_error'],operator=op,kernel=scalar,reserve=reserve_value)
                errors.append(conditional_error(op,nominal,coords,amplitude*noise['receiver_error'],
                    training_epochs=cut,metric=metric))
            result=summarize_pair(*errors,standard_deviation=sigma,absolute_limit_m=r['absolute_limit_m'],
                relative_limit=r['relative_limit']);rows.append(dict(seed=seed,**result))
            context.save(f'seed-{seed}.json',dict(seed=seed,summary=result,array_sha256=noise['array_sha256']))
            stream=io.BytesIO();np.savez_compressed(stream,errors_neu_m=np.array(errors))
            context.save_bytes(f'seed-{seed}.npz',stream.getvalue())
        journal.verify()
        if any(journal.count(identity,key)!=value for key,value in construction.items()):
            raise ValueError('complete construction charges differ')
        context.save('matched-summary.json',dict(rows=rows,seeds=r['seeds'],law=payload['law'],duration_s=payload['duration_s']))
        return dict(passed=all(v['passed'] for v in rows),realizations=len(rows),passed_realizations=sum(v['passed'] for v in rows),
            prediction_qualified=False,global_remainder_bound_established=False,confidence_calibrated=False,
            optimizer_starts=0,original_reads=0,protected_reads=0,scientific_decision='abstain')
    finally:
        if budget is not None:context.save('native-prepayment.json',budget.snapshot())
        context.note_file(journal.path)


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/noise_nonlinearity_study.py','analysis/tests/test_noise_nonlinearity_study.py',
        'analysis/lll/studies/qualification.py','docs/noisy-prediction-benchmark/NONLINEAR_PLAN.md',
        'docs/noisy-prediction-benchmark/NONLINEAR_EXECUTION.md'])


def prepare(root,*,qualification,parent_qualification,identity='known-calibration-noise-nonlinearity-20261025'):
    if qualification is None or parent_qualification is None:raise ValueError('native and lifecycle qualifications required')
    import re
    if not isinstance(identity,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',identity):raise ValueError('safe fresh identity required')
    from lll.studies.artifacts import atomic,encoded,safe_path
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    from lll.airquantumgrav_inventory import environment
    from lll.compute_budget import environment as threads
    root=Path(root).resolve();env=environment()
    if env['numerical_environment']!=threads(workers=1,threads=1):raise ValueError('one-thread worker environment required')
    own,report=checked(root,qualification,sources=qualification_sources(root),environment=env,minimum_tests=6,
        required_tests=['test_nonlinearity_matrix_has_fixed_seeds_and_finite_separate_allowances',
            'test_nonlinearity_keeps_bridge_prepayment_on_construction_failure',
            'test_nonlinearity_runs_all_fixed_paths_through_frozen_adapter'])
    parent=json.loads(safe_path(root,parent_qualification).read_bytes())
    if not {'analysis/lll/noise_nonlinearity.py','analysis/tests/test_native_noise_nonlinearity.py'}<=set(parent['sources']):
        raise ValueError('native source bindings missing')
    native,native_report=checked(root,parent_qualification,sources=sorted(parent['sources']),environment=env,minimum_tests=21,
        required_tests=[f'test_native_nonlinear_noise_wrapper_and_antithetic_response[True-False-0-{law}-training_kernels0]'
            for law in ('increment','point')])
    base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh finite study required')
    base.mkdir(parents=True);inputs={}
    for index,(key,raw) in enumerate(dict(recipe=encoded(recipe()),
            qualification_request=own,qualification_report=report,**{'qualification-environment':encoded(env),
            'native-parent-request':native,'native-parent-report':native_report}).items()):
        path=base/f'input-{index:03d}';atomic(path,raw);inputs[key]=str(path.relative_to(root))
    definition=dict(id=identity,scope=SCOPE,adapter='analysis/lll/noise_nonlinearity_study.py',
        sources=sorted(set(qualification_sources(root))|set(parent['sources'])),inputs=inputs,tasks=tasks(),
        workers=2,threads=1,maximum_wall_s=recipe()['maximum_wall_s'])
    atomic(base/'definition.json',encoded(definition));m=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+identity,allocation=m['allocation'],limits=m['limits'])
