# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite native adapter algebra controls; no fitted or original observations."""
import pytest


def sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,[
        'analysis/lll/ilvis0_native_error_training.py','analysis/lll/airquantumgrav_prediction.py',
        'analysis/lll/ilvis0_forecast.py','analysis/lll/studies/qualification.py',
        'analysis/lll/studies/allowances.py','analysis/tests/run_numerical.py',
        'analysis/tests/test_native_structured_training.py','analysis/tests/test_structured_native_training.py',
        'analysis/tests/test_native_point_noise_adapter.py','analysis/tests/test_ilvis0_noise_history.py',
        'analysis/tests/test_ilvis0_noise_step.py','analysis/tests/test_linear_point_noise.py',
        'analysis/tests/test_state_space_covariance.py','docs/integrated-noise-covariance/TRAINING_PLAN.md'])


def allowances():
    result={'builds':dict(builds=2)}
    for law in ('increment','point'):
        for model in (0,1,2):
            for profile in (False,True):
                for height in (False,True):
                    result[f'{law}:{model}:{int(profile)}:{int(height)}']=dict(
                        native_calls=450,packet_steps=15000,packet_query_visits=300000)
    return result


@pytest.fixture(scope='session')
def training_kernels(tmp_path_factory,request):
    import gzip,json,os,time
    from pathlib import Path
    from lll.airquantumgrav_inventory import environment
    from lll.studies.artifacts import atomic,digest,encoded,safe_path
    from lll.studies.journal import Journal
    from lll.studies.allowances import PrepaidCase
    from lll.ilvis0_noise_step import load
    from lll.ilvis0_wide_tangent import load as wide_load
    root=Path.cwd();definition=getattr(request,'param',{})
    from lll.studies.dependencies import source_closure
    names=source_closure(root,sources(root)+list(definition.get('additional_sources',[])))
    hashes={n:digest(safe_path(root,n).read_bytes()) for n in names}
    frozen_request=os.environ.get('LLL_NATIVE_TRAINING_REQUEST')
    if frozen_request:
        frozen=json.loads(safe_path(root,frozen_request).read_bytes())
        if frozen['sources']!=hashes or frozen['environment']!=environment():
            raise ValueError('native training sources/environment changed before qualification')
    directory=tmp_path_factory.mktemp('native-structured-training')
    path=Path(os.environ.get('LLL_NATIVE_TRAINING_JOURNAL',str(directory/'charges.sqlite')))
    if path.exists():raise ValueError('fresh qualification journal required; no retry')
    limits=definition.get('allowances',allowances());freeze=digest(encoded(dict(sources=hashes,limits=limits)))
    journal=Journal(path,freeze=freeze,limits=limits);started=time.monotonic()
    with PrepaidCase(journal,'builds',require_exact=True) as budget:
        kernel,metadata=load(directory,expected_source_sha256=hashes['analysis/lll/ilvis0_tangent.cpp'],
            expected_bridge_sha256=hashes['analysis/lll/ilvis0_noise_bridge.cpp'],
            expected_wide_loader_sha256=hashes['analysis/lll/ilvis0_wide_tangent.py'],
            reserve_build=lambda:budget.reserve(builds=1))
        budget.reserve(builds=1);_,reference=wide_load(directory,
            expected_source_sha256=hashes['analysis/lll/ilvis0_tangent.cpp'])
    state=dict(kernel=kernel,directory=directory,hashes=hashes,started=started,
        journal=journal,path=path,results=[],outcomes=[budget.snapshot()],
        maximum_wall_s=definition.get('maximum_wall_s',300))
    yield state
    journal.verify()
    if frozen_request:
        artifacts={}
        for label,sn,bn,meta in (
            ('bridge',metadata['source_file'],metadata['binary_file'],metadata),
            ('reference','wide-tangent-'+reference['source_sha256']+'.cpp',
             'wide-tangent-'+reference['source_sha256']+'.so',reference)):
            for kind,name in (('source',sn),('binary',bn)):
                raw=(directory/name).read_bytes();assert digest(raw)==meta[kind+'_sha256']
                compressed=gzip.compress(raw,mtime=0);target=path.with_name(path.stem+'.'+label+'.'+kind+'.gz')
                atomic(target,compressed);artifacts[target.name]=dict(raw_sha256=digest(raw),gzip_sha256=digest(compressed))
        atomic(path.with_suffix('.compilation.json'),encoded(dict(bridge=metadata,reference=reference,
            journal_freeze=freeze,artifacts=artifacts,results=state['results'],outcomes=state['outcomes'],
            elapsed_s=time.monotonic()-started)))


