# SPDX-License-Identifier: AGPL-3.0-or-later
"""An exact algebraic bound on an already-defined nonlinear remainder.

This changes no calibration box, reference, derivative or shared coefficient.
The supplied change bound must hold on the SAME domain used by its consumer.
Native propagation and the adequacy of that domain are separate qualifications.
"""
from fractions import Fraction as F
import hashlib
import json
import math


def _f(value):
    try:
        value=float(value)
        if not math.isfinite(value):raise ValueError('finite coefficients required')
        return F(value)
    except (ValueError,TypeError,OverflowError):raise ValueError('finite coefficients required') from None


def enclose(jacobian,lower,upper,center,component_change,original_remainder):
    """Bound r=f-f0-J(x-x0) using |f_i-f0_i|<=D_i and a physical box.

The center need not lie in the box. A small total function change alone does
not make the Taylor remainder small: it can cancel a large linear response.
Every linear response is retained before intersecting the original norm cap.
"""
    from lll.ilvis0_exact_scale import sqrt_upper
    from lll.ilvis0_saved_prediction_audit import endpoint
    n=len(lower)
    if (not 1<=n<=256 or len(upper)!=n or len(center)!=n or len(jacobian)!=3
            or any(len(row)!=n for row in jacobian) or len(component_change)!=3):
        raise ValueError('complete physical box, three Jacobian rows and component bounds required')
    lo=list(map(_f,lower));hi=list(map(_f,upper));z=list(map(_f,center))
    jac=[list(map(_f,row)) for row in jacobian];change=list(map(_f,component_change));original=_f(original_remainder)
    if any(a>b for a,b in zip(lo,hi,strict=True)) or any(v<0 for v in [*change,original]):
        raise ValueError('ordered domain and nonnegative supplied bounds required')
    linear_lo=[];linear_hi=[];rest_lo=[];rest_hi=[];components=[]
    for row,d in zip(jac,change,strict=True):
        a=sum((min(v*(x-c),v*(y-c)) for v,x,y,c in zip(row,lo,hi,z,strict=True)),F(0))
        b=sum((max(v*(x-c),v*(y-c)) for v,x,y,c in zip(row,lo,hi,z,strict=True)),F(0))
        left=max(-original,-d-b);right=min(original,d-a)
        if left>right:raise ValueError('inconsistent remainder restrictions; no region may be silently discarded')
        linear_lo.append(str(a));linear_hi.append(str(b));rest_lo.append(str(left));rest_hi.append(str(right))
        components.append(endpoint(max(abs(left),abs(right)),True))
    square=sum((F(v)**2 for v in components),F(0))
    radius=min(float(original),sqrt_upper(square))
    definition=dict(jacobian=[[str(v) for v in row] for row in jac],lower=list(map(str,lo)),upper=list(map(str,hi)),
        center=list(map(str,z)),component_change=list(map(str,change)),original_remainder=str(original))
    binding=hashlib.sha256(json.dumps(definition,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return dict(version='ilvis0-change-conditioned-taylor-remainder-v1',input_binding=binding,
        linear_lower=linear_lo,linear_upper=linear_hi,remainder_lower=rest_lo,remainder_upper_components=rest_hi,
        component_upper=components,remainder_upper=radius,original_remainder=float(original),
        physical_parameter_count=n,requires_original_change_domain=True,changes_shared_coefficients=False,
        native_propagation_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')
