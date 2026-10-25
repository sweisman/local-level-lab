# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def error_fixture():
    import numpy as np
    from test_state_space_covariance import fixture,dense_reference,operator
    initial,steps=fixture()
    return operator(initial,steps),dense_reference(initial,steps),initial,steps


def make_problem(covariance,*,observation_error=None,profile=False):
    import numpy as np
    from lll.ilvis0_estimator import Bounds,PARAMETERS
    from lll.ilvis0_shape import TangentProblem
    dt=np.full(10,.005);theta=np.zeros((10,3));dv=np.zeros((10,3));dv[:,2]=-9.8*dt
    initial=dict(latitude_rad=.5,longitude_rad=-.3,height_m=1000.,
        velocity_ned_mps=np.array([100.,0.,0.]),attitude_body_to_ned=np.eye(3))
    limits=dict.fromkeys(PARAMETERS,.01);limits['time_offset']=.0001
    kwargs={} if observation_error is None else dict(observation_error=observation_error)
    return TangentProblem(theta,dv,dt,np.array([.01,.025,.04]),np.tile([.5,-.3,1000.],(3,1)),
        covariance,initial,Bounds(limits),tangent_kernel=lambda *args:0,
        fit_earth_removal=profile,clock_hypothesis='header_elapsed',
        processing_hypothesis='unsubtracted_increment_hypothesis',maximum_interval_s=.005,
        gravity_mps2=9.8,disc_radius_m=6371000.,**kwargs)


def test_training_prefix_whitening_inverse_and_logdet_match_dense_reference():
    import numpy as np
    op,cov,_,_=error_fixture();prefix=op.prefix(3);values=np.sin(np.arange(9*27).reshape(9,27)/13)
    lower=np.linalg.cholesky(cov[:9,:9])
    np.testing.assert_allclose(prefix.whiten(values),np.linalg.solve(lower,values),rtol=2e-12,atol=2e-12)
    np.testing.assert_allclose(prefix.unwhiten(prefix.whiten(values)),values,rtol=2e-12,atol=2e-12)
    assert prefix.log_determinant==pytest.approx(2*np.log(np.diag(lower)).sum(),rel=2e-12)
    assert prefix.epoch_count==3 and prefix.observation_dimension==3 and prefix.shares_parent_storage is True


def test_training_prefix_identity_and_values_ignore_later_error_design():
    import numpy as np
    from test_state_space_covariance import operator
    op,_,initial,steps=error_fixture();steps[-1]['white_loading']*=3
    changed=operator(initial,steps)
    assert op.configuration!=changed.configuration
    assert op.prefix(3).configuration==changed.prefix(3).configuration
    values=np.arange(9.)
    np.testing.assert_array_equal(op.prefix(3).whiten(values),changed.prefix(3).whiten(values))


@pytest.mark.parametrize('cutoff',[0,6])
def test_training_prefix_rejects_unsupported_cutoff(cutoff):
    op,_,_,_=error_fixture()
    with pytest.raises(ValueError):op.prefix(cutoff)


@pytest.mark.parametrize('profile',[False,True])
def test_structured_problem_constructs_without_dense_factor_and_keeps_all_columns(monkeypatch,profile):
    import numpy as np
    from scipy.linalg import solve_triangular
    op,cov,_,_=error_fixture();prefix=op.prefix(3);lower=np.linalg.cholesky(cov[:9,:9])
    def forbidden(*args,**kwargs):raise AssertionError('structured problem allocated a dense factor')
    monkeypatch.setattr(np.linalg,'cholesky',forbidden)
    problem=make_problem(None,observation_error=prefix,profile=profile)
    assert problem.cholesky is None and len(problem.bounds.active)==26+int(profile)
    difference=np.arange(9,dtype=float).reshape(3,3)/100;wrapped=difference.copy()
    wrapped[:,1]=(wrapped[:,1]+np.pi)%(2*np.pi)-np.pi
    np.testing.assert_allclose(problem.whiten(difference),solve_triangular(lower,wrapped.ravel(),lower=True),rtol=2e-12,atol=2e-12)
    matrix=np.sin(np.arange(9*len(problem.bounds.active)).reshape(9,-1)/11)
    np.testing.assert_allclose(problem.whiten_columns(matrix),solve_triangular(lower,matrix,lower=True),rtol=2e-12,atol=2e-12)
    np.testing.assert_allclose(problem.unwhiten_stacked(problem.whiten_stacked(matrix[:,0])),matrix[:,0],rtol=2e-12,atol=2e-12)
    assert problem.error_log_determinant==prefix.log_determinant


