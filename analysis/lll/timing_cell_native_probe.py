# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fresh physical checks of saved proposals; no solving or convergence decision."""
import math
import numpy as np


def probe(evaluate,point,*,active,proposals,expected_cost,expected_linearization,bounds,
          physical_step,reserve,check_continue,maximum_evaluations=8):
    from lll.ilvis0_solver_position import POLICY
    from lll.ilvis0_solver_refinement import POLICY as STOPPING,projected_stationarity
    u=np.asarray(point,float);names=list(active);lo,hi=(np.asarray(v,float) for v in bounds)
    if (u.shape!=(27,) or len(names)!=27 or len(set(names))!=27 or 'time_offset' not in names
            or lo.shape!=u.shape or hi.shape!=u.shape or np.any(lo>=hi)
            or not all(np.all(np.isfinite(v)) for v in (u,lo,hi)) or np.any(u<lo) or np.any(u>hi)
            or type(maximum_evaluations) is not int or not 2<maximum_evaluations<=8
            or not isinstance(proposals,list) or len(proposals) not in (3,6)
            or len(proposals)+2>maximum_evaluations or not math.isfinite(expected_cost) or expected_cost<0
            or any(not callable(v) for v in (evaluate,physical_step,reserve,check_continue))):
        raise ValueError('complete finite saved proposals and eight-sweep cap required')
    checked=[];indices=set()
    for item in proposals:
        p,a,b=(np.asarray(item[k],float) for k in ('point','lower','upper'))
        index=item['index'];cost=item['predicted_cost'];predicted=np.asarray(item['predicted_residual'],float)
        if (type(index) is not int or index<0 or index in indices or item['active']!=names
                or any(v.shape!=u.shape or not np.all(np.isfinite(v)) for v in (p,a,b))
                or np.any(a>=b) or np.any(a<lo) or np.any(b>hi) or np.any(p<a) or np.any(p>b)
                or not math.isfinite(cost) or cost<0 or predicted.ndim!=1 or not len(predicted)
                or not np.all(np.isfinite(predicted))
                or not math.isclose(float(predicted@predicted),cost,rel_tol=1e-12,abs_tol=1e-12)):
            raise ValueError('every proposal must preserve columns and its feasible physical timing cell')
        indices.add(index);checked.append((item,p))
    calls=0;shape=None
    def counted(p):
        nonlocal calls,shape
        check_continue()
        if calls>=maximum_evaluations:raise RuntimeError('physical proposal allowance exhausted')
        reserve(evaluations=1);calls+=1
        rr,jj,b=evaluate(p.copy(),fresh=True);rr,jj=np.asarray(rr,float),np.asarray(jj,float)
        if (rr.ndim!=1 or not len(rr) or jj.shape!=(len(rr),27)
                or not np.all(np.isfinite(rr)) or not np.all(np.isfinite(jj))
                or shape is not None and shape!=rr.shape):
            raise ValueError('finite unchanged residual shape and all derivative columns required')
        shape=rr.shape
        return rr.copy(),jj.copy(),b
    r,j,b=counted(u);cost=float(r@r)
    if (cost!=expected_cost or not np.array_equal(r,np.asarray(expected_linearization['residual'],float))
            or not np.array_equal(j,np.asarray(expected_linearization['jacobian'],float))):
        raise ValueError('exact saved baseline residual, cost and Jacobian required')
    rr,jj,_=counted(u)
    if not np.array_equal(rr,r) or not np.array_equal(jj,j):
        raise ValueError('exact baseline repeat required')
    rows=[]
    for item,p in checked:
        rr,jj,bb=counted(p);actual=float(rr@rr)
        predicted=np.asarray(item['predicted_residual'],float)
        if predicted.shape!=r.shape:raise ValueError('complete saved linear prediction required')
        difference=np.asarray(physical_step(rr-r),float)
        if difference.ndim!=2 or difference.shape[1]!=3 or not len(difference) or not np.all(np.isfinite(difference)):
            raise ValueError('finite common NEU position change required')
        rms=np.sqrt(np.mean(difference**2,axis=0));maximum=np.max(abs(difference),axis=0)
        change=abs(actual-cost)/max(actual,cost,1.)
        stationarity=float(projected_stationarity(p,rr,jj)[0])
        rows.append(dict(index=item['index'],point=p.tolist(),residual=rr.tolist(),jacobian=jj.tolist(),
            boundaries=bb,actual_cost=actual,actual_cost_delta=actual-cost,predicted_cost=item['predicted_cost'],
            prediction_cost_error=actual-item['predicted_cost'],relative_cost_change=change,
            residual_remainder_norm=float(np.linalg.norm(rr-predicted)),
            stationarity=stationarity,position_delta_neu_m=difference.tolist(),
            position_rms_neu_m=rms.tolist(),position_max_abs_neu_m=maximum.tolist(),
            cost_stable=bool(change<=STOPPING['relative_cost_tolerance']),
            stationary=bool(stationarity<=STOPPING['stationarity_tolerance']),
            position_stable=bool(np.all(rms<=POLICY['position_rms_tolerance_m'])
                and np.all(maximum<=POLICY['position_max_tolerance_m']))))
    return dict(version='saved-timing-cell-native-probe-v1',point=u.tolist(),active_parameters=names,
        baseline=dict(cost=cost,residual=r.tolist(),jacobian=j.tolist(),boundaries=b),repeatability=dict(exact=True),
        proposals=rows,evaluations=calls,maximum_evaluations=maximum_evaluations,
        thresholds=dict(relative_cost=STOPPING['relative_cost_tolerance'],stationarity=STOPPING['stationarity_tolerance'],
            position_rms_m=POLICY['position_rms_tolerance_m'],position_max_m=POLICY['position_max_tolerance_m']),
        stopping_probe=dict(passed=None,not_executed=True),labels_changed=False,nonlinear_fit_starts=0,
        confidence_calibrated=False,scientific_decision='abstain')
