# SPDX-License-Identifier: AGPL-3.0-or-later
"""Whole-history necessary scalar constraints on fixed 200-packet groups."""
import numpy as np

from .ilvis0_channel_envelope import ENVELOPES, MODELS, integration_intervals, coordinate_error_box
from .ilvis0_calibrated_bounds import calibrated_increment_bounds, compare_envelopes
from .ilvis0_common_support import match_support
from .ilvis0_derivative_bounds import jet_error_bounds
from .ilvis0_receiver_derivatives import LocalPolynomial
from .ilvis0_force_bounds import force_bounds


def central_average_bounds(intervals_s, central_magnitude_bounds, *, center_s,
                           offset_bounds_s, maximum_rate_mps3):
    """Exact integral of the Lipschitz distance on a disjoint interval union.

    Bounds q(center), then integrate |q(t+offset)-q(center)| <= L*|t+offset-center|.
    A triangle inequality separates common timing uncertainty conservatively.
    Supplied physical bounds are assumptions; no calibrated coverage follows.
    """
    intervals = np.asarray(intervals_s, float)
    magnitude = np.asarray(central_magnitude_bounds, float)
    offset = np.asarray(offset_bounds_s, float)
    if (intervals.ndim != 2 or intervals.shape[1] != 2 or not len(intervals)
            or not np.all(np.isfinite(intervals)) or np.any(intervals[:, 1] <= intervals[:, 0])
            or np.any(intervals[1:, 0] < intervals[:-1, 1])):
        raise ValueError('finite positive ordered disjoint integration intervals required')
    if (magnitude.shape != (2,) or not np.all(np.isfinite(magnitude))
            or magnitude[0] < 0. or magnitude[1] < magnitude[0]):
        raise ValueError('nonnegative ordered central magnitude interval required')
    if offset.shape != (2,) or not np.all(np.isfinite(offset)) or offset[1] < offset[0]:
        raise ValueError('finite ordered common-offset interval required')
    if not np.isfinite(center_s) or not np.isfinite(maximum_rate_mps3) or maximum_rate_mps3 < 0.:
        raise ValueError('finite center and nonnegative magnitude-rate bound required')
    x = intervals-center_s
    primitive = x*abs(x)/2.
    duration = float(np.sum(intervals[:, 1]-intervals[:, 0]))
    averaging = float(maximum_rate_mps3*np.sum(primitive[:, 1]-primitive[:, 0])/duration)
    timing = float(maximum_rate_mps3*np.max(abs(offset)))
    bounds = [max(0., float(magnitude[0]-averaging-timing)), float(magnitude[1]+averaging+timing)]
    if not np.all(np.isfinite(bounds)): raise ValueError('unrepresentable prediction bound')
    return dict(bounds_mps2=bounds, averaging_error_mps2=averaging,
        synchronization_error_mps2=timing, statistical_coverage_calibrated=False,
        scientific_decision='abstain')


def inventory(values, receiver_times, segment):
    """Time/completeness selection only; never inspect measured force values."""
    values = np.asarray(values, float); times = np.asarray(receiver_times, float)
    if times.ndim != 1 or not len(times) or not np.all(np.isfinite(times)) or np.any(np.diff(times) <= 0.):
        raise ValueError('ordered finite receiver times required')
    start, end = segment['start_s'], segment['end_s']
    if not np.isfinite(start) or not np.isfinite(end) or end <= start: raise ValueError('saved interval required')
    clocks = {name: integration_intervals(values, name) for name in ('nominal', 'header')}
    groups = []
    for first in range(0, len(values), 200):
        count = min(200, len(values)-first); reason = 'eligible'
        spans = {name: [float(intervals[first, 0]), float(intervals[first+count-1, 1])]
            for name, intervals in clocks.items()}
        if count != 200: reason = 'partial_packet_group'
        elif min(s[0] for s in spans.values()) < start or max(s[1] for s in spans.values()) > end:
            reason = 'outside_saved_stretch'
        else:
            centers = [sum(span)/2. for span in spans.values()]
            if (min(centers)-16. < max(start, times[0])
                    or max(centers)+16. > min(end, times[-1])):
                reason = 'receiver_support_margin'
        groups.append(dict(group_index=first//200, first_packet=first, packet_count=count,
            clock_spans_s=spans, eligible=reason == 'eligible', reason=reason))
    return dict(groups=groups, total_packets=len(values), selected_packets=sum(g['packet_count'] for g in groups if g['eligible']),
        selection_used_gyro=False, selection_used_force=False)