@pytest.fixture
def native_training_case(request,training_kernels):
    import time
    from lll.studies.allowances import PrepaidCase
    from lll.studies.artifacts import atomic,encoded
    p=request.node.callspec.params;k=training_kernels
    identity=f"{p['law']}:{p['model']}:{int(p['profile'])}:{int(p['height'])}"
    budget=PrepaidCase(k['journal'],identity,require_exact=False)
    def reserve(**counts):
        if time.monotonic()-k['started']>k['maximum_wall_s']:raise ValueError('cooperative finite allowance exhausted')
        budget.reserve(**counts)
    try:
        with budget:yield dict(k,reserve=reserve)
    finally:
        k['outcomes'].append(budget.snapshot())
        atomic(k['path'].with_suffix('.outcomes.json'),encoded(k['outcomes']))


@pytest.mark.parametrize('law',['increment','point'])
@pytest.mark.parametrize('model',[0,1,2])
@pytest.mark.parametrize('profile',[False,True])
@pytest.mark.parametrize('height',[False,True])
def test_native_training_error_adapter(native_training_case,law,model,profile,height):
    import math
    import numpy as np
    from types import SimpleNamespace
    from scipy.linalg import solve_triangular
    from lll.ilvis0_exploratory import MODELS
    from lll.ilvis0_wide_tangent import load,evaluate
    from lll.ilvis0_error_model import Spec
    from lll.ilvis0_forecast import native_forecast
    from lll.ilvis0_native_error_training import ErrorTrainingFactory,build_training_operator,diagnose_forecast
    from test_native_point_noise_adapter import generated_case,noise_for
    k=native_training_case;name=MODELS[model];n=160;cut=10;total=12
    base,truth,_=generated_case(model,profile,height,600)
    for attr in ('theta','dv','dt'):setattr(base,attr,getattr(base,attr)[:n].copy())
    ends=np.cumsum(base.dt);indices=np.linspace(10,140,total).astype(int)
    base.gps_times=np.r_[0.,ends[:-1]][indices]+np.resize([.37,.61,.83],total)*base.dt[indices]
    base.gps=np.zeros((total,3))
    limits={key:value for key,value in base.bounds.limits.items() if key!='earth_removal'}
    reference,_=load(k['directory'],expected_source_sha256=k['hashes']['analysis/lll/ilvis0_tangent.cpp'],
        gravity_anchor_height_m=2200. if height else None)
    def call(problem,point,operation):
        k['reserve'](native_calls=1,packet_steps=len(problem.dt),
            packet_query_visits=len(problem.dt)*len(problem.gps_times))
        return operation()
    # Only this separate generator knows its original state and planted point.
    target=call(base,truth,lambda:evaluate(base,truth,name,kernel=reference))[0]
    times=base.gps_times;count=int(np.searchsorted(ends,times[cut-1]+limits['time_offset']))+1
    anchor=float(target[0,2]) if height else None
    native,_=load(k['directory'],expected_source_sha256=k['hashes']['analysis/lll/ilvis0_tangent.cpp'],
        gravity_anchor_height_m=anchor)
    spec=Spec(white=np.eye(3)*.2,offset=np.eye(3)*.1,drift=np.eye(3)*.05,
        components=((.13,np.eye(3)*.3),(.7,np.eye(3)*.4)),drift_origin_s=0.,drift_span_s=1.)
    transforms=np.repeat(np.diag([1e-7,2e-7,.2])[None],total,axis=0)
    weight=SimpleNamespace(times=times[:cut],spec=spec,transforms=transforms[:cut],
        source_sha256='0'*64,descriptor={'generated':True},configuration='fixed-generated-policy')
    noise=noise_for(law)
    factory=ErrorTrainingFactory(noise=noise,noise_kernel=k['kernel'],gravity_anchor_height_m=anchor,
        maximum_packets=n,maximum_queries=total,maximum_bytes=1000000,anchor_policy='normalized-midpoint-v1')
    def history_charge(**work):
        # The existing protocol calls one bridge step one packet visit.
        k['reserve'](native_calls=work['native_calls'],packet_steps=work['packet_visits'])
    problem=factory(times[:cut],target[:cut],theta=base.theta[:count],dv=base.dv[:count],dt=base.dt[:count],
        model=name,limits=limits,profile=profile,clock='header_elapsed',maximum_interval_s=.007,
        kernel=None,tangent_kernel=native,training_weight=weight,time_origin_s=0.,reserve=history_charge)
    assert problem.cholesky is None and len(problem.bounds.active)==26+int(profile)
    assert problem.error_descriptor['anchor_normalized_point']==[0.]*(26+int(profile))
    point=np.linspace(-.025,.025,len(problem.bounds.active))
    def build_charge(**work):k['reserve'](**work)
    full,descriptor=build_training_operator(theta=base.theta,dv=base.dv,dt=base.dt,times=times,
        initial=problem.initial,bounds=problem.bounds,model=name,gravity_mps2=problem.gravity,
        disc_radius_m=problem.radius,noise=noise,receiver_spec=spec,receiver_transforms=transforms,
        noise_kernel=k['kernel'],gravity_anchor_height_m=anchor,maximum_packets=n,maximum_queries=total,
        maximum_bytes=1000000,anchor_policy='normalized-midpoint-v1',reserve=build_charge)
    assert problem.observation_error.prefix(cut).configuration==full.prefix(cut).configuration
    u=full.unwhiten(np.eye(3*total));covariance=u@u.T
    lower=np.linalg.cholesky(covariance[:3*cut,:3*cut])
    residual,jac,_=call(problem,point,lambda:problem.residual_tangent(point,name))
    _,delta,rawjac,_=call(problem,point,lambda:evaluate(problem,point,name,kernel=native))
    dense_residual=solve_triangular(lower,delta.ravel(),lower=True)
    dense_jac=solve_triangular(lower,rawjac,lower=True)
    np.testing.assert_allclose(residual,dense_residual,rtol=1e-9,atol=1e-8)
    np.testing.assert_allclose(jac,dense_jac,rtol=1e-9,atol=1e-8)
    np.testing.assert_allclose(problem.unwhiten_stacked(residual),delta.ravel(),rtol=1e-9,atol=1e-8)
    np.testing.assert_allclose(problem.error_log_determinant,2*np.log(np.diag(lower)).sum(),rtol=1e-12,atol=1e-10)
    discrepancies=[]
    for column,parameter in enumerate(problem.bounds.active):
        step=.01 if parameter.startswith('gyro_bias') else (.001 if parameter=='earth_removal' else .0001)
        plus=point.copy();minus=point.copy();plus[column]+=step;minus[column]-=step
        a=call(problem,plus,lambda:evaluate(problem,plus,name,kernel=native))[1]
        b=call(problem,minus,lambda:evaluate(problem,minus,name,kernel=native))[1]
        numerical=solve_triangular(lower,((a-b)/(2*step)).ravel(),lower=True)
        error=np.linalg.norm(numerical-jac[:,column]);scale=np.linalg.norm(jac[:,column])
        assert error<=2e-4*scale+1e-7,(parameter,error,scale)
        discrepancies.append(float(error/max(scale,1e-3)))
    def forecast_charge(**work):k['reserve'](native_calls=work['native_calls'],packet_steps=n,
        packet_query_visits=work['packet_visits'])
    forecast=native_forecast(problem,point,name,theta=base.theta,dv=base.dv,dt=base.dt,times=times,
        maximum_interval_s=.007,reserve=forecast_charge,retain_training_difference=True)
    np.testing.assert_array_equal(forecast['training_coordinate_difference'],delta)
    diagnostic=diagnose_forecast(problem,point,forecast,full,bound_margin=1e-6,
        parameter_scales=np.ones(len(point)),prediction_scales=np.ones(6),
        rank_rtol=1e-10,estimability_rtol=1e-8,estimability_atol=1e-10)
    cross=covariance[3*cut:,:3*cut];earlier=-delta.ravel()
    conditional=cross@np.linalg.solve(covariance[:3*cut,:3*cut],earlier)
    np.testing.assert_allclose(diagnostic['fixed_parameters']['mean_adjustment'].ravel(),conditional,
        rtol=1e-9,atol=1e-8)
    assert diagnostic['later_observations_used'] is False and diagnostic['confidence_calibrated'] is False
    assert diagnostic['linear_calibration']['status'] in ('estimable','unidentifiable','linear_step_outside_bounds')
    k['results'].append(dict(law=law,model=name,profile=profile,height=height,packets=n,
        training_epochs=cut,prediction_epochs=2,columns=len(point),maximum_derivative_discrepancy=max(discrepancies),
        covariance_state_dimension=full.state_dimension,operator_bytes=full.storage_bytes,
        linear_status=diagnostic['linear_calibration']['status'],before_cast_difference_preserved=True))
