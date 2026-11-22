"""Earlier-only local calibration uncertainty for the ESA development fit."""
import numpy as np
import pytest


def example():
    from lll.state_space_covariance import LinearInnovations
    steps=[dict(transition=np.eye(3)*.9,process_loading=np.eye(3)*.03,
        observation=np.eye(3),white_loading=np.eye(3)*.1) for _ in range(4)]
    operator=LinearInnovations(steps,epoch_count=4,state_dimension=3,
        observation_dimension=3,initial_loading=np.eye(3)*.1,
        maximum_bytes=100000,design_is_fixed=True,error_distribution='gaussian')
    coordinates=np.tile([.5,.2,100.],(4,1))
    design=np.zeros((12,1));design[2::3,0]=1.
    saved=dict(coordinates=coordinates.tolist(),jacobian=design.tolist(),
        training_epochs=2,prediction_epochs=2,
        training_coordinate_difference=np.array([[0.,0.,-.05],[0.,0.,-.05]]).tolist(),
        active_parameters=['accel_bias_z'])
    fit=dict(active_parameters=['accel_bias_z'],normalized_parameters=[0.])
    earlier=dict(coordinates=coordinates[:2].tolist())
    recipe=dict(rank_rtol=1e-12,estimability_rtol=1e-10,estimability_atol=1e-12)
    return operator,saved,fit,recipe,earlier


def test_local_uncertainty_keeps_training_only_and_adds_parameter_variance():
    from lll.esa_linear_uncertainty_study import linear_diagnostic
    operator,saved,fit,recipe,earlier=example()
    result=linear_diagnostic(operator,saved,fit,recipe,earlier,training_epochs=2)
    assert result['status']=='estimable'
    assert result['training_rank']==1
    assert result['parameter_count']==1
    assert result['later_observations_used'] is False
    assert result['parameter_step_inside_bounds'] is True
    assert np.asarray(result['receiver_mean']).shape==(2,3)
    assert np.asarray(result['receiver_covariance']).shape==(2,3,3)
    fixed=operator.conditional_marginals(state=operator.apply_block(
        np.array([0.,0.,.05,0.,0.,.05]),first_epoch=0)[1])
    assert result['receiver_covariance'][0][2][2]>fixed['covariance'][0,2,2]


def test_local_uncertainty_rejects_changed_earlier_support():
    from lll.esa_linear_uncertainty_study import linear_diagnostic
    operator,saved,fit,recipe,earlier=example()
    saved['training_coordinate_difference']=saved['training_coordinate_difference'][:1]
    with pytest.raises(ValueError,match='earlier'):
        linear_diagnostic(operator,saved,fit,recipe,earlier,training_epochs=2)