def prepare_group(values, receiver_times, coordinates, group, clock, receiver_error_m, *, on_operator=None):
    values = np.asarray(values, float); receiver_times = np.asarray(receiver_times, float)
    coordinates = np.asarray(coordinates, float)
    if not group['eligible'] or group['packet_count'] != 200:
        raise ValueError('preselected complete packet group required')
    first = group['first_packet']; ids = np.arange(first, first+200)
    intervals = integration_intervals(values, clock)[ids]
    center = float((intervals[0, 0]+intervals[-1, 1])/2.)
    selected = abs(receiver_times-center) <= 16.
    times = receiver_times[selected]-center; points = coordinates[selected]
    if len(times) < 17: return dict(supported=False, reason='insufficient_receiver_epochs')
    relative = intervals-center
    # The window is expanded for unknown latency, rather than throwing away
    # boundary packets or choosing different measurements under the two clocks.
    support = match_support(times, relative, [relative[0, 0]-.15, relative[-1, 1]+.15],
        time_offset_bounds_s=[-.15, .15], maximum_receiver_gap_s=2., integration_hypothesis=clock+' integration intervals')
    if not support['accepted'] or len(support['packet_indices']) != 200:
        return dict(supported=False, reason=support['reason'], support=support)
    error_box = coordinate_error_box(points, receiver_error_m)
    if on_operator is not None: on_operator()
    operator = LocalPolynomial(times, 0., np.eye(3*len(times)), degree=4, maximum_gap_s=2.)
    estimate = operator.apply(points)
    jet = np.concatenate([estimate[key] for key in ('position', 'rate', 'acceleration')])
    error = jet_error_bounds(operator.weights, times, 0., derivative_envelopes=ENVELOPES,
        coordinate_error_bounds=np.tile(error_box, (len(times), 1)))['total_jet_error_bounds']
    conflict = np.maximum(0., abs(jet)-error) > ENVELOPES[:3].ravel()
    return dict(supported=not np.any(conflict), reason='observable_derivative_envelope_conflict' if np.any(conflict) else 'supported',
        center_utc_s=center, support=support, jet=jet, error=error, first_packet=first,
        coordinate_error_box=error_box, receiver_times_relative_s=times, receiver_coordinates=points,
        observable_envelope_conflicts=np.flatnonzero(conflict))


def assess_group(values, batch, *, model, velocity_scale, on_force=None):
    if model not in MODELS: raise ValueError('frozen physical candidate required')
    if not batch['supported']: return dict(supported=False, reason=batch['reason'])
    jet, error = np.asarray(batch['jet']), np.asarray(batch['error'])
    if on_force is not None: on_force()
    force = force_bounds(np.column_stack((jet-error, jet+error)), model=model,
        background_rate_bounds_rads=[7.292115e-5]*2 if model == 'sphere_rotating' else [0., 0.],
        gravity_bounds_mps2=[9.7, 9.9], disc_radius_m=6371000.)
    intervals = np.asarray(batch['support']['nominal_intervals_s'])
    prediction = central_average_bounds(intervals, force['magnitude_bounds_mps2'], center_s=0.,
        offset_bounds_s=[-.15, .15], maximum_rate_mps3=2.)
    first = batch['first_packet']; raw = np.asarray(values)[first:first+200, 3:6]
    if (raw.shape != (200, 3) or np.any(raw != np.rint(raw)) or np.any(raw < -2**31)
            or np.any(raw > 2**31-1)): raise ValueError('original signed integer packet group required')
    duration = np.diff(intervals, axis=1).ravel(); comparisons = {}
    for name, gain, offset in [('zero', 0., 0.), ('narrow', .01, .05), ('broad', .15, .25)]:
        measurement = calibrated_increment_bounds(raw.astype(np.int32), np.column_stack((duration, duration)),
            scale_mps_per_count=velocity_scale, count_uncertainty=1., gain_bounds=[[-gain, gain]]*3,
            offset_bounds_mps2=[[-offset, offset]]*3, maximum_force_direction_rate_rads=1.,
            period_hypothesis=batch['support']['integration_hypothesis'])
        observed = [measurement['continuous_magnitude_lower_mps2'], measurement['continuous_magnitude_upper_mps2']]
        comparisons[name] = dict(compare_envelopes(observed, prediction['bounds_mps2']),
            measured_bounds_mps2=observed, predicted_bounds_mps2=prediction['bounds_mps2'])
    return dict(supported=True, reason='supported', comparisons=comparisons, prediction=prediction,
        packet_count=200, integration_duration_s=float(duration.sum()), scientific_decision='abstain')


def shared_zero_check(rows):
    """Only a common gain/offset point; other shared uncertainties are relaxed."""
    rows = list(rows)
    supported = [r for r in rows if r.get('supported')]
    return dict(zero_calibration_not_excluded_everywhere=bool(rows) and len(supported) == len(rows)
        and all(r['comparisons']['zero']['relation'] == 'overlap' for r in supported),
        unsupported_groups=len(rows)-len(supported),
        joint_receiver_history_feasibility_established=False,
        joint_latency_gravity_feasibility_established=False,
        full_gyro_free_reconstruction_established=False, scientific_decision='abstain')
