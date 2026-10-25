# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def history_sources():
    import hashlib
    from pathlib import Path
    names=('analysis/lll/covariance_roots.py','analysis/lll/ilvis0_noise_history.py',
        'analysis/lll/ilvis0_noise_step.py','analysis/lll/ilvis0_noise_bridge.cpp',
        'analysis/lll/ilvis0_tangent.cpp','analysis/lll/ilvis0_wide_tangent.py',
        'analysis/lll/measurement_noise.py','analysis/lll/state_space_covariance.py',
        'analysis/tests/test_ilvis0_noise_history.py','analysis/tests/test_ilvis0_noise_step.py',
        'docs/native-noise-linearization/HISTORY_PLAN.md')
    return {n:hashlib.sha256(Path(n).read_bytes()).hexdigest() for n in names}


@pytest.fixture(scope='session')
def history_kernels(tmp_path_factory):
    import gzip
    import os
    import time
    from pathlib import Path
    from lll.studies.artifacts import atomic,digest,encoded
    from lll.studies.journal import Journal
    from lll.ilvis0_noise_step import load
    from lll.ilvis0_wide_tangent import load as wide_load
    directory=tmp_path_factory.mktemp('noise-history-kernels');sources=history_sources()
    path=Path(os.environ.get('LLL_NOISE_HISTORY_JOURNAL',str(directory/'charges.sqlite')))
    if path.exists():raise ValueError('fresh full-history qualification journal required')
    limits=dict(native_calls=24000,packet_steps=32000,builds=2)
    freeze=digest(encoded(dict(sources=sources,scope='generated complete native histories',limits=limits)))
    journal=Journal(path,freeze=freeze,limits={'qualification':limits});journal.start('qualification')
    started=time.monotonic()
    def reserve(**counts):
        if time.monotonic()-started>1800:raise ValueError('cooperative full-history time allowance exhausted')
        for key,value in counts.items():journal.reserve('qualification',key,value)
    def build():reserve(builds=1)
    kernel,metadata=load(directory,
        expected_source_sha256=sources['analysis/lll/ilvis0_tangent.cpp'],
        expected_bridge_sha256=sources['analysis/lll/ilvis0_noise_bridge.cpp'],
        expected_wide_loader_sha256=sources['analysis/lll/ilvis0_wide_tangent.py'],reserve_build=build)
    build();_,rm=wide_load(directory,expected_source_sha256=sources['analysis/lll/ilvis0_tangent.cpp'])
    result=dict(kernel=kernel,reserve=reserve,directory=directory,sources=sources,results=[])
    yield result
    journal.verify()
    assert journal.count('qualification','builds')==2
    if 'LLL_NOISE_HISTORY_JOURNAL' in os.environ:
        artifacts={}
        for label,source_name,binary_name,meta in (
                ('bridge',metadata['source_file'],metadata['binary_file'],metadata),
                ('reference','wide-tangent-'+rm['source_sha256']+'.cpp','wide-tangent-'+rm['source_sha256']+'.so',rm)):
            for kind,name,key in (('source',source_name,'source_sha256'),('binary',binary_name,'binary_sha256')):
                raw=(directory/name).read_bytes();assert digest(raw)==meta[key]
                target=path.with_name(path.stem+'.'+label+'.'+kind+'.gz')
                compressed=gzip.compress(raw,mtime=0);atomic(target,compressed)
                artifacts[target.name]=dict(raw_sha256=digest(raw),gzip_sha256=digest(compressed))
        atomic(path.with_suffix('.compilation.json'),encoded(dict(bridge=metadata,reference=rm,
            artifacts=artifacts,charged={k:journal.count('qualification',k) for k in limits},
            journal_freeze=freeze,results=result['results'],elapsed_s=time.monotonic()-started)))


