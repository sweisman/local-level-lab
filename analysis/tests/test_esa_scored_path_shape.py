# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_scored_path_shape import project_residual


def test_quadratic_path_component_is_recovered_with_correlated_errors():
    times = np.arange(1., 7.)
    phases = times / times[-1]
    error = np.column_stack((0.4 * phases, -0.5 + 2. * phases**2, 0.1 + phases))
    lower = np.eye(error.size) + 0.2 * np.eye(error.size, k=-1)
    result = project_residual(times, 0., error, lower)
    assert result['df'] == 9
    assert result['residual_df'] == error.size - 9
    assert result['tail_neu_m'] == pytest.approx(error[-1])
    assert result['projected_energy'] == pytest.approx(result['total_energy'])
    assert result['residual_energy'] == pytest.approx(0., abs=1e-24)


def test_orthogonal_motion_error_remains_in_the_residual():
    times = np.arange(1., 5.)
    error = np.zeros((4, 3))
    error[:, 2] = [-1., 3., -3., 1.]
    result = project_residual(times, 0., error, np.eye(error.size))
    assert result['total_energy'] == pytest.approx(20.)
    assert result['residual_energy'] == pytest.approx(20.)
    assert result['projected_energy'] == pytest.approx(0., abs=1e-24)
