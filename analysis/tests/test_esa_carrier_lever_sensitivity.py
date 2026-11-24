import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from lll.esa_carrier_lever_sensitivity import relative_rotations, score_bound, score_weights_ecef
from lll.gnss_position import ecef, geodetic


def test_partial_angles_compose_in_body_order():
    observed = relative_rotations([0, 1, 2], [[.4, 0, 0], [0, .6, 0]], .5, [.75, 1.5, 2])
    x = Rotation.from_rotvec([.2, 0, 0])
    expected = [Rotation.from_rotvec([.1, 0, 0]),
                x*Rotation.from_rotvec([0, .3, 0]), x*Rotation.from_rotvec([0, .6, 0])]
    np.testing.assert_allclose(observed, [r.as_matrix() for r in expected], atol=1e-14)


@pytest.mark.parametrize('edges, targets', [([0, 1, 1], [1]), ([0, 1, 2], [2.1]),
                                            ([0, 1, 2], [1.5, 1.4])])
def test_invalid_packet_or_score_order_is_rejected(edges, targets):
    with pytest.raises(ValueError, match='strictly ordered'):
        relative_rotations(edges, np.zeros((2, 3)), .2, targets)


def test_ecef_weights_include_receiver_metric():
    position = np.array([1.12, -.8, 2500.])
    metric = np.array([6.3e6, 3.1e6, 1.])
    weights = np.array([.43, -.8, .1])
    xyz = np.asarray(ecef(*position))
    step = np.array([.06, .08, -.03])
    reference = np.dot(weights*metric, np.subtract(geodetic(xyz+step), geodetic(xyz-step)))/2
    actual, = score_weights_ecef([position], metric, [weights])
    assert actual @ step == pytest.approx(reference, abs=5e-9)


def test_bound_covers_arbitrary_orientation_and_accounts_for_cancellation():
    rng = np.random.default_rng(3687)
    rotations = Rotation.from_rotvec(rng.random((8, 3))*.2).as_matrix()
    weights = rng.normal(size=(8, 3))
    bound = score_bound(rotations, weights)
    for _ in range(30):
        initial = Rotation.from_rotvec(rng.normal(size=3)).as_matrix()
        offset = rng.normal(size=3)
        displacement = (rotations-np.eye(3))@offset
        assert abs(np.sum(weights*(displacement@initial.T))) <= bound*np.linalg.norm(offset)
    assert score_bound([rotations[0], rotations[0]], [weights[0], -weights[0]]) == 0
    chord = np.linalg.norm(rotations[0]-np.eye(3), ord=2)
    assert score_bound(rotations[:1], weights[:1]) == pytest.approx(chord*np.linalg.norm(weights[0]))
