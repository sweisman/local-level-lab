# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction

import numpy as np

from lll.state_space_covariance import LinearInnovations
from lll.state_space_directional_bound import adjoint_intervals, directional_bound


def test_adjoint_contains_exact_scalar_reference_including_training_feedback():
    count = 5
    op = LinearInnovations((dict(transition=[[1.]], process_loading=[[0.]],
        observation=[[1.]], white_loading=[[.2]]) for _ in range(count)),
        epoch_count=count, state_dimension=1, observation_dimension=1,
        initial_loading=[[1.]], maximum_bytes=16000, design_is_fixed=True,
        error_distribution='gaussian')
    direction = [0., 0., 0., -.5, 1.]
    lower, upper = adjoint_intervals(op, direction)
    exact = []
    for column in range(count):
        mean = Fraction(0)
        value = Fraction(0)
        for i in range(count):
            innovation = Fraction(int(i == column)) - Fraction(op._observation[i, 0, 0])*mean
            value += Fraction(direction[i])*innovation/Fraction(op._lower[i, 0, 0])
            mean = Fraction(op._transition[i, 0, 0])*mean + Fraction(op._gain[i, 0, 0])*innovation
        exact.append(value)
        assert Fraction(lower[column]) <= value <= Fraction(upper[column])
    assert any(value != 0 for value in exact[:3])
    assert np.max(upper-lower) < 1e-11
    assert Fraction(directional_bound(lower, upper, np.ones(count))) >= sum(map(abs, exact))