def test_dense_problem_retains_existing_values_and_reports_normalization():
    import numpy as np
    from scipy.linalg import solve_triangular
    _,cov,_,_=error_fixture();problem=make_problem(cov[:9,:9])
    assert problem.observation_error is None
    matrix=np.sin(np.arange(9*26).reshape(9,26)/13)
    np.testing.assert_array_equal(problem.whiten_columns(matrix),solve_triangular(problem.cholesky,matrix,lower=True))
    assert problem.error_log_determinant==pytest.approx(np.linalg.slogdet(cov[:9,:9])[1],rel=2e-12)


@pytest.mark.parametrize('bad',['both','epochs','type'])
def test_structured_problem_rejects_ambiguous_or_misaligned_weights(bad):
    import numpy as np
    op,_,_,_=error_fixture()
    with pytest.raises(ValueError):make_problem(np.eye(9) if bad=='both' else None,
        observation_error=object() if bad=='type' else op if bad=='epochs' else op.prefix(3))


def test_physical_stopping_step_uses_matching_structured_inverse():
    import numpy as np
    from lll.ilvis0_solver_position import physical_residual_step,physical_metric
    op,_,_,_=error_fixture();problem=make_problem(None,observation_error=op.prefix(3))
    coordinates=np.array([[1e-9,2e-9,.001],[-2e-9,1e-9,-.002],[3e-9,-1e-9,.003]])
    whitened=problem.whiten_stacked(coordinates.ravel())
    expected=coordinates.copy();expected[:,1]=(expected[:,1]+np.pi)%(2*np.pi)-np.pi
    np.testing.assert_allclose(physical_residual_step(problem,whitened),expected*physical_metric(problem.gps),rtol=2e-7,atol=1e-10)


def test_training_score_retains_candidate_covariance_normalization():
    import numpy as np
    from lll.ilvis0_native_error_training import gaussian_training_score
    _,cov,_,_=error_fixture();a=make_problem(cov[:9,:9]);b=make_problem(cov[:9,:9]*4)
    sa=gaussian_training_score(a,residual_sum_squares=2.)
    sb=gaussian_training_score(b,residual_sum_squares=2.)
    expected=.5*(2.+np.linalg.slogdet(cov[:9,:9])[1]+9*np.log(2*np.pi))
    assert sa['negative_log_likelihood']==pytest.approx(expected,rel=2e-12)
    assert sb['negative_log_likelihood']-sa['negative_log_likelihood']==pytest.approx(9*np.log(2),rel=2e-12)
    assert sa['row_count']==9 and sa['model_comparison_calibrated'] is False


def forecast_fixture(problem):
    import numpy as np
    coordinates=np.tile([.5,-.3,1000.],(5,1));coordinates[:3]-=.001
    return dict(coordinates=coordinates,jacobian=np.zeros((15,len(problem.bounds.active))),
        active_parameters=list(problem.bounds.active),training_epochs=3,prediction_epochs=2,
        continuous_propagation_without_gps_reset=True,prediction_receiver_positions_used=False)


def diagnose(problem,point,forecast,op):
    import numpy as np
    from lll.ilvis0_native_error_training import diagnose_forecast
    return diagnose_forecast(problem,point,forecast,op,bound_margin=1e-6,
        parameter_scales=np.ones(len(problem.bounds.active)),prediction_scales=np.ones(6),
        rank_rtol=1e-12,estimability_rtol=1e-10,estimability_atol=1e-12)


@pytest.mark.parametrize('at_bound',[False,True])
def test_calibration_diagnostic_withholds_unrestricted_covariance_at_bounds(at_bound):
    import numpy as np
    op,_,_,_=error_fixture();problem=make_problem(None,observation_error=op.prefix(3))
    point=np.zeros(len(problem.bounds.active));point[0]=1. if at_bound else 0.
    result=diagnose(problem,point,forecast_fixture(problem),op)
    assert result['confidence_calibrated'] is False
    assert result['fixed_parameters']['parameter_uncertainty_included'] is False
    if at_bound:
        assert result['linear_calibration']['status']=='active_bounds_unsupported'
        assert 'covariance' not in result['linear_calibration']
    else:
        assert result['linear_calibration']['status']=='estimable'
        assert result['linear_calibration']['nonlinear_coverage_established'] is False


