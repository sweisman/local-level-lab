# SPDX-License-Identifier: AGPL-3.0-or-later
"""Short, prepaid native connection controls; no fitted or observed data."""
import pytest

from test_native_structured_training import training_kernels,native_training_case,allowances

DEFINITION=dict(additional_sources=['analysis/tests/test_native_bounded_controls.py',
    'analysis/lll/ilvis0_bounded_error_forecast.py','analysis/lll/bounded_state_prediction.py',
    'analysis/tests/test_native_bounded_forecast.py','docs/integrated-noise-covariance/NATIVE_BOUNDED_CONTROLS_PLAN.md'],
    allowances=allowances(),maximum_wall_s=180.)


@pytest.mark.parametrize('training_kernels',[DEFINITION],indirect=True)
@pytest.mark.parametrize('law',['increment','point'])
@pytest.mark.parametrize('model',[0,1,2])
@pytest.mark.parametrize('profile',[False,True])
@pytest.mark.parametrize('height',[False,True])
def test_bounded_native_connection_matches_dense_linear_envelope(native_training_case,law,model,profile,height):
    import numpy as np
    from types import SimpleNamespace
    from lll.ilvis0_exploratory import MODELS
    from lll.ilvis0_wide_tangent import load,evaluate
    from lll.ilvis0_error_model import Spec
    from lll.ilvis0_forecast import native_forecast
    from lll.ilvis0_native_error_training import ErrorTrainingFactory
    from lll.ilvis0_bounded_error_forecast import BoundedForecastErrorDiagnostic,diagnose_bounded_forecast
    from lll.ilvis0_bounded_prediction import Region,predict,known_scale
    from test_native_point_noise_adapter import generated_case,noise_for
    k=native_training_case;name=MODELS[model];n=160;cut=10;total=12
    base,truth,_=generated_case(model,profile,height,600)
    for attr in ('theta','dv','dt'):setattr(base,attr,getattr(base,attr)[:n].copy())
    ends=np.cumsum(base.dt);indices=np.linspace(10,140,total).astype(int)
    times=np.r_[0.,ends[:-1]][indices]+np.resize([.37,.61,.83],total)*base.dt[indices]
    base.gps_times=times;base.gps=np.zeros((total,3))
    limits={key:value for key,value in base.bounds.limits.items() if key!='earth_removal'}
    reference,_=load(k['directory'],expected_source_sha256=k['hashes']['analysis/lll/ilvis0_tangent.cpp'],
        gravity_anchor_height_m=2200. if height else None)
    k['reserve'](native_calls=1,packet_steps=n,packet_query_visits=n*total)
    target=evaluate(base,truth,name,kernel=reference)[0]
    count=int(np.searchsorted(ends,times[cut-1]+limits['time_offset']))+1
    anchor=float(target[0,2]) if height else None
    native,_=load(k['directory'],expected_source_sha256=k['hashes']['analysis/lll/ilvis0_tangent.cpp'],
        gravity_anchor_height_m=anchor)
    spec=Spec(white=np.eye(3)*.2,offset=np.eye(3)*.1,drift=np.eye(3)*.05,
        components=((.13,np.eye(3)*.3),(.7,np.eye(3)*.4)),drift_origin_s=0.,drift_span_s=1.)
    transforms=np.repeat(np.diag([1e-7,2e-7,.2])[None],total,axis=0)
    weight=SimpleNamespace(times=times[:cut],spec=spec,transforms=transforms[:cut],
        source_sha256='0'*64,descriptor={'generated':True},configuration='fixed-generated-policy')
    factory=ErrorTrainingFactory(noise=noise_for(law),noise_kernel=k['kernel'],gravity_anchor_height_m=anchor,
        maximum_packets=n,maximum_queries=total,maximum_bytes=1000000,anchor_policy='normalized-midpoint-v1')
    charge=lambda **work:k['reserve'](native_calls=work['native_calls'],packet_steps=work['packet_visits'])
    problem=factory(times[:cut],target[:cut],theta=base.theta[:count],dv=base.dv[:count],dt=base.dt[:count],
        model=name,limits=limits,profile=profile,clock='header_elapsed',maximum_interval_s=.007,
        kernel=None,tangent_kernel=native,training_weight=weight,time_origin_s=0.,reserve=charge)
    point=np.zeros(len(problem.bounds.active));point[list(problem.bounds.active).index('gyro_bias_z')]=1.
    def forecast_charge(**work):k['reserve'](native_calls=work['native_calls'],packet_steps=n,
        packet_query_visits=work['packet_visits'])
    forecast=native_forecast(problem,point,name,theta=base.theta,dv=base.dv,dt=base.dt,times=times,
        maximum_interval_s=.007,reserve=forecast_charge,retain_training_difference=True)
    # Capture the exact single operator extension without constructing it again.
    full=[];original=factory.extend
    def captured(*args,**kwargs):
        value=original(*args,**kwargs);full.append(value[0]);return value
    factory.extend=captured
    diagnostic=BoundedForecastErrorDiagnostic(factory,target='physical_position',
        receiver_transform_policy='last-training-transform-v1',bound_margin=1e-6,
        rank_rtol=1e-10,estimability_rtol=1e-8,estimability_atol=1e-10,
        scale_value=1.,scale_source_id='declared-linear-control',training_remainder_radius=0.,
        future_remainder_bounds=np.zeros(6),alpha_training=.01,alpha_prediction=.01)
    result=diagnostic(problem,point,forecast,theta=base.theta,dv=base.dv,dt=base.dt,times=times,reserve=charge)
    assert len(full)==1 and result['linear_calibration']['status']=='active_bounds_unsupported'
    bounded=result['bounded_calibration'];op=full[0];m=3*cut
    assert bounded['supported'] and bounded['parameter_count']==26+int(profile)
    factor=op.unwhiten(np.eye(3*total));covariance=factor@factor.T
    carry=np.linalg.solve(covariance[:m,:m],covariance[:m,m:]).T
    lower=np.linalg.cholesky(covariance[:m,:m]);jac=forecast['jacobian']
    earlier=-forecast['training_coordinate_difference'].ravel()
    region=Region(np.linalg.solve(lower,earlier),np.linalg.solve(lower,jac[:m]),
        np.column_stack((-1-point,1-point)),scale=known_scale(1.,source_id='declared-linear-control',covariance_id=op.configuration),
        covariance_id=op.configuration,remainder_radius=0.,alpha=.01,rank_tolerance=1e-10,design_is_fixed=False)
    expected=predict(region,forecast['coordinates'][cut:].ravel()+carry@earlier,jac[m:]-carry@jac[:m],
        conditional_variance=np.diag(covariance[m:,m:]-carry@covariance[:m,m:]),
        training_response_norm=np.linalg.norm(carry@lower,axis=1),future_remainder_bounds=np.zeros(6),
        alpha=.01,prediction_ids=bounded['prediction_ids'])
    assert expected['supported']
    for key in ('lower','upper'):
        np.testing.assert_allclose(bounded[key],expected[key],rtol=1e-8,atol=1e-8)
    missing=diagnose_bounded_forecast(problem,point,forecast,op,
        scale=known_scale(1.,source_id='declared-linear-control',covariance_id=op.configuration),
        training_remainder_radius=None,future_remainder_bounds=None,alpha_training=.01,alpha_prediction=.01,
        bound_margin=1e-6,parameter_scales=np.ones(len(point)),prediction_scales=np.ones(6),
        rank_rtol=1e-10,estimability_rtol=1e-8,estimability_atol=1e-10)
    assert missing['bounded_calibration']['supported'] is False and not result['confidence_calibrated']
    k['results'].append(dict(law=law,model=name,profile=profile,height=height,packets=n,
        training_epochs=cut,prediction_epochs=2,columns=len(point),bounded_supported=True,
        missing_remainder_supported=False,nonlinear_coverage_established=False,
        before_cast_difference_preserved=True,original_boundary_label_preserved=True,
        maximum_coordinate_width=float(np.max(bounded['upper']-bounded['lower']))))
