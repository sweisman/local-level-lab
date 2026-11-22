"""Conservative receiver-only support decisions under stated motion errors."""

import pytest

from lll.ilvis0_receiver_support import SupportPolicy, select_support
from lll.ilvis0_support_stability import bound_support


POLICY = SupportPolicy(
    half_windows_s=(2., 4.), maximum_gap_s=1.1, minimum_samples=5,
    minimum_speed_mps=100., maximum_speed_mps=300.,
    maximum_course_span_deg=5., maximum_speed_span_mps=10.,
    maximum_vertical_rate_span_mps=1.)


def example(*, vertical=None, course=None):
    times = tuple(float(i) for i in range(11))
    motion = dict(times_s=times, speed_mps=(200.,)*11,
                  course_deg=course or (10.,)*11,
                  vertical_rate_mps=vertical or (0.,)*11)
    selected = select_support(times, motion['speed_mps'], motion['course_deg'],
                              motion['vertical_rate_mps'], target_s=5.,
                              policy=POLICY)
    return motion, selected


def test_zero_and_small_errors_preserve_selected_longest_window():
    motion, selected = example()
    result = bound_support(motion, selected, policy=POLICY,
                           speed_error_mps=.1, course_error_deg=.05,
                           vertical_error_mps=.1)
    assert result['candidate_status'] == ['certain_accept', 'certain_accept']
    assert result['selected_half_window_stable'] is True
    assert result['abstention_stable'] is False


def test_vertical_threshold_becomes_uncertain_without_claiming_a_flip():
    vertical = (0.,)*3 + (.98,)*5 + (0.,)*3
    motion, selected = example(vertical=vertical)
    result = bound_support(motion, selected, policy=POLICY,
                           speed_error_mps=0., course_error_deg=0.,
                           vertical_error_mps=.05)
    assert selected['selected_half_window_s'] == 4.
    assert result['candidate_status'] == ['certain_accept', 'uncertain']
    assert result['selected_half_window_stable'] is False


def test_certain_rejection_survives_bounded_error():
    vertical = (0.,)*3 + (1.5,)*5 + (0.,)*3
    motion, selected = example(vertical=vertical)
    result = bound_support(motion, selected, policy=POLICY,
                           speed_error_mps=0., course_error_deg=0.,
                           vertical_error_mps=.1)
    assert result['candidate_status'] == ['certain_accept', 'certain_reject']
    assert result['selected_half_window_stable'] is True


def test_course_unwrap_branch_does_not_receive_false_certificate():
    course = (10.,)*4 + (190.,)*7
    motion, selected = example(course=course)
    result = bound_support(motion, selected, policy=POLICY,
                           speed_error_mps=0., course_error_deg=1.,
                           vertical_error_mps=0.)
    assert result['candidate_status'][1] == 'uncertain'


def test_negative_or_nonfinite_errors_rejected():
    motion, selected = example()
    for bad in (-.1, float('nan')):
        with pytest.raises(ValueError):
            bound_support(motion, selected, policy=POLICY,
                          speed_error_mps=bad, course_error_deg=0.,
                          vertical_error_mps=0.)
