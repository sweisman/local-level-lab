# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F

import numpy as np
import pytest

from lll.ilvis0_coupled_map import StaticMap
from test_ilvis0_coupled_map import reference


@pytest.mark.parametrize('fixed', [False, True])
def test_linked_direction_encloses_full_oracle(fixed):
    from lll.ilvis0_linked_directional import directional_bound

    ref = reference(fixed=fixed)
    model = StaticMap(ref, expected_report=ref.report())
    lower = ref.parent.lower if fixed else np.full(27, -.18)
    upper = ref.parent.upper if fixed else np.full(27, .34)
    coefficients = [(F(i-25, 13), F(i-25, 13) + F(1, 10**7)) for i in range(51)]
    bound = directional_bound(model, lower, upper, coefficients)
    for point in (lower, upper, (lower+upper)/2, np.linspace(lower[0], upper[0], 27)):
        vector = np.r_[point-ref.parent.center, ref.normalized_values_at(point)]
        for endpoint in (0, 1):
            score = sum(c[endpoint]*F(v) for c, v in zip(coefficients, vector, strict=True))
            assert bound.lo <= score <= bound.hi


def test_force_matrix_cancellation_is_kept_before_interval_evaluation():
    from lll.ilvis0_linked_directional import directional_bound

    ref = reference()
    model = StaticMap(ref, expected_report=ref.report())
    r, a, matrix = ref.parent, ref.acceleration, ref.transform
    force = [F(v)/F(a.period)-F(r.limits[12+j])*F(r.center[12+j])
             for j, v in enumerate(a.raw_delta_v)]
    coefficients = [F(0)]*51
    coefficients[39] = F(a.caps[6])
    for j in range(3):
        coefficients[42+j] = -F(matrix.caps[j])*force[j]
    box = [(q, q) for q in coefficients]
    lower = r.center.copy()
    upper = r.center.copy()
    lower[:3], upper[:3] = -.2, .25
    limit = directional_bound(model, lower, upper, box)
    assert max(abs(limit.lo), abs(limit.hi)) < 1e-7
    components = model.bound(lower, upper)
    separate = sum(abs(float(q))*max(abs(v.value.lo), abs(v.value.hi))
                   for q, v in zip(coefficients[27:], components, strict=True))
    assert separate > .01
