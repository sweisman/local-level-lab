# SPDX-License-Identifier: AGPL-3.0-or-later
"""Ideal initial-force center/row differences from a frozen common field.

The certificate exposes, rather than silently changes, the reference center,
all 27 rows and the nonlinear-cap check. A training consumer must qualify the
transfer of these differences separately. Existing shared columns are untouched.
"""
from fractions import Fraction as F
import numpy as np
from .ilvis0_transform_native import TransformReference
from .ilvis0_rotation_roundoff import enclose as rotation
from .ilvis0_rotation_derivative import enclose as derivative
from .ilvis0_exact_scale import sqrt_upper
from .ilvis0_saved_prediction_audit import endpoint

VERSION='ilvis0-initial-source-reference-bridge-v2'


def _norm(values):return F(sqrt_upper(sum((F(v)**2 for v in values),F(0))))


def _product(a,b):
    values=[x*y for x in a for y in b]
    return min(values),max(values)


def _linear(coefficients,intervals):
    pairs=[_product((v,v),interval) for v,interval in zip(coefficients,intervals,strict=True)]
    return sum((v[0] for v in pairs),F(0)),sum((v[1] for v in pairs),F(0))


def certify(reference,lower,upper):
    if not isinstance(reference,TransformReference):raise ValueError('typed initial source reference required')
    r=reference.parent;a=reference.acceleration;lower=np.asarray(lower,float);upper=np.asarray(upper,float)
    if (lower.shape!=(27,) or upper.shape!=(27,) or not np.all(np.isfinite(lower)) or not np.all(np.isfinite(upper))
            or np.any(lower>upper) or np.any(lower<r.lower) or np.any(upper>r.upper)):
        raise ValueError('contained physical domain required')
    limits=list(map(lambda v:F(float(v)),r.limits));center=list(map(lambda v:F(float(v)),r.center))
    p=[l*z for l,z in zip(limits,center,strict=True)];nominal=r.limits*r.center
    widths=[max(abs(F(float(lo))-z),abs(F(float(hi))-z)) for lo,hi,z in zip(lower,upper,center,strict=True)]
    dp=_norm(p[i]-F(float(nominal[i])) for i in range(3))
    rp=rotation(nominal[:3],r._r_center);dj=derivative(nominal[:3])
    initial=[[F(float(v)) for v in row] for row in r.initial_r]
    # Exponential and its first derivative are Lipschitz in a skew angle with
    # constants one; the second Fréchet derivative has norm at most one.
    local=[[(F(rp['lower'][i][j])-dp,F(rp['upper'][i][j])+dp) for j in range(3)] for i in range(3)]
    mounted=[[ _linear(initial[i],[local[k][j] for k in range(3)]) for j in range(3)] for i in range(3)]
    dmounted=[]
    for direction in range(3):
        matrix=[[(F(dj['lower'][direction][i][j])-dp,F(dj['upper'][direction][i][j])+dp)
            for j in range(3)] for i in range(3)]
        dmounted.append([[_linear(initial[i],[matrix[k][j] for k in range(3)]) for j in range(3)] for i in range(3)])
    dt=F(a.period);raw=[F(float(v)) for v in a.raw_delta_v]
    force=[(raw[i]-p[12+i]*dt)/(1+p[18+i])/dt for i in range(3)]
    source_center=[_linear(force,mounted[i]) for i in range(3)]
    jac=[[(F(0),F(0)) for _ in range(27)] for _ in range(3)]
    for axis in range(3):
        for direction in range(3):
            pose=_linear(force,dmounted[direction][axis])
            jac[axis][direction]=tuple(v*limits[direction] for v in pose)
            for column,scalar in ((12+direction,-limits[12+direction]/(1+p[18+direction])),
                    (18+direction,-force[direction]*limits[18+direction]/(1+p[18+direction]))):
                jac[axis][column]=_product(mounted[axis][direction],(scalar,scalar))
    old_center=[F(float(v)) for v in a.center]
    old_center[2]-=F(a.gravity)+p[24]
    old_jac=[[F(float(v)) for v in row] for row in a.jacobian];old_jac[2][24]-=limits[24]
    row_lower=[];row_upper=[];padding=[];center_lower=[];center_upper=[]
    for axis in range(3):
        clo=source_center[axis][0]-old_center[axis];chi=source_center[axis][1]-old_center[axis]
        center_lower.append(str(clo));center_upper.append(str(chi));lo=clo;hi=chi;rl=[];rh=[]
        for column in range(27):
            left=jac[axis][column][0]-old_jac[axis][column];right=jac[axis][column][1]-old_jac[axis][column]
            rl.append(str(left));rh.append(str(right))
            delta=(F(float(lower[column]))-center[column],F(float(upper[column]))-center[column])
            addition=_product((left,right),delta);lo+=addition[0];hi+=addition[1]
        row_lower.append(rl);row_upper.append(rh)
        padding.append(endpoint(max(abs(lo),abs(hi)),True))
    angle_change=_norm(limits[i]*widths[i] for i in range(3))
    force_change=[];force_remainder=[]
    for axis in range(3):
        db=limits[12+axis]*widths[12+axis];dg=limits[18+axis]*widths[18+axis]
        low_gain=limits[18+axis]*min(F(float(lower[18+axis])),center[18+axis])
        high_gain=limits[18+axis]*max(F(float(upper[18+axis])),center[18+axis])
        low_bias=limits[12+axis]*min(F(float(lower[12+axis])),center[12+axis])
        high_bias=limits[12+axis]*max(F(float(upper[12+axis])),center[12+axis])
        if low_gain<=-1:raise ValueError('positive physical gain denominator required')
        corners=[(raw[axis]-b*dt)/(1+g)/dt for b in (low_bias,high_bias)
            for g in (low_gain,high_gain)]
        force_change.append(max(abs(v-force[axis]) for v in corners))
        numerator=raw[axis]-p[12+axis]*dt;denominator=1+p[18+axis]
        force_remainder.append(abs(numerator)*dg*dg/(denominator**2*(1+low_gain)*dt)
            +db*dg/(denominator*(1+low_gain)))
    gram=[[sum((initial[k][i]*initial[k][j] for k in range(3)),F(0)) for j in range(3)] for i in range(3)]
    norm_initial=F(sqrt_upper(min(sum((gram[i][i] for i in range(3)),F(0)),
        max(sum((abs(v) for v in row),F(0)) for row in gram))))
    nonlinear=norm_initial*(angle_change**2*_norm(force)/2+
        min(F(2),angle_change)*_norm(force_change)+_norm(force_remainder))
    return dict(version=VERSION,reference_binding=reference.binding,source_id=r.source_id,
        lower=lower.tolist(),upper=upper.tolist(),center_lower=center_lower,center_upper=center_upper,
        row_lower=row_lower,row_upper=row_upper,padding=padding,physical_parameter_count=27,
        nonlinear_remainder=str(nonlinear),original_nonlinear_cap=a.remainder,
        nonlinear_cap_sufficient=nonlinear<=F(a.remainder),
        normalized_parameter_product_error=str(dp),nonlinear_cap_expanded=False,
        training_adapter_qualified=False,native_propagation_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
