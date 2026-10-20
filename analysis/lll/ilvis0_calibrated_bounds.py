# SPDX-License-Identifier: AGPL-3.0-or-later
"""Deterministic calibrated-increment enclosures, not observational coverage."""
import numpy as np

from .ilvis0_increment_bounds import magnitude_bounds


def calibrated_increment_bounds(counts, period_bounds_s, *, scale_mps_per_count,
                                count_uncertainty, gain_bounds, offset_bounds_mps2,
                                period_hypothesis, maximum_force_direction_rate_rads):
    """Enclose corrected increments (dv-offset*T)/(1+gain) under stated bounds.

    Gain/offset intervals are common across packets; interval propagation
    relaxes that dependence and can be conservative. Overlap with a prediction
    does not prove a single constant calibration explains the whole history.
    The direction-rate hypothesis concerns the CORRECTED continuous body force.
    Preserve count integers and explicit period hypotheses through validation.
    """
    base = magnitude_bounds(counts, period_bounds_s, scale_mps_per_count=scale_mps_per_count,
        count_uncertainty=count_uncertainty, period_hypothesis=period_hypothesis,
        maximum_force_direction_rate_rads=maximum_force_direction_rate_rads)
    gain = np.asarray(gain_bounds, float)
    offset = np.asarray(offset_bounds_mps2, float)
    for item in (gain, offset):
        if (item.shape != (3, 2) or not np.all(np.isfinite(item))
                or np.any(item[:, 1] < item[:, 0])):
            raise ValueError('finite ordered three-axis calibration intervals required')
    if np.any(gain[:, 0] <= -1.):
        raise ValueError('gain correction denominator must remain positive')
    counts = np.asarray(counts).astype(float)
    period = np.asarray(period_bounds_s, float)
    with np.errstate(over='ignore', invalid='ignore'):
        delta_lo = (counts-count_uncertainty)*scale_mps_per_count
        delta_hi = (counts+count_uncertainty)*scale_mps_per_count
        products = [period[:, time, None]*offset[:, axis] for time in (0, 1) for axis in (0, 1)]
        numerator_lo = delta_lo-np.maximum.reduce(products)
        numerator_hi = delta_hi-np.minimum.reduce(products)
        corrected = [value/(1.+gain[:, endpoint])
            for value in (numerator_lo, numerator_hi) for endpoint in (0, 1)]
        lo = np.minimum.reduce(corrected)
        hi = np.maximum.reduce(corrected)
        closest = np.where((lo <= 0.) & (hi >= 0.), 0., np.minimum(abs(lo), abs(hi)))
        farthest = np.maximum(abs(lo), abs(hi))
        minimum = np.linalg.norm(closest, axis=1)
        maximum = np.linalg.norm(farthest, axis=1)
        lower = float(minimum.sum()/period[:, 1].sum())
        upper = float(maximum.sum()/period[:, 0].sum())
    if not np.isfinite(lower) or not np.isfinite(upper):
        raise ValueError('calibrated increment bound exceeds finite range')
    continuous_upper = None
    if base['continuous_force_upper_bound_established']:
        angle = maximum_force_direction_rate_rads*period[:, 1]/2.
        continuous_upper = float(np.sum(maximum/np.cos(angle))/period[:, 0].sum())
        if not np.isfinite(continuous_upper):
            raise ValueError('continuous calibrated force bound exceeds finite range')
    base.update(packet_force_lower_mps2=minimum/period[:, 1],
        packet_force_upper_mps2=maximum/period[:, 0],
        time_weighted_magnitude_lower_mps2=lower, time_weighted_magnitude_upper_mps2=upper,
        continuous_magnitude_lower_mps2=lower, continuous_magnitude_upper_mps2=continuous_upper,
        gain_bounds=gain.copy(), offset_bounds_mps2=offset.copy(),
        calibration_uncertainty_included=True, constant_parameter_dependence_relaxed=True,
        formal_rounding_certificate=False)
    return base


def compare_envelopes(measured_bounds, predicted_bounds):
    """Report a necessary scalar constraint, never a full fit or detection."""
    def validate(bounds):
        if len(bounds) != 2 or bounds[0] is None or not np.isfinite(bounds[0]) or bounds[0] < 0.:
            raise ValueError('finite nonnegative lower magnitude bound required')
        if bounds[1] is None:
            return False
        if not np.isfinite(bounds[1]) or bounds[1] < bounds[0]:
            raise ValueError('ordered finite magnitude bounds required')
        return True
    measured_ok = validate(measured_bounds)
    predicted_ok = validate(predicted_bounds)
    supported = measured_ok and predicted_ok
    gap = max(0., predicted_bounds[0]-measured_bounds[1], measured_bounds[0]-predicted_bounds[1]) if supported else None
    return dict(relation=('disjoint' if gap > 0. else 'overlap') if supported else 'unsupported',
        minimum_gap_mps2=gap, incompatible_under_declared_bounds=bool(supported and gap > 0.),
        complete_history_feasibility_established=False, statistical_coverage_calibrated=False,
        scientific_decision='abstain')
