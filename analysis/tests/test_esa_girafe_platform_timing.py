# SPDX-License-Identifier: AGPL-3.0-or-later
"""Controls for matching one clock and predicting two held-out alignments."""

import numpy as np
import pytest

from lll.esa_girafe_platform_timing import alignment_scores, locate_clock, tenth_second_force
from lll.esa_girafe_platform_component_timing import candidate_offset


def signal(seed, length=110):
    return 9.8+np.cumsum(np.random.default_rng(seed).normal(0., .002, length))


def test_unique_anchor_recovers_clock_and_force_amplitude():
    platform = signal(20)
    reference = signal(21, 850)
    reference[120:230] = 1.8*platform-7.
    ref_times = 38_500.05+.1*np.arange(len(reference))
    platform_times = 512.05+.1*np.arange(len(platform))
    result = locate_clock(ref_times, reference, platform_times, platform)
    assert result['passes']
    assert result['best_offset_s'] == pytest.approx(ref_times[120]-platform_times[0])
    assert result['best_correlation'] == pytest.approx(1.)
    assert result['amplitude'] == pytest.approx(1.8)


def test_a_repeated_fingerprint_does_not_lock_the_clock():
    platform = signal(3)
    reference = signal(7, 850)
    reference[120:230] = platform
    reference[610:720] = platform
    result = locate_clock(0.1*np.arange(len(reference)), reference,
                          0.1*np.arange(len(platform)), platform)
    assert result['best_correlation'] == pytest.approx(1.)
    assert result['alternate_correlation'] == pytest.approx(1.)
    assert not result['passes']


def test_a_strong_holdout_match_on_a_different_clock_fails():
    platform = signal(34)
    reference = signal(81, 910)
    reference[500:610] = platform
    rt = 39_000.+.1*np.arange(len(reference))
    pt = 4_200.+.1*np.arange(len(platform))
    offset = rt[500]-pt[0]
    assert locate_clock(rt, reference, pt, platform, locked_offset=offset)['passes']
    changed = locate_clock(rt, reference, pt, platform, locked_offset=offset+.5)
    assert changed['best_correlation'] == pytest.approx(1.)
    assert changed['independent_offset_change_s'] == pytest.approx(-.5)
    assert not changed['passes']


def test_force_grid_keeps_only_complete_supports_and_original_units():
    time = .02+np.arange(5_383)/1024.
    rows = np.column_stack((time, np.zeros((len(time), 2)), np.full(len(time), -9.8)))
    centers, magnitudes = tenth_second_force(rows)
    assert centers[0] == pytest.approx(.15)
    assert centers[-1] == pytest.approx(5.15)
    np.testing.assert_allclose(magnitudes, 9.8, atol=1e-12, rtol=0.)


def test_candidate_clock_selection_only_tolerates_representation_rounding():
    parent = dict(coarse_clock_passed=False, ranges=[
        dict(status='scored', alignment=dict(best_offset_s=offset))
        for offset in (50431.96739992, 38474.267399920005, 38474.26739992)])
    assert candidate_offset(parent) == 38474.267399920005
    parent['ranges'][2]['alignment']['best_offset_s'] += .1
    with pytest.raises(ValueError, match='equal candidate offsets'):
        candidate_offset(parent)


def test_a_remote_large_excursion_does_not_create_a_peak_in_a_quiet_window():
    platform = signal(41)
    reference = np.zeros(1200)
    reference[12] = 1e8
    reference[620:730] = platform-9.8
    scores, _ = alignment_scores(reference, platform)
    assert np.isneginf(scores[300])
    assert np.argmax(scores) == 620
    assert scores[620] == pytest.approx(1., abs=1e-12)


def test_shared_width_compares_only_complete_centered_differences():
    from lll.esa_girafe_platform_vertical_response import force_response

    platform = signal(18)
    reference = 2.*platform+3.
    width = 7
    direct = np.diff(np.convolve(platform, np.ones(width)/width, mode='valid'))
    score = force_response(platform, reference, width)
    assert score['paired_differences'] == len(direct)
    assert score['correlation'] == pytest.approx(1.)
    assert score['platform_rms'] == pytest.approx(direct.std())
    assert score['reference_rms'] == pytest.approx(2.*direct.std())
    assert score['difference_rms'] == pytest.approx(direct.std())


def test_held_force_cell_means_use_elapsed_time():
    from lll.esa_girafe_platform_timing import held_cell_means

    time = [0., .2, .7, 1.]
    force = [[1.], [3.], [5.]]
    values = held_cell_means(time, force, [.1, .4, .8])
    np.testing.assert_allclose(values[:, 0], [7./3., 3.5])
    with pytest.raises(ValueError, match='bracket'):
        held_cell_means(time, force, [.1, 1.1])


@pytest.mark.parametrize('delay, passes', [(0, True), (4, False)])
def test_independent_force_requires_the_locked_clock(delay, passes):
    from lll.esa_girafe_platform_imar_force import lag_scores

    platform = signal(27)
    reference = signal(28, len(platform)+40)
    start = 20+delay
    reference[start:start+len(platform)] = 1.2*platform-1.5
    score = lag_scores(platform, reference)
    assert len(score['scores']) == 41
    assert score['best']['lag_tenths_s'] == delay
    assert score['best']['correlation'] == pytest.approx(1.)
    assert bool(score['passes']) is passes
