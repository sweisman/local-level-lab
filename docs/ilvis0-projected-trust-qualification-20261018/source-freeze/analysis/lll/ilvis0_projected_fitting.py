# SPDX-License-Identifier: AGPL-3.0-or-later
"""Projected native objective and bounded software controls, never an evidence gate.

All IMU inputs, initial conditions and nuisance columns remain in the full
problem. Only receiver coordinates entering the likelihood are marginalized.
The control solver applies existing fresh-position stability limits to retained
coordinates only and cannot qualify an observed fit or change a disposition.
"""
import numpy as np

from .ilvis0_estimator import EvaluationLimit
from .ilvis0_observation_projection import ReceiverProjection
from . import ilvis0_solver_position as position

VERSION='ilvis0-projected-fitting-controls-v2'


class ControlBudget:
    """Charge generated-motion work before execution; no retries implicit here."""
    def __init__(self,*,maximum_native_sweeps,maximum_starts):
        if any(type(x) is not int or x<0 for x in (maximum_native_sweeps,maximum_starts)):
            raise ValueError('finite nonnegative integer software allowances required')
        self.maximum_native_sweeps=maximum_native_sweeps;self.maximum_starts=maximum_starts
        self.native_sweeps=0;self.starts=0

    def charge_native(self):
        if self.native_sweeps>=self.maximum_native_sweeps:
            raise EvaluationLimit('generated-motion native allowance exhausted')
        self.native_sweeps+=1

    def charge_start(self):
        if self.starts>=self.maximum_starts:
            raise EvaluationLimit('generated-motion start allowance exhausted')
        self.starts+=1


class ProjectedProblem:
    """Preserve the full prediction problem and project its likelihood only."""
    def __init__(self,full_problem,axes):
        lower=np.asarray(full_problem.cholesky,float)
        gps=np.asarray(full_problem.gps,float)
        if (gps.ndim!=2 or gps.shape[1]!=3 or len(gps)<2
                or not np.all(np.isfinite(gps)) or lower.shape!=(gps.size,gps.size)
                or not np.all(np.isfinite(lower)) or np.any(np.diag(lower)<=0)
                or np.any(np.triu(lower,1)!=0)):
            raise ValueError('full receiver layout and lower covariance factor required')
        self.full_problem=full_problem;self.bounds=full_problem.bounds
        covariance=lower@lower.T
        self.projection=ReceiverProjection(covariance,axes)
        indices=self.projection.indices
        self.retained_cholesky=np.linalg.cholesky(covariance[np.ix_(indices,indices)])

    def residual_tangent(self,point,model):
        self.bounds.decode(point)
        residual,jac,boundaries=self.full_problem.residual_tangent(point,model)
        residual,jac=self.projection.apply(residual,jac)
        if jac.shape[1]!=len(self.bounds.active):
            raise ValueError('every active nuisance column must be retained')
        return residual,jac,boundaries

    def predict(self,point,model):
        """Return all coordinates; omitted likelihood axes are not erased."""
        return self.full_problem.predict(point,model)

    def report(self):
        return dict(self.projection.report(),version=VERSION,
            active_parameters=list(self.bounds.active),prediction_coordinates='all three',
            unscored_coordinates_checked=False,archival_stability_qualified=False)

    def physical_step(self,delta):
        """Restore retained prediction changes to metres; unscored axes stay zero.

        Zero entries are placeholders, not a claim that unscored predictions are
        stable. Initial coordinates remain full; this is not altitude independence.
        """
        delta=np.asarray(delta,float)
        if delta.shape!=(len(self.projection.indices),) or not np.all(np.isfinite(delta)):
            raise ValueError('finite projected residual difference required')
        restored=np.zeros(self.projection.full_size)
        restored[self.projection.indices]=self.retained_cholesky@delta
        restored=restored.reshape(-1,3)
        restored[:,1]=(restored[:,1]+np.pi)%(2*np.pi)-np.pi
        return restored*position.physical_metric(self.full_problem.gps)


def fit_control(problem,model,*,start,maximum_evaluations=80):
    """Reuse bounded steps and fresh cost/stationarity/retained-position checks.

    Numerical convergence, rank and known-answer recovery are separate outputs.
    Rank-deficient optima do not imply unique parameter estimates. This routine
    is for generated/constructed controls, not production or archival decisions.
    """
    if type(maximum_evaluations) is not int or not 6<=maximum_evaluations<=80:
        raise ValueError('finite control allowance in [6,80] required')
    point=np.array(start,float);problem.bounds.decode(point)
    if not len(point):raise ValueError('at least one active control parameter required')
    result=position.fit_candidate(problem,model,start=point,maximum_evaluations=maximum_evaluations,
                                  physical_step=problem.physical_step)
    saved=result['local_linearization'];jac=np.array(saved['jacobian'])
    singular=np.linalg.svd(jac,compute_uv=False)
    cutoff=max(jac.shape)*np.finfo(float).eps*(float(singular[0]) if len(singular) else 0.)
    rank=int(np.sum(singular>cutoff))
    termination=result['termination']
    if not result['converged'] and ('allowance' in result['message'] or result['evaluations']==maximum_evaluations):
        termination='budget'
    # Keep the full trace/linearization in the native solver's own result; the
    # software-control record retains the outcome and fresh stability evidence.
    return dict(version=VERSION,model=model,converged=result['converged'],termination=termination,
        message=result['message'],evaluations=result['evaluations'],maximum_evaluations=maximum_evaluations,
        active_parameters=list(problem.bounds.active),normalized_parameters=result['normalized_parameters'],
        parameters=result['parameters'],residual_sum_squares=result['residual_sum_squares'],
        exact_projected_gradient_relative=float(result['exact_projected_gradient_relative']),
        stationarity_tolerance=result['stationarity_tolerance'],stability_probe=result['stability_probe'],
        numerical_rank=rank,columns=len(point),nuisance_fully_observable=rank==len(point),
        singular_values=singular.tolist(),numerical_rank_cutoff=cutoff,
        gps_epochs_at_packet_boundaries=result['gps_epochs_at_packet_boundaries'],
        retained_coordinates=list(problem.projection.axes),unscored_coordinates_checked=False,
        archival_stability_qualified=False,scientific_decision='abstain')
