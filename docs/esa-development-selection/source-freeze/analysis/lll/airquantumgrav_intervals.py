# SPDX-License-Identifier: AGPL-3.0-or-later
"""Explicit engineering-rate quadrature hypothesis, never logged increments."""
import math

VERSION='esa-imar-actual-period-right-endpoint-v1'
HYPOTHESIS='right_endpoint_rectangular_rate_assumption'


def construct(record,*,hypothesis):
    if hypothesis!=HYPOTHESIS:raise ValueError('explicit supported rate-sampling hypothesis required')
    original=dict(record);dt=record['dt_s']
    force=list(record['acceleration_mps2']);rate=list(record['angular_rate_rads'])
    if len(force)!=3 or len(rate)!=3 or not all(math.isfinite(v) for v in force+rate):raise ValueError('six finite engineering channels required')
    if dt is not None and (not math.isfinite(dt) or dt<=0.):raise ValueError('positive actual interval required')
    supported=dt is not None and dt<=1.5/300.
    reason='supported' if supported else 'no_preceding_interval' if dt is None else 'unsupported_gap'
    return dict(source_record=original,version=VERSION,hypothesis=hypothesis,supported=supported,reason=reason,
        dt_s=dt,angle_increment_rad=[v*dt for v in rate] if supported else None,
        velocity_increment_mps=[v*dt for v in force] if supported else None,
        constructed_not_logged_increments=True,independent_interval_interpretation_verified=False,
        corrections_applied=False,scientific_decision='abstain')
