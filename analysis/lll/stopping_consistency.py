# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite saved-point derivative diagnostics; no nonlinear optimization."""
import numpy as np

VERSION='saved-point-stopping-consistency-v1'
STEPS=(1e-3,1e-4,1e-5)


def probe(evaluate, point, *, bounds, frozen_probe, reserve, check_continue,
          maximum_evaluations=170, steps=STEPS):
    """Keep every coordinate, use feasible stencils and charge before execution.

    Derivative/repeatability discrepancies are retained outcomes. Invalid inputs
    or exhausted allowances raise without attempting another evaluation.
    The caller supplies the unchanged physical stopping probe and its metric.
    """
    u=np.asarray(point,float)
    low,high=(np.asarray(v,float) for v in bounds)
    if (u.ndim!=1 or not len(u) or low.shape!=u.shape or high.shape!=u.shape
            or not all(np.all(np.isfinite(v)) for v in (u,low,high))
            or np.any(low>=high) or np.any(u<low) or np.any(u>high)
            or type(maximum_evaluations) is not int or not 1<=maximum_evaluations<=170
            or len(steps)!=3 or any(not np.isfinite(h) or h<=0 for h in steps)
            or any(not callable(v) for v in (evaluate,frozen_probe,reserve,check_continue))):
        raise ValueError('finite feasible saved point, full bounds and diagnostic allowance required')
    stencils=[]
    for k in range(len(u)):
        entries=[]
        for h in steps:
            if low[k]<=u[k]-h and u[k]+h<=high[k]: kind='centered'
            elif u[k]+2*h<=high[k]: kind='forward'
            elif u[k]-2*h>=low[k]: kind='backward'
            else: raise ValueError('finite difference stencil cannot fit inside the declared box')
            entries.append((float(h),kind))
        stencils.append(entries)
    calls=0;shape=None;last=None
    def counted(p,fresh=False):
        nonlocal calls,shape,last
        v=np.asarray(p,float)
        if v.shape!=u.shape or not np.all(np.isfinite(v)) or np.any(v<low) or np.any(v>high):
            raise ValueError('infeasible diagnostic point')
        check_continue()
        if calls>=maximum_evaluations:raise RuntimeError('diagnostic evaluation allowance exhausted')
        reserve(evaluations=1);calls+=1
        r,j,b=evaluate(v.copy(),fresh=True)
        r,j=np.asarray(r,float),np.asarray(j,float)
        if (r.ndim!=1 or not len(r) or j.shape!=(len(r),len(u))
                or not np.all(np.isfinite(r)) or not np.all(np.isfinite(j))
                or (shape is not None and r.shape!=shape)):
            raise ValueError('finite residual and every unchanged derivative column required')
        shape=r.shape;last=(v.copy(),r.copy(),j.copy())
        return r.copy(),j.copy(),b
    base=[counted(u,True) for _ in range(3)]
    r,j,_=base[0]
    repeat=dict(exact=all(np.array_equal(r,v[0]) and np.array_equal(j,v[1]) for v in base[1:]),
        residual_max_abs=max(float(np.max(abs(v[0]-r))) for v in base[1:]),
        jacobian_max_abs=max(float(np.max(abs(v[1]-j))) for v in base[1:]))
    derivatives=[]
    for k,entries in enumerate(stencils):
        rows=[]
        for h,kind in entries:
            direction=np.zeros_like(u);direction[k]=h
            if kind=='centered':
                a=counted(u+direction)[0];b=counted(u-direction)[0]
                difference=(a-b)/(2*h)
            else:
                sign=1 if kind=='forward' else -1
                a=counted(u+sign*direction)[0];b=counted(u+2*sign*direction)[0]
                difference=sign*(-3*r+4*a-b)/(2*h)
            rows.append(dict(step=h,stencil=kind,error_norm=float(np.linalg.norm(difference-j[:,k])),
                analytic_norm=float(np.linalg.norm(j[:,k])),difference_norm=float(np.linalg.norm(difference)),
                difference=difference.tolist()))
        derivatives.append(dict(column=k,analytic=j[:,k].tolist(),steps=rows))
    # All native evaluations made by the supplied unchanged probe also pass
    # through the same charged callback; at most one fresh evaluation is allowed.
    before=calls
    def stopping_evaluate(p,fresh=False):
        if calls>before:raise RuntimeError('one unchanged fresh stopping evaluation permitted')
        return counted(p,fresh)
    stopping=frozen_probe(u.copy(),r.copy(),j.copy(),stopping_evaluate)
    signed=None
    if calls>before:
        v,fresh,_=last;cost=float(r@r);predicted=r+j@(v-u)
        signed=dict(actual_cost_delta=float(fresh@fresh)-cost,
            predicted_cost_delta=float(predicted@predicted)-cost,
            point=v.tolist(),cost=float(fresh@fresh))
    singular=np.linalg.svd(j,compute_uv=False)
    return dict(version=VERSION,columns=len(u),evaluations=calls,maximum_evaluations=maximum_evaluations,
        point=u.tolist(),cost=float(r@r),repeatability=repeat,derivatives=derivatives,
        stopping_probe=stopping,signed_probe=signed,singular_values=singular.tolist(),
        singular_value_ratio=float(singular[-1]/singular[0]) if singular[0]>0 else 0.,
        nonlinear_fit_starts=0,labels_changed=False,confidence_calibrated=False,
        scientific_decision='abstain')