def settings(zero=False):
    import numpy as np
    return dict(gyro_white_psd=np.eye(3)*(0. if zero else .003**2),
        accel_white_psd=np.eye(3)*(0. if zero else .02**2),
        gyro_bias_covariance=np.eye(3)*(0. if zero else .004**2),
        accel_bias_covariance=np.eye(3)*(0. if zero else .03**2),
        gyro_bias_tau_s=2.4,accel_bias_tau_s=4.1)


def test_loading_root_preserves_scaled_singular_gramian_without_variance_repair():
    import numpy as np
    from lll.covariance_roots import loading_root
    matrix=np.array([[1e-12,2e-12,0.],[0.,0.,0.],[3.,6.,0.],[2e5,-1e5,4e5]])
    root=loading_root(matrix,maximum_rows=15,maximum_columns=32)
    scales=np.array([1e12,1.,1.,1e-5]);a=root*scales[:,None];b=matrix*scales[:,None]
    np.testing.assert_allclose(a@a.T,b@b.T,rtol=2e-14,atol=2e-14)
    assert np.array_equal(root[1],np.zeros(root.shape[1]))
    assert loading_root(np.zeros((15,0)),maximum_rows=15,maximum_columns=32).shape==(15,0)


def independent_packet_covariance(dt,values):
    import numpy as np
    from lll.measurement_noise import ou_moments
    covariance=np.zeros((12,12))
    for start,white,bias,tau in ((0,values['gyro_white_psd'],values['gyro_bias_covariance'],values['gyro_bias_tau_s']),
            (3,values['accel_white_psd'],values['accel_bias_covariance'],values['accel_bias_tau_s'])):
        m={k:v[0] for k,v in ou_moments(np.array([dt]),tau_s=tau).items()}
        sl=slice(start,start+3);end=slice(start+6,start+9)
        covariance[sl,sl]=white*dt+bias*m['integral_variance']
        covariance[end,end]=bias*m['state_variance']
        covariance[sl,end]=covariance[end,sl]=bias*m['state_integral_covariance']
    return covariance


@pytest.mark.parametrize('zero',[False,True])
def test_packet_noise_loading_matches_increment_endpoint_law_and_initial_bias(zero):
    import numpy as np
    from lll.ilvis0_noise_history import PacketNoise
    values=settings(zero);noise=PacketNoise(**values);dt=.005;root,rho,mean=noise.at(dt)
    np.testing.assert_allclose(root@root.T,independent_packet_covariance(dt,values),rtol=2e-13,atol=1e-20)
    initial=noise.initial_loading()
    np.testing.assert_allclose((initial@initial.T)[9:12,9:12],values['gyro_bias_covariance'])
    assert root.shape[0]==12 and root.shape[1]<=12 and rho.shape==mean.shape==(6,)
    assert np.all(rho>0) and np.all(rho<1) and np.all(mean>0)


def test_packet_noise_preserves_rank_deficient_axes_and_rejects_negative_variance():
    import numpy as np
    from lll.ilvis0_noise_history import PacketNoise
    values=settings()
    for key in ('gyro_white_psd','accel_white_psd','gyro_bias_covariance','accel_bias_covariance'):
        values[key]=np.diag([values[key][0,0],0.,0.])
    noise=PacketNoise(**values);root,_,_=noise.at(.007)
    expected=independent_packet_covariance(.007,values)
    np.testing.assert_allclose(root@root.T,expected,rtol=3e-13,atol=1e-20)
    np.testing.assert_array_equal(root[[1,2,4,5,7,8,10,11]],np.zeros((8,root.shape[1])))
    values['gyro_white_psd'][1,1]=-1e-20
    with pytest.raises(ValueError,match='nonnegative'):PacketNoise(**values)


@pytest.mark.parametrize('shape',[(2,33),(16,2)])
def test_loading_compression_enforces_declared_work_dimensions(shape):
    import numpy as np
    from lll.covariance_roots import loading_root
    with pytest.raises(ValueError):loading_root(np.zeros(shape),maximum_rows=15,maximum_columns=32)


