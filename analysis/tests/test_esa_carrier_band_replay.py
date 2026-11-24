# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.esa_carrier_band_replay import correction
from lll.esa_carrier_phase_support import GAMMA, L1_WAVELENGTH, L2_WAVELENGTH


def bands(l1_m, l2_m, *, l2_code='2W', flag=0):
    return dict(l1=(l1_m/L1_WAVELENGTH, 0), l2={l2_code: (l2_m/L2_WAVELENGTH, flag)})


def test_common_range_and_fixed_band_offsets_cancel():
    start = bands(4., 8.)
    changing_ionosphere_m = .01
    for common in (0., 1., 22_000.):
        stop = bands(4.+common-changing_ionosphere_m, 8.+common-GAMMA*changing_ionosphere_m)
        assert correction(start, stop) == pytest.approx(changing_ionosphere_m, abs=1e-10)


def test_lock_loss_or_changed_code_does_not_make_a_correction():
    start = bands(4., 8.)
    assert correction(start, bands(4., 8., flag=1)) is None
    assert correction(start, bands(4., 8., l2_code='2X')) is None
