# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite branch-local derivatives and correction decomposition; never a fit."""
import math
import numpy as np

SPACINGS_S=(1e-5,1e-6,1e-7)


def probe(evaluate,point,*,active,correction,timing_center,timing_scale,expected_cost,
          expected_actual_cost_change,reserve,check_continue,bounds,maximum_evaluations=64,
          expected_linearization=None):
    u=np.asarray(point,float);delta=np.asarray(correction,float);active=list(active)
    lo,hi=(np.asarray(v,float) for v in bounds)
    if (u.ndim!=1 or not 1<=len(u)<=27 or delta.shape!=u.shape or len(active)!=len(u)
            or len(set(active))!=len(active) or 'time_offset' not in active
            or lo.shape!=u.shape or hi.shape!=u.shape or np.any(lo>=hi)
            or not all(np.all(np.isfinite(v)) for v in (u,delta,lo,hi)) or np.any(u<lo) or np.any(u>hi)
            or not all(math.isfinite(v) for v in (timing_center,timing_scale,expected_cost,expected_actual_cost_change))
            or timing_scale<=0 or expected_cost<0 or expected_actual_cost_change<0
            or type(maximum_evaluations) is not int or not 1<=maximum_evaluations<=64
            or any(not callable(v) for v in (evaluate,reserve,check_continue))):
        raise ValueError('finite saved point, full columns and fixed bounded diagnostic required')
    column=active.index('time_offset');center=float(timing_center)
    if center<lo[column]-1e-10 or center>hi[column]+1e-10:
        raise ValueError('timing boundary is outside the physical bounds')
    center=float(np.clip(center,lo[column],hi[column]))
    if np.any(u+delta<lo-1e-10) or np.any(u+delta>hi+1e-10):
        raise ValueError('saved correction violates physical bounds')
    calls=0;shape=None
    def counted(v):
        nonlocal calls,shape
        check_continue()
        if calls>=maximum_evaluations:raise RuntimeError('diagnostic evaluation allowance exhausted')
        if v.shape!=u.shape or np.any(v<lo) or np.any(v>hi):raise ValueError('infeasible diagnostic point')
        reserve(evaluations=1);calls+=1
        rr,jj,b=evaluate(v.copy(),fresh=True);rr,jj=np.asarray(rr,float),np.asarray(jj,float)
        if (rr.ndim!=1 or not len(rr) or jj.shape!=(len(rr),len(u))
                or not all(np.all(np.isfinite(a)) for a in (rr,jj)) or shape is not None and rr.shape!=shape):
            raise ValueError('finite residual and every original derivative column required')
        shape=rr.shape
        return rr.copy(),jj.copy(),b
    r,j,b=counted(u);cost=float(r@r)
    if cost!=expected_cost:raise ValueError('exact saved baseline cost replay required')
    if expected_linearization is not None and (
            not np.array_equal(r,np.asarray(expected_linearization['residual'],float))
            or not np.array_equal(j,np.asarray(expected_linearization['jacobian'],float))):
        raise ValueError('exact saved residual and complete Jacobian replay required')
    repeated=counted(u)
    if not np.array_equal(r,repeated[0]) or not np.array_equal(j,repeated[1]):
        raise ValueError('saved residual and Jacobian do not replay exactly')
    corrections=[]
    for kind in ('full','time_only','other_only'):
        step=delta.copy()
        if kind=='time_only':step[:]=0.;step[column]=delta[column]
        elif kind=='other_only':step[column]=0.
        shifted=np.clip(u+step,lo,hi);actual=counted(shifted)[0];linear=r+j@(shifted-u)
        actual_cost=float(actual@actual);predicted_cost=float(linear@linear)
        change=abs(actual_cost-cost)/max(actual_cost,cost,1.)
        corrections.append(dict(kind=kind,point=shifted.tolist(),actual_cost=actual_cost,
            actual_cost_delta=actual_cost-cost,predicted_cost_delta=predicted_cost-cost,
            relative_cost_change=change,residual_remainder_norm=float(np.linalg.norm(actual-linear))))
    full_matches=math.isclose(corrections[0]['relative_cost_change'],expected_actual_cost_change,
                             rel_tol=1e-7,abs_tol=1e-12)
    at_center=u.copy();at_center[column]=center;center_value=counted(at_center)
    branches=[]
    for spacing in SPACINGS_S:
        h=spacing/timing_scale;epsilon=h/4
        for side in (-1,1):
            v=u.copy();v[column]=center+side*h
            entry=dict(side=side,spacing_s=spacing,point=v.tolist(),feasible=bool(
                lo[column]<=v[column]-epsilon and v[column]+epsilon<=hi[column]))
            if not entry['feasible']:branches.append(entry);continue
            rr,jj,bb=counted(v);step=np.zeros_like(u);step[column]=epsilon
            plus=counted(v+step)[0];minus=counted(v-step)[0];fd=(plus-minus)/(2*epsilon)
            analytic=jj[:,column];an=float(np.linalg.norm(analytic));dn=float(np.linalg.norm(fd))
            scale=1e-8+1e-6*max(an,dn);error=float(np.linalg.norm(fd-analytic))
            branches.append(dict(entry,cost=float(rr@rr),residual=rr.tolist(),jacobian=jj.tolist(),
                boundaries=bb,analytic=analytic.tolist(),difference=fd.tolist(),analytic_norm=an,
                difference_norm=dn,error_norm=error,comparison_scale=scale,error_ratio=error/scale))
    return dict(version='saved-timing-boundary-probe-v1',point=u.tolist(),columns=len(u),
        baseline=dict(cost=cost,residual=r.tolist(),jacobian=j.tolist(),boundaries=b),
        repeatability=dict(exact=True),corrections=corrections,full_correction_replayed=full_matches,
        center=dict(normalized_time_offset=center,cost=float(center_value[0]@center_value[0])),
        branches=branches,evaluations=calls,maximum_evaluations=maximum_evaluations,
        stopping_probe=dict(passed=None,not_executed=True),labels_changed=False,
        nonlinear_fit_starts=0,confidence_calibrated=False,scientific_decision='abstain')