def test_conditioned_forecast_uses_receiver_minus_model_with_the_correct_sign():
    import numpy as np
    op,cov,_,_=error_fixture();problem=make_problem(None,observation_error=op.prefix(3))
    forecast=forecast_fixture(problem);saved=forecast['coordinates'].copy()
    result=diagnose(problem,np.zeros(len(problem.bounds.active)),forecast,op)
    earlier=(problem.gps-forecast['coordinates'][:3]).ravel()
    expected=cov[9:,:9]@np.linalg.solve(cov[:9,:9],earlier)
    np.testing.assert_allclose(result['fixed_parameters']['mean']-saved[3:],expected.reshape(2,3),rtol=1e-9,atol=1e-12)
    np.testing.assert_array_equal(forecast['coordinates'],saved)
    assert result['later_observations_used'] is False


def test_forecast_diagnostic_rejects_a_different_training_split():
    import numpy as np
    op,_,_,_=error_fixture();problem=make_problem(None,observation_error=op.prefix(3))
    forecast=forecast_fixture(problem);forecast['training_epochs']=4
    with pytest.raises(ValueError):diagnose(problem,np.zeros(len(problem.bounds.active)),forecast,op)


@pytest.mark.parametrize('profile',[False,True])
def test_midpoint_error_builder_uses_declared_source_law_and_preserves_inputs(monkeypatch,profile):
    import numpy as np
    from lll import ilvis0_noise_step
    from lll.ilvis0_native_error_training import build_training_operator
    from lll.linear_point_noise import LinearPointNoise
    from lll.ilvis0_error_model import Spec
    from test_linear_point_noise import settings
    from test_native_point_noise_adapter import fake_native
    calls=[]
    def native(kernel,**kwargs):
        calls.append(kwargs['removal']);return fake_native(kernel,**kwargs)
    monkeypatch.setattr(ilvis0_noise_step,'evaluate',native)
    problem=make_problem(np.eye(9),profile=profile);saved=problem.theta.copy()
    spec=Spec(white=np.eye(3),components=((1.,np.eye(3)*.2),))
    op,descriptor=build_training_operator(theta=problem.theta,dv=problem.dv,dt=problem.dt,
        times=problem.gps_times,initial=problem.initial,bounds=problem.bounds,model='sphere_rotating',
        gravity_mps2=problem.gravity,disc_radius_m=problem.radius,noise=LinearPointNoise(**settings()),
        receiver_spec=spec,receiver_transforms=np.repeat(np.diag([1e-7,2e-7,.2])[None],3,axis=0),
        noise_kernel=None,gravity_anchor_height_m=None,maximum_packets=10,maximum_queries=3,
        maximum_bytes=100000,anchor_policy='normalized-midpoint-v1',reserve=lambda **counts:None)
    assert op.epoch_count==3 and op.state_dimension==30
    assert descriptor['anchor_normalized_point']==[0.]*(26+int(profile))
    assert descriptor['source_law']=='linear_rate_points' and descriptor['model']=='sphere_rotating'
    assert descriptor['weights_depend_on_fitted_residuals'] is False
    assert calls and all(x==(.5 if profile else 0.) for x in calls)
    np.testing.assert_array_equal(problem.theta,saved)


def test_midpoint_builder_rejects_undeclared_anchor_before_native_work():
    import numpy as np
    from lll.ilvis0_native_error_training import build_training_operator
    from lll.ilvis0_noise_history import PacketNoise
    from lll.ilvis0_error_model import Spec
    from test_ilvis0_noise_history import settings
    problem=make_problem(np.eye(9))
    def forbidden(**kwargs):raise AssertionError('invalid anchor reached native work')
    with pytest.raises(ValueError,match='anchor'):build_training_operator(
        theta=problem.theta,dv=problem.dv,dt=problem.dt,times=problem.gps_times,initial=problem.initial,
        bounds=problem.bounds,model='sphere_rotating',gravity_mps2=problem.gravity,disc_radius_m=problem.radius,
        noise=PacketNoise(**settings()),receiver_spec=Spec(white=np.eye(3)),
        receiver_transforms=np.repeat(np.eye(3)[None],3,axis=0),noise_kernel=None,
        gravity_anchor_height_m=None,maximum_packets=10,maximum_queries=3,maximum_bytes=100000,
        anchor_policy='choose-after-the-fit',reserve=forbidden)


