# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.conditioned_shape_calibration import projected_direction
from lll.state_space_covariance import LinearInnovations


def test_direction_retains_only_the_nonquadratic_shape_difference():
    times = np.arange(10., dtype=float)
    cut = 3
    operator = LinearInnovations((dict(transition=[[1.]], process_loading=[[0.]],
        observation=np.zeros((3, 1)), white_loading=np.eye(3)) for _ in times),
        epoch_count=len(times), state_dimension=1, observation_dimension=3,
        initial_loading=[[0.]], maximum_bytes=16000, design_is_fixed=True,
        error_distribution='gaussian')
    t = times[cut:]
    difference = np.column_stack((t*t + (-1.)**t, 2*t, -t*t))
    design = np.column_stack((np.ones_like(t), t, t*t))
    remainder = difference - design @ np.linalg.lstsq(design, difference, rcond=None)[0]
    direction, distance = projected_direction(operator, times, difference, cut)
    assert distance == pytest.approx(np.linalg.norm(remainder))
    np.testing.assert_allclose(direction.reshape(-1, 3)*distance, remainder, atol=1e-12)
