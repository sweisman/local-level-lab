# SPDX-License-Identifier: AGPL-3.0-or-later
from lll.esa_carrier_phase_support import L1_WAVELENGTH, L2_WAVELENGTH
from lll.esa_nuuk_clock_aware import clock_aware_residual


def endpoints(satellites):
    first = {p: dict(code_m=22e6, l1=(0., 0), l2={'2W': (0., 0)}, doppler=.6) for p in satellites}
    last = {p: dict(first[p]) for p in satellites}
    return dict(satellites=first), dict(satellites=last)


def no_range_change(first, last, satellites, codes):
    return dict.fromkeys(satellites, 0.)


def test_common_doppler_shift_keeps_original_phase_but_satellite_slip_is_rejected():
    prns = set(range(1, 10))
    first, last = endpoints(prns)
    last['satellites'][9].update(l1=(1.2, 0), l2={'2W': (1.2*L1_WAVELENGTH/L2_WAVELENGTH, 0)})
    last['satellites'][8]['l2'] = {'2W': (1., 0)}
    last['satellites'][7]['l1'] = (0., 1)
    assert clock_aware_residual(first, last, prns, prns, no_range_change) == dict.fromkeys(range(1, 7), 0.)
    assert last['satellites'][1]['doppler'] == .6


def test_too_few_peers_leaves_original_doppler_check_in_place():
    prns = set(range(1, 6))
    first, last = endpoints(prns)
    assert clock_aware_residual(first, last, prns, prns, no_range_change) == {}
