# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.ilvis0_recorded_motion_rate import rate_bracket


def test_count_uncertainty_and_nominal_witness_bracket_known_rate():
    counts = np.array([[0., 0., 1000.], [0., 0., 1000.]])
    frame = np.array([[0., 0., 1.], [np.sin(.3), 0., np.cos(.3)]])
    result = rate_bracket(counts, frame, [0., 2.], twists=128)
    assert result['initial_upper_rads'] == pytest.approx(.15)
    assert 0.149 < result['lower_rads'] <= .15 <= result['upper_rads']+1e-12
    assert result['maximum_count_direction_error_rad'] > 0.
