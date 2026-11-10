# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate unit-scale stopping candidate; never relabel or resume frozen fits."""
import numpy as np
from scipy.optimize import least_squares,lsq_linear

from . import ilvis0_estimator as estimator
from .ilvis0_solver_refinement import POLICY,StableStop,projected_stationarity

VERSION='ilvis0-unit-scale-verified-stop-v1'


def verify_stability(point,residual,jac,evaluate):
    """Verify a bounded local correction with an actual fresh residual/tangent.

    This is local first-order/stability evidence, not proof of a global optimum.
    The evaluator must charge its fresh call against the same finite allowance.
    """
    stationarity=projected_stationarity(point,residual,jac)[0]
    if stationarity>POLICY['stationarity_tolerance']:
        return dict(passed=False,reason='not_stationary')
    correction=lsq_linear(jac,-residual,bounds=(-1-point,1-point),method='bvls',
        tol=POLICY['stability_probe_linear_tolerance'],
        max_iter=POLICY['stability_probe_linear_maximum_iterations'])
    if not correction.success or not np.all(np.isfinite(correction.x)):
        return dict(passed=False,reason='local_linear_solve_unfinished')
    predicted=residual+jac@correction.x; cost=float(residual@residual)
    predicted_cost=float(predicted@predicted)
    predicted_change=abs(predicted_cost-cost)/max(cost,predicted_cost,1.)
    predicted_step=float(np.linalg.norm(predicted-residual)/max(np.linalg.norm(residual),1.))
    if (predicted_change>POLICY['relative_cost_tolerance'] or
        predicted_step>POLICY['relative_residual_step_tolerance']):
        return dict(passed=False,reason='linear_correction_not_stable',
            predicted_cost_change=predicted_change,predicted_residual_step=predicted_step)
    probe=np.clip(point+correction.x,-1.,1.)
    fresh,fresh_jac,_=evaluate(probe,fresh=True)
    actual_cost=float(fresh@fresh)
    change=abs(actual_cost-cost)/max(actual_cost,cost,1.)
    step=float(np.linalg.norm(fresh-residual)/max(np.linalg.norm(residual),1.))
    fresh_stationarity=projected_stationarity(probe,fresh,fresh_jac)[0]
    passed=bool(change<=POLICY['relative_cost_tolerance'] and
        step<=POLICY['relative_residual_step_tolerance'] and
        fresh_stationarity<=POLICY['stationarity_tolerance'])
    return dict(passed=passed,reason='fresh_stability_verified' if passed else 'fresh_probe_not_stable',
        predicted_cost_change=predicted_change,predicted_residual_step=predicted_step,
        actual_cost_change=change,actual_residual_step=step,fresh_stationarity=fresh_stationarity,
        normalized_parameter_step=float(np.linalg.norm(probe-point)))


def fit_candidate(problem,model,*,start=None,maximum_evaluations=200):
    """Original staging/box/unit scaling, with verified additional stopping exits.

    Reserve one fresh final tangent, one fresh stability probe, and two prediction
    sweeps within the existing allowance. Budget exhaustion by itself never passes.
    """
    if not 6<=maximum_evaluations<=200: raise ValueError('finite allowance in [6,200] required')
    point=np.zeros(len(problem.bounds.active)) if start is None else np.array(start,float)
    problem.bounds.decode(point)
    calls=0; cache=None; best=None; limit=maximum_evaluations-4
    def evaluate(u,fresh=False):
        nonlocal calls,cache,best
        if not fresh and cache is not None and np.array_equal(u,cache[0]): return cache[1:]
        if calls>=limit: raise estimator.EvaluationLimit('native tangent evaluation allowance exhausted')
        calls+=1; residual,jac,boundaries=problem.residual_tangent(u,model)
        if not np.all(np.isfinite(residual)) or not np.all(np.isfinite(jac)):
            raise ValueError('nonfinite residual or tangent')
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
    monitor=StableStop(); history=[]; callback_stop=False; callback_point=None
    def callback(intermediate_result):
        nonlocal callback_stop,callback_point
        u=intermediate_result.x; residual,jac,_=evaluate(u)
        stable=monitor.observe(u,residual,jac)
        history.append(dict(evaluations=calls,cost=float(residual@residual),
            stationarity=monitor.stationarity,relative_cost_change=monitor.cost_change,
            relative_residual_step=monitor.residual_step,
            parameters_at_limits=int(np.count_nonzero(abs(u)>=.999))))
        if stable:
            callback_stop=True; callback_point=u.copy(); raise StopIteration
    success=False; message='not started'
    try:
        solution=least_squares(lambda u:evaluate(u)[0],point,jac=lambda u:evaluate(u)[1],
            bounds=(-1.,1.),x_scale=1.,ftol=None,xtol=1e-11,gtol=1e-8,
            max_nfev=limit-calls,callback=callback)
        success=bool(solution.success); message=str(solution.message)
    except estimator.EvaluationLimit as error: message=str(error)
    if best is None: raise ValueError('no finite candidate evaluation')
    point=best[1].copy(); limit=maximum_evaluations-2
    residual,jac,boundaries=evaluate(point,fresh=True)
    stationarity,gradient,projected,scaled=projected_stationarity(point,residual,jac)
    stopped_stably=bool(callback_stop and np.array_equal(point,callback_point))
    probe=None
    if not success and not stopped_stably and stationarity<=POLICY['stationarity_tolerance']:
        probe=verify_stability(point,residual,jac,evaluate)
    verified=bool(probe and probe['passed'])
    converged=bool(stationarity<=POLICY['stationarity_tolerance'] and
        (success or stopped_stably or verified))
    termination=('scipy_stop' if success else 'three_stable_callbacks' if stopped_stably
        else 'fresh_bounded_stability' if verified else 'unresolved')
    _,singular,right=np.linalg.svd(jac,full_matrices=False)
    return dict(version=VERSION,model=model,parameters=problem.bounds.decode(point),
        normalized_parameters=point.tolist(),active_parameters=list(problem.bounds.active),
        residual_sum_squares=float(residual@residual),evaluations=calls,
        maximum_evaluations=maximum_evaluations,initialization_evaluations=stage_calls,
        initialization_message=stage_message,solver_reported_success=success,
        stopping_rule_verified=bool(converged and not success),converged=converged,
        message=message,termination=termination,stability_probe=probe,
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
