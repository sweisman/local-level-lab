# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.shared_motion_carrier import signed_product_comparison


def test_product_update_combines_signs_after_removing_receiver_clock():
    required = np.array([1., -1., 0.])
    broadcast_residual = np.array([-0.5, 0.5, 0.])
    orbit = np.array([3.25, 2.75, 3.])
    clock = np.array([4.75, 3.25, 4.])
    result = signed_product_comparison(required, broadcast_residual, orbit, clock)
    assert result['products_m'] == pytest.approx(required)
    assert result['fixed_residual_m'] == pytest.approx(-1.5*required)
    assert result['shifted_residual_m'] == pytest.approx(broadcast_residual)