@pytest.mark.parametrize('profile',[False,True])
@pytest.mark.parametrize('with_diagnostic',[False,True])
def test_prediction_protocol_passes_only_earlier_material_to_structured_factory(monkeypatch,profile,with_diagnostic):
    import math
    import numpy as np
    from types import SimpleNamespace
    from lll import airquantumgrav_error_policy,ilvis0_training_forecast,ilvis0_forecast
    from lll.airquantumgrav_prediction import train_and_forecast
    from lll.ilvis0_shape import TangentProblem
    template=make_problem(np.eye(9),profile=profile);op,_,_,_=error_fixture();calls=[];saved={}
    times=np.array([.01,.025,.04,.06,.08]);dt=np.full(20,.005);theta=np.zeros((20,3))
    dv=np.zeros((20,3));dv[:,2]=-9.8*dt
    rows=[dict(latitude_deg=math.degrees(.5),longitude_deg=math.degrees(-.3),height_m=1000.) for _ in range(3)]
    def forbidden(*args,**kwargs):raise AssertionError('dense construction reached the structured path')
    weight=SimpleNamespace(times=times[:3],configuration='generated-weight',descriptor={'test':True},
        source_sha256='0'*64,dense=forbidden)
    monkeypatch.setattr(airquantumgrav_error_policy,'build',lambda *args,**kwargs:weight)
    monkeypatch.setattr(ilvis0_training_forecast,'training_problem',forbidden)
    def factory(earlier_times,gps,**kwargs):
        calls.append((earlier_times.copy(),gps.copy(),kwargs['theta'].copy()))
        assert kwargs['training_weight'] is weight and len(kwargs['dt'])==9
        problem=TangentProblem(kwargs['theta'],kwargs['dv'],kwargs['dt'],earlier_times,gps,None,
            template.initial,template.bounds.base,tangent_kernel=kwargs['tangent_kernel'],
            fit_earth_removal=profile,clock_hypothesis='header_elapsed',
            processing_hypothesis='unsubtracted_increment_hypothesis',maximum_interval_s=.005,
            gravity_mps2=9.8,disc_radius_m=6371000.,observation_error=op.prefix(3))
        problem.frozen_error_model='sphere_rotating'
        problem.error_descriptor=dict(operator_configuration=problem.observation_error.configuration)
        return problem
    def fit(problem,model,**kwargs):
        assert problem.observation_error is not None
        return dict(active_parameters=list(problem.bounds.active),normalized_parameters=np.zeros(len(problem.bounds.active)),
            residual_sum_squares=0.,converged=True)
    monkeypatch.setattr(ilvis0_training_forecast,'fit_training',fit)
    def forecast(problem,point,model,**kwargs):
        return dict(coordinates=np.tile([.5,-.3,1000.],(5,1)),active_parameters=list(problem.bounds.active),
            training_coordinate_difference=np.zeros((3,3)),training_residual_subtraction='native-before-binary64-cast',
            normalized_parameters=np.asarray(point).tolist(),frozen_error_model=model,
            error_training_configuration=problem.observation_error.configuration)
    monkeypatch.setattr(ilvis0_forecast,'native_forecast',forecast)
    def diagnostic(problem,point,forecast,**kwargs):
        assert 'forecast.json' in saved
        assert set(kwargs)=={'theta','dv','dt','times','reserve'}
        return dict(raw_coordinates=forecast['coordinates'],fixed_parameters=dict(mean=np.tile([.5,-.3,1000.],(2,1))),
            training_epochs=3,prediction_epochs=2,later_observations_used=False,
            confidence_calibrated=False,prediction_target='physical_position',
            linear_calibration=dict(status='active_bounds_unsupported'))
    result=train_and_forecast(theta=theta,dv=dv,dt=dt,times=times,training_rows=rows,time_origin_s=0.,
        model='sphere_rotating',profile=profile,policy_id='generated-policy',start=0,
        limits=template.bounds.base.limits,maximum_evaluations=8,maximum_interval_s=.005,
        kernel=None,tangent_kernel=lambda *args:0,reserve=lambda **counts:None,
        save=lambda name,value:saved.update({name:value}),check_continue=lambda:None,
        training_error_factory=factory,
        **(dict(forecast_error_diagnostic=diagnostic) if with_diagnostic else {}))
    assert len(calls)==1 and len(calls[0][0])==len(calls[0][1])==3
    assert len(calls[0][2])==9 and result['training_epochs']==3
    assert 'training-error-operator.json' in saved and len(saved['fit.json']['active_parameters'])==26+int(profile)
    if with_diagnostic:
        assert isinstance(saved['forecast-error-diagnostic.json']['fixed_parameters']['mean'],list)
        assert result['forecast_error_diagnostic']['prediction_target']=='physical_position'


