# SPDX-License-Identifier: AGPL-3.0-or-later
"""Research-only interval-aware verification; frozen/default solvers unchanged."""
import numpy as np

from .ilvis0_solver_position import POLICY as POSITION
from .ilvis0_solver_refinement import POLICY as STOPPING,projected_stationarity

VERSION='ilvis0-timing-cell-verification-v1'
VERIFICATION_EVALUATIONS=36


def verify(point,residual,jac,evaluate,physical_step,*,active,cells,reserve_linear,check_continue=None):
    from .timing_cells import bounded_step
    u,r,j=(np.asarray(v,float) for v in (point,residual,jac));names=list(active)
    check=(lambda:None) if check_continue is None else check_continue
    if (u.ndim!=1 or not 1<=len(u)<=27 or len(names)!=len(u) or len(set(names))!=len(names)
            or 'time_offset' not in names or np.any(abs(u)>1) or r.ndim!=1 or not len(r)
            or j.shape!=(len(r),len(u)) or any(not np.all(np.isfinite(v)) for v in (u,r,j))
            or not isinstance(cells,list) or not 1<=len(cells)<=17
            or any(not callable(v) for v in (evaluate,physical_step,reserve_linear,check))):
        raise ValueError('complete finite point, cells, columns and counted callbacks required')
    column=names.index('time_offset');previous=None
    for cell in cells:
        lo,hi,anchor=(cell[k] for k in ('lower','upper','anchor'))
        if (not np.all(np.isfinite([lo,hi,anchor])) or not -1<=lo<=anchor<=hi<=1
                or previous is not None and np.nextafter(previous,np.inf)!=lo):
            raise ValueError('complete ordered adjacent-float timing cells required')
        previous=hi
    if not any(c['lower']<=u[column]<=c['upper'] for c in cells):
        raise ValueError('current point omitted from timing cells')
    calls=0
    def fresh(p):
        nonlocal calls
        check()
        if calls>=VERIFICATION_EVALUATIONS-1:raise RuntimeError('timing verification allowance exhausted')
        calls+=1
        rr,jj,b=evaluate(p.copy(),fresh=True);rr,jj=np.asarray(rr,float),np.asarray(jj,float)
        if rr.shape!=r.shape or jj.shape!=j.shape or not np.all(np.isfinite(rr)) or not np.all(np.isfinite(jj)):
            raise ValueError('finite unchanged residual and every derivative column required')
        return rr.copy(),jj.copy(),b
    stationarity=projected_stationarity(u,r,j)[0]
    if stationarity>STOPPING['stationarity_tolerance']:
        return dict(passed=False,reason='not_stationary',fresh_evaluations=0,cells=[],confidence_calibrated=False)
    repeated,repeated_j,_=fresh(u)
    if not np.array_equal(r,repeated) or not np.array_equal(j,repeated_j):
        return dict(passed=False,reason='baseline_not_repeatable',fresh_evaluations=calls,cells=[],confidence_calibrated=False)
    cost=float(r@r);rows=[]
    for index,cell in enumerate(cells):
        check();anchor=u.copy();anchor[column]=cell['anchor'];rr,jj,_=fresh(anchor)
        lo=-np.ones(len(u));hi=np.ones(len(u));lo[column]=cell['lower'];hi[column]=cell['upper']
        linear=bounded_step(rr,jj,anchor,lo,hi,active=names,reserve=reserve_linear)
        if not linear['linear_success']:
            rows.append(dict(index=index,linear=linear,passed=False,reason='cell_linear_solve_unfinished'));continue
        p=np.asarray(linear['point'],float);actual,actual_j,b=fresh(p)
        delta=np.asarray(physical_step(actual-r),float)
        if delta.ndim!=2 or not len(delta) or delta.shape[1]!=3 or not np.all(np.isfinite(delta)):
            raise ValueError('finite common physical position change required')
        actual_cost=float(actual@actual);change=abs(actual_cost-cost)/max(actual_cost,cost,1.)
        fresh_stationarity=projected_stationarity(p,actual,actual_j)[0]
        rms=np.sqrt(np.mean(delta**2,axis=0));maximum=np.max(abs(delta),axis=0)
        stable=bool(change<=STOPPING['relative_cost_tolerance'])
        stationary=bool(fresh_stationarity<=STOPPING['stationarity_tolerance'])
        position=bool(np.all(rms<=POSITION['position_rms_tolerance_m'])
            and np.all(maximum<=POSITION['position_max_tolerance_m']))
        rows.append(dict(index=index,linear=linear,point=p.tolist(),residual=actual.tolist(),jacobian=actual_j.tolist(),
            boundaries=b,actual_cost=actual_cost,relative_cost_change=change,fresh_stationarity=fresh_stationarity,
            position_delta_neu_m=delta.tolist(),position_rms_neu_m=rms.tolist(),position_max_abs_neu_m=maximum.tolist(),
            cost_stable=stable,stationary=stationary,position_stable=position,passed=stable and stationary and position))
    passed=bool(rows) and all(row['passed'] for row in rows)
    return dict(version=VERSION,passed=passed,reason='all_timing_cells_stable' if passed else 'timing_cell_not_stable',
        original_stationarity=stationarity,cells=rows,fresh_evaluations=calls,maximum_fresh_evaluations=35,
        linear_solves=len(rows),all_active_parameters=names,baseline_repeat_exact=True,
        relative_cost_tolerance=STOPPING['relative_cost_tolerance'],stationarity_tolerance=STOPPING['stationarity_tolerance'],
        position_rms_tolerance_m=POSITION['position_rms_tolerance_m'],position_max_tolerance_m=POSITION['position_max_tolerance_m'],
        confidence_calibrated=False,scientific_decision='abstain')


