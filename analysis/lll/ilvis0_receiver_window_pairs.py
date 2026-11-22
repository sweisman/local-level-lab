# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare fixed receiver-window decisions on exactly overlapping GPS streams."""

import math
import statistics

from .ilvis0_receiver_overlap import _time_index
from .ilvis0_receiver_support import (
    SupportPolicy, motion_from_enhanced_positions, select_support)


def compare_pair(left_rows, right_rows, *, policy, minimum_matches=100,
                 target_spacing_s=10., edge_margin_s=15.):
    """Use the same target times; never interpolate or inspect IMU data."""
    if (not isinstance(policy, SupportPolicy) or
            type(minimum_matches) is not int or minimum_matches < 2 or
            not math.isfinite(target_spacing_s) or target_spacing_s <= 0 or
            not math.isfinite(edge_margin_s) or edge_margin_s < 0):
        raise ValueError('fixed policy, target grid and match count required')
    left = _time_index(left_rows)
    right = _time_index(right_rows)
    tags = sorted(left.keys() & right.keys())
    if len(tags) < minimum_matches:
        raise ValueError('insufficient exact receiver time matches')
    if tags[-1]-tags[0] < 2*edge_margin_s*1000:
        raise ValueError('common receiver period has no target support')
    motions = [motion_from_enhanced_positions(
        rows, maximum_gap_s=policy.maximum_gap_s)
        for rows in (left_rows, right_rows)]
    count = math.floor((tags[-1]-tags[0])/1000/target_spacing_s -
                       2*edge_margin_s/target_spacing_s + 1e-9) + 1
    targets = [tags[0]/1000+edge_margin_s+i*target_spacing_s
               for i in range(count)]
    decisions = []
    both_accept = both_reject = disagree = same_width = 0
    for target in targets:
        selected = [select_support(
            motion['times_s'], motion['speed_mps'], motion['course_deg'],
            motion['vertical_rate_mps'], target_s=target, policy=policy)
            for motion in motions]
        widths = [row['selected_half_window_s'] for row in selected]
        if widths[0] is None and widths[1] is None:
            both_reject += 1
        elif widths[0] is None or widths[1] is None:
            disagree += 1
        else:
            both_accept += 1
            same_width += widths[0] == widths[1]
        decisions.append(dict(target_gps_s=target,
                              left_half_window_s=widths[0],
                              right_half_window_s=widths[1],
                              left_reasons=[window['reason']
                                            for window in selected[0]['windows']],
                              right_reasons=[window['reason']
                                             for window in selected[1]['windows']]))
    differences = [float(left[tag]['velocity_up_mps'])-
                   float(right[tag]['velocity_up_mps']) for tag in tags]
    if not all(math.isfinite(value) for value in differences):
        raise ValueError('finite paired vertical receiver velocities required')
    offset = statistics.median(differences)
    residual = [value-offset for value in differences]
    return dict(matched_epochs=len(tags), targets=len(targets),
                both_accept=both_accept, both_reject=both_reject,
                disagree=disagree, same_width_when_both_accept=same_width,
                vertical_velocity_difference_median_mps=offset,
                vertical_velocity_difference_mad_mps=statistics.median(
                    abs(value) for value in residual),
                vertical_velocity_difference_rms_mps=math.sqrt(
                    statistics.mean(value*value for value in residual)),
                target_details=decisions, interpolated_measurements=False,
                imu_observations_used=False, fused_navigation_used=False,
                scientific_decision='abstain')
