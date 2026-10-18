# SPDX-License-Identifier: AGPL-3.0-or-later
"""Projected trust engine with a bounded curvature correction; frozen code unchanged."""
from pathlib import Path
import types
import numpy as np
from scipy.optimize import lsq_linear
from .ilvis0_projected_fitting import ProjectedProblem,ControlBudget
from . import ilvis0_solver_trust_v2 as trust

VERSION='ilvis0-projected-trust-controls-v2'


def engine():
    """Private, fail-closed extension of the preserved trust engine.

    A rejected full step already supplies a fresh tangent at that trial point.
    One additional bounded Newton correction can restore the curved trajectory.
    Only the combined actual improvement can be accepted; final gates are shared.
    """
    source=Path(trust.__file__).read_text()
    anchor='''            step_bounds=(np.maximum(-1-point,-radius),np.minimum(1-point,radius))'''
    addition='''                # Rejected full-point tangent: one bounded curvature correction.
                curved=lsq_linear(trial_jac,-trial_residual,bounds=(-1-full_point,1-full_point),
                    method='bvls',tol=POLICY['linear_tolerance'],max_iter=POLICY['linear_maximum_iterations'])
                if curved.success and np.all(np.isfinite(curved.x)):
                    corrected=boundary.snap_bounds(np.clip(full_point+curved.x,-1,1))
                    if not np.array_equal(corrected,full_point):
                        corrected_r,corrected_j,_=evaluate(corrected)
                        corrected_cost=float(corrected_r@corrected_r)
                        combined_reduction=cost-corrected_cost
                        combined_ratio=combined_reduction/full_reduction
                        accept_curve=combined_reduction>0 and combined_ratio>=POLICY['acceptance_ratio']
                        history.append(dict(evaluation=calls,accepted=bool(accept_curve),cost=corrected_cost,
                            method='bounded_curvature_correction',actual_reduction=combined_reduction,
                            predicted_first_step_reduction=full_reduction,agreement_ratio=combined_ratio,
                            ratio_reference='first linear step; combined move accepted by actual decrease',
                            normalized_step=float(np.linalg.norm(corrected-point)),
                            correction_norm=float(np.linalg.norm(curved.x))))
                        if accept_curve:
                            point,residual,jac,cost=corrected,corrected_r,corrected_j,corrected_cost
                            continue
'''
    if source.count(anchor)!=1:raise ValueError('unrecognized preserved trust engine layout')
    source=source.replace(anchor,addition+anchor)
    module=types.ModuleType('lll._projected_curvature_core');module.__package__='lll'
    exec(compile(source,trust.__file__,'exec'),module.__dict__)
    module.VERSION=VERSION
    module.POLICY=dict(module.POLICY,step_method='full bounded step; bounded curvature correction; trust fallback')
    return module


def fit_control(problem,model,*,start,maximum_evaluations=160):
    if type(maximum_evaluations) is not int or not 6<=maximum_evaluations<=160:
        raise ValueError('finite projected control allowance in [6,160] required')
    result=engine().fit_candidate(problem,model,start=start,maximum_evaluations=maximum_evaluations,
                                  physical_step=problem.physical_step)
    jac=np.array(result['local_linearization']['jacobian'])
    singular=np.linalg.svd(jac,compute_uv=False)
    cutoff=max(jac.shape)*np.finfo(float).eps*singular[0]
    rank=int(np.sum(singular>cutoff))
    result.update(projected_version=VERSION,retained_coordinates=list(problem.projection.axes),
        numerical_rank=rank,columns=jac.shape[1],numerical_full_column_rank=rank==jac.shape[1],
        numerical_rank_cutoff=float(cutoff),unscored_coordinates_checked=False,
        archival_stability_qualified=False,scientific_decision='abstain')
    return result
