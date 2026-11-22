"""A whole later path shares one bounded nuisance correction."""

import numpy as np
import pytest


def test_known_interior_correction_uses_all_future_rows():
    from lll.joint_future_profile import profile_future
    design = np.array([[1., 0.], [0., 1.], [1., 1.]])
    result = profile_future(design @ [0.2, -0.3], design,
                            lower=[-1., -1.], upper=[1., 1.], rank_rtol=1e-10)
    assert result['profiled_squared_residual'] == pytest.approx(0., abs=1e-20)
    assert result['correction'] == pytest.approx([.2, -.3])
    assert result['rank'] == 2
    assert result['scientific_decision'] == 'abstain'


def test_path_difference_outside_nuisance_space_remains():
    from lll.joint_future_profile import profile_future
    result = profile_future([1., 2., 3.], [[1.], [1.], [1.]],
                            lower=[-5.], upper=[5.], rank_rtol=1e-10)
    assert result['correction'] == pytest.approx([2.])
    assert result['profiled_squared_residual'] == pytest.approx(2.)


def test_boundary_solution_and_rank_deficiency_are_explicit():
    from lll.joint_future_profile import profile_future
    result = profile_future([4., 4.], [[1., 1.], [1., 1.]],
                            lower=[-1., -1.], upper=[1., 1.], rank_rtol=1e-10)
    assert result['rank'] == 1
    assert result['profiled_squared_residual'] == pytest.approx(8.)
    assert len(result['at_bound_columns']) == 2


def test_row_and_column_permutations_preserve_profile_cost():
    from lll.joint_future_profile import profile_future
    design = np.array([[1., 2.], [3., -1.], [0., 1.], [1., 0.]])
    residual = np.array([.1, 2., -1., .3])
    a = profile_future(residual, design, lower=[-.4, -.5], upper=[.5, .7],
                       rank_rtol=1e-10)
    b = profile_future(residual[[3, 1, 0, 2]], design[[3, 1, 0, 2]][:, [1, 0]],
                       lower=[-.5, -.4], upper=[.7, .5], rank_rtol=1e-10)
    assert a['profiled_squared_residual'] == pytest.approx(
        b['profiled_squared_residual'], abs=1e-12)


def test_nonfinite_or_incomplete_columns_fail_closed():
    from lll.joint_future_profile import profile_future
    with pytest.raises(ValueError):
        profile_future([1., 2.], [[1.], [float('nan')]],
                       lower=[-1.], upper=[1.], rank_rtol=1e-10)
    with pytest.raises(ValueError):
        profile_future([1., 2.], [[1., 0.], [0., 1.]],
                       lower=[-1.], upper=[1.], rank_rtol=1e-10)
