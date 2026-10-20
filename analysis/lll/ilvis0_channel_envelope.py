# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite descriptive scalar envelopes; no gyro, fused attitude or optimizer."""
import numpy as np

from .ilvis0_calibrated_bounds import calibrated_increment_bounds, compare_envelopes
from .ilvis0_common_support import match_support, bound_prediction_average
from .ilvis0_derivative_bounds import jet_error_bounds
from .ilvis0_force_bounds import force_bounds
from .ilvis0_receiver_derivatives import LocalPolynomial

MODELS = ('sphere_rotating', 'sphere_still', 'flat_still')
FRACTIONS = (.1, .5, .9)
ENVELOPES = np.array([[np.pi/2, 2*np.pi, 20000.], [1e-4, 5e-4, 2.],
    [1e-7, 5e-7, .2], [1e-9, 5e-9, .05], [1e-11, 5e-11, .01], [1e-13, 5e-13, .002]])


def centers(segment):
    start, end = segment['start_s'], segment['end_s']
    if not np.isfinite(start) or not np.isfinite(end) or end-start < 240.:
        raise ValueError('unchanged qualifying stretch required')
    return [float(start+fraction*(end-start)) for fraction in FRACTIONS]


def integration_intervals(values, clock):
    values = np.asarray(values, float)
    if values.ndim != 2 or values.shape[1] < 6 or not len(values) or not np.all(np.isfinite(values)):
        raise ValueError('finite extracted packets required')
    if clock == 'nominal':
        origin = values[0, 1]-values[0, 2]
        edges = origin+np.arange(len(values)+1)*.005
        return np.column_stack((edges[:-1], edges[1:]))
    if clock == 'header':
        return np.column_stack((values[:, 1]-values[:, 2], values[:, 1]))
    raise ValueError('explicit nominal/header hypothesis required')


def coordinate_error_box(coordinates, metres):
    coordinates = np.asarray(coordinates, float)
    if (coordinates.ndim != 2 or coordinates.shape[1] != 3 or not np.all(np.isfinite(coordinates))
            or not np.isfinite(metres) or metres <= 0. or np.any(abs(np.diff(coordinates[:, 1])) > np.pi)):
        raise ValueError('finite smooth coordinate chart and positive distance allowance required')
    latitude = metres/6300000.
    extreme = float(np.max(abs(coordinates[:, 0])))+latitude
    if extreme >= np.pi/2-1e-6:
        raise ValueError('polar receiver uncertainty unsupported')
    return np.array([latitude, metres/(6300000.*np.cos(extreme)), metres])


def prepare_jets(values, receiver_times, coordinates, center, clock, receiver_error_m, *, on_operator=None):
    """Receiver-only estimates and explicit boxes on fixed whole-packet support."""
    receiver_times = np.asarray(receiver_times, float)
    coordinates = np.asarray(coordinates, float)
    if coordinates.shape != (len(receiver_times), 3):
        raise ValueError('matching receiver epochs/coordinates required')
    selected = abs(receiver_times-center) <= 16.
    times = receiver_times[selected]-center
    points = coordinates[selected]
    if len(times) < 17:
        raise ValueError('at least seventeen receiver epochs in fixed support required')
    error_box = coordinate_error_box(points, receiver_error_m)
    intervals = integration_intervals(values, clock)-center
    support = match_support(times, intervals, [-.5, .5], time_offset_bounds_s=[-.15, .15],
        maximum_receiver_gap_s=2., integration_hypothesis=clock+' integration intervals')
    if not support['accepted']:
        return dict(supported=False, reason=support['reason'], support=support, operators=0)
    indices = support['packet_indices']
    if len(indices) > 256:
        raise ValueError('frozen per-batch operator allowance exceeded')
    estimates, bounds, conflicts = [], [], []
    # Fixed regression weights only. This matrix is not an estimated receiver covariance.
    weights = np.eye(3*len(times))
    for midpoint in support['nominal_intervals_s'].mean(axis=1):
        if on_operator is not None: on_operator()
        operator = LocalPolynomial(times, float(midpoint), weights, degree=4, maximum_gap_s=2.)
        estimate = operator.apply(points)
        jet = np.concatenate([estimate[key] for key in ('position', 'rate', 'acceleration')])
        error = jet_error_bounds(operator.weights, times, midpoint, derivative_envelopes=ENVELOPES,
            coordinate_error_bounds=np.tile(error_box, (len(times), 1)))['total_jet_error_bounds']
        conflict = np.maximum(0., abs(jet)-error) > ENVELOPES[:3].ravel()
        if np.any(conflict):
            conflicts.append(dict(midpoint_s=float(midpoint), components=np.flatnonzero(conflict).tolist()))
        estimates.append(jet); bounds.append(error)
    return dict(supported=not conflicts, reason='observable_derivative_envelope_conflict' if conflicts else 'supported',
        support=support, operators=len(estimates), jets=np.array(estimates), errors=np.array(bounds),
        coordinate_error_box=error_box, observable_envelope_conflicts=conflicts,
        receiver_times_relative_s=times, receiver_coordinates=points)


