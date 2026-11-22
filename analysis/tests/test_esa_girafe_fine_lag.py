# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known shifts and exact elapsed-time rebinning controls."""

import numpy as np
import pytest


def test_fine_cells_pass_constant_and_weight_elapsed_time():
    from lll.esa_girafe_fine_lag import lagged_cell_means
    from lll.esa_girafe_platform_timing import held_cell_means

    t = np.arange(0., 6.004, .004)
    force = 9.8+np.cos(t[:-1]**2)
    shifted = lagged_cell_means(t, force, first=2.1, count=12)
    assert shifted.shape == (401, 12)
    for lag in (-200, -7, 0, 200):
        edges = 2.1+(np.arange(13)*10+lag)/100.
        direct = held_cell_means(t, force[:, None], edges)[:, 0]
        np.testing.assert_allclose(shifted[lag+200], direct, atol=1e-12, rtol=0.)


def test_known_subcell_shift_recovers_earlier_time():
    from lll.esa_girafe_fine_lag import lagged_cell_means, score_lags

    t = np.arange(0., 15.004, .004)
    force = 9.8+np.cos(t[:-1]**2)
    reference = lagged_cell_means(t, force, first=2.1, count=100)
    rows = score_lags(reference[193], reference, width=11)
    peak = max(rows, key=lambda score: score['correlation'])
    assert peak['lag_ms'] == -70
    assert peak['correlation'] == pytest.approx(1.)
