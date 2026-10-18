# SPDX-License-Identifier: AGPL-3.0-or-later
"""Constructed matrix controls; no recordings, native integration or fitting."""
import numpy as np
import pytest


def helper():
    from lll import ilvis0_projected_endpoint as endpoint
    return endpoint


def test_column_scaling_maps_bounds_and_predictions_without_removing_nulls():
    jac=np.array([[1000.,0.,0.],[0.,.001,0.],[1.,.002,0.]])
    point=np.array([.99,-.5,.4]);residual=np.array([-20.,.01,1.])
    before=point.copy(),jac.copy()
    steps=helper().linear_steps(point,residual,jac)
    assert set(steps)=={'unscaled','column_scaled'}
    for row in steps.values():
        step=np.array(row['correction'])
        assert step.shape==(3,) and np.all(abs(point+step)<=1+1e-12)
        assert np.dot(residual+jac@step,residual+jac@step)<=residual@residual+1e-10
        assert row['columns']==3 and row['rank']==2
    assert np.array_equal(point,before[0]) and np.array_equal(jac,before[1])


def test_directions_keep_all_columns_and_report_expected_weak_axis():
    rows=helper().directions(np.diag([100.,.01,1e-8]),['a','b','c'])
    assert rows['columns']==3 and rows['rank']==3
    assert abs(rows['weak_directions'][0]['components']['c'])==pytest.approx(1.)
    assert rows['condition_ratio']==pytest.approx(1e10)


def test_derivative_errors_are_axis_specific_and_fail_closed():
    expected=np.array([[2.,0.],[0.,4.]])
    result=helper().derivative_errors(expected,expected+np.array([[.1,0.],[0.,-.2]]),['x','y'])
    assert result['x']['maximum_absolute_error']==pytest.approx(.1)
    assert result['y']['maximum_absolute_error']==pytest.approx(.2)
    with pytest.raises(ValueError):helper().derivative_errors(expected,np.ones((2,1)),['x','y'])
