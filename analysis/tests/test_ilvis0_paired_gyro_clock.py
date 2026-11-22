# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll.ilvis0_paired_gyro_clock import PacketRates, compare, split_windows


def test_window_sums_signed_packets_and_ignores_partial_edges():
    edges = np.array([0., .05, .15, .25, .35, .40])
    dt = np.diff(edges)
    increments = np.array([[50, 0, 0], [2, -1, 0], [-2, -1, 0], [30, 0, 0], [50, 0, 0]])
    rates = PacketRates(edges[1:], dt, increments)
    mean, coverage = rates.windows(np.array([.04]), .22)
    np.testing.assert_allclose(mean, [[0., -10., 0.]])
    np.testing.assert_allclose(coverage, [.2/.22])


def test_shifted_windows_cannot_cross_split_or_overlap_end():
    earlier, later = split_windows(np.arange(10.), 1., 10., .30)
    assert np.flatnonzero(earlier).tolist() == [1, 2, 3]
    assert np.flatnonzero(later).tolist() == [6, 7, 8]


def stream(delay, later_delay=None):
    # Same angular motion up to fixed mounting, offset and clock delay.
    dt = .005
    ends = dt*np.arange(1, 32001)
    time = ends-dt/2.
    delay = np.where(time < 80., delay, delay if later_delay is None else later_delay)
    u = time-delay
    rates = np.column_stack((np.sin(u*.88), .7*np.cos(u*.42), .4*np.sin(u*1.29)))
    return PacketRates(ends, np.full(len(ends), dt), rates*dt)


def test_align_from_earlier_half_only_and_recover_delay():
    left = stream(0.)
    stable = compare(left, stream(.10), duration=160., width=.25, reserve=lambda: None)
    interrupted = compare(left, stream(.10, later_delay=-.10), duration=160., width=.25, reserve=lambda: None)
    assert stable['shift_s'] == interrupted['shift_s'] == .10
    assert stable['earlier_curve'] == interrupted['earlier_curve']
    assert stable['later']['shifted']['vector_rms_dph'] < 1e-10
    assert interrupted['later']['shifted']['vector_rms_dph'] > interrupted['later']['zero']['vector_rms_dph']
