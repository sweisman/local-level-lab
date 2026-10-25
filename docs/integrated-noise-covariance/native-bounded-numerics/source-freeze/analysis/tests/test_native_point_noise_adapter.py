# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def test_ordinary_native_controls_do_not_require_local_qualification_files(tmp_path,monkeypatch):
    monkeypatch.delenv('LLL_NATIVE_POINT_REQUEST',raising=False)
    monkeypatch.setenv('LLL_PREPAID_REQUEST','missing-local-qualification.json')
    assert qualified_preflight(tmp_path) is False


def test_formal_native_controls_cannot_skip_their_explicit_qualification(tmp_path,monkeypatch):
    monkeypatch.setenv('LLL_NATIVE_POINT_REQUEST','missing-frozen-request.json')
    with pytest.raises(FileNotFoundError):qualified_preflight(tmp_path)


def qualified_preflight(root):
    """Formal runs bind saved evidence; ordinary tests need no local data."""
    import json,os
    main_path=os.environ.get('LLL_NATIVE_POINT_REQUEST')
    if main_path is None:return False
    from lll.studies.artifacts import digest,safe_path
    from lll.studies.qualification import VERSION,checked
    from lll.airquantumgrav_inventory import environment
    main=json.loads(safe_path(root,main_path).read_bytes())
    if (main.get('version')!=VERSION or main['environment']!=environment()
            or any(digest(safe_path(root,n).read_bytes())!=sha for n,sha in main['sources'].items())):
        raise ValueError('native point qualification source/environment changed before work')
    request_path=os.environ.get('LLL_PREPAID_REQUEST',
        'data/ilvis0-source-point-development/prepaid-allowance-request-20261024.json')
    declared=json.loads(safe_path(root,request_path).read_bytes())
    checked(root,request_path,sources=sorted(declared['sources']),environment=environment(),minimum_tests=16,
        required_tests=['test_prepaid_case_charges_all_work_before_execution_and_keeps_attempts_separate',
            'test_partial_prepayment_failure_never_exposes_a_worker_allowance',
            'test_strict_prepaid_case_rejects_missing_declared_work_without_refund',
            'test_prepaid_identity_cannot_restart_with_a_new_counter'])
    return True


def native_source_hashes():
    from pathlib import Path
    from lll.studies.artifacts import digest
    names=('analysis/lll/ilvis0_tangent.cpp','analysis/lll/ilvis0_noise_bridge.cpp',
        'analysis/lll/ilvis0_wide_tangent.py','analysis/lll/ilvis0_noise_step.py',
        'analysis/lll/ilvis0_noise_history.py','analysis/lll/linear_point_noise.py',
        'analysis/lll/state_space_covariance.py','analysis/lll/receiver_noise_states.py',
        'analysis/lll/studies/allowances.py','analysis/tests/test_native_point_noise_adapter.py',
        'docs/native-noise-linearization/POINT_NATIVE_PLAN.md')
    return {n:digest(Path(n).read_bytes()) for n in names}


def case_allowances():
    limits={'builds':dict(builds=2)}
    for law in ('increment','point'):
        for model in (0,1,2):
            for profile in (False,True):
                for height in (False,True):
                    suffix=f'{law}:{model}:{int(profile)}:{int(height)}'
                    limits['long:'+suffix]=dict(native_calls=610,packet_steps=1209)
                    directions=30 if law=='increment' else 36
                    copies=2 if not profile and not height else 1
                    count=4+directions*8*copies
                    limits['short:'+suffix]=dict(native_calls=count,packet_steps=count)
    for model in (0,1):limits[f'receiver:{model}']=dict(native_calls=610,packet_steps=1209)
    for model in (0,1,2):
        for profile in (False,True):
            for height in (False,True):
                limits[f'legacy:{model}:{int(profile)}:{int(height)}']=dict(native_calls=9,packet_steps=12)
    assert sum(v.get('native_calls',0) for v in limits.values())==23984
    assert sum(v.get('packet_steps',0) for v in limits.values())==39594
    return limits


