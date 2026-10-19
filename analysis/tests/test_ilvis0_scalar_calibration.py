# SPDX-License-Identifier: AGPL-3.0-or-later
"""Local algebra controls, not calibrated observation-model tests."""
import numpy as np
import pytest

from lll import ilvis0_scalar_calibration as calibration


LIMITS=np.array([.15,.15,.15,.25,.25,.25,.05])


def example():
    rng=np.random.default_rng(912)
    body=rng.normal(size=(20,3))+[0.,0.,-9.81]
    force=rng.normal(size=(20,3))+[0.,0.,-9.81]
    return body,force


def test_all_seven_local_columns_match_independent_differences():
    body,force=example()
    result=calibration.analyze(body,force,LIMITS)
    def independent(point):
        measured=(body-point[3:6])/(1.+point[:3])
        target=force-np.array([0.,0.,point[6]])
        return np.sqrt(np.sum(measured**2,axis=1))-np.sqrt(np.sum(target**2,axis=1))
    for column in range(7):
        step=np.zeros(7);step[column]=1e-5*LIMITS[column]
        difference=(independent(step)-independent(-step))/(2e-5)
        np.testing.assert_allclose(result['scaled_jacobian'][:,column],difference,atol=3e-10,rtol=3e-8)


def test_exact_projection_removes_only_calibration_tangent():
    body,force=example()
    result=calibration.analyze(body,force,LIMITS)
    jacobian=result['scaled_jacobian']
    assert jacobian.shape==(20,7) and result['rank']==7
    residual=np.linalg.norm(body,axis=1)-np.linalg.norm(force,axis=1)
    projected=result['projected_residual']
    np.testing.assert_allclose(jacobian.T@projected,0.,atol=1e-12)
    np.testing.assert_allclose(projected,residual+jacobian@result['linear_step_scaled'],atol=1e-12)
    assert result['projected_rms_mps2']<=result['uncorrected_rms_mps2']
    assert result['scientific_decision']=='abstain'
    assert not result['nonlinear_identifiability_established']


def test_constant_vertical_force_keeps_dependent_columns_and_allows_no_local_distinction():
    body=np.tile([0.,0.,-9.8],(12,1));force=np.tile([0.,0.,-9.81],(12,1))
    result=calibration.analyze(body,force,LIMITS)
    assert result['rank']==1 and result['scaled_jacobian'].shape==(12,7)
    assert len(result['singular_values'])==7
    assert result['projected_rms_mps2']<1e-12
    assert result['linear_step_within_bounds']
    assert result['nonlinear_rms_at_linear_step_mps2'] is not None


def test_large_linear_correction_is_not_reported_as_feasible_calibration():
    body=np.tile([0.,0.,-1.],(12,1));force=np.tile([0.,0.,-100.],(12,1))
    result=calibration.analyze(body,force,LIMITS)
    assert result['projected_rms_mps2']<1e-10
    assert not result['linear_step_within_bounds']
    assert result['nonlinear_rms_at_linear_step_mps2'] is None


def test_feasible_step_reports_actual_nonlinear_residual_not_projected_value():
    body=np.tile([0.,0.,-9.],(12,1));force=np.tile([0.,0.,-9.81],(12,1))
    result=calibration.analyze(body,force,LIMITS)
    assert result['linear_step_within_bounds']
    step=result['linear_step_physical']
    actual=np.linalg.norm((body-step[3:6])/(1.+step[:3]),axis=1)-np.linalg.norm(force-[0.,0.,step[6]],axis=1)
    assert result['nonlinear_rms_at_linear_step_mps2']==pytest.approx(np.sqrt(np.mean(actual**2)))
    assert result['nonlinear_rms_at_linear_step_mps2']>1e-4


@pytest.mark.parametrize('field,value',[
    ('body',np.zeros((4,3))),('force',np.zeros((4,3))),
    ('body',np.ones((4,2))),('force',np.ones((5,3))),
    ('body',np.full((4,3),np.nan)),('body',np.empty((0,3))),
    ('limits',np.ones(6)),('limits',np.zeros(7)),
    ('limits',np.array([1.,.15,.15,.25,.25,.25,.05])),
    ('rcond',0.),('rcond',np.nan),('rcond',1.),
])
def test_invalid_inputs_fail_closed(field,value):
    arguments=dict(body=np.tile([1.,2.,3.],(4,1)),force=np.tile([2.,3.,4.],(4,1)),limits=LIMITS,rcond=1e-10)
    arguments[field]=value
    with pytest.raises(ValueError):calibration.analyze(**arguments)
