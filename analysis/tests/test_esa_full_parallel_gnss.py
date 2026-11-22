"""Full-flight matched receiver windows stay distinct and time corrected."""

import pytest


def receiver(time, *, east_m=0.0, speed=0.0):
    return dict(time_s=time, latitude_deg=0.0,
                longitude_deg=east_m / 111319.49079327357,
                height_m=0.0, north_mps=0.0, east_mps=speed, up_mps=0.0)


def test_window_pairs_use_fixed_reference_indices_and_signed_time_offset():
    from lll.esa_full_parallel_gnss import summarize_window_pairs
    reference = [receiver(float(i)) for i in range(8)]
    matched = [(i, receiver(float(i) + .001, east_m=1.001, speed=1.0))
               for i in range(8)]
    result = summarize_window_pairs(reference, matched, [(0, 4), (4, 8)])
    assert [r['matched_epochs'] for r in result] == [4, 4]
    assert result[0]['maximum_absolute_offset_s'] == pytest.approx(.001)
    assert result[0]['raw']['rms'][1] == pytest.approx(1.001, abs=1e-7)
    assert result[0]['time_adjusted']['rms'][1] == pytest.approx(1.0, abs=1e-7)


def test_unmatched_window_is_reported_without_fabricated_agreement():
    from lll.esa_full_parallel_gnss import summarize_window_pairs
    reference = [receiver(float(i)) for i in range(6)]
    result = summarize_window_pairs(reference, [(0, receiver(0.))],
                                    [(0, 3), (3, 6)])
    assert result[0]['matched_epochs'] == 1
    assert result[1]['matched_epochs'] == 0
    assert result[1]['raw'] is None


def test_reused_or_misordered_matches_are_rejected():
    from lll.esa_full_parallel_gnss import summarize_window_pairs
    reference = [receiver(float(i)) for i in range(5)]
    with pytest.raises(ValueError, match='unique ordered'):
        summarize_window_pairs(reference,
                               [(0, receiver(0.)), (0, receiver(0.))],
                               [(0, 5)])
    with pytest.raises(ValueError, match='fixed windows'):
        summarize_window_pairs(reference, [], [(0, 3), (4, 5)])