@pytest.fixture(scope='session')
def point_kernels(tmp_path_factory):
    import gzip,json,os,time
    from pathlib import Path
    from lll.studies.artifacts import atomic,digest,encoded
    from lll.studies.journal import Journal
    from lll.studies.allowances import PrepaidCase
    from lll.ilvis0_noise_step import load
    from lll.ilvis0_wide_tangent import load as wide_load
    qualified_preflight(Path.cwd())
    directory=tmp_path_factory.mktemp('native-point-errors');sources=native_source_hashes()
    path=Path(os.environ.get('LLL_NATIVE_POINT_JOURNAL',str(directory/'charges.sqlite')))
    if path.exists():raise ValueError('fresh native point-adapter qualification journal required')
    limits=case_allowances();freeze=digest(encoded(dict(sources=sources,scope='native incremental and rate-point errors',limits=limits)))
    journal=Journal(path,freeze=freeze,limits=limits);started=time.monotonic()
    with PrepaidCase(journal,'builds',require_exact=True) as builds:
        kernel,metadata=load(directory,expected_source_sha256=sources['analysis/lll/ilvis0_tangent.cpp'],
            expected_bridge_sha256=sources['analysis/lll/ilvis0_noise_bridge.cpp'],
            expected_wide_loader_sha256=sources['analysis/lll/ilvis0_wide_tangent.py'],
            reserve_build=lambda:builds.reserve(builds=1))
        builds.reserve(builds=1);_,rm=wide_load(directory,expected_source_sha256=sources['analysis/lll/ilvis0_tangent.cpp'])
    result=dict(kernel=kernel,directory=directory,sources=sources,journal=journal,
        started=started,results=[],outcomes=[builds.snapshot()],path=path)
    yield result
    journal.verify()
    assert len(result['outcomes'])==len(limits)==63
    assert all(row['state']=='complete' and row['attempted']==row['prepaid'] for row in result['outcomes'])
    if 'LLL_NATIVE_POINT_JOURNAL' in os.environ:
        artifacts={}
        for label,source_name,binary_name,meta in (
                ('bridge',metadata['source_file'],metadata['binary_file'],metadata),
                ('reference','wide-tangent-'+rm['source_sha256']+'.cpp','wide-tangent-'+rm['source_sha256']+'.so',rm)):
            for kind,name,key in (('source',source_name,'source_sha256'),('binary',binary_name,'binary_sha256')):
                raw=(directory/name).read_bytes();assert digest(raw)==meta[key]
                target=path.with_name(path.stem+'.'+label+'.'+kind+'.gz');compressed=gzip.compress(raw,mtime=0)
                atomic(target,compressed);artifacts[target.name]=dict(raw_sha256=digest(raw),gzip_sha256=digest(compressed))
        atomic(path.with_suffix('.compilation.json'),encoded(dict(bridge=metadata,reference=rm,
            artifacts=artifacts,journal_freeze=freeze,results=result['results'],outcomes=result['outcomes'],
            charged=dict(native_calls=23984,packet_steps=39594,builds=2),elapsed_s=time.monotonic()-started)))


@pytest.fixture
def native_case(request,point_kernels):
    import time
    from lll.studies.allowances import PrepaidCase
    from lll.studies.artifacts import atomic,encoded
    params=request.node.callspec.params;name=request.function.__name__
    model=params['model'];profile=params.get('profile',False);height=params.get('height',False)
    if name.endswith('long_nominal_history'):identity=f"long:{params['law']}:{model}:{int(profile)}:{int(height)}"
    elif name.endswith('nonlinear_covariance'):identity=f"short:{params['law']}:{model}:{int(profile)}:{int(height)}"
    elif name.endswith('full_receiver_path'):identity=f'receiver:{model}'
    elif name.endswith('legacy_combined_path'):identity=f'legacy:{model}:{int(profile)}:{int(height)}'
    else:raise ValueError('undeclared native qualification case')
    budget=PrepaidCase(point_kernels['journal'],identity,require_exact=True)
    def reserve(**counts):
        if time.monotonic()-point_kernels['started']>600:raise ValueError('cooperative native point allowance exhausted')
        budget.reserve(**counts)
    try:
        with budget:yield dict(point_kernels,reserve=reserve)
    finally:
        point_kernels['outcomes'].append(budget.snapshot())
        atomic(point_kernels['path'].with_suffix('.outcomes.json'),encoded(point_kernels['outcomes']))