def fit_candidate(problem,model,*,start,maximum_evaluations=200,physical_step=None,
                  reserve_linear=None,check_continue=None):
    """Compose existing fitting and near-zero rules with explicit final checking."""
    from .ilvis0_solver_trust_v2 import fit_candidate as ordinary
    from .ilvis0_near_zero import fit_candidate as near_zero
    from .ilvis0_solver_position import verify_stability
    from .timing_intervals import local_cells
    check=(lambda:None) if check_continue is None else check_continue
    if (not callable(check) or reserve_linear is not None and not callable(reserve_linear)
            or type(maximum_evaluations) is not int or not 8<=maximum_evaluations<=600):
        raise ValueError('finite complete fitting allowance and counted providers required')
    names=list(problem.bounds.active);timed='time_offset' in names
    if timed and maximum_evaluations<40:raise ValueError('timing verification requires at least40 total evaluations')
    solves=0;geometry=[]
    def charge():
        nonlocal solves
        check()
        if reserve_linear is not None:reserve_linear()
        solves+=1
    def checker(u,r,j,evaluate,physical):
        if not timed:
            if projected_stationarity(u,r,j)[0]<=STOPPING['stationarity_tolerance']:charge()
            return verify_stability(u,r,j,evaluate,physical)
        try:
            g=local_cells(problem.dt,problem.gps_times,scale=problem.bounds.limits['time_offset'],
                point=float(u[names.index('time_offset')]))
        except ValueError as error:
            return dict(passed=False,reason='unsupported_timing_geometry',detail=str(error),cells=[],fresh_evaluations=0)
        geometry.append(g)
        return verify(u,r,j,evaluate,physical,active=names,cells=g['cells'],reserve_linear=charge,check_continue=check)
    def provider(*args,**kwargs):
        return ordinary(*args,**kwargs,stability_verifier=checker,
            verification_evaluations=VERIFICATION_EVALUATIONS if timed else 2,reserve_linear=charge)
    check()
    result=near_zero(problem,model,start=start,maximum_evaluations=maximum_evaluations,
        physical_step=physical_step,ordinary_provider=provider)
    result.update(version=VERSION,linear_solves=solves,timing_geometry=geometry,
        final_verification_reserve=VERIFICATION_EVALUATIONS if timed else 2,
        ordinary_fitting_method_unchanged=True,near_zero_policy_unchanged=True,
        production_qualified=False,confidence_calibrated=False)
    return result
