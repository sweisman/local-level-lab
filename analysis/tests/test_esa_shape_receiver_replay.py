# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_shape_receiver_replay import score_paths


def test_score_reproduces_shape_margin_and_ignores_later_quadratic_offsets():
    cut = 3
    times = np.arange(11.)
    sphere = np.zeros((11, 3))
    flat = sphere.copy()
    flat[cut:, 0] = np.arange(8.)**3
    later_t = np.arange(8.)
    design = np.column_stack((later_t**0, later_t, later_t**2))
    direction = flat[cut:, 0] - design @ np.linalg.lstsq(design, flat[cut:, 0], rcond=None)[0]
    nominal = np.linalg.norm(direction)
    unit = np.zeros((8, 3))
    unit[:, 0] = direction / nominal

    changed = sphere.copy()
    changed[cut:, 0] += 11. + 4. * later_t - .3 * later_t**2
    result = score_paths(
        lambda x: x, times, cut, unit.ravel(), nominal, sphere, flat,
        dict(original=sphere, shifted=changed, midpoint=(sphere + flat) / 2, other=flat),
    )
    assert result['original']['signed_midpoint'] == pytest.approx(-nominal / 2)
    assert result['shifted']['signed_midpoint'] == pytest.approx(-nominal / 2)
    assert result['midpoint']['signed_midpoint'] == pytest.approx(0., abs=1e-12)
    assert result['other']['signed_midpoint'] == pytest.approx(nominal / 2)
    assert result['other']['sphere_squared_error'] == pytest.approx(nominal**2)
    assert result['other']['disc_squared_error'] == pytest.approx(0.)
