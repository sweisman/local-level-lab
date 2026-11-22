"""Fitted-point forecast tangents must replay sealed training evidence."""
import numpy as np
import pytest


def fixture():
    from lll.state_space_covariance import LinearInnovations
    steps=[dict(transition=np.eye(3)*.9,process_loading=np.eye(3)*.03,
        observation=np.eye(3),white_loading=np.eye(3)*.1) for _ in range(4)]
    operator=LinearInnovations(steps,epoch_count=4,state_dimension=3,
        observation_dimension=3,initial_loading=np.eye(3)*.1,
        maximum_bytes=100000,design_is_fixed=True,error_distribution='gaussian')
    coordinates=np.tile([.5,.2,100.],(4,1))
    jacobian=np.zeros((12,1));jacobian[2::3,0]=1.
    whitened=operator.prefix(2).whiten(jacobian[:6]).tolist()
    saved=dict(coordinates=coordinates.tolist(),active_parameters=['accel_bias_z'])
    generated=dict(coordinates=coordinates.copy(),jacobian=jacobian,
        active_parameters=['accel_bias_z'])
    fit=dict(active_parameters=['accel_bias_z'],
        local_linearization=dict(jacobian=whitened))
    return operator,saved,generated,fit


def test_fitted_tangent_replay_accepts_matching_positions_and_whitened_columns():
    from lll.esa_linear_uncertainty_v2_study import verify_fitted_tangent
    operator,saved,generated,fit=fixture()
    result=verify_fitted_tangent(operator,saved,generated,fit,training_epochs=2)
    assert result['training_columns']==1
    assert result['maximum_position_difference_m']==pytest.approx(0.)
    assert result['training_jacobian_replayed'] is True


def test_fitted_tangent_replay_rejects_a_changed_derivative_or_position():
    from lll.esa_linear_uncertainty_v2_study import verify_fitted_tangent
    operator,saved,generated,fit=fixture()
    generated['jacobian'][2,0]+=1.
    with pytest.raises(ValueError,match='training Jacobian'):
        verify_fitted_tangent(operator,saved,generated,fit,training_epochs=2)
    operator,saved,generated,fit=fixture()
    generated['coordinates'][2,2]+=.01
    with pytest.raises(ValueError,match='forecast positions'):
        verify_fitted_tangent(operator,saved,generated,fit,training_epochs=2)


def test_forecast_problem_uses_base_bounds_accepted_by_native_constructor():
    from lll.esa_linear_uncertainty_v2_study import make_forecast_problem
    from lll.ilvis0_estimator import Bounds
    operator,_,_,_=fixture()
    material=dict(prefix=dict(theta=np.zeros((3,3)),dv=np.zeros((3,3)),
        dt=np.ones(3)),gps_times=np.array([1.,2.]),
        gps=np.tile([.5,.2,100.],(2,1)),
        initial=dict(latitude_rad=.5,longitude_rad=.2,height_m=100.,
            velocity_ned_mps=np.zeros(3),attitude_body_to_ned=np.eye(3)),
        tangent_kernel=lambda *args:None,gravity=9.8)
    problem=make_forecast_problem(material,dict(limits=dict(gyro_bias_z=.01),
        maximum_interval_s=2.),operator.prefix(2))
    assert isinstance(problem.bounds.base,Bounds)
    assert problem.clock_hypothesis=='header_elapsed'
