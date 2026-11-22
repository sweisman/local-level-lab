# SPDX-License-Identifier: AGPL-3.0-or-later
import math

import numpy as np
import pytest

from lll.carrier_anchor_error import anchor_residuals, anchor_uncertainty
from lll.carrier_score_bound import range_operator


def test_anchor_adjoint_uses_both_pair_signs_and_removes_common_clock():
    basis = np.eye(3)
    pairs = [(basis+2., -basis), (basis*2., basis)]
    row_weights = np.array([1., 2., 3., 5., 7., 9.])
    score = np.array([[0., 2., 0.], [0., 0., 1.], [2., 0., 0.]])
    expected = score-(range_operator(pairs, 3).T@row_weights).reshape(3, 3)
    actual = anchor_residuals(score, [0, 1, 2],
                              {i: (*p, row_weights[3*i:3*i+3]) for i, p in enumerate(pairs)})
    assert actual == pytest.approx(expected)
    with pytest.raises(ValueError, match='adjacent'):
        anchor_residuals(score, [0, 1, 2], {0: (*pairs[0], row_weights[:3])})


def test_anchor_box_bound_separates_common_and_independent_errors():
    result = anchor_uncertainty([[1., -2., 0.], [-1., 2., 3.]], free_count=4, free_weight_norm=.1)
    pad = math.sqrt(12)*.1
    assert result['all_anchor_axis_to_score'] == pytest.approx(9.+pad)
    assert result['common_axis_to_score'] == pytest.approx(3.+pad)
