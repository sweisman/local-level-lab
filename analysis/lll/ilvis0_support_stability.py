"""Conservative receiver-window decisions under declared motion-error ranges.

The bounds apply independently to each reported motion value. They do not
estimate the receiver's actual errors or alter a saved support decision.
"""

from dataclasses import asdict
import json
import math

from .ilvis0_receiver_support import SupportPolicy, select_support


def bound_support(motion, selected, *, policy, speed_error_mps,
                  course_error_deg, vertical_error_mps):
    errors = (speed_error_mps, course_error_deg, vertical_error_mps)
    if (not isinstance(policy, SupportPolicy) or
            any(isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or value < 0 for value in errors)):
        raise ValueError('nonnegative finite motion-error bounds required')
    if json.dumps(selected.get('policy'), sort_keys=True) != json.dumps(
            asdict(policy), sort_keys=True):
        raise ValueError('support policy differs from bounded policy')
    expected = select_support(
        motion['times_s'], motion['speed_mps'], motion['course_deg'],
        motion['vertical_rate_mps'], target_s=selected['target_s'],
        policy=policy)
    if json.dumps(selected, sort_keys=True) != json.dumps(expected, sort_keys=True):
        raise ValueError('original receiver support differs from supplied motion')

    statuses = []
    for window in selected['windows']:
        if window['reason'] in ('incomplete_support', 'sample_count', 'gap'):
            statuses.append('certain_reject')
            continue
        first, last = window['first_index'], window['last_index'] + 1
        speed = motion['speed_mps'][first:last]
        course = motion['course_deg'][first:last]
        branch_stable = course_error_deg == 0 or all(
            abs((right-left+180.) % 360. - 180.) < 180.-2*course_error_deg
            for left, right in zip(course, course[1:]))
        speed_span = window['speed_span_mps']
        vertical_span = window['vertical_rate_span_mps']
        course_span = window['course_span_deg']
        certainly_accept = (
            min(speed)-speed_error_mps >= policy.minimum_speed_mps and
            max(speed)+speed_error_mps <= policy.maximum_speed_mps and
            speed_span+2*speed_error_mps <= policy.maximum_speed_span_mps and
            vertical_span+2*vertical_error_mps <=
            policy.maximum_vertical_rate_span_mps and
            branch_stable and
            course_span+2*course_error_deg <= policy.maximum_course_span_deg)
        certainly_reject = (
            min(speed)+speed_error_mps < policy.minimum_speed_mps or
            max(speed)-speed_error_mps > policy.maximum_speed_mps or
            speed_span-2*speed_error_mps > policy.maximum_speed_span_mps or
            vertical_span-2*vertical_error_mps >
            policy.maximum_vertical_rate_span_mps or
            (branch_stable and course_span-2*course_error_deg >
             policy.maximum_course_span_deg))
        statuses.append('certain_accept' if certainly_accept else
                        'certain_reject' if certainly_reject else 'uncertain')

    chosen = selected['selected_half_window_s']
    stable = (chosen is not None and all(
        status == ('certain_accept' if window['half_window_s'] == chosen
                   else 'certain_reject')
        for window, status in zip(selected['windows'], statuses)
        if window['half_window_s'] >= chosen))
    abstention = chosen is None and all(
        status == 'certain_reject' for status in statuses)
    return dict(candidate_status=statuses,
                selected_half_window_stable=stable,
                abstention_stable=abstention,
                assumed_speed_error_mps=float(speed_error_mps),
                assumed_course_error_deg=float(course_error_deg),
                assumed_vertical_error_mps=float(vertical_error_mps),
                scientific_decision='abstain')
