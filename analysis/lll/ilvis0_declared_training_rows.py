# SPDX-License-Identifier: AGPL-3.0-or-later
"""Necessary rows from supplied bound reports and explicitly declared allowances.

This audits arithmetic and shape, not the provenance or validity of a native
bound report or an error law. Callers must check those prerequisites separately.
No future measurements enter this interface. Frozen short controls are unchanged.
"""
from fractions import Fraction as F
import math

from .ilvis0_saved_prediction_audit import endpoint
from .ilvis0_training_remainder_audit import scaled_design


def _rows(value,count,columns,name):
    if (not isinstance(value,(list,tuple)) or len(value)!=count
            or any(not isinstance(row,(list,tuple)) or len(row)!=columns
                   or any(type(v) not in (int,float) or not math.isfinite(v) for v in row)
                   for row in value)):
        raise ValueError('complete finite '+name+' required')
    return [[float(v) for v in row] for row in value]


def training_rows(training,reports,*,observation_allowance_m):
    region=training['region']; times=training['times_s']; n=len(times)
    if (not 1<=n<=256 or any(type(t) not in (int,float) or not math.isfinite(t) for t in times)
            or times[0]<0. or any(b<=a for a,b in zip(times,times[1:]))
            or region['parameter_count']!=78 or len(region['center'])!=78 or len(reports)!=n
            or any(type(v) not in (int,float) or not math.isfinite(v) for v in region['center'])):
        raise ValueError('complete ordered training epochs and all 78 coordinates required')
    noise=_rows(observation_allowance_m,n,3,'observation allowances')
    if any(v<0. for row in noise for v in row):
        raise ValueError('nonnegative observation allowances required')
    nominal=_rows(training['nominal'],n,3,'native centers')
    observations=_rows(training['observations'],n,3,'training observations')
    design=_rows(region['design'],3*n,51,'saved training design')
    if len(training['jacobian'])!=n:
        raise ValueError('complete training Jacobians required')
    arithmetic=F(region['arithmetic_allowance'])
    if arithmetic<0:raise ValueError('nonnegative saved arithmetic allowance required')
    rows=[]; lower=[]; upper=[]
    for epoch,report in enumerate(reports):
        if report['time_s']!=times[epoch] or report['center']!=nominal[epoch]:
            raise ValueError('training time or transferred native center changed')
        matrix=scaled_design(training['jacobian'][epoch],report,region['coordinate_scale'])
        if matrix!=design[3*epoch:3*epoch+3]:
            raise ValueError('training coefficient changed; no silent basis transfer')
        remainder=report['unshared_remainder']
        if (len(remainder)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) or v<0.
                                   for v in remainder)):
            raise ValueError('complete nonnegative finite propagation remainder required')
        for axis,row in enumerate(matrix):
            shift=sum((F(v)*F(c) for v,c in zip(row,region['center'][:51],strict=True)),F(0))
            delta=(F(observations[epoch][axis])-F(nominal[epoch][axis]))*F(region['coordinate_scale'][axis])
            radius=F(remainder[axis])*F(region['coordinate_scale'][axis])+F(noise[epoch][axis])+arithmetic
            rows.append(row+[0.]*27)
            lower.append(endpoint(shift+delta-radius,False))
            upper.append(endpoint(shift+delta+radius,True))
    return dict(design=rows+[[-v for v in row] for row in rows],upper=upper+[-v for v in lower],
        physical_parameter_count=27,parameter_count=78,original_expression_columns=51,
        observation_allowance_m=noise,arithmetic_allowance_m=float(arithmetic),new_rows=6*n,
        error_law_qualified=False,future_observations_used=False,scientific_decision='abstain')
