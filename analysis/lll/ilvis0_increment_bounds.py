# SPDX-License-Identifier: AGPL-3.0-or-later
"""Deterministic increment-quantization bounds, not a noise or clock estimate."""
import numpy as np


def magnitude_bounds(counts,period_bounds_s,*,scale_mps_per_count,count_uncertainty,period_hypothesis):
    """Bound packet-mean force norms and their duration-weighted aggregate.

    Counts remain signed int32 observations. count_uncertainty declares an
    inclusive componentwise count-error bound; no rounding mode or independent
    random error is presumed. Each positive lower/upper period bounds the actual
    integration duration under a named hypothesis, not necessarily elapsed
    packet-header time. Bounds cover quantization and declared durations only.

    Norms of integrated body vectors can underestimate continuous force norms
    during rotation. The upper bounds below apply to packet means, not to
    instantaneous or continuously averaged specific-force magnitude.
    """
    counts=np.asarray(counts);period=np.asarray(period_bounds_s,float)
    if (counts.ndim!=2 or counts.shape[1]!=3 or not len(counts) or counts.dtype.kind!='i'
            or np.any(counts<-(2**31)) or np.any(counts>2**31-1)):
        raise ValueError('nonempty signed int32-range N by 3 counts required')
    if (period.shape!=(len(counts),2) or not np.all(np.isfinite(period))
            or np.any(period[:,0]<=0.) or np.any(period[:,1]<period[:,0])):
        raise ValueError('matching positive ordered finite integration-period bounds required')
    if (not np.isfinite(scale_mps_per_count) or scale_mps_per_count<=0.
            or not np.isfinite(count_uncertainty) or count_uncertainty<0.):
        raise ValueError('positive finite scale and nonnegative finite count error required')
    if not isinstance(period_hypothesis,str) or not period_hypothesis.strip():
        raise ValueError('explicit integration-period hypothesis required')
    lower=(counts.astype(float)-count_uncertainty)*scale_mps_per_count
    upper=(counts.astype(float)+count_uncertainty)*scale_mps_per_count
    closest=np.where((lower<=0.) & (upper>=0.),0.,np.minimum(abs(lower),abs(upper)))
    farthest=np.maximum(abs(lower),abs(upper))
    minimum=np.linalg.norm(closest,axis=1);maximum=np.linalg.norm(farthest,axis=1)
    packet_lower=minimum/period[:,1];packet_upper=maximum/period[:,0]
    aggregate_lower=float(np.sum(minimum)/np.sum(period[:,1]))
    aggregate_upper=float(np.sum(maximum)/np.sum(period[:,0]))
    if (not np.all(np.isfinite(packet_lower)) or not np.all(np.isfinite(packet_upper))
            or not np.isfinite(aggregate_lower) or not np.isfinite(aggregate_upper)):
        raise ValueError('increment or integration-period bounds exceed finite range')
    return dict(packet_force_lower_mps2=packet_lower,packet_force_upper_mps2=packet_upper,
        time_weighted_magnitude_lower_mps2=aggregate_lower,
        time_weighted_magnitude_upper_mps2=aggregate_upper,
        period_hypothesis=period_hypothesis,scale_mps_per_count=float(scale_mps_per_count),
        count_uncertainty=float(count_uncertainty),
        aggregation='sum of packet increment norms / total integration duration',
        continuous_force_upper_bound_established=False,statistical_coverage_calibrated=False,
        calibration_uncertainty_included=False,scientific_decision='abstain')
