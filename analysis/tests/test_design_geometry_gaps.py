# SPDX-License-Identifier: AGPL-3.0-or-later
"""Supported courses after a gap remain usable in analytic route design."""
import numpy as np
import pytest

from lll.design_geometry import geometry_problem


@pytest.mark.parametrize('crab', ['wind', 'wind_tas'])
def test_missing_course_does_not_poison_later_supported_bins(crab):
    t = np.arange(4500.)
    heading = np.radians(350. + t * .01)
    psi = np.angle(np.exp(1j * heading))
    supported = (t < 1800.) | (t > 1900.)
    psi[~supported] = np.nan
    speed = np.full(len(t), 250.)
    kin = dict(t=t, psi=psi, psi_dot=np.full(len(t), np.radians(.01)),
               speed=speed, v_n=speed * np.cos(heading), v_e=speed * np.sin(heading),
               lat=np.full(len(t), np.radians(45.)), h=np.full(len(t), 11000.),
               vz=np.zeros(len(t)), bearing_ok=supported)
    design = dict(simulator=dict(trajectory_input={'mode':'simulated_high_rate'},
                  turn_seconds=5., mount='tray', mount_yaw_deg=20., mount_tilt_deg=4.))
    problem = geometry_problem(design, [20., 40., 60.], crab, kin=(kin, 4500.))
    assert np.any(problem.bins['t'] < 1800.) and np.any(problem.bins['t'] > 1900.)
    assert np.isfinite(problem.bins['psi']).all()
    assert not np.any((problem.bins['t'] + 30. >= 1800.) & (problem.bins['t'] - 30. <= 1900.))
    np.testing.assert_allclose(np.sin(problem.bins['psi']), np.sin(np.radians(350. + problem.bins['t'] * .01)), atol=1e-12)
    z = np.zeros(problem.npar); z[:3] = [1., 1., 0.]
    pred, J = problem.prediction(z, True)
    assert np.isfinite(pred).all() and np.isfinite(J).all()
