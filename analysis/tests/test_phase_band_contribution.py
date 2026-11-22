# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np

from lll.esa_carrier_phase_support import GAMMA, L1_WAVELENGTH, L2_WAVELENGTH
from lll.phase_band_contribution import bands


def test_band_decomposition_recovers_both_paths_despite_distinct_clock_terms():
    design = np.array([[1., 0., 0.], [0., 1., 0.], [0., 0., 1.], [-1., 0., 0.], [0., -1., 0.]])
    l1, l2 = np.array([.04, -.07, .18]), np.array([.19, .37, -.21])
    combined = (GAMMA*l1-l2)/(GAMMA-1.)
    phase_air = np.zeros((5, 2))
    phase_base = np.ones_like(phase_air)*1e6
    base_delta = 1290.
    air_delta = (np.column_stack((design@l1+2.2, design@l2+5.7))+base_delta)/[L1_WAVELENGTH, L2_WAVELENGTH]
    base_delta = np.array([base_delta/L1_WAVELENGTH, base_delta/L2_WAVELENGTH])
    result = bands(phase_air+air_delta, phase_base+base_delta, phase_air, phase_base, combined, design)
    np.testing.assert_allclose(result['l1_position'], l1, atol=1e-10)
    np.testing.assert_allclose(result['l2_position'], l2, atol=1e-10)
