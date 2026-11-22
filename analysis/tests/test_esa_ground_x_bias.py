# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_ground_x_bias import ground_profile


def test_varied_static_directions_recover_known_bias_with_fixed_gains():
    force = 9.8*np.vstack((np.eye(3),-np.eye(3)))
    bias = np.array([.1,-.02,.04])
    good = ground_profile([force+bias], [.1]*3, [0.]*3, .1)
    wrong = ground_profile([force+bias], [.1]*3, [0.]*3, -.1)
    assert good['settled']
    assert good['bias_mps2'] == pytest.approx(bias,abs=1e-8)
    assert good['max_squared_half_spread_mps4'] == pytest.approx(0.,abs=1e-9)
    assert wrong['max_squared_half_spread_mps4'] >= 3.9-1e-8
