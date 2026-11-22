"""Local boundary profiles are descriptive and preserve active constraints."""

import numpy as np
import pytest


def test_one_bound_profiles_after_free_nuisance_projection():
    from lll.esa_fit_adjusted_boundary_report import profile_one_bound

    jacobian = np.array([[1.,0.],[0.,2.],[0.,0.]])
    residual = np.array([0.,1.,0.])
    lower = profile_one_bound(residual,jacobian,active_index=1,
                              free_indices=[0],normalized_value=-1.)
    assert lower['free_rank'] == 1
    assert lower['curvature'] == pytest.approx(4.)
    assert lower['slope'] == pytest.approx(4.)
    assert lower['unbounded_step'] == pytest.approx(-.5)
    assert lower['local_cost_gain_if_unbounded'] == pytest.approx(1.)
    assert lower['unbounded_step_points_outside'] is True

    upper = profile_one_bound(-residual,jacobian,active_index=1,
                              free_indices=[0],normalized_value=1.)
    assert upper['unbounded_step_points_outside'] is True
    assert upper['local_cost_gain_if_unbounded'] == pytest.approx(1.)


def test_unidentifiable_bound_direction_does_not_claim_cost_gain():
    from lll.esa_fit_adjusted_boundary_report import profile_one_bound

    jacobian = np.array([[1.,2.],[0.,0.],[0.,0.]])
    result = profile_one_bound(np.array([1.,0.,0.]),jacobian,
        active_index=1,free_indices=[0],normalized_value=-1.)
    assert result['estimable'] is False
    assert result['local_cost_gain_if_unbounded'] is None


def test_joint_active_profile_keeps_correlated_bounds_together():
    from lll.esa_fit_adjusted_boundary_report import profile_active_set

    jacobian = np.array([[1.,0.,0.],[0.,2.,0.],[0.,0.,3.],[0.,0.,0.]])
    result = profile_active_set(np.array([0.,1.,1.,0.]),jacobian,
        active_indices=[1,2],free_indices=[0],normalized_values=[-1.,-1.])
    assert result['free_rank'] == 1
    assert result['active_rank_after_free_projection'] == 2
    assert result['local_cost_gain_if_all_unbounded'] == pytest.approx(2.)
    assert result['unbounded_steps'] == pytest.approx([-.5,-1/3])
    assert result['unbounded_solution_outside_bounds'] is True
