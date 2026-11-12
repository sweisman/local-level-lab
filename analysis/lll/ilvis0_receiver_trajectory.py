# SPDX-License-Identifier: AGPL-3.0-or-later
"""Receiver-only trajectory connection for the channel diagnostic.

Reported latitude/longitude are interpreted in their supplied geodetic chart.
This is a conditional trajectory estimate, not independent Earth-model evidence.
"""

import numpy as np

from .ilvis0_receiver_derivatives import LocalPolynomial
from .ilvis0_receiver_support import (
    SupportPolicy, motion_from_gga_fixes, select_support)


VERSION = 'ilvis0-receiver-trajectory-from-gga-v2'


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
                  support=support, trajectory=None,
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
    return result
