# SPDX-License-Identifier: AGPL-3.0-or-later
"""Checked local proposals; the physical calibration domain stays unchanged."""
from fractions import Fraction as F
import math


def policy():
    return dict(initial_radius=.001,minimum_radius=1e-9,maximum_radius=.1,
        shrink=.5,grow=2.,search_margin_m=.01,advance_margin_m=.02,
        minimum_progress_m=1e-6,minimum_ratio=.1,good_ratio=.75,
        maximum_proposals=31,maximum_trial_checks=3,maximum_lp_calls_per_proposal=2,
        maximum_exact_checks_per_proposal=8,centering_progress_retention=.98)


def audit_step(problem,origin,point,*,radius):
    from lll.ilvis0_truth_probes import audit_pair
    try:
        p=list(map(float,origin['point']));q=list(map(float,point))
        value=[list(map(float,row)) for row in origin['prediction']]
        jac=[[list(map(float,row)) for row in epoch] for epoch in origin['jacobian']]
    except (TypeError,ValueError,OverflowError) as exc:
        raise ValueError('finite complete state required') from exc
    n=len(problem['training_s'])
    if (len(p)!=27 or len(q)!=27 or len(value)!=n+1 or len(jac)!=n+1
            or any(len(row)!=3 for row in value) or any(len(epoch)!=3 for epoch in jac)
            or any(len(row)!=27 for epoch in jac for row in epoch)
            or any(not math.isfinite(v) for v in p+q+[v for row in value for v in row]
                +[v for epoch in jac for row in epoch for v in row])
            or isinstance(radius,bool) or not math.isfinite(radius) or not 0<radius<=1.):
        raise ValueError('finite complete27-coordinate state and positive local radius required')
    delta=[F(float(b))-F(float(a)) for a,b in zip(p,q,strict=True)]
    maximum=max(map(abs,delta));within=maximum<=F(radius)
    inside=all(F(a)<=F(float(x))<=F(b) for a,x,b in
        zip(problem['physical_lower'],q,problem['physical_upper'],strict=True))
    if not within or not inside:
        return dict(admissible=False,maximum_step_exact=str(maximum),training_margin_exact=None,
            reason='trust radius or original physical bounds exceeded')
    predicted=[[F(value[i][j])+sum((F(c)*d for c,d in zip(jac[i][j],delta,strict=True)),F(0))
        for j in range(3)] for i in range(n+1)]
    record=dict(binding=problem['binding'],times_s=problem['training_s']+[problem['future_s']],
        point=q,prediction=predicted,status=0)
    audit=audit_pair(problem,record,record);margin=F(audit['training_margin_exact'][0])
    future=(predicted[-1][0]-F(value[-1][0]))*F(problem['coordinate_scale'][0])
    return dict(admissible=margin>=F(policy()['search_margin_m']),maximum_step_exact=str(maximum),
        training_margin_exact=str(margin),linear_north_change_exact=str(future),
        physical_parameter_count=27,physical_domain_changed=False)


