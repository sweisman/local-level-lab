# SPDX-License-Identifier: AGPL-3.0-or-later
import math
import pytest
from lll.ilvis0_refinement import constant_bias_example,motion_scales,globe_disc_profile


def test_constant_signal_is_absorbed_without_calibration():
    to_rads=math.pi/(180*3600)
    result=constant_bias_example([0,8*to_rads,0],20*to_rads)
    assert result['fully_absorbed']
    assert result['remaining_rads']==(0,0,0)
    constrained=constant_bias_example([0,8*to_rads,0],1*to_rads)
    assert constrained['remaining_rads'][1]==pytest.approx(7*to_rads)


def test_motion_scales_are_smaller_than_current_envelopes():
    low,high=motion_scales(140),motion_scales(256)
    assert low['horizontal_curvature_dph']==pytest.approx(4.533,rel=.001)
    assert high['horizontal_curvature_dph']==pytest.approx(8.288,rel=.001)
    assert high['gyro_bound_to_curvature_ratio']>2
    assert high['accel_bound_to_centripetal_ratio']>20


def candidates():
    return [dict(model=n,converged=True,exact_projected_gradient_relative=1e-6,residual_sum_squares=c)
            for n,c in [('sphere_rotating',3.),('sphere_still',5.),('flat_still',10.)]]


def test_globe_union_keeps_partial_scientific_question():
    result=globe_disc_profile(candidates())
    assert result['conditional_disc_minus_globe_cost']==7
    assert result['scientific_decision']=='abstain'
    assert not result['calibrated']


def test_no_comparison_from_unfinished_or_false_convergence():
    rows=candidates();rows[1]['converged']=False
    assert globe_disc_profile(rows)['conditional_disc_minus_globe_cost'] is None
    rows=candidates();rows[2]['exact_projected_gradient_relative']=.01
    assert globe_disc_profile(rows)['conditional_disc_minus_globe_cost'] is None


def test_duplicate_candidates_and_invalid_cost_rejected():
    with pytest.raises(ValueError):globe_disc_profile([candidates()[0]]*3)
    rows=candidates();rows[0]['residual_sum_squares']=math.nan
    with pytest.raises(ValueError):globe_disc_profile(rows)
