# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.esa_carrier_clock_step import normalized_pair
from lll.esa_carrier_phase_support import F1, F2, L1_WAVELENGTH, L2_WAVELENGTH


def test_one_millisecond_clock_change_preserves_motion_on_both_bands():
    elapsed = .4990012
    travel = 120. * elapsed
    first = dict(l1=(1e7, 0), l2={'2W': (2e7, 0)}, doppler=-120. / L1_WAVELENGTH, code_m=22e6)
    second = first | dict(
        l1=(1e7 + F1 * .001 + travel / L1_WAVELENGTH, 0),
        l2={'2W': (2e7 + F2 * .001 + travel / L2_WAVELENGTH, 0)},
    )
    pair, reason = normalized_pair(first, second, .001, elapsed)
    assert reason is None
    assert pair['ionosphere_free_displacement_m'] == pytest.approx(travel, abs=2e-9)
    second['l2']['2W'] = (second['l2']['2W'][0] + 1, 0)
    assert normalized_pair(first, second, .001, elapsed)[1] == 'dual_phase'
