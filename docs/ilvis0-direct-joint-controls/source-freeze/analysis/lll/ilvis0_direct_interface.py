# SPDX-License-Identifier: AGPL-3.0-or-later
"""Checked bridge from directional native bounds to the existing joint schema."""
from copy import deepcopy
from fractions import Fraction as F
import math
import numpy as np
from . import ilvis0_direct_native as candidate
from .ilvis0_directional_acceleration import DirectionalAcceleration
from .ilvis0_conditioned_acceleration import ConditionedAcceleration
from .ilvis0_transform_native import TransformReference,TransformEnclosure
from .ilvis0_transform_envelope import _force_source
from .ilvis0_saved_prediction_audit import endpoint
from .ilvis0_training_remainder_audit import scaled_design
from .ilvis0_dyadic_timing import MATCHED_FIELDS


def matched_bounds(before,after):
    """Require unchanged maps and nonwidening, complete finite radii."""
    remainders=('unshared_remainder','position_unshared_remainder','force_unshared_remainder','lever_unshared_remainder')
    different=[key for key in MATCHED_FIELDS if key not in remainders
        and (key not in before or key not in after or before[key]!=after[key])]
    invalid=[]
    for key in remainders:
        try:
            a=np.asarray(before[key],float);b=np.asarray(after[key],float)
            valid=(a.shape==b.shape==(3,) and np.all(np.isfinite(a)) and np.all(np.isfinite(b))
                and np.all(a>=0) and np.all(b>=0) and np.all(b<=a))
        except (KeyError,TypeError,ValueError):valid=False
        if not valid:invalid.append(key)
    return dict(passed=not different and not invalid,maps_preserved=not different,
        remainders_nonwidening=not invalid,different_fields=different,invalid_remainders=invalid,
        fields_checked=len(MATCHED_FIELDS))


def bridge(report,reference,proof,native_center,scale):
    if (not isinstance(report,candidate.TransformEnclosure) or not isinstance(reference,TransformReference)
            or not isinstance(proof,(DirectionalAcceleration,ConditionedAcceleration))):
        raise ValueError('typed directional bound, reference and proof required')
    metadata=deepcopy(report.metadata);r=reference.parent
    proof.match(reference.report(),metadata['lower'],metadata['upper'])
    if (metadata['conditioning']!=proof.report() or metadata['source_id']!=r.source_id
            or metadata['reference_binding']!=reference.binding
            or metadata['normalized_center']!=r.center.tolist()
            or metadata['retained_acceleration_remainder']!=reference.acceleration.remainder
            or report.previous_coefficients.binding!=r.binding
            or report.acceleration_coefficients.binding!=reference.acceleration.binding
            or report.transform_coefficients.binding!=reference.transform.binding):
        raise ValueError('directional source, common blocks or retained remainder changed')
    center=np.asarray(native_center,float);units=np.asarray(scale,float)
    if center.shape!=(3,) or units.shape!=(3,) or not np.all(np.isfinite(center)) or not np.all(np.isfinite(units)) or np.any(units<=0):
        raise ValueError('three finite native coordinates and positive scales required')
    differences=[abs(F(float(a))-F(float(b))) for a,b in zip(center,report.center)]
    if max(d*F(float(s)) for d,s in zip(differences,units))>F(1,1000000):
        raise ValueError('directional native center exceeds qualified agreement limit')
    remainders=[endpoint(F(float(v))+d,True) for v,d in zip(report.unshared_remainder,differences)]
    metadata.update(native_candidate_version=candidate.VERSION,center_transfer=list(map(str,differences)),
        bridge_version='ilvis0-direct-source-joint-schema-v1',original_bound_center=report.center.tolist())
    value=TransformEnclosure(center,remainders,report.previous_coefficients,report.acceleration_coefficients,
        report.transform_coefficients,metadata)
    _force_source(value,reference)
    return value


def training_rows(training,reports):
    region=training['region'];times=training['times_s'];n=len(times)
    if (region['parameter_count']!=78 or len(region['center'])!=78 or len(reports)!=n
            or not 1<=n<=32 or len(region['design'])!=3*n):
        raise ValueError('complete bounded training epochs and all 78 enclosure columns required')
    rows=[];lower=[];upper=[];noise=F(.001);arithmetic=F(region['arithmetic_allowance'])
    if arithmetic<0:raise ValueError('nonnegative saved arithmetic allowance required')
    for epoch,report in enumerate(reports):
        if report['time_s']!=times[epoch] or report['center']!=training['nominal'][epoch]:
            raise ValueError('training time or transferred native center changed')
        matrix=scaled_design(training['jacobian'][epoch],report,region['coordinate_scale'])
        if matrix!=region['design'][3*epoch:3*epoch+3]:
            raise ValueError('a training coefficient changed; no silent basis transfer permitted')
        for axis,row in enumerate(matrix):
            if not math.isfinite(report['unshared_remainder'][axis]) or report['unshared_remainder'][axis]<0:
                raise ValueError('nonnegative finite propagation remainder required')
            shift=sum((F(v)*F(c) for v,c in zip(row,region['center'][:51],strict=True)),F(0))
            delta=(F(training['observations'][epoch][axis])-F(training['nominal'][epoch][axis]))*F(region['coordinate_scale'][axis])
            radius=F(report['unshared_remainder'][axis])*F(region['coordinate_scale'][axis])+noise+arithmetic
            rows.append(row+[0.]*27);lower.append(endpoint(shift+delta-radius,False));upper.append(endpoint(shift+delta+radius,True))
    return dict(design=rows+[[-v for v in row] for row in rows],upper=upper+[-v for v in lower],
        physical_parameter_count=27,parameter_count=78,original_expression_columns=51,
        observation_allowance_m=.001,arithmetic_allowance_m=float(arithmetic),new_rows=6*n)