def propose_step(problem,origin,*,sign,radius,reserve):
    import numpy as np
    import warnings
    from scipy.optimize import linprog,OptimizeWarning
    from lll.ilvis0_truth_probes import audit_pair
    if type(sign) is not int or sign not in (-1,1):raise ValueError('one fixed signed direction required')
    if isinstance(radius,bool) or not math.isfinite(radius) or not 0<radius<=1.:
        raise ValueError('finite positive local radius required')
    reserve()  # Both LPs and all exact checks are reserved before execution.
    settings=policy();p=np.asarray(origin['point'],float);value=np.asarray(origin['prediction'],float)
    jac=np.asarray(origin['jacobian'],float);units=np.asarray(problem['coordinate_scale'],float)
    base=audit_step(problem,origin,p,radius=radius)
    if not base['admissible']:raise ValueError('origin must be inside the declared linear search margin')
    audit_pair(problem,origin,origin)
    lo=list(map(F,problem['physical_lower']));hi=list(map(F,problem['physical_upper']))
    pf=list(map(lambda v:F(float(v)),p));rf=F(radius);margin=F(settings['search_margin_m'])
    a=(jac[:-1]*units[None,:,None]).reshape(-1,27)*radius
    residual=((value[:-1]-np.asarray(problem['observations'],float))*units).ravel()
    allowance=(np.asarray(problem['allowance_m'],float)-np.asarray(problem['numerical_error_m'],float)
        -settings['search_margin_m']).ravel()
    objective=sign*jac[-1,0]*units[0]*radius
    # Positive/negative algorithmic step variables preserve every physical column.
    # An inactive column can stay at zero, rather than taking an arbitrary box edge.
    signed=np.column_stack([a,-a]);c=np.r_[objective,-objective]
    bounds=([(0.,max(0.,min(1.,float((h-x)/rf)))) for x,h in zip(pf,hi,strict=True)]
        +[(0.,max(0.,min(1.,float((x-l)/rf)))) for x,l in zip(pf,lo,strict=True)])
    history=[];checks=2
    def solve(stage,cost,design,bound,box):
        if len(history)>=settings['maximum_lp_calls_per_proposal']:
            raise ValueError('reserved LP count exceeded')
        success=False;status=-1;message='';raw=np.array([])
        try:
            row_scale=np.maximum(1.,np.maximum(np.max(abs(design),axis=1),abs(bound)))
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore',message='Unrecognized options detected:.*threads',category=OptimizeWarning)
                result=linprog(cost,A_ub=design/row_scale[:,None],b_ub=bound/row_scale,bounds=box,
                    method='highs-ds',options=dict(threads=1,time_limit=1.,
                        primal_feasibility_tolerance=1e-9,dual_feasibility_tolerance=1e-9))
            status=int(result.status);message=str(result.message)
            raw=np.asarray(result.x,float) if result.x is not None else np.array([])
            success=bool(result.success) and raw.shape==(len(box),) and bool(np.all(np.isfinite(raw)))
        except (ValueError,RuntimeError,ArithmeticError) as exc:
            message=type(exc).__name__+': '+str(exc)
        history.append(dict(stage=stage,status=status,message=message,success=success,shape=list(raw.shape),
            solution=[float(x) if math.isfinite(float(x)) else str(x) for x in raw.ravel()]))
        return success,raw
    def represented(z):
        nonlocal checks
        delta=[F(float(x))*rf for x in z];limit=F(1)
        for x,d,l,h in zip(pf,delta,lo,hi,strict=True):
            if d:limit=min(limit,rf/abs(d),(h-x)/d if d>0 else (l-x)/d)
        for i in range(len(problem['training_s'])):
            for j in range(3):
                scale=F(problem['coordinate_scale'][j])
                r=(F(float(value[i,j]))-F(problem['observations'][i][j]))*scale
                change=sum((F(float(co))*d for co,d in zip(jac[i,j],delta,strict=True)),F(0))*scale
                allowed=F(problem['allowance_m'][i][j])-F(problem['numerical_error_m'][j])-margin
                if change:limit=min(limit,(allowed-r)/change if change>0 else (-allowed-r)/change)
        alpha=F(99,100)*max(F(0),limit)
        for _ in range(settings['maximum_trial_checks']):
            point=[float(x+alpha*d) for x,d in zip(pf,delta,strict=True)]
            audit=audit_step(problem,origin,point,radius=radius);checks+=1
            if audit['admissible']:return True,point,audit,alpha
            alpha/=2
        return False,p.tolist(),base,F(0)
    norm=max(1.,float(np.max(abs(c))))
    success,raw=solve('progress',-c/norm,np.vstack([signed,-signed]),
        np.r_[allowance-residual,allowance+residual],bounds)
    point=p.tolist();checked=base;alpha=F(0);z=np.zeros(27);centered=False
    if success:
        z=raw[:27]-raw[27:]
        success,point,checked,alpha=represented(z)
    gain=sign*F(checked.get('linear_north_change_exact','0'))
    if success and gain>0:
        # The first checked point is itself a feasible witness for this second LP.
        # Minimize normalized training residual, retaining its directional progress.
        gain_float=float(gain)
        if F(gain_float)>gain:gain_float=math.nextafter(gain_float,-math.inf)
        design=np.vstack([np.column_stack([signed,-allowance]),
            np.column_stack([-signed,-allowance]),np.r_[-c,0.][None,:]])
        bound=np.r_[-residual,residual,-gain_float]
        ok,raw_center=solve('center_training',np.r_[np.zeros(54),1.],design,bound,bounds+[(0.,1.)])
        if ok:
            z_center=raw_center[:27]-raw_center[27:54]
            valid,point_center,audit_center,alpha_center=represented(z_center)
            center_gain=sign*F(audit_center.get('linear_north_change_exact','0'))
            if (valid and center_gain>=F(settings['centering_progress_retention'])*gain
                    and F(audit_center['training_margin_exact'])>=F(checked['training_margin_exact'])):
                point=point_center;checked=audit_center;alpha=alpha_center;z=z_center;centered=True
    if checks>settings['maximum_exact_checks_per_proposal']:
        raise ValueError('reserved exact check count exceeded')
    return dict(point=point,audit=checked,lp_success=success,lp_status=history[0]['status'],
        lp_message=history[0]['message'],lp_history=history,lp_calls=len(history),centering_used=centered,
        lp_step_normalized=z.tolist(),contraction_exact=str(alpha),exact_checks=checks,
        linear_north_change_exact=checked.get('linear_north_change_exact','0'),
        physical_parameter_count=27,lp_variable_count=55 if len(history)>1 else 54,
        exact_optimum_claimed=False,region_infeasibility_claimed=False,
        numerical_error_bound_qualified=False,observational_coverage_qualified=False)


