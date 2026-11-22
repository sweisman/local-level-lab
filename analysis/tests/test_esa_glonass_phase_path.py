# SPDX-License-Identifier: AGPL-3.0-or-later
from lll.esa_glonass_phase_path import common_ephemeris
from lll.glonass_code import Ephemeris


def test_one_healthy_channel_bound_ephemeris_covers_both_transmissions():
    def state(epoch, channel=-4, unhealthy=0):
        return Ephemeris(1, 2269, epoch, (20e6, 10e6, 7e6), (0., 2e3, 0.),
                         (0., 0., 0.), 0., 0., unhealthy, channel)

    before, after = state(1000), state(2799.5)
    candidate = common_ephemeris([before, after, state(1900, -3), state(1900, unhealthy=1)],
                                 2269, (1899.6, 1900.1), -4)
    assert candidate == after
    assert common_ephemeris([before], 2269, (1899.6, 1900.1), -4) is None
