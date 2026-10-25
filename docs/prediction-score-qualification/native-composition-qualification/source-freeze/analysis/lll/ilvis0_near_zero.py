# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate numerical stopping proposal for a near-zero sum-of-squares cost.

This does not certify floating-point integration error, parameter identification,
calibrated uncertainty or a physical model. Historical stopping labels stay fixed.
"""
import numpy as np

from .ilvis0_solver_refinement import POLICY as STOPPING,projected_stationarity
from .ilvis0_solver_position import POLICY as POSITION

POLICY=dict(maximum_computed_cost=STOPPING['relative_cost_tolerance'],
    fresh_evaluations=2,lower_computed_sum_of_squares=0.,
    stationarity_tolerance=STOPPING['stationarity_tolerance'],
    position_rms_tolerance_m=POSITION['position_rms_tolerance_m'],
    position_max_tolerance_m=POSITION['position_max_tolerance_m'])
VERSION='ilvis0-near-zero-trust-composition-v1'


def verify(point,evaluate,physical_step):
    """Two fresh values at one feasible point; never step along a null direction.

    The caller charges both evaluations within its existing finite allowance.
    A nonnegative numerical objective within the declared absolute floor of zero
    needs no unique calibration vector. Nonzero optima use other stopping checks.
    """
    if not callable(evaluate) or not callable(physical_step):
        raise ValueError('callable evaluation and physical repeat conversion required')
    u=np.asarray(point,dtype=float)
    if u.ndim!=1 or not len(u) or np.any(abs(u)>1) or not np.all(np.isfinite(u)):
        raise ValueError('finite feasible normalized point required')
    snapshots=[]
    for _ in range(POLICY['fresh_evaluations']):
        residual,jac,_=evaluate(u.copy(),fresh=True)
        r,j=np.asarray(residual,float),np.asarray(jac,float)
        if (r.ndim!=1 or not len(r) or j.shape!=(len(r),len(u))
                or not np.all(np.isfinite(r)) or not np.all(np.isfinite(j))):
            raise ValueError('finite residual with every active derivative column required')
        if snapshots and r.shape!=snapshots[0][0].shape:
            raise ValueError('repeat residual shape changed')
        cost=float(r@r);stationarity=projected_stationarity(u,r,j)[0]
        if not np.isfinite(cost) or not np.isfinite(stationarity):
            raise ValueError('finite computed objective and stationarity required')
        snapshots.append((r.copy(),cost,stationarity))
        if cost>POLICY['maximum_computed_cost'] or stationarity>POLICY['stationarity_tolerance']:
            return dict(passed=False,reason='not_near_zero_and_stationary',fresh_evaluations=len(snapshots))
    delta=np.asarray(physical_step(snapshots[1][0]-snapshots[0][0]),float)
    if delta.ndim!=2 or delta.shape[1]!=3 or not len(delta) or not np.all(np.isfinite(delta)):
        raise ValueError('finite physical position-repeat difference required')
    rms=np.sqrt(np.mean(delta*delta,axis=0));maximum=np.max(abs(delta),axis=0)
    passed=bool(np.all(rms<=POLICY['position_rms_tolerance_m'])
        and np.all(maximum<=POLICY['position_max_tolerance_m']))
    return dict(passed=passed,reason='near_zero_repeat_verified' if passed else 'position_repeat_not_stable',
        fresh_evaluations=2,computed_objective_gap_upper=max(v[1] for v in snapshots),
        computed_costs=[v[1] for v in snapshots],stationarity=[v[2] for v in snapshots],
        position_rms_neu_m=rms.tolist(),position_max_abs_neu_m=maximum.tolist(),policy=POLICY,
        parameter_identification_established=False,confidence_calibrated=False,
        floating_point_integration_error_certified=False,scientific_decision='abstain')


def fit_candidate(problem,model,*,start,maximum_evaluations=200,physical_step=None):
    """Compose the existing solver with two budgeted near-zero repeats.

    Nonzero objectives retain the ordinary stationarity/position gate. The two
    extra calls are reserved by reducing the ordinary solver's ceiling, never
    by extending a completed allowance. This function makes a new result only.
    """
    from .ilvis0_solver_trust_v2 import fit_candidate as ordinary
    from .ilvis0_solver_position import physical_residual_step
    from .ilvis0_estimator import EvaluationLimit
    if type(maximum_evaluations) is not int or not 8<=maximum_evaluations<=600:
        raise ValueError('finite evaluation allowance in [8,600] required')
    class Counted:
        calls=0
        def __getattr__(self,name):return getattr(problem,name)
        def residual_tangent(self,u,candidate):
            if self.calls>=maximum_evaluations:raise EvaluationLimit('total tangent allowance exhausted')
            self.calls+=1
            return problem.residual_tangent(u,candidate)
    counted=Counted();ordinary_limit=maximum_evaluations-POLICY['fresh_evaluations']
    fit=ordinary(counted,model,start=start,maximum_evaluations=ordinary_limit,physical_step=physical_step)
    if counted.calls!=fit['evaluations']:raise ValueError('ordinary evaluation accounting differs')
    ordinary_converged=fit['converged'];ordinary_probe=fit['stability_probe'];probe=None;trace=[]
    if fit['residual_sum_squares']<=POLICY['maximum_computed_cost']:
        def fresh(u,fresh=False):
            if not fresh:raise ValueError('fresh repeat required')
            r,j,b=counted.residual_tangent(u,model)
            trace.append(dict(evaluation=counted.calls,cost=float(r@r),fresh=True))
            return r,j,b
        transform=physical_step if physical_step is not None else lambda d:physical_residual_step(problem,d)
        probe=verify(np.asarray(fit['normalized_parameters']),fresh,transform)
        fit.update(converged=bool(probe['passed']),stopping_rule_verified=bool(probe['passed']),
            stability_verified=bool(probe['passed']),stability_probe=probe,
            termination='near_zero_repeat' if probe['passed'] else 'unresolved')
    fit.update(version=VERSION,ordinary_version=fit['version'],ordinary_converged=ordinary_converged,
        ordinary_stability_probe=ordinary_probe,ordinary_maximum_evaluations=ordinary_limit,
        maximum_evaluations=maximum_evaluations,evaluations=counted.calls,near_zero_probe=probe,
        evaluation_trace=fit['evaluation_trace']+trace,
        stability_policy=dict(fit['stability_policy'],near_zero_policy=POLICY),
        parameter_identification_established=False,confidence_calibrated=False)
    return fit
