# SPDX-License-Identifier: AGPL-3.0-or-later
"""Conditional whole-forecast bound for a supplied affine Gaussian law.

One calibration ellipsoid covers all retained parameter directions. A union
bound divides the future-noise allowance over every reported coordinate.
This is a mathematical control, not observed-aircraft coverage validation.
"""
import math


def envelope(training_design, training_observation, future_contrast,
             conditional_base, conditional_std, lower_bounds, upper_bounds,
             *, calibration_alpha, simultaneous_alpha, rank_rtol):
    import numpy as np
    from .bounded_linear_prediction import envelope as marginal_envelope

    base = np.asarray(conditional_base, dtype=float)
    if (base.ndim != 1 or base.size < 1 or
            not isinstance(calibration_alpha, (int, float)) or
            not isinstance(simultaneous_alpha, (int, float)) or
            not math.isfinite(calibration_alpha) or
            not math.isfinite(simultaneous_alpha) or
            not 0 < calibration_alpha < simultaneous_alpha < 1):
        raise ValueError('finite whole-forecast and calibration allowances required')
    future_per_coordinate = (simultaneous_alpha-calibration_alpha)/base.size
    if 1-future_per_coordinate/2 == 1:
        raise ValueError('future allowance is below representable Gaussian tail')
    result = marginal_envelope(
        training_design, training_observation, future_contrast,
        conditional_base, conditional_std, lower_bounds, upper_bounds,
        calibration_alpha=calibration_alpha,
        future_alpha=future_per_coordinate, rank_rtol=rank_rtol)
    result.update(
        scope='affine_known_gaussian_box_bonferroni',
        coordinate_count=base.size,
        calibration_alpha=calibration_alpha,
        future_alpha_per_coordinate=future_per_coordinate,
        affine_conditional_simultaneous_lower_bound=1-simultaneous_alpha,
        affine_conditional_simultaneous_bound_derived=True,
        simultaneous_coverage_established=False,
        simultaneous_condition='supplied affine Gaussian covariance law is correct and true calibration lies in supplied box',
        observed_aircraft_coverage_established=False,
        nonlinear_aircraft_coverage_established=False,
        scientific_decision='abstain')
    return result
