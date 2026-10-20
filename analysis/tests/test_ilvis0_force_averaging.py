# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent integrated rotating-force controls for a declared direction cone."""
import math

import numpy as np
import pytest

from lll.ilvis0_increment_bounds import magnitude_bounds


def bounds(counts,period,beta):
    return magnitude_bounds(np.asarray(counts,np.int32),np.asarray(period,float),
        scale_mps_per_count=1e-8,count_uncertainty=.5,period_hypothesis='declared interval',
        maximum_force_direction_rate_rads=beta)


def test_no_direction_assumption_still_leaves_continuous_upper_unknown():
    result=bounds([[0,0,9810000]],[[.01,.01]],None)
    assert not result['continuous_force_upper_bound_established']
    assert result['continuous_magnitude_upper_mps2'] is None


def test_zero_direction_rate_has_no_averaging_loss_even_for_changing_magnitude():
    result=bounds([[0,0,9810000]],[[.01,.01]],0.)
    assert result['continuous_force_upper_bound_established']
    assert result['continuous_magnitude_upper_mps2']==result['time_weighted_magnitude_upper_mps2']


@pytest.mark.parametrize('period,beta,jerk',[(.005,.1,0.),(.005,1.,100.),(1.,math.pi/2,0.),(.01,2.,-50.)])
def test_independent_integrated_rotating_force_is_inside_bound(period,beta,jerk):
    half=period/2;a=9.81
    # Exact integrals of (a+jerk*t)*(sin(beta*t),0,-cos(beta*t)).
    x=2*jerk*(-half*math.cos(beta*half)/beta+math.sin(beta*half)/beta**2)
    z=-2*a*math.sin(beta*half)/beta
    counts=np.rint(np.array([[x,0.,z]])/1e-8).astype(np.int32)
    result=bounds(counts,[[period,period]],beta)
    assert result['continuous_magnitude_lower_mps2']<=a<=result['continuous_magnitude_upper_mps2']
    assert not result['statistical_coverage_calibrated']
    assert result['direction_rate_is_assumed']


def test_complete_rotation_does_not_create_a_finite_zero_force_conclusion():
    result=bounds([[0,0,0]],[[1.,1.]],2*math.pi)
    assert not result['continuous_force_upper_bound_established']
    assert result['continuous_magnitude_upper_mps2'] is None
    assert not result['direction_cone_supported'][0]


def test_uncertain_period_uses_the_largest_possible_rotation_cone():
    result=bounds([[0,0,4905000]],[[.004,.006]],1.)
    expected=result['packet_force_upper_mps2'][0]/math.cos(.006/2)
    assert result['continuous_magnitude_upper_mps2']==pytest.approx(expected)


@pytest.mark.parametrize('beta',[-1.,np.nan,np.inf])
def test_invalid_direction_rate_is_rejected(beta):
    with pytest.raises(ValueError):bounds([[0,0,9810000]],[[.01,.01]],beta)