def assess(values, batch, *, model, velocity_scale, calibration, on_force=None):
    if model not in MODELS or calibration not in ('narrow', 'broad'):
        raise ValueError('frozen candidate/calibration required')
    if not batch['supported']:
        return dict(supported=False, reason=batch['reason'], force_boxes=0, scientific_decision='abstain')
    support = batch['support']; indices = support['packet_indices']
    raw = np.asarray(values)[indices, 3:6]
    if np.any(raw != np.rint(raw)) or np.any(raw < -2**31) or np.any(raw > 2**31-1):
        raise ValueError('original signed counts not exactly representable')
    counts = raw.astype(np.int32)
    duration = np.diff(support['nominal_intervals_s'], axis=1).ravel()
    gain, offset = (.01, .05) if calibration == 'narrow' else (.15, .25)
    measured = calibrated_increment_bounds(counts, np.column_stack((duration, duration)),
        scale_mps_per_count=velocity_scale, count_uncertainty=1.,
        gain_bounds=[[-gain, gain]]*3, offset_bounds_mps2=[[-offset, offset]]*3,
        period_hypothesis=support['integration_hypothesis'], maximum_force_direction_rate_rads=1.)
    magnitude = []
    for jet, error in zip(np.asarray(batch['jets']), np.asarray(batch['errors'])):
        if on_force is not None: on_force()
        result = force_bounds(np.column_stack((jet-error, jet+error)), model=model,
            background_rate_bounds_rads=[7.292115e-5]*2 if model == 'sphere_rotating' else [0., 0.],
            gravity_bounds_mps2=[9.70, 9.90], disc_radius_m=6371000.)
        magnitude.append(result['magnitude_bounds_mps2'])
    magnitude = np.asarray(magnitude)
    lower = bound_prediction_average(support, magnitude[:, 0], reference_offset_s=0.,
        maximum_magnitude_rate_mps3=2.)
    upper = bound_prediction_average(support, magnitude[:, 1], reference_offset_s=0.,
        maximum_magnitude_rate_mps3=2.)
    measured_bounds = [measured['continuous_magnitude_lower_mps2'], measured['continuous_magnitude_upper_mps2']]
    predicted_bounds = [lower['lower_mps2'], upper['upper_mps2']]
    comparison = compare_envelopes(measured_bounds, predicted_bounds)
    return dict(supported=True, reason='supported', model=model, calibration=calibration,
        force_boxes=len(magnitude), measured_bounds_mps2=measured_bounds, predicted_bounds_mps2=predicted_bounds,
        continuous_packet_coverage=support['continuous_packet_coverage'], packet_count=len(indices),
        integration_duration_s=float(duration.sum()),
        ambiguous_boundary_packets=len(support['boundary_ambiguous_indices']),
        synchronization_bound_mps2=lower['synchronization_error_bound_mps2'],
        averaging_bound_mps2=lower['packet_averaging_error_bound_mps2'],
        **comparison)