def fake_native(kernel,**case):
    import numpy as np
    case['reserve'](native_calls=1)
    a=np.eye(9);g=np.zeros((9,6));g[6:9,:3]=np.eye(3)
    h=np.zeros((3,15));h[:,6:9]=np.eye(3);h[:,9:12]=np.eye(3)
    return dict(coordinates=case['coordinates']+case['theta'],velocity=case['velocity'],
        rotation=case['rotation'],observation=case['coordinates']+case['theta'],
        state_jacobian=np.column_stack((a,g)),observation_jacobian=h)


def point_history(monkeypatch):
    import numpy as np
    from lll import ilvis0_noise_step
    from lll.ilvis0_noise_history import NativeNoiseHistory
    from lll.linear_point_noise import LinearPointNoise
    from test_linear_point_noise import settings
    monkeypatch.setattr(ilvis0_noise_step,'evaluate',fake_native)
    noise=LinearPointNoise(**settings());dt=np.array([.005,.007,.004]);times=np.array([.002,.009,.014])
    history=NativeNoiseHistory(kernel=None,coordinates=np.zeros(3),velocity=np.zeros(3),
        rotation=np.eye(3),theta=np.zeros((3,3)),delta_v=np.zeros((3,3)),dt=dt,query_times=times,
        time_offset_s=0.,model=2,gravity=9.8,radius=6371000.,removal=0.,anchor_height=None,
        lever=np.zeros(3),correction_scales=np.array([1.,2.,3.,4.,5.,6.]),noise=noise,
        white_loadings=np.repeat((np.eye(3)*1e-4)[None],3,axis=0),maximum_packets=3,
        maximum_epochs=3,reserve=lambda **counts:None)
    return history


def gyro_only_reference(history):
    import numpy as np
    from test_linear_point_noise import settings
    from lll.ilvis0_noise_history import associate_queries
    values=settings();dt=history.dt;times=np.r_[0.,np.cumsum(dt)]
    indices,fractions=associate_queries(dt,history.queries,time_offset_s=0.)
    points=np.kron(np.eye(4),values['gyro_point_covariance'])
    points+=np.kron(np.exp(-abs(times[:,None]-times[None,:])/values['gyro_bias_tau_s']),values['gyro_bias_covariance'])
    weights=np.zeros((3,4))
    for row,(packet,fraction) in enumerate(zip(indices,fractions)):
        for i in range(packet):weights[row,i:i+2]+=dt[i]/2
        weights[row,packet:packet+2]+=dt[packet]*fraction/2
    mapping=np.kron(weights,np.diag(history.correction_scales[:3]))
    return mapping@points@mapping.T


def operator(steps,initial,dimension,n):
    from lll.state_space_covariance import LinearInnovations
    return LinearInnovations(steps,epoch_count=n,state_dimension=dimension,observation_dimension=3,
        initial_loading=initial,maximum_bytes=200000,design_is_fixed=True,error_distribution='gaussian',
        observation_form='before_transition_shared_noise')


def test_native_history_accepts_21_state_point_law_and_keeps_neighbor_noise(monkeypatch):
    import numpy as np
    history=point_history(monkeypatch)
    assert history.state_dimension==21
    op=operator(history.steps(),history.noise.initial_loading(),21,3)
    u=op.unwhiten(np.eye(9))
    np.testing.assert_allclose(u@u.T,gyro_only_reference(history)+np.eye(9)*1e-8,rtol=2e-12,atol=1e-20)


