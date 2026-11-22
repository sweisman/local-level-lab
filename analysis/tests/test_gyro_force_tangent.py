# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np
from scipy.spatial.transform import Rotation

from lll.gyro_force_tangent import box_project_gradient, corrected_transport


def test_all_packet_derivatives_match_direct_noncommuting_rotation_differences():
    rng = np.random.default_rng(921)
    theta = rng.normal(scale=.07, size=(21, 3))
    theta[::6] = 0.
    dt = rng.uniform(.002, .004, len(theta))
    force = rng.normal(size=theta.shape) + [0., 0., 9.81]
    limits = np.array([[.1]*3, [.02]*3, [4.8e-6]*3, [.01]*3])
    point = rng.uniform(-.7, .7, size=12)

    def independent(p):
        ab, ag, gb, gg = (p.reshape(4, 3)*limits)
        increments = (theta-dt[:, None]*gb)/(1.+gg)
        velocities = (force-ab)/(1.+ag)
        prefix = Rotation.identity()
        result = []
        for vector, v in zip(increments, velocities, strict=True):
            result.append((prefix*Rotation.from_rotvec(vector/2.)).apply(v))
            prefix *= Rotation.from_rotvec(vector)
        return np.asarray(result)

    actual, jac = corrected_transport(theta, force, dt, point, limits)
    np.testing.assert_allclose(actual, independent(point), atol=1e-13)
    h = 1e-4
    for axis in np.eye(12):
        tangent = (independent(point+h*axis)-independent(point-h*axis))/(2*h)
        np.testing.assert_allclose(tangent, jac @ axis, rtol=1e-7, atol=1e-10)


def test_box_projection_keeps_only_feasible_descent_components():
    assert box_project_gradient(np.array([-1., 1., 0.]), [10., -5., .003]) == .003
    assert box_project_gradient(np.array([-1., 1., 0.]), [-10., 5., .003]) == 10.


def test_packet_support_uses_integer_charge_endpoints():
    from lll.esa_direction_exact_gradient import early_support

    times = np.arange(400, dtype=float)
    clock = np.linspace(-.1, 400.1, 120061)
    supports = early_support(times, clock, 25)
    assert len(supports) == 8
    assert all(type(window.stop) is int and abs(weights.sum()-1.) < 1e-10 for window, weights in supports)