def test_query_association_keeps_sequential_clock_and_unrounded_boundary_fraction():
    import numpy as np
    from lll.ilvis0_noise_history import associate_queries
    dt=np.full(600,.005);elapsed=0.;ends=[]
    for interval in dt:elapsed+=float(interval);ends.append(elapsed)
    queries=np.array([ends[119],ends[299],ends[598]])
    indices,fractions=associate_queries(dt,queries,time_offset_s=0.)
    np.testing.assert_array_equal(indices,[119,299,598])
    exact=(queries-np.array(ends)[indices-1])/dt[indices]
    np.testing.assert_array_equal(fractions,exact)
    assert np.any(fractions!=1.)  # The native clock is not silently repaired.


@pytest.mark.parametrize('bad',['reverse','duplicate_packet','before_start','after_end'])
def test_query_association_rejects_unsupported_grid_before_any_native_call(bad):
    import numpy as np
    from lll.ilvis0_noise_history import associate_queries
    queries=[.002,.008]
    if bad=='reverse':queries=queries[::-1]
    elif bad=='duplicate_packet':queries=[.001,.002]
    elif bad=='before_start':queries=[0.,.008]
    else:queries=[.002,.02]
    with pytest.raises(ValueError):associate_queries(np.array([.005,.005]),queries,time_offset_s=0.)


def test_stream_uses_every_packet_and_preserves_shared_partial_query_noise(monkeypatch):
    import numpy as np
    from lll import ilvis0_noise_step
    from lll.ilvis0_noise_history import NativeNoiseHistory, PacketNoise
    from lll.state_space_covariance import LinearInnovations
    calls=[];charges=[]
    def evaluate(kernel,**case):
        case['reserve'](native_calls=1);calls.append(float(case['dt']))
        a=np.eye(9);g=np.zeros((9,6));g[6:9,:3]=np.eye(3)
        observed=np.zeros((3,15));observed[:,:9]=np.eye(9)[6:9];observed[:,9:12]=np.eye(3)
        return dict(coordinates=case['coordinates']+case['theta'],velocity=case['velocity'],
            rotation=case['rotation'],observation=case['coordinates']+case['theta'],
            state_jacobian=np.column_stack((a,g)),observation_jacobian=observed)
    monkeypatch.setattr(ilvis0_noise_step,'evaluate',evaluate)
    dt=np.array([.005,.007,.004,.006]);theta=np.full((4,3),.002,dtype=np.longdouble)
    original=theta.copy();noise=PacketNoise(**settings());times=np.array([.002,.015])
    history=NativeNoiseHistory(kernel=None,coordinates=np.zeros(3),velocity=np.zeros(3),
        rotation=np.eye(3),theta=theta,delta_v=np.zeros((4,3)),dt=dt,query_times=times,
        time_offset_s=0.,model=2,gravity=9.8,radius=6371000.,removal=0.,anchor_height=None,
        lever=np.zeros(3),correction_scales=np.array([1.,2.,3.,4.,5.,6.]),noise=noise,
        white_loadings=np.repeat((np.eye(3)*1e-4)[None],2,axis=0),maximum_packets=4,
        maximum_epochs=2,reserve=lambda **counts:charges.append(counts))
    steps=list(history.steps())
    assert len(steps)==2 and len(calls)==6 and len(charges)==6
    assert all(c==dict(native_calls=1,packet_steps=1) for c in charges)
    np.testing.assert_array_equal(theta,original)
    np.testing.assert_allclose(history.final_state['coordinates'],theta.sum(axis=0))
    assert np.any(steps[0]['observation_process_loading'])
    # Independently expand the full driver history. Partial and endpoint use
    # the same full-packet error, and initial OU biases persist across packets.
    width=6+12*4;state=np.zeros((15,width));state[:,:6]=noise.initial_loading()
    predicted=[];fractions={0:.002/.005,2:(.015-.012)/.004}
    for i,interval in enumerate(dt):
        root,rho,mean=noise.at(float(interval));scales=history.correction_scales
        f=np.eye(15);f[9:,9:]=np.diag(rho);f[6:9,9:12]=-np.diag(scales[:3]*mean[:3])
        b=np.zeros((15,12));b[6:9,:3]=-np.diag(scales[:3]);b[9:,6:]=np.eye(6)
        driver=np.zeros((12,width));driver[:,6+12*i:18+12*i]=root
        if i in fractions:
            fraction=fractions[i]
            h=np.zeros((3,15));h[:,6:9]=np.eye(3)
            h[:,9:12]=-np.diag(scales[:3]*mean[:3]*fraction)
            d=np.zeros((3,12));d[:,:3]=-np.diag(scales[:3]*fraction)
            predicted.append(h@state+d@driver)
        state=f@state+b@driver
    direct=np.vstack(predicted);expected=direct@direct.T+np.eye(6)*1e-8
    operator=LinearInnovations(steps,epoch_count=2,state_dimension=15,observation_dimension=3,
        initial_loading=noise.initial_loading(),maximum_bytes=100000,design_is_fixed=True,
        error_distribution='gaussian',observation_form='before_transition_shared_noise')
    unwhitening=operator.unwhiten(np.eye(6))
    np.testing.assert_allclose(unwhitening@unwhitening.T,expected,rtol=1e-12,atol=1e-19)
    with pytest.raises(ValueError,match='once'):list(history.steps())