def search_witness(problem,initial,oracle,*,sign,max_queries,reserve,save):
    """Finite trust steps through the unchanged physical calibration domain."""
    import numpy as np
    from lll.ilvis0_truth_probes import audit_pair
    if type(sign) is not int or sign not in (-1,1) or type(max_queries) is not int or not 1<=max_queries<=32:
        raise ValueError('one fixed direction and at most32native batches required')
    settings=policy();cache={};calls=0;lp_calls=0;solver_calls=0;exact_checks=0;best=None
    radius=settings['initial_radius'];n=len(problem['training_s']);units=problem['coordinate_scale']
    times=problem['training_s']+[problem['future_s']]
    schema=dict(binding=problem['binding'],times_s=times,point=list(initial),
        prediction=list(problem['observations'])+[[0.,0.,0.]],status=0)
    audit_pair(problem,schema,schema)
    def query(point):
        nonlocal calls,best
        p=np.array(point,float,copy=True)
        if (p.shape!=(27,) or not np.all(np.isfinite(p))
                or np.any(p<problem['physical_lower']) or np.any(p>problem['physical_upper'])):
            raise ValueError('finite in-box point required; never clip a proposal')
        key=p.tobytes()
        if key in cache:return cache[key]
        if calls>=max_queries:raise ValueError('fixed native budget exhausted')
        reserve();calls+=1
        save('proposal',dict(index=calls,point=p.tolist(),saved_before_native=True))
        try:raw=oracle(p.copy())
        except Exception as exc:
            save('native-error',dict(index=calls,error=type(exc).__name__,message=str(exc)));raise
        save('native',dict(index=calls,output=raw))
        try:
            if type(raw['status']) is not int or raw['status']!=0:raise ValueError()
            value=np.asarray(raw['prediction'],float);jac=np.asarray(raw['jacobian'],float)
            if (value.shape!=(n+1,3) or jac.shape!=(n+1,3,27)
                    or not np.all(np.isfinite(value)) or not np.all(np.isfinite(jac))):raise ValueError()
        except (KeyError,TypeError,ValueError) as exc:
            raise ValueError('successful finite native values and all27columns required') from exc
        record=dict(binding=problem['binding'],times_s=times,point=p.tolist(),
            prediction=value.tolist(),jacobian=jac.tolist(),status=0)
        audit=audit_pair(problem,record,record);save('feasibility',dict(index=calls,audit=audit))
        score=sign*F(float(value[-1,0]))*F(units[0]);margin=F(audit['training_margin_exact'][0])
        result=dict(record=record,index=calls,margin=margin,score=score)
        cache[key]=result
        if audit['training_feasible'][0] and (best is None or score>best['score']):best=result
        return result
    current=query(initial)
    if best is None or current['margin']<F(settings['advance_margin_m']):
        raise ValueError('predeclared origin must fit training with the advance margin')
    stopping='proposal limit reached'
    def reserve_lp():
        nonlocal lp_calls
        if lp_calls>=settings['maximum_proposals']:raise ValueError('fixed LP allowance exhausted')
        lp_calls+=1
        save('lp-reservation',dict(index=lp_calls,maximum=settings['maximum_proposals'],
            lp_calls_reserved=settings['maximum_lp_calls_per_proposal'],
            exact_checks_reserved=settings['maximum_exact_checks_per_proposal']))
    for _ in range(settings['maximum_proposals']):
        if calls>=max_queries:stopping='native budget exhausted';break
        if radius<settings['minimum_radius']:stopping='trust radius floor reached';break
        previous=lp_calls
        proposal=propose_step(problem,current['record'],sign=sign,radius=radius,reserve=reserve_lp)
        if lp_calls!=previous+1:raise ValueError('one advance LP reservation required per proposal')
        save('linear-proposal',dict(index=lp_calls,origin_index=current['index'],proposal=proposal,radius=radius))
        if proposal['exact_checks']>settings['maximum_exact_checks_per_proposal']:
            raise ValueError('exact proposal work exceeds reservation')
        if proposal['lp_calls']>settings['maximum_lp_calls_per_proposal']:
            raise ValueError('LP solver calls exceed reservation')
        solver_calls+=proposal['lp_calls']
        exact_checks+=proposal['exact_checks']
        if not proposal['lp_success'] or not proposal['audit']['admissible']:
            radius*=settings['shrink'];continue
        predicted=sign*F(proposal['linear_north_change_exact'])
        if predicted<=F(settings['minimum_progress_m']):stopping='no improving feasible linear step';break
        trial=query(proposal['point']);actual=trial['score']-current['score'];ratio=actual/predicted
        accepted=(actual>F(settings['minimum_progress_m']) and ratio>=F(settings['minimum_ratio'])
            and trial['margin']>=F(settings['advance_margin_m']))
        before=radius
        if accepted:
            current=trial
            if ratio>=F(settings['good_ratio']):radius=min(settings['maximum_radius'],radius*settings['grow'])
        else:radius*=settings['shrink']
        save('trust-step',dict(index=lp_calls,trial_index=trial['index'],accepted=accepted,
            predicted_north_change_exact=str(predicted),actual_north_change_exact=str(actual),ratio_exact=str(ratio),
            training_margin_exact=str(trial['margin']),radius_before=before,radius_after=radius))
    if calls>=max_queries:stopping='native budget exhausted'
    return dict(native_queries=calls,stopping_reason=stopping,optimizer_success=False,
        best_point=best['record']['point'],best_record=best['record'],best_training_feasible=True,
        best_training_margin_exact=str(best['margin']),parameter_count=27,search_margin_m=settings['search_margin_m'],
        auxiliary_work=dict(proposal_steps=lp_calls,lp_proposals=solver_calls,
            lp_calls_reserved=lp_calls*settings['maximum_lp_calls_per_proposal'],
            exact_checks_reserved=lp_calls*settings['maximum_exact_checks_per_proposal'],
            exact_checks_executed=exact_checks),policy=settings,future_observations_used=False,
        outer_bound_qualified=False,numerical_error_bound_independently_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