def test_point_and_receiver_path_retains_all_33_states(monkeypatch):
    import numpy as np
    from lll.receiver_noise_states import ReceiverAugmentation
    from lll.ilvis0_error_model import Spec,covariance
    history=point_history(monkeypatch)
    spec=Spec(white=np.eye(3)*1e-8,offset=np.eye(3)*2e-8,drift=np.eye(3)*1e-8,
        components=((.01,np.eye(3)*3e-8),(.03,np.eye(3)*4e-8)),drift_origin_s=0.,drift_span_s=.02)
    augmented=ReceiverAugmentation(history.steps(),times=history.queries,spec=spec,
        transforms=np.repeat(np.eye(3)[None],3,axis=0),state_dimension=21,
        initial_loading=history.noise.initial_loading(),maximum_epochs=3)
    assert augmented.state_dimension==33
    op=operator(augmented.steps(),augmented.initial_loading,33,3);u=op.unwhiten(np.eye(9))
    np.testing.assert_allclose(u@u.T,gyro_only_reference(history)+covariance(history.queries,spec),rtol=2e-12,atol=1e-20)


def test_innovations_supports_declared_40_state_limit_without_dense_epoch_storage():
    import numpy as np
    from lll.state_space_covariance import LinearInnovations
    from test_state_space_covariance import dense_reference
    initial=np.eye(40)*.02
    steps=[dict(transition=np.eye(40)*.9,process_loading=np.eye(40)*.01,
        observation=np.sin(np.arange(120).reshape(3,40)/13),white_loading=np.eye(3)) for _ in range(2)]
    op=LinearInnovations(steps,epoch_count=2,state_dimension=40,observation_dimension=3,
        initial_loading=initial,maximum_bytes=100000,design_is_fixed=True,error_distribution='gaussian')
    u=op.unwhiten(np.eye(6))
    np.testing.assert_allclose(u@u.T,dense_reference(initial,steps),rtol=1e-12,atol=1e-13)
    assert op.storage_bytes<30000
    with pytest.raises(ValueError):LinearInnovations([],epoch_count=2,state_dimension=41,
        observation_dimension=3,initial_loading=None,maximum_bytes=100000,
        design_is_fixed=True,error_distribution='gaussian')


def generated_case(model,profile,height,n):
    import numpy as np
    from test_ilvis0_noise_history import generated_history
    from lll.ilvis0_shape import PARAMETERS
    base,point,args=generated_history(model,profile,height,600 if n==600 else 4)
    base.dt=base.dt[:n];phase=np.arange(n+1)
    rates=np.column_stack((.2+.03*np.sin(phase/9),-.3+.02*np.cos(phase/7),.1+.04*np.sin(phase/11)))
    forces=np.column_stack((.4+.02*np.cos(phase/5),.2+.03*np.sin(phase/8),-9.8+.02*np.cos(phase/13)))
    base.theta=(rates[:-1]+rates[1:])*(base.dt[:,None]/2)
    base.dv=(forces[:-1]+forces[1:])*(base.dt[:,None]/2)
    if n==2:base.gps_times=base.gps_times[:2]
    base.gps=np.zeros((len(base.gps_times),3))
    values=dict(zip(base.bounds.active,point))
    p=np.array([values.get(name,0.)*base.bounds.limits.get(name,0.) for name in PARAMETERS],dtype=np.longdouble)
    dt=base.dt.astype(np.longdouble)[:,None]
    args.update(theta=(base.theta.astype(np.longdouble)-p[9:12]*dt)/(1+p[15:18]),
        delta_v=(base.dv.astype(np.longdouble)-p[12:15]*dt)/(1+p[18:21]),dt=base.dt,
        query_times=base.gps_times,maximum_packets=n,maximum_epochs=len(base.gps_times))
    return base,point,args


