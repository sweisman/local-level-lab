# SPDX-License-Identifier: AGPL-3.0-or-later
import math

import numpy as np
import pytest

from lll import gnss_doppler as doppler
from lll import gnss_position as gps


def test_doppler_rate_sign_and_frequency_slot():
    assert doppler.code_rate('G', 250., 0) == pytest.approx(-250*gps.C/1575.42e6)
    assert doppler.code_rate('R', -250., -4) == pytest.approx(250*gps.C/(1602e6-4*.5625e6))


def test_doppler_gps_selection_preserves_mixed_epoch_framing():
    epoch = b'> 2023 07 06 16 52 30.0000000  0  2\n'
    gps_row = f'G12{24e6:14.3f}  {-50:14.3f}  \n'.encode()
    beidou_row = b'C12\n'
    fields = {'G': ('C1C', 'D1C'), 'C': ('C2I',)}
    rows = list(doppler.observation_epochs(epoch+gps_row+beidou_row, fields, systems=('G',)))
    assert rows == [((2269, 406350.0), {'G': {12: (24e6, -50.)}})]
    with pytest.raises(ValueError, match='complete'):
        list(doppler.observation_epochs(epoch+gps_row, fields, systems=('G',)))


def test_implicit_signal_geometry_recovers_velocity_and_clock_drift():
    receiver = gps.ecef(.9, -.8, 1600.)
    rotation = gps.local_rotation(.9, -.8)
    velocity = rotation.T @ np.array([50., -12., 5.])
    clock_rate = -1.7
    sample = []
    for i, (az, el) in enumerate(((5, 22), (48, 41), (99, 65), (157, 30),
                                  (213, 38), (272, 45), (323, 75)), 1):
        az, el = map(math.radians, (az, el))
        unit = np.array([math.cos(az)*math.cos(el), math.sin(az)*math.cos(el), math.sin(el)])
        position = receiver+22e6*(rotation.T@unit)
        sat_vel = np.array([-1000.+120*i, 2100.-177*i, 891.+50*i])
        sat_clock_rate = i*4e-10

        def distance(s, r):
            return np.linalg.norm(s-r) + gps.OMEGA/gps.C*np.cross(s, r)[2]

        delay = distance(position, receiver)/gps.C

        def measured(t):
            r = receiver+t*velocity
            tau = t
            for _ in range(5):
                h = distance(position+tau*sat_vel, r)
                tau = t+delay-h/gps.C
            return h+clock_rate*t-gps.C*sat_clock_rate*tau

        pseudorange_rate = (measured(.125)-measured(-.125))/.25
        sample.append((i, position, sat_vel, sat_clock_rate, pseudorange_rate))
    sol = doppler.solve_velocity(receiver, sample)
    assert sol['status'] == 'converged'
    assert sol['velocity_neu_mps'] == pytest.approx([50., -12., 5.], abs=1e-6)
    assert sol['clock_drift_mps'] == pytest.approx(clock_rate, abs=1e-6)
    assert doppler.solve_velocity(receiver, sample[:4])['status'] == 'abstain'
