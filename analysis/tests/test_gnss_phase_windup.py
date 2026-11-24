# SPDX-License-Identifier: AGPL-3.0-or-later
from math import pi

import numpy as np
import pytest
from scipy.spatial.transform import Rotation


def test_fractional_phase_rotates_with_upright_receiver_for_any_ray():
    from lll.gnss_phase_windup import fractional_phase

    east, north, up = np.eye(3)
    transmit = np.array([east, -north])
    for ray in (up, [.6, 0., .8], [0., .8, .6]):
        base = fractional_phase(ray, transmit, [east, north])
        rotated = Rotation.from_rotvec(.8*up).apply([east, north])
        assert fractional_phase(ray, transmit, rotated) == pytest.approx(base-.8)


def test_boresight_phase_and_branch_crossing_use_signed_conventions():
    from lll.gnss_phase_windup import fractional_phase, range_change

    east, north, up = np.eye(3)
    transmit = [north, east]
    assert fractional_phase(up, transmit, [east, north]) == pytest.approx(pi/2)
    from lll.esa_carrier_phase_support import C, F1, F2
    assert range_change(pi-.03, -pi+.01) == pytest.approx(.04*C/(2*pi*(F1+F2)))
    with pytest.raises(ValueError, match='short'):
        range_change(0., pi/2)


def test_phase_fails_on_null_dipole_or_invalid_ray():
    from lll.gnss_phase_windup import fractional_phase

    east, north, up = np.eye(3)
    with pytest.raises(ValueError, match='dipole'):
        fractional_phase(up, [east, north], [east, north])
    with pytest.raises(ValueError, match='unit ray'):
        fractional_phase(up*2, [east, -north], [east, north])
