# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-polytope diagnosis; exact dual bounds, never native integration."""
from fractions import Fraction as F
import math

import numpy as np
from . import ilvis0_affine_support as support


def project(lower,upper,design,bound,*,before_proposal):
    lo=np.asarray(lower,float);hi=np.asarray(upper,float)
    if lo.shape!=(27,) or hi.shape!=lo.shape:raise ValueError('all 27 ordered coordinates required')
    rows=[]
    for axis in range(27):
        objective=np.zeros(27);objective[axis]=1.
        before_proposal();high=support.propose(lo,hi,design,bound,objective)
        before_proposal();low=support.propose(lo,hi,design,bound,-objective)
        left=max(float(lo[axis]),-low['upper']);right=min(float(hi[axis]),high['upper'])
        if left>right:raise ValueError('contradictory exact coordinate support requires diagnosis')
        rows.append(dict(parameter_index=axis,previous_lower=float(lo[axis]),previous_upper=float(hi[axis]),
            lower=left,upper=right,upper_certificate=str(high['exact_upper']),negated_lower_certificate=str(low['exact_upper']),
            upper_multipliers=high['multipliers'],lower_multipliers=low['multipliers'],
            upper_proposal_used=high['proposal_used'],lower_proposal_used=low['proposal_used'],
            width_ratio=(right-left)/(hi[axis]-lo[axis]) if hi[axis]>lo[axis] else 1.,
            narrowed=bool(right-left<(hi[axis]-lo[axis])*(1.-1e-6))))
    return rows


def width_breakdown(lower,upper,remainder,certificates,*,arithmetic=1e-5):
    if len(lower)!=3 or len(upper)!=3 or len(remainder)!=3 or len(certificates)!=3 or not math.isfinite(arithmetic) or arithmetic<0:
        raise ValueError('complete three-axis saved support required')
    affine=[];nonlinear=[];errors=[];actual=[]
    for lo,hi,r,c in zip(lower,upper,remainder,certificates):
        a=F(c['upper'])+F(c['negated_lower']);n=2*F(float(r))
        width=F(float(hi))-F(float(lo));difference=width-a-n-2*F(float(arithmetic))
        if a<0 or n<0 or difference<0 or difference>F(1,100000000):
            raise ValueError('saved endpoints do not reconcile with exact affine/nonlinear widths')
        affine.append(float(a));nonlinear.append(float(n));errors.append(float(difference));actual.append(float(width))
    return dict(affine_width_m=affine,nonlinear_width_m=nonlinear,arithmetic_width_m=2*arithmetic,
        saved_width_m=actual,maximum_reconciliation_error_m=max(errors))
