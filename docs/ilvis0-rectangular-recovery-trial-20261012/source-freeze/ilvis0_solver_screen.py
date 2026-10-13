# SPDX-License-Identifier: AGPL-3.0-or-later
"""Deterministic small analytic solver screen; never read airborne data."""
import numpy as np
from scipy.optimize import least_squares

from . import ilvis0_solver_controls as controls
from .ilvis0_solver_refinement import projected_stationarity

VERSION='ilvis0-analytic-solver-screen-v1'
VARIANTS=('dense_jac','dense_unit','lsmr_jac')
NAMES=controls.ANALYTIC+('mixed_interior','mixed_boundary')


class Mixed:
    def __init__(self,matrix,target):
        self.matrix=matrix; self.target=target
        self.bounds=controls.ControlBounds(27)

    def residual_tangent(self,point,model):
        return np.r_[self.matrix@point-self.target,1.],np.vstack([self.matrix,np.zeros((1,27))]),0


def mixed_problem(name):
    if name not in ('mixed_interior','mixed_boundary'): raise ValueError('unknown mixed control')
    rng=np.random.default_rng(20261011)
    left=np.linalg.qr(rng.normal(size=(27,27)))[0]
    right=np.linalg.qr(rng.normal(size=(27,27)))[0]
    matrix=left@np.diag(np.geomspace(5e4,.001,27))@right.T
    optimum=rng.uniform(-.4,.4,27)
    if name=='mixed_boundary': optimum[:2]=[1.,-1.]
    return Mixed(matrix,matrix@optimum),optimum


def one(name,start_index,variant):
    if name in controls.ANALYTIC:
        problem,optimum,expected,unique=controls.analytic_problem(name)
    else:
        problem,optimum=mixed_problem(name); expected=1.; unique=False
    initial=controls.starts(len(optimum),3)[start_index]
    cache=None; calls=0
    def evaluate(point,fresh=False):
        nonlocal cache,calls
        if not fresh and cache is not None and np.array_equal(point,cache[0]): return cache[1:]
        if calls>=199 and not fresh: raise controls.EvaluationLimit('analytic screen allowance exhausted')
        if calls>=200: raise controls.EvaluationLimit('fresh screen allowance exhausted')
        calls+=1
        residual,jac,_=problem.residual_tangent(point,'control')
        cache=(point.copy(),residual,jac)
        return residual,jac
    kwargs=dict(x_scale=1. if variant=='dense_unit' else 'jac',tr_solver='lsmr' if variant=='lsmr_jac' else 'exact')
    if variant=='lsmr_jac': kwargs['tr_options']=dict(regularize=True,atol=1e-12,btol=1e-12,maxiter=200)
    success=False; point=initial.copy(); message='not started'
    accepted=0
    def callback(intermediate_result):
        nonlocal accepted,point
        accepted+=1; point=intermediate_result.x.copy()
    try:
        result=least_squares(lambda x:evaluate(x)[0],initial,jac=lambda x:evaluate(x)[1],
            bounds=(-1.,1.),ftol=None,xtol=1e-11,gtol=1e-8,max_nfev=199,callback=callback,**kwargs)
        point=result.x.copy(); success=bool(result.success); message=str(result.message)
    except controls.EvaluationLimit as error: message=str(error)
    residual,jac=evaluate(point,fresh=True)
    stationarity=projected_stationarity(point,residual,jac)[0]
    cost=float(residual@residual)
    exact=problem.residual_tangent(optimum,'reference')[0]
    error=float(np.linalg.norm(residual-exact))
    parameter_error=float(np.max(abs(point-optimum))) if unique else None
    passed=bool(success and stationarity<=1e-4 and abs(cost-expected)<=1e-7
        and error<=1e-4 and (not unique or parameter_error<=1e-5))
    return dict(identity=f'{variant}::{name}::{start_index}',variant=variant,control=name,
        start_index=start_index,passed=passed,solver_reported_success=success,
        stationarity=stationarity,objective=cost,known_optimum_objective=expected,
        residual_error_to_known_optimum=error,parameter_error=parameter_error,
        evaluations=calls,accepted_iterations=accepted,message=message)


def run():
    rows=[one(name,i,variant) for variant in VARIANTS for name in NAMES for i in range(3)]
    return dict(version=VERSION,results=rows,maximum_evaluations_per_start=200,
        observed_fit_starts=0,native_predictions=0,qualifies_archival_solver=False,
        scientific_decision='abstain')
