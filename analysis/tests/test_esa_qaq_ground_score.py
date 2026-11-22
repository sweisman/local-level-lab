# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.esa_carrier_phase_support import L1_WAVELENGTH, L2_WAVELENGTH
from lll.esa_qaq_ground_score import reference_residual


def test_qaq_compares_only_the_frozen_dual_frequency_arc():
    signals = dict(code_m=2.3e7, doppler=30.25/L1_WAVELENGTH, l1=(1e8, 0), l2={'2W': (8e7, 0)})
    first = dict(seconds=0., week=2269, satellites={1: signals, 2: signals})
    last = dict(first, seconds=1., satellites={
        1: dict(signals, l1=(1e8-30.25/L1_WAVELENGTH, 0), l2={'2W': (8e7-30.25/L2_WAVELENGTH, 0)}),
        2: dict(signals, l2={'2X': (8e7, 0)})})

    def model(a, b, prns, codes):
        assert prns == [1] and codes == [[2.3e7], [2.3e7]]
        return {1: -30.}

    assert reference_residual(first, last, [1, 2], {1, 2}, model) == pytest.approx({1: -.25}, abs=1e-8)
    assert reference_residual(first, last, [1, 2], {2}, model) == {}
