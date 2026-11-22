# SPDX-License-Identifier: AGPL-3.0-or-later
"""Receiver-only trajectory connection for the channel diagnostic.

Reported latitude/longitude are interpreted in their supplied geodetic chart.
This is a conditional trajectory estimate, not independent Earth-model evidence.
"""

import numpy as np

from .ilvis0_error_model import Spec, covariance as receiver_covariance
from .ilvis0_receiver_derivatives import LocalPolynomial
from .ilvis0_receiver_support import (
    SupportPolicy, motion_from_enhanced_positions, motion_from_gga_fixes,
    select_support)


VERSION = 'ilvis0-receiver-trajectory-from-gga-v3'
MAX_LOCAL_RECEIVER_EPOCHS = 128


def _selected_coordinates(rows, first, last, ellipsoidal_height_m):
    """Keep the longitude chart independent of excluded receiver fixes."""
    selected = rows[first:last+1]
    return np.column_stack((
        np.deg2rad([row['latitude_deg'] for row in selected]),
        np.unwrap(np.deg2rad([row['longitude_deg'] for row in selected])),
        np.asarray(ellipsoidal_height_m)[first:last+1]))


def local_trajectory_from_gga(fixes, coordinate_covariance, *, target_s, policy, degree):
    """Select one receiver-only support and fit its declared local polynomial.

    ``coordinate_covariance`` is epoch-major in latitude radians, longitude
    radians, and ellipsoidal metres. It is a supplied assumption, not estimated
    here. No gyro, fused attitude, or withheld observation enters this function.
    """
    if not isinstance(policy, SupportPolicy):
        raise ValueError('explicit receiver support policy required')
    rows = tuple(fixes)
    n = len(rows)
    covariance = np.asarray(coordinate_covariance, dtype=float)
    if (covariance.shape != (3*n, 3*n) or not np.all(np.isfinite(covariance))
            or not np.allclose(covariance, covariance.T, rtol=1e-12, atol=0.)):
        raise ValueError('finite symmetric full receiver coordinate covariance required')
    motion = motion_from_gga_fixes(rows, maximum_gap_s=policy.maximum_gap_s)
    support = select_support(
        motion['times_s'], motion['speed_mps'], motion['course_deg'],
        motion['vertical_rate_mps'], target_s=target_s, policy=policy)
    result = dict(version=VERSION, source='primary_receiver_gga',
                  motion_version=motion['version'],
                  measurement_time_key='utc_week_s',
                  height_convention=motion['height_convention'],
                  coordinate_units=('rad', 'rad', 'm'),
                  coordinate_metric='reported geodetic receiver coordinates',
                  support=support, trajectory=None, derivative_weights=None,
                  covariance_calibrated=False, scientific_decision='abstain')
    selected = support['selected_indices']
    if selected is None:
        return result
    first, last = selected
    coordinates = _selected_coordinates(
        rows, first, last, motion['ellipsoidal_height_m'])
    indices = np.arange(3*first, 3*(last+1))
    local_covariance = covariance[np.ix_(indices, indices)]
    operator = LocalPolynomial(
        motion['times_s'][first:last+1], target_s, local_covariance,
        degree=degree, maximum_gap_s=policy.maximum_gap_s)
    result['trajectory'] = operator.apply(coordinates)
    result['derivative_weights'] = operator.weights.copy()
    return result


def local_trajectory_from_gga_spec(fixes, spec, *, target_s, policy, degree,
                                    transforms=None):
    """Select from the full GGA history, factor only the selected local law.

    ``spec`` has a fixed full-record drift origin and span. Local covariance
    uses the same law restricted to the selected epochs; no excluded receiver
    value or later model residual chooses the window.
    """
    if not isinstance(policy, SupportPolicy) or not isinstance(spec, Spec):
        raise ValueError('receiver support policy and error Spec required')
    rows = tuple(fixes)
    motion = motion_from_gga_fixes(rows, maximum_gap_s=policy.maximum_gap_s)
    return _local_trajectory_from_motion_spec(
        rows, motion, spec, target_s=target_s, policy=policy,
        degree=degree, transforms=transforms)


def local_trajectory_from_enhanced_spec(positions, spec, *, target_s,
                                        policy, degree, transforms=None):
    """Use the primary receiver's enhanced positions and GNSS velocities."""
    if not isinstance(policy, SupportPolicy) or not isinstance(spec, Spec):
        raise ValueError('receiver support policy and error Spec required')
    rows = tuple(positions)
    motion = motion_from_enhanced_positions(
        rows, maximum_gap_s=policy.maximum_gap_s)
    return _local_trajectory_from_motion_spec(
        rows, motion, spec, target_s=target_s, policy=policy,
        degree=degree, transforms=transforms)


def _local_trajectory_from_motion_spec(rows, motion, spec, *, target_s,
                                      policy, degree, transforms=None):
    """Common local derivative fit after source-specific GNSS motion parsing."""
    n = len(rows)
    a = None if transforms is None else np.asarray(transforms, dtype=float)
    if a is not None and (a.shape != (n, 3, 3) or
                          not np.all(np.isfinite(a)) or
                          np.any(np.linalg.slogdet(a)[0] == 0)):
        raise ValueError('finite invertible full receiver transforms required')
    support = select_support(
        motion['times_s'], motion['speed_mps'], motion['course_deg'],
        motion['vertical_rate_mps'], target_s=target_s, policy=policy)
    result = dict(version=VERSION, source=motion['source'],
                  motion_version=motion['version'],
                  measurement_time_key=motion.get('measurement_time_key',
                                                  'utc_week_s'),
                  height_convention=motion['height_convention'],
                  coordinate_units=('rad', 'rad', 'm'),
                  coordinate_metric='reported geodetic receiver coordinates',
                  covariance_model='supplied_structured_spec',
                  support=support, trajectory=None, derivative_weights=None,
                  covariance_calibrated=False, scientific_decision='abstain')
    selected = support['selected_indices']
    if selected is None:
        return result
    first, last = selected
    if last-first+1 > MAX_LOCAL_RECEIVER_EPOCHS:
        raise ValueError('selected local receiver support exceeds declared limit')
    local_times = motion['times_s'][first:last+1]
    local_covariance = receiver_covariance(
        local_times, spec,
        transforms=None if a is None else a[first:last+1])
    operator = LocalPolynomial(
        local_times, target_s, local_covariance, degree=degree,
        maximum_gap_s=policy.maximum_gap_s)
    coordinates = _selected_coordinates(
        rows, first, last, motion['ellipsoidal_height_m'])
    result['trajectory'] = operator.apply(coordinates)
    result['derivative_weights'] = operator.weights.copy()
    return result
