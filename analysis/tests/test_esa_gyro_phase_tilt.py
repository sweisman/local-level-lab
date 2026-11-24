import math

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.spatial.transform import Rotation

from lll.esa_gyro_phase_tilt import phase_limit, lower_endpoint_elevations
from lll.gnss_phase_windup import fractional_phase


@pytest.mark.parametrize('tilt,elevation', [(0, 5), (5, 5), (33, 5), (25, 66)])
def test_phase_cap_matches_integral_and_bounds_actual_receiver_rotations(tilt, elevation):
    t, e = map(math.radians, (tilt, elevation))
    actual, = phase_limit(np.array([t]), np.array([e]))
    integral, _ = quad(lambda u: math.tan(math.pi/4+(u-e)/2), 0., t)
    assert actual == pytest.approx(integral, abs=1e-14)
    dipoles = np.eye(3)[:2]
    transmit = [dipoles[0], -dipoles[1]]
    ray = np.array([math.cos(e), 0, math.sin(e)])
    start = fractional_phase(ray, transmit, dipoles)
    for azimuth in np.linspace(0, 2*math.pi, 50, endpoint=False):
        rotation = Rotation.from_rotvec(t*np.array([math.cos(azimuth), math.sin(azimuth), 0.]))
        stop = fractional_phase(ray, transmit, rotation.apply(dipoles))
        assert abs(math.remainder(stop-start, 2*math.pi)) <= actual + 1e-14


def test_elevation_uses_the_lower_of_both_adjacent_pairs():
    np.testing.assert_allclose(lower_endpoint_elevations([7, 5, 8, 9]),
                               np.radians([7, 5, 5, 8, 9]))


def test_antipodal_ray_is_rejected():
    with pytest.raises(ValueError, match='opposite'):
        phase_limit(np.array([math.pi*3/4]), np.array([-math.pi/4]))
