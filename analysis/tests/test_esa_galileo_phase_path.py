# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.esa_galileo_phase_path import E1, E5B, C, carrier_change, check_clock_samples


def test_phase_combination_removes_first_order_ionosphere():
    geometric = 33.0
    iono_e1 = .01
    iono_e5b = iono_e1*(E1/E5B)**2
    first = (28e6, (200., 0), (300., 0), None)
    second = (28e6+geometric, (200+(geometric-iono_e1)*E1/C, 0),
              (300+(geometric-iono_e5b)*E5B/C, 0), None)
    assert carrier_change(first, second, doppler=False) == pytest.approx(geometric)
    assert carrier_change(first, second, doppler=True) is None
    assert carrier_change(first, second[:2]+((second[2][0], 1), None), doppler=False) is None


def test_clocks_must_agree_at_every_shared_tracking_knot():
    clocks = {8: {388200: 1e-5, 388500: 1e-5}}
    reference = {8: {388200: 1e-5+3e-13, 388500: 1e-5-4e-13}}
    assert check_clock_samples(clocks, reference, {8})['checked'] == 2
    clocks[8][388500] += 2e-12
    with pytest.raises(ValueError, match='clock'):
        check_clock_samples(clocks, reference, {8})
