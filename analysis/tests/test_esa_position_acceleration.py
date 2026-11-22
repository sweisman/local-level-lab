import numpy as np
import pytest

from lll import esa_position_acceleration as motion
from lll.ilvis0_solver_position import physical_metric


def test_cubic_motion_retains_vertical_sign_and_cross_time_bounds():
    t = np.arange(11.) - 5.
    coordinates = np.repeat([[1., -.4, 800.]], len(t), axis=0)
    coordinates[:, 2] += .1*t + .5*.3*t**2 - .002*t**3
    matrix = np.repeat(np.diag([.01, .02, .04])[None, :, :], len(t), axis=0)
    result = motion.from_positions(t, coordinates, matrix, center=5)
    assert result['acceleration_ned_m_s2'] == pytest.approx([0, 0, -.3], abs=1e-11)
    assert result['force_magnitude_m_s2'] == pytest.approx(10.11, abs=1e-11)
    quadratic = np.column_stack((np.ones(len(t)), t, t**2, t**3))
    acceleration_weights = 2*np.linalg.pinv(quadratic)[2]
    assert result['reported_independent_sd_m_s2'] == pytest.approx(.2*np.linalg.norm(acceleration_weights))
    assert result['reported_arbitrary_correlation_upper_sd_m_s2'] == pytest.approx(.2*abs(acceleration_weights).sum())


def test_position_kinematics_include_changing_metric_and_background_terms():
    t = np.linspace(-5., 5., 11)
    coordinate = np.asarray([1., -.4, 800.])
    scale = physical_metric(coordinate[None, :])[0]
    center_speed = np.array([80., 43., .2])
    coordinates = coordinate + t[:, None]*center_speed/scale
    matrix = np.repeat((.01*np.eye(3))[None, :, :], len(t), axis=0)
    result = motion.from_positions(t, coordinates, matrix, center=5)
    assert result['velocity_ned_m_s'] == pytest.approx([80, 43, -.2], abs=1e-9)
    # The north/east metric changes along this path despite linear coordinates.
    assert abs(result['acceleration_ned_m_s2'][1]) > .0005
    assert result['force_magnitude_m_s2'] < 9.81
