# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.esa_nuuk_carrier_screen import inspect_satellite, doppler_pattern
from lll.esa_carrier_phase_support import L1_WAVELENGTH, L2_WAVELENGTH


def obs(travel=0., doppler=0., lock=0, extra=0.):
    return dict(code_m=22e6, l1=(travel / L1_WAVELENGTH, lock), doppler=doppler,
                l2={'2W': ((travel + extra) / L2_WAVELENGTH, 0)})


def test_diagnostic_uses_signed_doppler_and_same_rejection_order():
    assert inspect_satellite(obs(), obs(extra=.1, doppler=.8)) == ('l1_doppler', .4)
    assert inspect_satellite(obs(), obs(extra=.1)) == ('dual_phase', 0.)
    assert inspect_satellite(obs(), obs(lock=1, doppler=.8)) == ('loss_of_lock', None)
    assert inspect_satellite(obs(), obs(doppler=-.6)) == ('passes', -.3)


def test_doppler_pattern_preserves_common_offset_and_dispersion():
    result = doppler_pattern([.49, .5, .51, .5, .5])
    assert result['median_cycles'] == .5
    assert result['centered_rms_cycles'] == pytest.approx((.0002/5)**.5)
    assert doppler_pattern([.5]*4) is None
