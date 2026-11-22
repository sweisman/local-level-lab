# SPDX-License-Identifier: AGPL-3.0-or-later
import math

import numpy as np
import pytest
from scipy.integrate import solve_ivp

from lll import glonass_code as glo
from lll import gnss_position as gps


def test_navigation_decodes_utc_clock_and_si_axes():
    version = f"{'     3.04           N: GNSS NAV DATA    M: MIXED':60}RINEX VERSION / TYPE"
    leap = f"{'    18    18  1929     7':60}LEAP SECONDS"
    end = f"{'':60}END OF HEADER"
    state = [
        'R01 2023 07 05 23 45 00 6.080884486437E-05-1.250000000000E-09 3.438000000000E+05',
        '    -8.004302734375E+03 2.888936996460E+00-4.656612873077E-09 0.000000000000E+00',
        '    -1.140609863281E+04 4.611644744873E-01-1.862645149231E-09-4.000000000000E+00',
        '     2.136384033203E+04 1.329985618591E+00-0.000000000000E+00 0.000000000000E+00',
    ]
    (record,) = glo.navigation('\n'.join([version, leap, end, *state]))
    assert (record.prn, record.week, record.epoch, record.channel) == (1, 2269, 344718., -4)
    assert record.position[0] == pytest.approx(-8004302.734375)
    assert record.velocity[1] == pytest.approx(461.1644744873)
    assert record.acceleration[1] == pytest.approx(-1.862645149231e-6)
    assert record.clock(60.) == pytest.approx(6.080884486437e-5-60*1.25e-9)
    with pytest.raises(ValueError, match='truncated'):
        glo.navigation('\n'.join([version, leap, end, *state[:-1]]))


@pytest.mark.parametrize('duration', [-900., 0., 900.])
def test_orbit_matches_independent_inertial_propagation(duration):
    mu, radius, j2, rate = 3.9860044e14, 6378136., .0010826257, 7.292115e-5
    r = np.array([-8004302.734, -11406098.63, 21363840.33])
    v = np.array([2888.937, 461.164, 1329.986])
    p = np.array([-4.6566e-6, -1.8626e-6, 0.])
    spin = np.array([0., 0., rate])

    def rotation(t):
        s, c = math.sin(rate*t), math.cos(rate*t)
        return np.array([[c, -s, 0.], [s, c, 0.], [0., 0., 1.]])

    def equation(t, state):
        r_eci = state[:3]
        dist = np.linalg.norm(r_eci)
        direction = r_eci/dist
        pole = np.array([0., 0., direction[2]])
        correction = 1.5*j2*(radius/dist)**2
        force = -mu/dist**2*((1+correction*(1-5*direction[2]**2))*direction
                             + 2*correction*pole)
        return np.r_[state[3:], force+rotation(t)@p]

    initial = np.r_[r, v+np.cross(spin, r)]
    solution = solve_ivp(equation, (0, duration), initial, method='DOP853', rtol=1e-13, atol=1e-10)
    assert solution.success
    expected = rotation(duration).T@solution.y[:3, -1]
    assert glo.propagate(r, v, p, duration) == pytest.approx(expected, abs=.02)


def test_position_solve_recovers_known_geometry_and_clock():
    lat, lon, height = map(float, (.9, -.8, 1700))
    target = gps.ecef(lat, lon, height)
    ecef_to_neu = gps.local_rotation(lat, lon)
    receiver_clock = 800.
    selected = []
    for prn, (az, elevation) in enumerate(((0, 25), (60, 45), (115, 68), (165, 30),
                                           (220, 55), (260, 36), (307, 77)), 1):
        a, e = map(math.radians, (az, elevation))
        direction = np.array([math.cos(e)*math.cos(a), math.cos(e)*math.sin(a), math.sin(e)])
        sat = target + 21e6*(ecef_to_neu.T@direction)
        clock = prn*1e-5
        sagnac = gps.OMEGA/gps.C*(sat[0]*target[1]-sat[1]*target[0])
        measured = 21e6+sagnac+receiver_clock-gps.C*clock+gps.troposphere(lat, height, e)
        selected.append(dict(sv_id=prn, satellite_ecef_m=sat, satellite_clock_s=clock,
                             observed_corrected_code_m=measured))
    solved = glo.solve(selected, 10000., 'dual_frequency', None, target+[500, -700, 400])
    assert solved['status'] == 'converged'
    assert solved['ecef_m'] == pytest.approx(target, abs=1e-5)
    assert solved['receiver_clock_m'] == pytest.approx(receiver_clock, abs=1e-5)
    assert glo.solve(selected[:4], 10000., 'dual_frequency', None, target)['status'] == 'abstain'
