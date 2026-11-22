# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np
from scipy.spatial.transform import Rotation

from lll.force_accel_calibration import corrected_directions, fit_calibration, objective
from lll.force_direction_alignment import unit_vectors


def fixture():
    rng = np.random.default_rng(214)
    axes = Rotation.from_rotvec(rng.normal(size=(16, 3))).as_matrix()
    force = rng.normal(size=(16, 3)) + [0., 0., 9.8]
    bias_limit, gain_limit = np.full(3, .1), np.full(3, .02)
    true = np.array([.23, -.38, .14, .6, -.24, .16])
    channels = axes*(force*(1.+true[3:]*gain_limit)+true[:3]*bias_limit)[:, None, :]
    reference = Rotation.from_rotvec([.3, -.15, .1]).apply(np.einsum('nij,nj->ni', axes, force))
    return reference, channels, axes, bias_limit, gain_limit, true


def test_profiled_objective_derivative_and_common_gain_gauge():
    reference, channels, axes, bias_limit, gain_limit, true = fixture()
    target = unit_vectors(reference)
    point = true/2.
    _, gradient, _, _, _ = objective(point, target, channels, axes, bias_limit, gain_limit)
    h = 1e-5
    finite = []
    for column in np.eye(6):
        a, b = (objective(point+s*h*column, target, channels, axes, bias_limit, gain_limit)[0]
                for s in (-1., 1.))
        finite.append((b-a)/(2*h))
    np.testing.assert_allclose(gradient, finite, atol=1e-12, rtol=1e-6)
    changed = point.copy()
    changed[3:] = ((1.+point[3:]*gain_limit)*1.002-1.)/gain_limit
    a, _ = corrected_directions(channels, axes, point, bias_limit, gain_limit)
    b, _ = corrected_directions(channels, axes, changed, bias_limit, gain_limit)
    np.testing.assert_allclose(a, b, atol=1e-14)


def test_bounded_calibration_and_rotation_do_not_see_later_observations():
    reference, channels, axes, bias_limit, gain_limit, _ = fixture()
    args = dict(training=12, bias_limit=bias_limit, gain_limit=gain_limit, start=np.zeros(6), max_calls=100)
    result = fit_calibration(reference, channels, axes, **args)
    assert result['passed'] and result['calibration_rank'] == 5
    assert result['later_rms_deg'] < 1e-5
    changed = reference.copy()
    changed[-4:] *= -1.
    later = fit_calibration(changed, channels, axes, **args)
    assert later['normalized_calibration'] == result['normalized_calibration']
    assert later['starting_rotation'] == result['starting_rotation']
    assert later['later_rms_deg'] > 179.