def generated_history(model,profile,height,n):
    import numpy as np
    from test_ilvis0_noise_step import reference_case
    case,base,point,limits,p=reference_case(model,profile,height)
    base.dt=np.resize(np.array([.005,.007,.004,.006]),n)
    phase=np.arange(n,dtype=float)
    rates=np.column_stack((.2+.03*np.sin(phase/9),-.3+.02*np.cos(phase/7),.1+.04*np.sin(phase/11)))
    forces=np.column_stack((.4+.02*np.cos(phase/5),.2+.03*np.sin(phase/8),-9.8+.02*np.cos(phase/13)))
    base.theta=rates*base.dt[:,None];base.dv=forces*base.dt[:,None]
    end=[];elapsed=0.
    for dt in base.dt:elapsed+=float(dt);end.append(elapsed)
    indices=np.array([0,1,2,3]) if n==4 else np.array([1,53,109,177,255,333,419,507,598])
    fractions=np.resize(np.array([.37,.61,.83]),len(indices))
    start=np.r_[0.,end[:-1]]
    base.gps_times=start[indices]+fractions*base.dt[indices]
    base.gps=np.zeros((len(indices),3))
    extended=p.astype(np.longdouble);dt=base.dt.astype(np.longdouble)[:,None]
    corrected_theta=(base.theta.astype(np.longdouble)-extended[9:12]*dt)/(1+extended[15:18])
    corrected_dv=(base.dv.astype(np.longdouble)-extended[12:15]*dt)/(1+extended[18:21])
    args={k:v for k,v in case.items() if k not in ('dt','theta','delta_v')}
    args.update(theta=corrected_theta,delta_v=corrected_dv,dt=base.dt,query_times=base.gps_times,
        time_offset_s=p[25],correction_scales=1/(1+p[15:21]),maximum_packets=n,
        maximum_epochs=len(indices))
    return base,point,args


