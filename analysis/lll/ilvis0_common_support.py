# SPDX-License-Identifier: AGPL-3.0-or-later
"""Whole-packet time support under an explicit integration/latency hypothesis."""
import numpy as np


def match_support(receiver_times_s, packet_intervals_s, window_s, *,
                  time_offset_bounds_s, maximum_receiver_gap_s, integration_hypothesis):
    """Plan common support without resampling or examining measured values.

    packet_intervals_s are EXPLICIT integration intervals on the packet clock,
    not intervals inferred here from header timestamps. The caller must name
    its physical integration hypothesis. A single unknown common time offset
    maps this clock into receiver time. This offset moves support, not duration.
    Frequency error, varying latency and uncertain periods need separate
    hypotheses/envelopes; this function does not silently cover them.

    Retain a whole packet only if every allowed offset places it inside the
    requested receiver-clock window. Report ambiguous boundary packets and
    internal gaps. Subsequent force predictions must average over the retained
    interval UNION at the SAME offset, not over the window or its convex hull.
    Acceptance establishes time support only, not physical or statistical fit.
    """
    receiver = np.asarray(receiver_times_s, float)
    intervals = np.asarray(packet_intervals_s, float)
    window = np.asarray(window_s, float)
    offset = np.asarray(time_offset_bounds_s, float)
    if (receiver.ndim != 1 or len(receiver) < 2 or not np.all(np.isfinite(receiver))
            or np.any(np.diff(receiver) <= 0.)):
        raise ValueError('at least two strictly increasing finite receiver times required')
    if (intervals.ndim != 2 or intervals.shape[1] != 2 or not len(intervals)
            or not np.all(np.isfinite(intervals)) or np.any(intervals[:, 1] <= intervals[:, 0])
            or np.any(intervals[1:, 0] < intervals[:-1, 1])):
        raise ValueError('nonempty positive ordered disjoint integration intervals required')
    if window.shape != (2,) or not np.all(np.isfinite(window)) or window[1] <= window[0]:
        raise ValueError('finite positive-duration comparison window required')
    if offset.shape != (2,) or not np.all(np.isfinite(offset)) or offset[1] < offset[0]:
        raise ValueError('finite ordered common time-offset bounds required')
    if not np.isfinite(maximum_receiver_gap_s) or maximum_receiver_gap_s <= 0.:
        raise ValueError('positive finite maximum receiver gap required')
    if not isinstance(integration_hypothesis, str) or not integration_hypothesis.strip():
        raise ValueError('explicit integration-period/time-tag hypothesis required')
    with np.errstate(over='ignore'):
        envelope = intervals + offset
    if not np.all(np.isfinite(envelope)):
        raise ValueError('time support exceeds finite range')
    retained = (envelope[:, 0] >= window[0]) & (envelope[:, 1] <= window[1])
    possible = (envelope[:, 1] > window[0]) & (envelope[:, 0] < window[1])
    indices = np.flatnonzero(retained)
    selected = intervals[indices].copy()
    gaps = np.empty((0, 2), float)
    if len(selected) > 1:
        separated = selected[1:, 0] > selected[:-1, 1]
        gaps = np.column_stack((selected[:-1, 1][separated], selected[1:, 0][separated]))
    duration = float(np.sum(selected[:, 1] - selected[:, 0]))
    if not np.isfinite(duration):
        raise ValueError('total integration duration exceeds finite range')
    receiver_indices = np.array([], dtype=int)
    receiver_gaps = np.empty((0, 2), float)
    reason = 'supported'
    if window[0] < receiver[0] or window[1] > receiver[-1]:
        reason = 'receiver_coverage'
    else:
        left = int(np.searchsorted(receiver, window[0], side='right') - 1)
        right = int(np.searchsorted(receiver, window[1], side='left'))
        receiver_indices = np.arange(left, right + 1)
        support = receiver[receiver_indices]
        large = np.diff(support) > maximum_receiver_gap_s
        receiver_gaps = np.column_stack((support[:-1][large], support[1:][large]))
        if len(receiver_gaps):
            reason = 'receiver_gap'
        elif not len(indices):
            reason = 'no_guaranteed_whole_packets'
    return dict(accepted=reason == 'supported', reason=reason,
        packet_indices=indices, nominal_intervals_s=selected,
        possible_support_s=envelope[indices].copy(),
        boundary_ambiguous_indices=np.flatnonzero(possible & ~retained),
        outside_window_indices=np.flatnonzero(~possible),
        receiver_indices=receiver_indices, receiver_gap_intervals_s=receiver_gaps,
        nominal_gap_intervals_s=gaps, continuous_packet_coverage=bool(len(indices) and not len(gaps)),
        total_integration_duration_s=duration, window_s=window.copy(),
        time_offset_bounds_s=offset.copy(), offset_is_common=True,
        integration_hypothesis=integration_hypothesis,
        aggregation_support='retained whole-packet union only',
        interpolated_measurements=False, timing_calibrated=False,
        scientific_decision='abstain')


def bound_prediction_average(support, midpoint_magnitudes_mps2, *, reference_offset_s,
                             maximum_magnitude_rate_mps3):
    """Bound a scalar prediction averaged on the SAME retained interval union.

    Values must be model magnitudes at each nominal interval midpoint plus the
    reference offset. Assume |dq/dt| <= L over each packet's full swept support
    for every allowed common offset. This is an explicit physical/trajectory
    assumption, not a rate estimated from excluded gyros or a fitted residual.

    Midpoint integration error <= L * sum(T_i**2)/(4*sum(T_i)); moving every
    interval by delta changes its average by <= L*abs(delta). Neither bound
    shrinks as independent random noise. Receiver estimation/truncation and
    calibration uncertainty remain separate; this is not a likelihood.
    """
    if not support['accepted']:
        raise ValueError('accepted common support required')
    values = np.asarray(midpoint_magnitudes_mps2, float)
    intervals = np.asarray(support['nominal_intervals_s'], float)
    offset = np.asarray(support['time_offset_bounds_s'], float)
    if (values.shape != (len(intervals),) or not np.all(np.isfinite(values))
            or np.any(values < 0.)):
        raise ValueError('one finite nonnegative predicted midpoint magnitude per packet required')
    if (not np.isfinite(reference_offset_s) or reference_offset_s < offset[0]
            or reference_offset_s > offset[1]):
        raise ValueError('reference offset must be inside declared common-offset envelope')
    rate = maximum_magnitude_rate_mps3
    if not np.isfinite(rate) or rate < 0.:
        raise ValueError('finite nonnegative magnitude-rate bound required')
    duration = intervals[:, 1] - intervals[:, 0]
    weights = duration / np.sum(duration)
    mean = float(np.dot(weights, values))
    averaging_error = float(rate * np.dot(weights, duration) / 4.)
    synchronization_error = float(rate * np.max(abs(offset - reference_offset_s)))
    upper = mean + averaging_error + synchronization_error
    if not np.isfinite(upper):
        raise ValueError('prediction bound exceeds finite range')
    return dict(midpoint_average_mps2=mean,
        lower_mps2=max(0., mean - averaging_error - synchronization_error), upper_mps2=upper,
        packet_averaging_error_bound_mps2=averaging_error,
        synchronization_error_bound_mps2=synchronization_error,
        maximum_magnitude_rate_mps3=float(rate), magnitude_rate_is_assumed=True,
        reference_offset_s=float(reference_offset_s),
        aggregation_support='retained whole-packet union only',
        receiver_derivative_error_included=False, calibration_uncertainty_included=False,
        statistical_coverage_calibrated=False, scientific_decision='abstain')
