# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from scipy.spatial.transform import Rotation


def test_ideal_phase_gradient_matches_independent_finite_rotations():
    from lll.esa_phase_windup_budget import phase_gradient

    east, north, up = np.eye(3)
    for rotation in (Rotation.identity(), Rotation.from_rotvec([.3, -.2, .5])):
        a, b, normal = rotation.apply([east, north, up])
        for ray in ([.6, 0., .8], [0., .8, .6], [0., 0., 1.]):
            satellite = rotation.apply(ray)
            k = -satellite

            def dipole(x, y):
                return x - k*np.dot(k, x) + np.cross(k, y)

            original = dipole(a, b)
            angles = []
            for axis in (a, b, normal):
                shifted = dipole(*Rotation.from_rotvec(axis*1e-7).apply([a, b]))
                angles.append(np.arctan2(k@np.cross(original, shifted), original@shifted)/1e-7)
            gradient = phase_gradient(satellite, normal)
            np.testing.assert_allclose(angles, np.array([a, b, normal])@gradient, atol=1e-7)
            assert gradient@normal == pytest.approx(-1.)
            assert np.linalg.norm(gradient + normal) <= 1.


def test_endpoint_weights_telescope_and_cancel_instantaneous_common_phase():
    from lll.esa_phase_windup_budget import endpoint_weights

    support = [[1, 2, 3], [1, 2, 4], [1, 2, 3]]
    weights = [3., -1., 7., 4., 0., -2., -2., 2., 0.]
    endpoint = [{1: .2, 2: -.4, 3: 1.},
                {1: .8, 2: .6, 3: -.3, 4: .4},
                {1: .4, 2: .7, 3: .1, 4: .9},
                {1: .7, 2: .5, 3: -.2}]
    expected = 0.
    for i, row in enumerate(support):
        change = np.array([endpoint[i+1][p]-endpoint[i][p] for p in row])
        expected += np.dot(weights[i*3:i*3+3], change-change.mean())
    mapped = endpoint_weights(support, weights)
    replay = sum(w*(data[p]+i) for i, (data, row) in enumerate(zip(endpoint, mapped, strict=True))
                 for p, w in row.items())
    assert replay == pytest.approx(expected)
    assert all(sum(w.values()) == pytest.approx(0.) for w in mapped)
    assert mapped[1][1] == pytest.approx(-10./3.)


def test_phase_scale_and_required_tilt_units():
    from lll.esa_carrier_phase_support import F1, F2, C
    from lll.esa_phase_windup_budget import tilt_budget

    result = tilt_budget([[1, 2], [1, 2]], [1., -1., 1., -1.], .001)
    assert result['endpoint_absolute_weight_sum'] == 4.
    assert result['per_degree'] == pytest.approx(4*C/((F1+F2)*360))
    assert result['equal_allowance_tilt_deg'] == pytest.approx(.001/result['per_degree'])


def test_invalid_support_and_unobservable_antenna_direction_are_rejected():
    from lll.esa_phase_windup_budget import endpoint_weights, phase_gradient

    for support, weights in (([[1, 1]], [1., -1.]), ([[1, 2]], [1.]), ([[1]], [1.])):
        with pytest.raises(ValueError):
            endpoint_weights(support, weights)
    with pytest.raises(ValueError):
        phase_gradient([0., 0., -1.], [0., 0., 1.])
