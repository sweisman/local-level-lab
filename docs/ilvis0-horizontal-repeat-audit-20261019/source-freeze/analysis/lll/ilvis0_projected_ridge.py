# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate ridge-probe candidate; physical scores and thresholds are unchanged."""
import types
import numpy as np
from scipy.optimize import lsq_linear
from . import ilvis0_projected_local as preceding

VERSION='ilvis0-horizontal-ridge-probe-v1'
RIDGE=1e-6


def _correction(jac,right,*,bounds,**kwargs):
    scale=np.maximum(np.linalg.norm(jac,axis=0),1.)
    matrix=np.vstack((jac/scale,np.sqrt(RIDGE)*np.eye(jac.shape[1])))
    result=lsq_linear(matrix,np.r_[right,np.zeros(jac.shape[1])],
                      bounds=(bounds[0]*scale,bounds[1]*scale),**kwargs)
    return types.SimpleNamespace(success=result.success,x=result.x/scale)


def verify_local(point,residual,jac,evaluate,physical_step):
    # Private function globals retain every old validation and final numerical
    # threshold. Only the affine proposal gets the displacement penalty.
    namespace=dict(preceding.verify_local.__globals__,lsq_linear=_correction)
    verify=types.FunctionType(preceding.verify_local.__code__,namespace)
    result=verify(point,residual,jac,evaluate,physical_step)
    return dict(result,ridge_penalty=RIDGE,regularization_changes_score=False,
                version=VERSION,local_stability_only=True)


def engine():
    core=preceding.engine()
    proxy=types.SimpleNamespace(**vars(core.position));proxy.verify_stability=verify_local;proxy.VERSION=VERSION
    core.position=proxy;core.VERSION=VERSION
    core.POLICY=dict(core.POLICY,local_correction='column-scaled ridge displacement; unregularized model score',ridge_penalty=RIDGE)
    return core


def fit_control(problem,model,*,start,maximum_evaluations=200):
    if type(maximum_evaluations) is not int or not 6<=maximum_evaluations<=600:
        raise ValueError('finite generated allowance in [6,600] required')
    result=engine().fit_candidate(problem,model,start=start,maximum_evaluations=maximum_evaluations,
                                  physical_step=problem.physical_step)
    jac=np.asarray(result['local_linearization']['jacobian']);singular=np.linalg.svd(jac,compute_uv=False)
    cutoff=max(jac.shape)*np.finfo(float).eps*singular[0]
    result.update(projected_version=VERSION,numerical_rank=int(np.sum(singular>cutoff)),columns=jac.shape[1],
        numerical_rank_cutoff=float(cutoff),retained_coordinates=list(problem.projection.axes),
        local_stability_only=True,unscored_coordinates_checked=False,archival_stability_qualified=False,
        scientific_decision='abstain',regularization_changes_score=False)
    return result