def noise_for(law):
    if law=='increment':
        from lll.ilvis0_noise_history import PacketNoise
        from test_ilvis0_noise_history import settings
        return PacketNoise(**settings())
    from lll.linear_point_noise import LinearPointNoise
    from test_linear_point_noise import settings
    return LinearPointNoise(**settings())


@pytest.mark.parametrize('law',['increment','point'])
@pytest.mark.parametrize('model',[0,1,2])
@pytest.mark.parametrize('profile',[False,True])
@pytest.mark.parametrize('height',[False,True])
def test_point_adapter_long_nominal_history(native_case,law,model,profile,height):
    import numpy as np
    from lll.ilvis0_noise_history import NativeNoiseHistory
    from lll.ilvis0_wide_tangent import load,evaluate
    base,point,args=generated_case(model,profile,height,600);k=native_case;noise=noise_for(law)
    history=NativeNoiseHistory(kernel=k['kernel'],**args,noise=noise,
        white_loadings=np.repeat(np.diag([1e-7,2e-7,.2])[None],9,axis=0),reserve=k['reserve'])
    dimension=21 if law=='point' else 15
    op=operator(history.steps(),noise.initial_loading(),dimension,9)
    reference,_=load(k['directory'],expected_source_sha256=k['sources']['analysis/lll/ilvis0_tangent.cpp'],
        gravity_anchor_height_m=args['anchor_height'])
    def counted(*a,**kw):k['reserve'](native_calls=1,packet_steps=600);return reference(*a,**kw)
    nominal=evaluate(base,point,('sphere_rotating','sphere_still','flat_still')[model],kernel=counted)[0]
    np.testing.assert_array_equal(history.observations.astype(float),nominal)
    np.testing.assert_allclose(op.whiten(op.unwhiten(np.eye(27))),np.eye(27),rtol=2e-12,atol=2e-12)
    assert history.final_state is not None and op.storage_bytes<50000
    k['results'].append(dict(kind='long',law=law,model=model,profile=profile,height=height,
        packets=600,queries=9,state_dimension=dimension,nominal_binary64_equal=True,operator_bytes=op.storage_bytes))


def independently_perturbed_points(k,args,driver,amount):
    import numpy as np
    from scipy.linalg import cholesky
    from test_linear_point_noise import settings
    from lll.ilvis0_noise_history import associate_queries
    from lll.ilvis0_noise_step import evaluate
    values=settings();bias_roots=np.zeros((6,6));white_roots=np.zeros((6,6))
    for i,family in enumerate(('gyro','accel')):
        sl=slice(3*i,3*i+3)
        bias_roots[sl,sl]=cholesky(values[family+'_bias_covariance'],lower=True)
        white_roots[sl,sl]=cholesky(values[family+'_point_covariance'],lower=True)
    initial=np.zeros((12,12));initial[:6,:6]=bias_roots;initial[6:,6:]=white_roots
    hidden=np.zeros(12,dtype=np.longdouble)
    if driver<12:hidden=initial[:,driver].astype(np.longdouble)*np.longdouble(amount)
    tau=np.repeat([values['gyro_bias_tau_s'],values['accel_bias_tau_s']],3)
    indices,fractions=associate_queries(args['dt'],args['query_times'],time_offset_s=args['time_offset_s'])
    state={name:args[name] for name in ('coordinates','velocity','rotation')}
    fixed={name:args[name] for name in ('model','gravity','radius','removal','anchor_height','lever')}
    output=[];query=0
    for i,interval in enumerate(args['dt']):
        rho=np.exp(-interval/tau);draw=np.zeros(12,dtype=np.longdouble)
        if driver>=12 and (driver-12)//12==i:
            root=np.zeros((12,12));root[:6,:6]=np.sqrt(-np.expm1(-2*interval/tau))[:,None]*bias_roots
            root[6:,6:]=white_roots
            draw=root[:,(driver-12)%12].astype(np.longdouble)*np.longdouble(amount)
        next_bias=rho*hidden[:6]+draw[:6];next_white=draw[6:]
        error=np.longdouble(interval/2)*(hidden[:6]+hidden[6:]+next_bias+next_white)
        error=error*args['correction_scales']
        theta=args['theta'][i]-error[:3];dv=args['delta_v'][i]-error[3:]
        def call(fraction):
            f=np.longdouble(fraction)
            def reserve(**counts):k['reserve'](**counts,packet_steps=1)
            return evaluate(k['kernel'],**state,**fixed,theta=theta*f,delta_v=dv*f,
                dt=np.longdouble(interval)*f,derivatives=False,reserve=reserve)
        if query<len(indices) and indices[query]==i:
            output.append(call(fractions[query])['observation']);query+=1
        full=call(1.);state={name:full[name] for name in state}
        hidden=np.r_[next_bias,next_white]
    return np.array(output,dtype=np.longdouble)


