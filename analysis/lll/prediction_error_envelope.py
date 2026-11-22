# SPDX-License-Identifier: AGPL-3.0-or-later
"""Conditional position-error bound from explicitly supplied physical limits.

This verifies the propagation algebra, not the limits supplied by a caller.
No archived aircraft error law or statistical coverage is inferred here.
"""

import math


def position_error_bound(
        horizon_s, *, initial_position_error_m,
        initial_velocity_error_mps, initial_attitude_error_rad,
        gyro_rate_error_rads, gyro_rate_drift_rads2,
        force_error_mps2, force_error_drift_mps3,
        unmodeled_acceleration_mps2, force_norm_bound_mps2,
        receiver_error_m):
    """Bound a local-Cartesian inertial position error under common dynamics.

    Every input is a nonnegative bound over the entire forecast interval.
    Angular-rate error may grow at most linearly with elapsed time. Specific
    force error may also grow linearly. The norm of the correctly measured
    force never exceeds ``force_norm_bound_mps2``. Differences from the common
    gravity/transport dynamics and other omitted motion must be included in
    ``unmodeled_acceleration_mps2``. That term needs its own independent limit.
    The attitude term uses the exact inequality
    ``||(R1-R2) f|| <= ||f|| * angle``; no small-angle approximation is needed.
    The result is conditional on these limits actually holding.
    """
    values = dict(horizon_s=horizon_s,
        initial_position_error_m=initial_position_error_m,
        initial_velocity_error_mps=initial_velocity_error_mps,
        initial_attitude_error_rad=initial_attitude_error_rad,
        gyro_rate_error_rads=gyro_rate_error_rads,
        gyro_rate_drift_rads2=gyro_rate_drift_rads2,
        force_error_mps2=force_error_mps2,
        force_error_drift_mps3=force_error_drift_mps3,
        unmodeled_acceleration_mps2=unmodeled_acceleration_mps2,
        force_norm_bound_mps2=force_norm_bound_mps2,
        receiver_error_m=receiver_error_m)
    if any(isinstance(value, bool) or not isinstance(value, (int, float))
           or not math.isfinite(value) or value < 0 for value in values.values()):
        raise ValueError('finite nonnegative physical bounds required for every term')
    t = float(horizon_s)
    f = float(force_norm_bound_mps2)
    terms = dict(
        initial_position=float(initial_position_error_m),
        initial_velocity=float(initial_velocity_error_mps)*t,
        initial_attitude=f*float(initial_attitude_error_rad)*t*t/2,
        gyro_rate=f*float(gyro_rate_error_rads)*t**3/6,
        gyro_rate_drift=f*float(gyro_rate_drift_rads2)*t**4/24,
        force_error=float(force_error_mps2)*t*t/2,
        force_error_drift=float(force_error_drift_mps3)*t**3/6,
        unmodeled_acceleration=float(unmodeled_acceleration_mps2)*t*t/2,
        receiver_error=float(receiver_error_m))
    total = math.fsum(terms.values())
    if not math.isfinite(total):
        raise ValueError('unrepresentable propagated bound')
    return dict(version='conditional-position-error-envelope-v1',
                horizon_s=t, terms_m=terms, total_m=total,
                assumptions=values, dynamics_scope='local_cartesian_common_dynamics',
                assumptions_empirically_verified=False,
                observed_coverage_qualified=False,
                scientific_decision='abstain')
