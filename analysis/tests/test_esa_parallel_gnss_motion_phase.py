"""Receiver-speed phases partition the late matched PPP points once."""

import pytest


def row(time, speed, up=0.0, east=0.0):
    return dict(time_s=time, latitude_deg=0.0,
                longitude_deg=east / 111319.49079327357, height_m=0.0,
                north_mps=0.0, east_mps=speed, up_mps=up)


def test_phase_rule_covers_boundary_and_vertical_motion():
    from lll.esa_parallel_gnss_motion_phase import phase
    assert phase(row(0., 50.)) == 'fast'
    assert phase(row(0., .5, up=.2)) == 'low_speed'
    assert phase(row(0., .5, up=.201)) == 'transition'
    assert phase(row(0., 49.9)) == 'transition'


def test_every_match_is_partitioned_and_time_corrected():
    from lll.esa_parallel_gnss_motion_phase import summarize_phase_pairs
    reference = [row(0., 60.), row(1., 10.), row(2., 0.)]
    matched = [(i, row(float(i) + .001, 1., east=1.001)) for i in range(3)]
    result = summarize_phase_pairs(reference, matched, start=0, end=3)
    assert [result[key]['matched_epochs'] for key in
            ('fast', 'transition', 'low_speed')] == [1, 1, 1]
    assert result['fast']['time_adjusted']['rms'][1] == pytest.approx(1.0, abs=1e-7)


def test_out_of_window_or_reused_match_is_rejected():
    from lll.esa_parallel_gnss_motion_phase import summarize_phase_pairs
    reference = [row(float(i), 60.) for i in range(3)]
    with pytest.raises(ValueError, match='window'):
        summarize_phase_pairs(reference, [(0, row(0., 0.))], start=1, end=3)
    with pytest.raises(ValueError, match='unique'):
        summarize_phase_pairs(reference, [(1, row(1., 0.)),
                                          (1, row(1., 0.))], start=1, end=3)
