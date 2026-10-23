# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact dual support certificates for necessary affine training constraints.

An LP provides a proposal only. For ANY nonnegative lambda, feasibility of
A*x<=b implies c*x<=lambda*b+max_box((c-A.T*lambda)*x). Every term of that
certificate is evaluated as a rational number from the supplied binary inputs.
Neither optimizer completion nor an infeasibility status is a scientific gate.
"""
from fractions import Fraction as F
import math
import warnings

import numpy as np
from scipy.optimize import linprog,OptimizeWarning


def _inputs(lower,upper,design,bound,objective):
    lo=np.asarray(lower,float);hi=np.asarray(upper,float);a=np.asarray(design,float)
    b=np.asarray(bound,float);c=np.asarray(objective,float)
    if (lo.ndim!=1 or not len(lo) or hi.shape!=lo.shape or c.shape!=lo.shape
            or a.ndim!=2 or a.shape[1]!=len(lo) or b.shape!=(len(a),)
            or a.size>65536 or len(lo)>256 or np.any(lo>hi)
            or any(not np.all(np.isfinite(v)) for v in (lo,hi,a,b,c))):
        raise ValueError('finite full parameter box and compatible bounded-size inequalities required')
    return lo,hi,a,b,c


def upper(lower,upper,design,bound,objective,multipliers):
    lo,hi,a,b,c=_inputs(lower,upper,design,bound,objective)
    weights=np.asarray(multipliers,float)
    if weights.shape!=b.shape or not np.all(np.isfinite(weights)) or np.any(weights<0):
        raise ValueError('finite nonnegative inequality multipliers required')
    lam=[F(float(v)) for v in weights]
    value=sum((w*F(float(v)) for w,v in zip(lam,b)),F(0))
    for j,coefficient in enumerate(c):
        remainder=F(float(coefficient))-sum((w*F(float(row[j])) for w,row in zip(lam,a)),F(0))
        value+=remainder*F(float(hi[j] if remainder>=0 else lo[j]))
    try:endpoint=float(value)
    except OverflowError:raise ValueError('finite outward endpoint unsupported') from None
    if not math.isfinite(endpoint):raise ValueError('finite outward endpoint unsupported')
    if F(endpoint)<value:endpoint=math.nextafter(endpoint,math.inf)
    if not math.isfinite(endpoint):raise ValueError('finite outward endpoint unsupported')
    return dict(upper=endpoint,exact_upper=value,multipliers=weights.copy(),parameter_count=len(lo),
        certificate='exact_nonnegative_dual_plus_full_box',region_emptiness_assessed=False,
        nonlinear_allowance_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')


def propose(lower,upper_box,design,bound,objective):
    lo,hi,a,b,c=_inputs(lower,upper_box,design,bound,objective)
    weights=np.zeros(len(b));used=False
    # HiGHS supports the forwarded threads option. SciPy warns solely because
    # it is not in its wrapper's option list; do not suppress other warnings.
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore',message='Unrecognized options detected:.*threads',category=OptimizeWarning)
            result=linprog(-c,A_ub=a,b_ub=b,bounds=list(zip(lo,hi)),method='highs-ds',
                options=dict(threads=1,time_limit=1.))
        if result.success:
            proposed=np.asarray(result.ineqlin.marginals,float)
            if proposed.shape==b.shape and np.all(np.isfinite(proposed)):
                weights=np.maximum(0.,-proposed);used=True
    except (ValueError,RuntimeError,ArithmeticError,AttributeError):pass
    certificate=upper(lo,hi,a,b,c,weights)
    fallback=upper(lo,hi,a,b,c,np.zeros(len(b)))
    # A mathematically valid but poor dual must not make the box bound worse.
    if certificate['exact_upper']>fallback['exact_upper']:certificate=fallback;used=False
    return dict(certificate,proposal_used=used,proposal_threads=1,proposal_cooperative_seconds=1.)


def project_coordinates(lower,upper_box,design,bound,*,axes,reserve):
    """Outer coordinate bounds; all physical/shared columns remain in each LP.

    Each proposal reserves its two internal exact checks plus an independent
    standard-library check. Failed proposals retain the original box. Coordinate
    intervals do not replace the original coupled inequalities or prove that
    any point in their Cartesian product is feasible.
    """
    from lll.ilvis0_saved_prediction_audit import support as independent,endpoint
    lo,hi,a,b,_=_inputs(lower,upper_box,design,bound,np.zeros(len(lower)))
    axes=list(axes)
    if not axes or any(type(i) is not int or not 0<=i<len(lo) for i in axes) or len(set(axes))!=len(axes):
        raise ValueError('nonempty unique in-range integer axes required')
    rows=[]
    for axis in axes:
        certificates=[]
        for sign in (1,-1):
            objective=np.zeros(len(lo));objective[axis]=sign
            reserve(1,3)
            proposal=propose(lo,hi,a,b,objective)
            value=independent(lo.tolist(),hi.tolist(),a.tolist(),b.tolist(),objective.tolist(),
                proposal['multipliers'].tolist())
            if value!=proposal['exact_upper']:raise ValueError('independent coordinate support disagrees')
            certificates.append(dict(sign=sign,exact_upper=str(value),
                multipliers=proposal['multipliers'].tolist(),proposal_used=proposal['proposal_used']))
        left=max(float(lo[axis]),endpoint(-F(certificates[1]['exact_upper']),False))
        right=min(float(hi[axis]),endpoint(F(certificates[0]['exact_upper']),True))
        if left>right:raise ValueError('contradictory coordinate supports require diagnosis')
        width=float(hi[axis])-float(lo[axis])
        rows.append(dict(parameter_index=axis,previous_lower=float(lo[axis]),previous_upper=float(hi[axis]),
            lower=left,upper=right,width_ratio=(right-left)/width if width else 1.,certificates=certificates))
    return dict(version='lll-exact-coordinate-projection-v1',parameter_count=len(lo),axes=axes,
        coordinates=rows,inequalities_preserved=True,region_emptiness_assessed=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
