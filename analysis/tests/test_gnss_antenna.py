# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from lll.gnss_antenna import Pattern, phase_corrections
from lll.gnss_orbex import attitude_series


def test_offset_and_pcv_signs_use_transmitter_and_receiver_axes():
    satellite = Pattern((0., 0., 2.), (0., 90.), 0., ((.003, .003),))
    antenna = Pattern((0., 0., 1.), (0., 90.), 0., ((.002, .002),))
    terrestrial_to_body = Rotation.from_euler('y', 90, degrees=True)
    transmitter, ground = phase_corrections([6.4e6, 0., 0.], [26e6, 0., 0.],
                                            terrestrial_to_body, (satellite, satellite), (antenna, antenna))
    assert transmitter == pytest.approx(-1.997, abs=1e-8)
    assert ground == pytest.approx(-.998, abs=1e-8)


def test_azimuth_wraps_and_interpolates_both_axes():
    pattern = Pattern((0., 0., 0.), (0., 10.), 180., ((0., 2.), (4., 10.), (0., 2.)))
    assert pattern.value(5., 90.) == pytest.approx(4.)
    assert pattern.value(5., -90.) == pytest.approx(4.)
    with pytest.raises(ValueError, match='outside'):
        pattern.value(11., 90.)


def test_range_correction_validates_boresight_on_orbit_position_tuples():
    pattern = Pattern((0., 0., 0.), (0., 90.), 0., ((0., 0.),))
    receiver, satellite = (6.4e6, 0., 0.), (26e6, 0., 0.)
    correct = Rotation.from_euler('y', 90, degrees=True)
    assert phase_corrections(receiver, satellite, correct, (pattern, pattern)) == pytest.approx([0., 0.])
    with pytest.raises(ValueError, match='body z'):
        phase_corrections(receiver, satellite, Rotation.identity(), (pattern, pattern))


def obx(gap=30):
    return iter(f'''%=ORBEX  0.09
+FILE/DESCRIPTION
 TIME_SYSTEM         GPS
 EPOCH_INTERVAL      30.000
 COORD_SYSTEM        IGS20
 FRAME_TYPE          ECEF
-FILE/DESCRIPTION
+EPHEMERIS/DATA
## 2023 07 06 00 00 00.0 1
 ATT G01 4 1 0 0 0
## 2023 07 06 00 {gap//60:02} {gap%60:02}.0 1
 ATT G01 4 -0.7071067811865476 0 0 -0.7071067811865476
-EPHEMERIS/DATA
%END_ORBEX
'''.splitlines())


def test_attitude_is_scalar_first_ecef_to_body_and_sign_invariant():
    series = attitude_series(obx(), {1}, week=2269, first=345600, last=345630)
    rotation = series[1](345615)
    assert rotation.apply([1., 0., 0.]) == pytest.approx([np.sqrt(.5), np.sqrt(.5), 0.])


def test_attitude_refuses_to_bridge_missing_samples():
    with pytest.raises(ValueError, match='30-second'):
        attitude_series(obx(gap=60), {1}, week=2269, first=345600, last=345660)