@pytest.mark.parametrize('law',['increment','point'])
@pytest.mark.parametrize('model',[0,1,2])
@pytest.mark.parametrize('profile',[False,True])
@pytest.mark.parametrize('height',[False,True])
def test_point_adapter_independent_nonlinear_covariance(native_case,law,model,profile,height):
    import numpy as np
    from test_ilvis0_noise_step import metric
    from test_ilvis0_noise_history import independently_perturbed_history
    from lll.ilvis0_noise_history import NativeNoiseHistory
    base,point,args=generated_case(model,profile,height,2);k=native_case;noise=noise_for(law)
    args['lever']=np.array([1.2,-.8,.5],dtype=np.longdouble)
    white=np.array([1e-12,1e-12,1e-5])
    history=NativeNoiseHistory(kernel=k['kernel'],**args,noise=noise,
        white_loadings=np.repeat(np.diag(white)[None],2,axis=0),reserve=k['reserve'])
    steps=list(history.steps());scales=np.array([(*metric(model,c),1.) for c in history.observations])
    for step,scale in zip(steps,scales):
        for name in ('observation','observation_process_loading','white_loading'):step[name]=scale[:,None]*step[name]
    dimension=21 if law=='point' else 15;op=operator(steps,noise.initial_loading(),dimension,2)
    u=op.unwhiten(np.eye(6));actual=u@u.T-np.diag(np.concatenate([(s*white)**2 for s in scales]))
    perturb=independently_perturbed_points if law=='point' else independently_perturbed_history
    directions=36 if law=='point' else 30;errors=[]
    for amount in ([.02,.01] if not profile and not height else [.02]):
        columns=[]
        for driver in range(directions):
            plus=perturb(k,args,driver,amount);minus=perturb(k,args,driver,-amount)
            columns.append((((plus-minus)/(2*np.longdouble(amount)))*scales).astype(float).ravel())
        loading=np.column_stack(columns);expected=loading@loading.T;norm=np.sqrt(np.diag(expected))
        difference=(actual-expected)/norm[:,None]/norm[None,:];errors.append(float(np.max(abs(difference))))
        np.testing.assert_allclose(actual/norm[:,None]/norm[None,:],expected/norm[:,None]/norm[None,:],rtol=3e-5,atol=3e-5)
    k['results'].append(dict(kind='short',law=law,model=model,profile=profile,height=height,
        packets=2,queries=2,driver_directions=directions,maximum_normalized_covariance_errors=errors))


