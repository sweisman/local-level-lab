# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.ilvis0_rf04_receiver_offset import compare_models, split_indices


def test_rf04_offset_recovers_delay_and_bias_while_testing_later_values():
    velocity = np.array([[220+i, i*(-1)**i] for i in range(12)], dtype=float)
    delta = .4*velocity + [3., -2.]
    early, later = np.arange(6), np.arange(6, 12)
    result = compare_models(velocity, delta, early, later)
    assert result['constant_and_delay']['delay_s'] == pytest.approx(.4)
    assert result['constant_and_delay']['offset_ne_m'] == pytest.approx([3., -2.])
    assert result['constant_and_delay']['later_rms_m'] < 1e-10
    delta[6:] += 100.
    changed = compare_models(velocity, delta, early, later)
    assert changed['constant_and_delay']['offset_ne_m'] == result['constant_and_delay']['offset_ne_m']
    assert changed['constant_and_delay']['later_rms_m'] > 100.


def test_rf04_offset_separates_halves_and_abstains_for_constant_velocity():
    earlier, later = split_indices(12)
    assert list(earlier) == [1, 2, 3, 4]
    assert list(later) == [7, 8, 9, 10]
    velocity = np.tile([200., 0.], (12, 1))
    result = compare_models(velocity, .4*velocity, earlier, later)
    assert result['delay_only']['delay_s'] == pytest.approx(.4)
    assert result['constant_and_delay'] is None
