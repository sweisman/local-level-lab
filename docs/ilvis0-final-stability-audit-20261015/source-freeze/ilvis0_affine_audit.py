# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit saved local systems without native predictions, refits or new labels."""
import numpy as np
from scipy.optimize import lsq_linear

VERSION='ilvis0-saved-affine-zero-step-audit-v1'


def step_metrics(point,residual,jac,step):
    point,residual,jac,step=map(lambda x:np.asarray(x,float),(point,residual,jac,step))
    if (jac.shape!=(len(residual),len(point)) or step.shape!=point.shape
            or not all(np.all(np.isfinite(x)) for x in (point,residual,jac,step))):
        raise ValueError('finite compatible local system required')
    # Wider accumulation checks whether a reported decrease is cancellation.
    wide=np.longdouble;initial=residual.astype(wide);updated=initial+jac.astype(wide)@step.astype(wide)
    before=float(initial@initial);after=float(updated@updated)
    return dict(affine_cost=after,affine_cost_change=after-before,
        relative_affine_cost_change=(after-before)/max(before,after,1.),
        improves_on_zero=after<before,feasible=bool(np.all(abs(point+step)<=1+1e-12)),
        normalized_step=float(np.linalg.norm(step)),step=step.tolist())


def assess(point,residual,jac):
    point,residual,jac=map(lambda x:np.asarray(x,float),(point,residual,jac))
    singular=np.linalg.svd(jac,compute_uv=False);scale=np.maximum(np.linalg.norm(jac,axis=0),1e-12)
    lower,upper=-1-point,1-point;methods=[]
    for name,factors in (('original_bvls',np.ones(len(point))),('column_scaled_bvls',scale)):
        fit=lsq_linear(jac/factors,-residual,bounds=(lower*factors,upper*factors),method='bvls',tol=1e-10,max_iter=100)
        methods.append(dict(method=name,success=bool(fit.success),status=int(fit.status),iterations=fit.nit,
                            optimality=float(fit.optimality),**step_metrics(point,residual,jac,fit.x/factors)))
    smallest=float(singular[-1]);largest=float(singular[0])
    return dict(version=VERSION,zero_step_cost=float(residual@residual),singular_values=singular.tolist(),
        condition_number=largest/smallest if smallest else None,
        diagnostic_rank_by_relative_cutoff={str(t):int(np.sum(singular>largest*t)) for t in (1e-6,1e-8,1e-10,1e-12)},
        column_norms=scale.tolist(),methods=methods,native_predictions=0,observed_fit_starts=0,
        original_labels_changed=False,scientific_decision='abstain')