@pytest.mark.parametrize('model',[0,1])
def test_point_adapter_full_receiver_path(native_case,model):
    import numpy as np
    from lll.ilvis0_noise_history import NativeNoiseHistory
    from lll.receiver_noise_states import ReceiverAugmentation
    from lll.ilvis0_error_model import Spec,covariance
    from lll.ilvis0_wide_tangent import load,evaluate
    base,point,args=generated_case(model,True,True,600);k=native_case;noise=noise_for('point');n=9
    units=np.array([1e-7,2e-7,.2])
    transforms=np.array([units[:,None]*np.array([[1.+i/20,.02,0.],[.01,1.1,0.],[0.,.02,.9-i/100]]) for i in range(n)])
    spec=Spec(white=np.eye(3)*.2,offset=np.eye(3)*.3,drift=np.eye(3)*.1,
        components=((.1,np.eye(3)*.4),(1.,np.eye(3)*.6)),drift_origin_s=-.1,drift_span_s=4.)
    history=NativeNoiseHistory(kernel=k['kernel'],**args,noise=noise,
        white_loadings=transforms*np.sqrt(.2),reserve=k['reserve'])
    steps=list(history.steps());native=operator(steps,noise.initial_loading(),21,n)
    u=native.unwhiten(np.eye(27));expected=u@u.T+covariance(base.gps_times,spec,transforms)
    for i,step in enumerate(steps):expected[3*i:3*i+3,3*i:3*i+3]-=step['white_loading']@step['white_loading'].T
    augmented=ReceiverAugmentation(iter(steps),times=base.gps_times,spec=spec,transforms=transforms,
        state_dimension=21,initial_loading=noise.initial_loading(),maximum_epochs=n)
    assert augmented.state_dimension==33
    combined=operator(augmented.steps(),augmented.initial_loading,33,n)
    scale=np.tile(1/units,n);expected=expected*scale[:,None]*scale[None,:]
    u=combined.unwhiten(np.eye(27))*scale[:,None]
    np.testing.assert_allclose(u@u.T,expected,rtol=5e-12,atol=5e-12)
    reference,_=load(k['directory'],expected_source_sha256=k['sources']['analysis/lll/ilvis0_tangent.cpp'],gravity_anchor_height_m=args['anchor_height'])
    def counted(*a,**kw):k['reserve'](native_calls=1,packet_steps=600);return reference(*a,**kw)
    prediction,_,jacobian,_=evaluate(base,point,('sphere_rotating','sphere_still')[model],kernel=counted)
    np.testing.assert_array_equal(history.observations.astype(float),prediction)
    dense=np.linalg.solve(np.linalg.cholesky(expected),jacobian*scale[:,None]);white=combined.whiten(jacobian)
    np.testing.assert_allclose(white,dense,rtol=5e-11,atol=2e-8)
    _,checkpoint=combined.apply_block(np.sin(np.arange(12)/4)/scale[:12],first_epoch=0)
    future=combined.conditional_marginals(state=checkpoint)
    mean=expected[12:,:12]@np.linalg.solve(expected[:12,:12],np.sin(np.arange(12)/4))
    conditional=expected[12:,12:]-expected[12:,:12]@np.linalg.solve(expected[:12,:12],expected[:12,12:])
    np.testing.assert_allclose(future['mean'].ravel()*scale[12:],mean,rtol=2e-11,atol=2e-11)
    for i,block in enumerate(future['covariance']):
        s=scale[12+3*i:15+3*i]
        np.testing.assert_allclose(block*s[:,None]*s[None,:],conditional[3*i:3*i+3,3*i:3*i+3],rtol=2e-11,atol=2e-11)
    k['results'].append(dict(kind='full_receiver',model=model,packets=600,queries=9,state_dimension=33,
        calibration_columns=27,conditioning_epochs=4,later_observations_used=False,nominal_binary64_equal=True))


@pytest.mark.parametrize('model',[0,1,2])
@pytest.mark.parametrize('profile',[False,True])
@pytest.mark.parametrize('height',[False,True])
def test_point_adapter_retains_legacy_combined_path(native_case,model,profile,height):
    from test_ilvis0_joint_prediction_errors import test_native_receiver_covariance_design_and_earlier_only_prediction
    test_native_receiver_covariance_design_and_earlier_only_prediction(native_case,model,profile,height)
    native_case['results'][-1]['kind']='legacy_combined'
