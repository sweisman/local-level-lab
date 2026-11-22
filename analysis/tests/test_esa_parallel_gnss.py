"""Parallel receiver comparison uses only time-matched training data."""

import pytest


def test_time_match_is_unique_and_does_not_interpolate():
    from lll.esa_parallel_gnss import match_times

    targets = [{'time_s': float(t)} for t in (1, 2, 3, 4)]
    source = [{'time_s': t} for t in (.8, 1.001, 1.2, 2.003, 3.0,
                                     3.002, 3.8, 4.0)]
    matched = match_times(targets, source, tolerance_s=.002)
    assert [x[0] for x in matched] == [0, 2, 3]
    assert [x[1]['time_s'] for x in matched] == [1.001, 3.0, 4.0]


def test_guard_never_yields_later_science_row():
    from lll.esa_parallel_gnss import earlier_lines

    def line(time):
        fields = ['00000001'] + ['0']*25 + [str(time), '2269',
                                         '6/07/2023', '12:00:00']
        return ' '.join(fields)+'\n'
    values = list(earlier_lines(iter(['header\n', line(9.0),
                                     line(10.5), line(11.0)]),
                                last_training_s=10.0,
                                tolerance_s=.002))
    assert values == ['header\n', line(9.0)]


def test_relative_neu_has_correct_sign_and_rejects_bad_coordinates():
    from lll.esa_parallel_gnss import relative_neu

    first = dict(latitude_deg=60.0, longitude_deg=10.0, height_m=100.0)
    other = dict(latitude_deg=60.00001, longitude_deg=10.00001,
                 height_m=100.25)
    north, east, up = relative_neu(first, other)
    assert 1.0 < north < 1.2
    assert .5 < east < .6
    assert up == pytest.approx(.25)
    with pytest.raises(ValueError, match='finite'):
        relative_neu(first, dict(latitude_deg=91, longitude_deg=10,
                                 height_m=100))