def test_native_forecast_rejects_a_different_frozen_error_model_before_charging():
    import numpy as np
    from lll.ilvis0_forecast import native_forecast
    op,_,_,_=error_fixture();problem=make_problem(None,observation_error=op.prefix(3))
    problem.frozen_error_model='sphere_rotating'
    def forbidden(**counts):raise AssertionError('mismatched model reached native work')
    dt=np.full(20,.005);theta=np.zeros((20,3));dv=np.zeros((20,3));dv[:,2]=-9.8*dt
    with pytest.raises(ValueError,match='model'):native_forecast(problem,np.zeros(len(problem.bounds.active)),
        'flat_still',theta=theta,dv=dv,dt=dt,times=np.array([.01,.025,.04,.06,.08]),
        maximum_interval_s=.005,reserve=forbidden)


@pytest.mark.parametrize('profile',[False,True])
def test_error_factory_initializes_from_earlier_inputs_and_binds_candidate(monkeypatch,profile):
    import numpy as np
    from types import SimpleNamespace
    from lll import ilvis0_noise_step,ilvis0_training_forecast
    from lll.ilvis0_error_model import Spec
    from lll.ilvis0_native_error_training import ErrorTrainingFactory
    from lll.linear_point_noise import LinearPointNoise
    from test_linear_point_noise import settings
    from test_native_point_noise_adapter import fake_native
    template=make_problem(np.eye(9),profile=profile);calls=[];charges=[]
    monkeypatch.setattr(ilvis0_noise_step,'evaluate',fake_native)
    def initialize(times,gps,**kwargs):
        calls.append((times.copy(),gps.copy(),kwargs['theta'].copy()))
        return template.initial,template.gravity
    monkeypatch.setattr(ilvis0_training_forecast,'initialize_training',initialize)
    weight=SimpleNamespace(times=template.gps_times+4000.,spec=Spec(white=np.eye(3),components=((1.,np.eye(3)*.2),)),
        transforms=np.repeat(np.diag([1e-7,2e-7,.2])[None],3,axis=0),source_sha256='0'*64,
        descriptor={'test':True},configuration='generated-receiver-policy')
    factory=ErrorTrainingFactory(noise=LinearPointNoise(**settings()),noise_kernel=lambda *args:0,
        gravity_anchor_height_m=None,maximum_packets=10,maximum_queries=3,maximum_bytes=100000,
        anchor_policy='normalized-midpoint-v1')
    # Build from the exact epoch subtraction used by the protocol.
    times=weight.times-4000.
    problem=factory(times,template.gps,theta=template.theta,dv=template.dv,dt=template.dt,
        model='sphere_rotating',limits=template.bounds.base.limits,profile=profile,clock='header_elapsed',
        maximum_interval_s=.005,kernel=None,tangent_kernel=lambda *args,**kwargs:0,
        training_weight=weight,time_origin_s=4000.,reserve=lambda **work:charges.append(work))
    assert len(calls)==1 and len(calls[0][0])==len(calls[0][1])==3
    assert problem.cholesky is None and len(problem.bounds.active)==26+int(profile)
    assert problem.frozen_error_model=='sphere_rotating' and problem.requires_extended_training_difference is True
    assert problem.error_descriptor['receiver_time_origin_s']==4000.
    assert problem.error_descriptor['initial_state_source']=='training-only-receiver-and-increments'
    assert charges and all(set(c)=={'native_calls','packet_visits'} for c in charges)
    with pytest.raises(ValueError,match='model'):problem.residual_tangent(np.zeros(len(problem.bounds.active)),'flat_still')