@pytest.mark.parametrize('model',[0,1,2])
@pytest.mark.parametrize('profile',[False,True])
@pytest.mark.parametrize('height',[False,True])
def test_complete_native_history_preserves_wide_mean_and_bounded_storage(history_kernels,model,profile,height):
    import numpy as np
    from lll.ilvis0_noise_history import NativeNoiseHistory,PacketNoise
    from lll.ilvis0_wide_tangent import load,evaluate
    from lll.state_space_covariance import LinearInnovations
    base,point,args=generated_history(model,profile,height,600);k=history_kernels
    snapshot={name:args[name].copy() for name in ('theta','delta_v','dt','coordinates','velocity','rotation')}
    history=NativeNoiseHistory(kernel=k['kernel'],**args,noise=PacketNoise(**settings()),
        white_loadings=np.repeat(np.diag([1e-7,2e-7,.2])[None],9,axis=0),reserve=k['reserve'])
    operator=LinearInnovations(history.steps(),epoch_count=9,state_dimension=15,observation_dimension=3,
        initial_loading=history.noise.initial_loading(),maximum_bytes=25000,design_is_fixed=True,
        error_distribution='gaussian',observation_form='before_transition_shared_noise')
    reference,_=load(k['directory'],expected_source_sha256=k['sources']['analysis/lll/ilvis0_tangent.cpp'],
        gravity_anchor_height_m=args['anchor_height'])
    def counted(*a,**kw):k['reserve'](native_calls=1,packet_steps=600);return reference(*a,**kw)
    original=evaluate(base,point,('sphere_rotating','sphere_still','flat_still')[model],kernel=counted)[0]
    np.testing.assert_array_equal(history.observations.astype(float),original)
    assert history.final_state is not None and operator.storage_bytes<25000
    for name,value in snapshot.items():np.testing.assert_array_equal(args[name],value)
    identity=np.eye(27)
    np.testing.assert_allclose(operator.whiten(operator.unwhiten(identity)),identity,rtol=2e-12,atol=2e-12)
    k['results'].append(dict(kind='long',model=model,profile=profile,height=height,
        packets=600,queries=9,nominal_binary64_equal=True,operator_bytes=operator.storage_bytes))


def independently_perturbed_history(k,args,driver,amount):
    """Nonlinear propagation; no state/input Jacobian or provider step is used."""
    import numpy as np
    from scipy.linalg import cholesky
    from lll.ilvis0_noise_step import evaluate
    from lll.ilvis0_noise_history import associate_queries
    values=settings();n=len(args['dt']);bias=np.zeros(6,dtype=np.longdouble)
    initial=np.zeros((6,6));initial[:3,:3]=cholesky(values['gyro_bias_covariance'],lower=True)
    initial[3:,3:]=cholesky(values['accel_bias_covariance'],lower=True)
    if driver<6:bias=initial[:,driver].astype(np.longdouble)*np.longdouble(amount)
    indices,fractions=associate_queries(args['dt'],args['query_times'],time_offset_s=args['time_offset_s'])
    state={name:args[name] for name in ('coordinates','velocity','rotation')}
    fixed={name:args[name] for name in ('model','gravity','radius','removal','anchor_height','lever')}
    output=[];j=0
    for i,interval in enumerate(args['dt']):
        innovation=np.zeros(12,dtype=np.longdouble)
        if driver>=6 and (driver-6)//12==i:
            root=cholesky(independent_packet_covariance(float(interval),values),lower=True)
            innovation=root[:,(driver-6)%12].astype(np.longdouble)*np.longdouble(amount)
        # Conditional OU means are independently expressed with exp/expm1.
        tau=np.repeat([values['gyro_bias_tau_s'],values['accel_bias_tau_s']],3)
        rho=np.exp(-interval/tau);mean=-tau*np.expm1(-interval/tau)
        corrected_error=args['correction_scales']*(mean*bias+innovation[:6])
        theta=args['theta'][i]-corrected_error[:3];dv=args['delta_v'][i]-corrected_error[3:]
        def call(fraction):
            f=np.longdouble(fraction)
            def reserve(**counts):k['reserve'](**counts,packet_steps=1)
            return evaluate(k['kernel'],**state,**fixed,theta=theta*f,delta_v=dv*f,
                dt=np.longdouble(interval)*f,derivatives=False,reserve=reserve)
        if j<len(indices) and indices[j]==i:
            output.append(call(fractions[j])['observation']);j+=1
        full=call(1.);state={name:full[name] for name in state}
        bias=rho*bias+innovation[6:]
    return np.array(output,dtype=np.longdouble)


