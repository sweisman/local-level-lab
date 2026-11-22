# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from scipy.integrate import quad

from lll.maneuver_error_roots import roots, turn_exposure


def test_exposure_is_causal_and_uses_packet_duration():
    dt = [.1,.1,.4,.4]
    angle = np.deg2rad(np.array([[0.,0.,1.],[0.,0.,0.],[0.,0.,0.],[0.,0.,0.]]))
    result = turn_exposure(dt,angle,[.2,.6,1.],previous_time=0.,threshold_deg_s=1.)
    assert result.tolist() == pytest.approx([9.8,0.,0.])


def test_transient_acceleration_impulse_matches_independent_integral():
    times = [1.,2.,3.,8.]
    k = roots(times, [0.,1.,0.,0.],previous_time=0.,decay_s=2.)
    pulse=k['maneuver'][:,2:4]
    assert np.all(pulse[:6]==0)
    t=8.-2.
    expected=quad(lambda s:(t-s)*np.exp(-s/2.),0.,t)[0]
    assert pulse[-3,0] == pytest.approx(expected)
    farther=k['persistent'][-3:, :]
    np.testing.assert_allclose(farther,np.eye(3)*32.)
