# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F

import numpy as np
import pytest

from lll.direct_residual_change_study import Control, control_increment
from lll.residual_curvature_solver import incremental_decrease


def test_direct_increment_preserves_an_improvement_below_rounding():
    residual = np.array([100., 0.])
    assert incremental_decrease(residual, residual, [-1e-17, 0.]) == pytest.approx(2e-15, abs=1e-30)
    assert incremental_decrease(residual, residual, [1e-17, 0.]) < 0
    with pytest.raises(ValueError, match='disagrees'):
        incremental_decrease(residual, residual, [-1e-7, 0.])


def test_direct_generated_residual_change_matches_exact_formula():
    problem = Control('weak', lambda **kwargs: None)
    prior = [.3500000014, -.23]
    optimum = [.35, -.23]
    reference = [F(x) for x in (problem.tx, problem.ty, problem.q, problem.offset, problem.bend, problem.slope)]
    tx, ty, q, offset, bend, slope = reference

    def exact(point):
        x, y = map(F, point)
        dx = x-tx
        return offset+q*dx**2, 25*(y-ty-bend*dx**2), slope*dx

    before, after = exact(prior), exact(optimum)
    change = control_increment(problem, prior, optimum)
    assert change == pytest.approx([float(b-a) for a, b in zip(before, after, strict=True)], rel=1e-12, abs=0)
    decrease = incremental_decrease(np.array(list(map(float, before))), np.array(list(map(float, after))), change)
    want = float(sum(a*a-b*b for a, b in zip(before, after, strict=True)))
    assert decrease == pytest.approx(want, rel=1e-12, abs=0)
