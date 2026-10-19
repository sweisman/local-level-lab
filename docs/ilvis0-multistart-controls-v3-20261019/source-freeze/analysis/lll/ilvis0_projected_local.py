# SPDX-License-Identifier: AGPL-3.0-or-later
"""Explicit local projected stability candidate; no changes to frozen gates."""
import types
import numpy as np
from scipy.optimize import lsq_linear
from .ilvis0_solver_refinement import POLICY as STOPPING,projected_stationarity
from . import ilvis0_solver_position as position,ilvis0_projected_trust as trust
from .ilvis0_projected_fitting import ProjectedProblem,ControlBudget

VERSION='ilvis0-projected-local-stability-v1'
LOCAL_RADIUS=.001


def verify_local(point,residual,jac,evaluate,physical_step):
    point=np.asarray(point,float);residual=np.asarray(residual,float);jac=np.asarray(jac,float)
    if (point.ndim!=1 or not len(point) or residual.ndim!=1 or not len(residual)
            or jac.shape!=(len(residual),len(point)) or np.any(abs(point)>1)
            or any(not np.all(np.isfinite(v)) for v in (point,residual,jac))):
        raise ValueError('finite feasible full-column local problem required')
    common=dict(columns=len(point),local_radius=LOCAL_RADIUS,local_stability_only=True)
    if projected_stationarity(point,residual,jac)[0]>STOPPING['stationarity_tolerance']:
        return dict(common,passed=False,reason='not_stationary')
    correction=lsq_linear(jac,-residual,
        bounds=(np.maximum(-1-point,-LOCAL_RADIUS),np.minimum(1-point,LOCAL_RADIUS)),
        method='bvls',tol=STOPPING['stability_probe_linear_tolerance'],
        max_iter=STOPPING['stability_probe_linear_maximum_iterations'])
    if not correction.success or not np.all(np.isfinite(correction.x)):
        return dict(common,passed=False,reason='local_linear_solve_unfinished')
    probe=np.clip(point+correction.x,-1.,1.);fresh,fresh_jac,_=evaluate(probe,fresh=True)
    physical=np.asarray(physical_step(fresh-residual),float)
    if physical.ndim!=2 or physical.shape[1]!=3 or not len(physical) or not np.all(np.isfinite(physical)):
        raise ValueError('finite retained-coordinate physical differences required')
    cost=float(residual@residual);fresh_cost=float(fresh@fresh)
    change=abs(fresh_cost-cost)/max(fresh_cost,cost,1.)
    stationarity=float(projected_stationarity(probe,fresh,fresh_jac)[0])
    rms=np.sqrt(np.mean(physical**2,axis=0));maximum=np.max(abs(physical),axis=0)
    passed=bool(change<=STOPPING['relative_cost_tolerance'] and stationarity<=STOPPING['stationarity_tolerance']
        and np.all(rms<=position.POLICY['position_rms_tolerance_m'])
        and np.all(maximum<=position.POLICY['position_max_tolerance_m']))
    return dict(common,passed=passed,reason='fresh_local_position_stability' if passed else 'fresh_local_probe_not_stable',
        actual_cost_change=change,fresh_stationarity=stationarity,position_rms_neu_m=rms.tolist(),
        position_max_abs_neu_m=maximum.tolist(),normalized_parameter_step=float(np.linalg.norm(probe-point)),
        maximum_normalized_coordinate_change=float(np.max(abs(probe-point))),
        unscored_coordinates_checked=False)


def engine():
    core=trust.engine()
    proxy=types.SimpleNamespace(**vars(core.position));proxy.verify_stability=verify_local;proxy.VERSION=VERSION
    core.position=proxy;core.VERSION=VERSION
    core.POLICY=dict(core.POLICY,stopping='fresh local projected stationarity/cost/position; no global-optimum claim',
        local_probe_radius=LOCAL_RADIUS,local_stability_only=True)
    return core


def fit_control(problem,model,*,start,maximum_evaluations=160):
    if type(maximum_evaluations) is not int or not 6<=maximum_evaluations<=160:
        raise ValueError('finite generated control allowance in [6,160] required')
    result=engine().fit_candidate(problem,model,start=start,maximum_evaluations=maximum_evaluations,
                                  physical_step=problem.physical_step)
    jac=np.asarray(result['local_linearization']['jacobian']);singular=np.linalg.svd(jac,compute_uv=False)
    cutoff=max(jac.shape)*np.finfo(float).eps*singular[0]
    result.update(projected_version=VERSION,numerical_rank=int(np.sum(singular>cutoff)),columns=jac.shape[1],
        numerical_rank_cutoff=float(cutoff),retained_coordinates=list(problem.projection.axes),
        local_stability_only=True,unscored_coordinates_checked=False,archival_stability_qualified=False,
        scientific_decision='abstain')
    return result
