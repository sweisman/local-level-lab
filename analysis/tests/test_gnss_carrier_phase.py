# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll.gnss_carrier_phase import L1_WAVELENGTH_M, matched_phase, recover_displacement
from lll.gnss_position import C, OMEGA


def test_carrier_phase_recovers_displacement_and_clock_change():
    anchor = np.array([6_378_737., 0., 0.])
    displacement = np.array([4., 220., -80.])
    motion = np.array([[1900., -1700., 800.]])
    directions = np.array([[.3, .9, 0.], [.7, -.6, .6], [.6, .4, -.5],
                           [.95, .2, .2], [.42, -.8, -.45], [.25, .3, .9]])
    start = anchor + 22e6*directions
    end = start+motion
    clock_change = 1400.
    satellite_clock = np.linspace(-1e-4, 1e-4, len(start))
    clock_increment = np.linspace(-3e-9, 1e-9, len(start))
    first_ion = np.arange(1., len(start)+1.)
    end_ion = first_ion+.2

    def modeled_ranges(satellite, receiver, clock, ion):
        return (np.linalg.norm(satellite-receiver, axis=1)
                + OMEGA/C*(satellite[:, 0]*receiver[1]-satellite[:, 1]*receiver[0])
                - C*clock - ion)

    ambiguity = 1e7 + np.arange(len(start))
    phase_a = ambiguity-modeled_ranges(start, anchor, satellite_clock, first_ion)/L1_WAVELENGTH_M
    phase_b = ambiguity-(modeled_ranges(end, anchor+displacement,
        satellite_clock+clock_increment, end_ion)+clock_change)/L1_WAVELENGTH_M
    result = recover_displacement(anchor, start, end, satellite_clock, satellite_clock+clock_increment,
        first_ion, end_ion, np.zeros(len(start)), np.zeros(len(start)), phase_a, phase_b, sign=-1)
    assert result['status']=='converged'
    np.testing.assert_allclose(result['displacement_ecef_m'], displacement, atol=2e-7, rtol=0)
    assert abs(result['receiver_clock_change_m']-clock_change) < 2e-7


def test_carrier_pairs_require_continuous_unambiguous_l1_tracking():
    def record(*rows):
        satellites = []
        for prn, slip_counter, half_cycle in rows:
            satellites.append(dict(system=0, antenna=0, sv_id=prn, flags=[0],
                signals=[dict(band=0, track_type=0, phase_loaded=True, range_loaded=True,
                              phase_cycles=1234., pseudorange_m=24e6, slip_counter=slip_counter,
                              half_cycle=half_cycle)]))
        return dict(format='RT27', satellites=satellites)

    a = record((1, 12, False), (2, 0, False), (3, 0, False), (4, 0, False))
    b = record((1, 12, False), (2, 1, False), (3, 0, True), (5, 0, False))
    assert set(matched_phase(a, b)) == {1}