def test_native_forecast_retains_before_cast_training_errors_without_later_positions():
    import ctypes
    import numpy as np
    from lll.ilvis0_forecast import native_forecast
    op,_,_,_=error_fixture();problem=make_problem(None,observation_error=op.prefix(3))
    problem.native_residual_difference_supported=True;calls=[]
    tiny=np.tile([1e-20,-2e-20,3e-16],(3,1))
    def native(*args,observations,difference):
        np.testing.assert_array_equal(observations[:3],problem.gps)
        np.testing.assert_array_equal(observations[3:],np.zeros((2,3)))
        args[15][:]=np.tile(problem.gps[0],(5,1));args[16][:]=0.
        difference[:3]=tiny;difference[3:]=args[15][3:]
        ctypes.cast(args[17],ctypes.POINTER(ctypes.c_int)).contents.value=5
        return 0
    problem.tangent_kernel=native
    dt=np.full(20,.005);theta=np.zeros((20,3));dv=np.zeros((20,3));dv[:,2]=-9.8*dt
    result=native_forecast(problem,np.zeros(len(problem.bounds.active)),'sphere_rotating',
        theta=theta,dv=dv,dt=dt,times=np.array([.01,.025,.04,.06,.08]),maximum_interval_s=.005,
        reserve=lambda **work:calls.append(work),retain_training_difference=True)
    np.testing.assert_array_equal(result['coordinates'][:3],problem.gps)
    np.testing.assert_array_equal(result['training_coordinate_difference'],tiny)
    assert len(calls)==1 and result['prediction_receiver_positions_used'] is False


def test_structured_diagnostic_requires_retained_before_cast_residuals():
    import numpy as np
    op,_,_,_=error_fixture();problem=make_problem(None,observation_error=op.prefix(3))
    problem.requires_extended_training_difference=True
    with pytest.raises(ValueError,match='before-cast'):diagnose(problem,
        np.zeros(len(problem.bounds.active)),forecast_fixture(problem),op)


def test_structured_diagnostic_rejects_mixed_fitted_point_artifacts():
    import numpy as np
    op,_,_,_=error_fixture();problem=make_problem(None,observation_error=op.prefix(3))
    problem.requires_extended_training_difference=True;problem.frozen_error_model='sphere_rotating'
    forecast=forecast_fixture(problem)
    forecast.update(training_coordinate_difference=np.zeros((3,3)),
        normalized_parameters=[0.]*len(problem.bounds.active),frozen_error_model='sphere_rotating',
        error_training_configuration=problem.observation_error.configuration)
    with pytest.raises(ValueError,match='point'):diagnose(problem,
        np.full(len(problem.bounds.active),.1),forecast,op)


@pytest.mark.parametrize('field,value',[
    ('frozen_error_model','flat_still'),('error_training_configuration','other-error-law'),
    ('training_residual_subtraction','rounded-coordinates'),('normalized_parameters',[0.])])
def test_structured_diagnostic_checks_artifact_binding(field,value):
    import numpy as np
    op,_,_,_=error_fixture();problem=make_problem(None,observation_error=op.prefix(3))
    problem.requires_extended_training_difference=True;problem.frozen_error_model='sphere_rotating'
    forecast=forecast_fixture(problem)
    forecast.update(training_coordinate_difference=np.zeros((3,3)),
        normalized_parameters=[0.]*len(problem.bounds.active),frozen_error_model='sphere_rotating',
        error_training_configuration=problem.observation_error.configuration,
        training_residual_subtraction='native-before-binary64-cast')
    forecast[field]=value
    with pytest.raises(ValueError):diagnose(problem,np.zeros(len(problem.bounds.active)),forecast,op)


def test_structured_diagnostic_accepts_bound_before_cast_training_artifact():
    import numpy as np
    op,_,_,_=error_fixture();problem=make_problem(None,observation_error=op.prefix(3))
    problem.requires_extended_training_difference=True;problem.frozen_error_model='sphere_rotating'
    forecast=forecast_fixture(problem)
    forecast.update(training_coordinate_difference=np.full((3,3),1e-20),
        normalized_parameters=[0.]*len(problem.bounds.active),frozen_error_model='sphere_rotating',
        error_training_configuration=problem.observation_error.configuration,
        training_residual_subtraction='native-before-binary64-cast')
    result=diagnose(problem,np.zeros(len(problem.bounds.active)),forecast,op)
    assert result['training_residual_precision']=='native-subtraction-before-binary64-cast'
    assert result['later_observations_used'] is False and result['confidence_calibrated'] is False
