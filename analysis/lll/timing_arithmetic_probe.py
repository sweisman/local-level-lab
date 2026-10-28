# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite matched derivatives at a saved point; no fit or stopping relabeling."""
import numpy as np

MODES=('baseline','boundary','longitude','both')
STEPS=(1e-3,1e-4,1e-5)


def full_precision_probe(evaluate,point,*,active,saved_cost,select,reserve,check_continue,bounds,frozen_probe):
    """One exact original replay, then the unchanged complete-column probe."""
    from lll.stopping_consistency import probe as complete
    u=np.asarray(point,float);lo,hi=(np.asarray(v,float) for v in bounds);active=list(active)
    if (u.ndim!=1 or not len(u) or len(active)!=len(u) or len(set(active))!=len(active)
            or lo.shape!=u.shape or hi.shape!=u.shape or np.any(lo>=hi)
            or not all(np.all(np.isfinite(v)) for v in (u,lo,hi)) or np.any(u<lo) or np.any(u>hi)
            or not np.isfinite(saved_cost) or saved_cost<0
            or any(not callable(v) for v in (evaluate,select,reserve,check_continue,frozen_probe))):
        raise ValueError('finite complete saved-point configuration required')
    select('baseline');check_continue();reserve(evaluations=1)
    r,j,b=evaluate(u.copy(),fresh=True);r,j=np.asarray(r,float),np.asarray(j,float)
    if (r.ndim!=1 or not len(r) or j.shape!=(len(r),len(u))
            or not all(np.all(np.isfinite(v)) for v in (r,j)) or float(r@r)!=saved_cost):
        raise ValueError('exact finite original baseline replay required')
    baseline=dict(cost=float(r@r),residual=r.tolist(),jacobian=j.tolist(),boundaries=b)
    select('compensated')
    result=complete(evaluate,u,bounds=(lo,hi),frozen_probe=frozen_probe,reserve=reserve,
        check_continue=check_continue,maximum_evaluations=170,steps=STEPS)
    result.update(baseline=baseline,candidate_mode='compensated',candidate_evaluations=result['evaluations'],
        evaluations=1+result['evaluations'],maximum_evaluations=171,baseline_evaluations=1)
    return result


def probe(evaluate,point,*,active,saved_cost,select,reserve,check_continue,bounds,
          maximum_evaluations=64):
    u=np.asarray(point,float);lo,hi=(np.asarray(v,float) for v in bounds);active=list(active)
    if (u.ndim!=1 or not len(u) or len(active)!=len(u) or len(set(active))!=len(active)
            or not {'gyro_bias_z','time_offset'}<=set(active) or lo.shape!=u.shape or hi.shape!=u.shape
            or not all(np.all(np.isfinite(v)) for v in (u,lo,hi)) or np.any(lo>=hi)
            or np.any(u<lo) or np.any(u>hi) or not np.isfinite(saved_cost) or saved_cost<0
            or type(maximum_evaluations) is not int or not 1<=maximum_evaluations<=64
            or any(not callable(v) for v in (evaluate,select,reserve,check_continue))):
        raise ValueError('finite saved point, complete columns and bounded diagnostic required')
    calls=0;shape=None;settings=[]
    def counted(v):
        nonlocal calls,shape
        check_continue()
        if calls>=maximum_evaluations:raise RuntimeError('diagnostic evaluation allowance exhausted')
        if v.shape!=u.shape or np.any(v<lo) or np.any(v>hi):raise ValueError('infeasible diagnostic point')
        reserve(evaluations=1);calls+=1
        r,j,b=evaluate(v.copy(),fresh=True);r,j=np.asarray(r,float),np.asarray(j,float)
        if (r.ndim!=1 or not len(r) or j.shape!=(len(r),len(u))
                or not all(np.all(np.isfinite(a)) for a in (r,j)) or (shape is not None and r.shape!=shape)):
            raise ValueError('finite residual and every original derivative column required')
        shape=r.shape
        return r.copy(),j.copy(),b
    for mode in MODES:
        select(mode);before=calls;r,j,b=counted(u);cost=float(r@r)
        if mode=='baseline' and cost!=saved_cost:raise ValueError('original baseline cost replay is not exact')
        columns=[]
        for name in ('gyro_bias_z','time_offset'):
            col=active.index(name);curves=[]
            for h in STEPS:
                step=np.zeros_like(u);step[col]=h
                if lo[col]<=u[col]-h and u[col]+h<=hi[col]:
                    stencil='centered';a=counted(u+step)[0];z=counted(u-step)[0];fd=(a-z)/(2*h)
                else:
                    sign=1 if u[col]+2*h<=hi[col] else -1
                    if not lo[col]<=u[col]+2*sign*h<=hi[col]:raise ValueError('feasible difference stencil required')
                    stencil='forward' if sign==1 else 'backward'
                    a=counted(u+sign*step)[0];z=counted(u+2*sign*step)[0]
                    fd=sign*(-3*r+4*a-z)/(2*h)
                error=fd-j[:,col];an=float(np.linalg.norm(j[:,col]));dn=float(np.linalg.norm(fd))
                curves.append(dict(step=h,stencil=stencil,analytic_norm=an,difference_norm=dn,
                    error_norm=float(np.linalg.norm(error)),signed_error=error.tolist(),difference=fd.tolist(),
                    comparison_scale=1e-8+1e-6*max(an,dn)))
            columns.append(dict(parameter=name,column=col,analytic=j[:,col].tolist(),steps=curves))
        if calls-before>16:raise RuntimeError('per-setting allowance exceeded')
        settings.append(dict(mode=mode,evaluations=calls-before,cost=cost,residual=r.tolist(),
            jacobian=j.tolist(),boundaries=b,derivatives=columns))
    return dict(version='saved-point-timing-arithmetic-probe-v1',settings=settings,columns=len(u),
        evaluations=calls,maximum_evaluations=maximum_evaluations,point=u.tolist(),
        stopping_probe=dict(passed=None,not_executed=True),labels_changed=False,nonlinear_fit_starts=0,
        confidence_calibrated=False,scientific_decision='abstain')
