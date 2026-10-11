# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate solver candidate: unit scaling in the full stage; frozen fits unchanged."""
import numpy as np
from scipy.optimize import least_squares

from . import ilvis0_estimator as estimator
from .ilvis0_solver_refinement import projected_stationarity

VERSION='ilvis0-full-stage-unit-scale-v1'


def fit_candidate(problem,model,*,start=None,maximum_evaluations=200):
    """Preserve original staging, feasible box, tolerances, acceptance and allowance."""
    if not 4<=maximum_evaluations<=200: raise ValueError('finite allowance in [4,200] required')
    point=np.zeros(len(problem.bounds.active)) if start is None else np.array(start,float)
    problem.bounds.decode(point)
    calls=0; cache=None; best=None; limit=maximum_evaluations-3
    def evaluate(u,fresh=False):
        nonlocal calls,cache,best
        if not fresh and cache is not None and np.array_equal(u,cache[0]): return cache[1:]
        if calls>=limit: raise estimator.EvaluationLimit('native tangent evaluation allowance exhausted')
        calls+=1; residual,jac,boundaries=problem.residual_tangent(u,model)
        if not np.all(np.isfinite(residual)) or not np.all(np.isfinite(jac)): raise ValueError('nonfinite tangent')
        cache=(u.copy(),residual,jac,boundaries); cost=float(residual@residual)
        if best is None or cost<best[0]: best=cost,u.copy()
        return residual,jac,boundaries
    staged=[i for i,name in enumerate(problem.bounds.active)
        if name.startswith(('attitude_','velocity_','position_','accel_gain_'))]
    stage_message='no staged parameters'; stage_calls=0
    if staged and len(point)>len(staged) and maximum_evaluations>=40:
        initial=point.copy(); end_stage=min(25,maximum_evaluations//5)
        def expand(x):
            full=initial.copy(); full[staged]=x; return full
        def stage_fun(x):
            if calls>=end_stage: raise estimator.EvaluationLimit('initialization stage complete')
            return evaluate(expand(x))[0]
        try:
            solution=least_squares(stage_fun,initial[staged],jac=lambda x:evaluate(expand(x))[1][:,staged],
                bounds=(-1.,1.),x_scale='jac',ftol=None,xtol=1e-11,gtol=1e-8,max_nfev=end_stage)
            stage_message=str(solution.message)
        except estimator.EvaluationLimit as error: stage_message=str(error)
        point=best[1].copy(); stage_calls=calls
    history=[]; previous=None
    def callback(intermediate_result):
        nonlocal previous
        u=intermediate_result.x; r,j,_=evaluate(u)
        cost=float(r@r)
        history.append(dict(evaluations=calls,cost=cost,
            stationarity=projected_stationarity(u,r,j)[0],
            relative_cost_change=abs(cost-previous[0])/max(cost,previous[0],1.) if previous else None,
            relative_residual_step=float(np.linalg.norm(r-previous[1])/max(np.linalg.norm(r),1.)) if previous else None,
            parameters_at_limits=int(np.count_nonzero(abs(u)>=.999))))
        previous=cost,r.copy()
    success=False; message='not started'
    try:
        solution=least_squares(lambda u:evaluate(u)[0],point,jac=lambda u:evaluate(u)[1],
            bounds=(-1.,1.),x_scale=1.,ftol=None,xtol=1e-11,gtol=1e-8,
            max_nfev=limit-calls,callback=callback)
        success=bool(solution.success); message=str(solution.message)
    except estimator.EvaluationLimit as error: message=str(error)
    if best is None: raise ValueError('no finite candidate evaluation')
    point=best[1]; limit=maximum_evaluations-2
    residual,jac,boundaries=evaluate(point,fresh=True)
    stationarity,gradient,projected,scaled=projected_stationarity(point,residual,jac)
    _,singular,right=np.linalg.svd(jac,full_matrices=False)
    return dict(version=VERSION,model=model,parameters=problem.bounds.decode(point),
        normalized_parameters=point.tolist(),active_parameters=list(problem.bounds.active),
        residual_sum_squares=float(residual@residual),evaluations=calls,
        maximum_evaluations=maximum_evaluations,initialization_evaluations=stage_calls,
        initialization_message=stage_message,solver_reported_success=success,
        converged=bool(success and stationarity<=1e-4),message=message,
        exact_projected_gradient_relative=stationarity,stationarity_tolerance=1e-4,
        gradient=gradient.tolist(),projected_gradient=projected.tolist(),
        scaled_projected_gradient=scaled.tolist(),singular_values=singular.tolist(),
        right_singular_vectors=right.tolist(),accepted_step_history=history,
        full_stage_x_scale=1.,initialization_x_scale='jac',
        active_bounds=[name for name,u in zip(problem.bounds.active,point) if abs(u)>=.999],
        gps_epochs_at_packet_boundaries=boundaries,
        derivative_method='forward automatic differentiation, 27 tangent lanes',
        latency_derivative_convention='left interval at a packet boundary; adjacent measured rates may differ',
        constant_bias_is_measured_drift=False,scientific_eligible=False,scientific_decision='abstain',
        calibration_bounds_supported=False,processing_independence_established=False,
        receiver_covariance_calibrated=False,clock_independently_established=False)
