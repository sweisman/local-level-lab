# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_original_whitening import score_change


def test_cost_change_preserves_small_increment_against_large_saved_loss():
    residual = np.array([1e10, .2, 0.])
    response = np.array([1e-12, 0., 0.])
    assert score_change(residual, response) == pytest.approx(.02)


def test_cost_change_rejects_misaligned_epochs():
    with pytest.raises(ValueError, match='aligned'):
        score_change([0., 0.], [[1.], [2.]])