@pytest.mark.parametrize('model',[0,1,2])
@pytest.mark.parametrize('profile',[False,True])
@pytest.mark.parametrize('height',[False,True])
def test_complete_noise_covariance_matches_independent_nonlinear_driver_differences(history_kernels,model,profile,height):
    import numpy as np
    from test_ilvis0_noise_step import metric
    from lll.ilvis0_noise_history import NativeNoiseHistory,PacketNoise
    from lll.state_space_covariance import LinearInnovations
    base,point,args=generated_history(model,profile,height,4);k=history_kernels
    # A fixed nonzero antenna arm makes all attitude noise directions observable.
    args['lever']=np.array([1.2,-.8,.5],dtype=np.longdouble)
    mean=NativeNoiseHistory(kernel=k['kernel'],**args,noise=PacketNoise(**settings()),
        white_loadings=np.repeat(np.diag([1e-12,1e-12,1e-5])[None],4,axis=0),reserve=k['reserve'])
    steps=list(mean.steps());scale=np.array([(*metric(model,c),1.) for c in mean.observations])
    for step,s in zip(steps,scale):
        for key in ('observation','observation_process_loading','white_loading'):step[key]=s[:,None]*step[key]
    operator=LinearInnovations(steps,epoch_count=4,state_dimension=15,observation_dimension=3,
        initial_loading=mean.noise.initial_loading(),maximum_bytes=100000,design_is_fixed=True,
        error_distribution='gaussian',observation_form='before_transition_shared_noise')
    unwhitening=operator.unwhiten(np.eye(12));white=np.concatenate([(s*np.array([1e-12,1e-12,1e-5]))**2 for s in scale])
    propagated=unwhitening@unwhitening.T-np.diag(white)
    errors=[]
    for amount in ([.02,.01] if not profile and not height else [.02]):
        columns=[]
        for driver in range(54):
            plus=independently_perturbed_history(k,args,driver,amount)
            minus=independently_perturbed_history(k,args,driver,-amount)
            columns.append((((plus-minus)/(2*np.longdouble(amount)))*scale).astype(float).ravel())
        loading=np.column_stack(columns);expected=loading@loading.T
        norm=np.sqrt(np.diag(expected));normalized=(propagated-expected)/norm[:,None]/norm[None,:]
        error=float(np.max(abs(normalized)));errors.append(error)
        np.testing.assert_allclose(propagated/norm[:,None]/norm[None,:],expected/norm[:,None]/norm[None,:],
            rtol=3e-5,atol=3e-5)
    k['results'].append(dict(kind='nonlinear_driver_covariance',model=model,profile=profile,height=height,
        packets=4,queries=4,driver_directions=54,maximum_normalized_errors=errors))


@pytest.mark.parametrize('zero',[False,True])
def test_native_history_zero_and_singular_sensor_noise_remain_unrepaired(history_kernels,zero):
    import numpy as np
    from lll.ilvis0_noise_history import NativeNoiseHistory,PacketNoise
    from lll.state_space_covariance import LinearInnovations
    _,_,args=generated_history(2,False,False,4);values=settings(zero)
    if not zero:
        for key in ('gyro_white_psd','accel_white_psd','gyro_bias_covariance','accel_bias_covariance'):
            values[key]=np.diag([values[key][0,0],0.,0.])
    white=np.diag([1e-8,2e-8,.1]);k=history_kernels
    history=NativeNoiseHistory(kernel=k['kernel'],**args,noise=PacketNoise(**values),
        white_loadings=np.repeat(white[None],4,axis=0),reserve=k['reserve'])
    steps=list(history.steps())
    if zero:
        assert all(not np.any(step['process_loading']) and not np.any(step['observation_process_loading']) for step in steps)
    operator=LinearInnovations(steps,epoch_count=4,state_dimension=15,observation_dimension=3,
        initial_loading=history.noise.initial_loading(),maximum_bytes=100000,design_is_fixed=True,
        error_distribution='gaussian',observation_form='before_transition_shared_noise')
    cov=operator.unwhiten(np.eye(12));cov=cov@cov.T
    if zero:np.testing.assert_allclose(cov,np.kron(np.eye(4),white@white.T),rtol=1e-14,atol=0.)
    else:assert np.all(np.isfinite(cov))
