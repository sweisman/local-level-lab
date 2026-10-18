# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed-endpoint matrix diagnostics; no fit, eligibility or rank-policy changes."""
import numpy as np
from scipy.optimize import lsq_linear


def matrix(value):
    value=np.asarray(value,float)
    if value.ndim!=2 or min(value.shape)<1 or not np.all(np.isfinite(value)):
        raise ValueError('nonempty finite matrix required')
    return value


def directions(jac,names):
    jac=matrix(jac);names=list(names)
    if len(names)!=jac.shape[1] or len(set(names))!=len(names):raise ValueError('every unique column name required')
    _,singular,vt=np.linalg.svd(jac,full_matrices=True)
    cutoff=max(jac.shape)*np.finfo(float).eps*singular[0]
    rank=int(np.sum(singular>cutoff))
    values=np.pad(singular,(0,max(0,len(names)-len(singular))))
    weak=[dict(singular_value=float(values[i]),components=dict(zip(names,vt[i].tolist())))
          for i in range(len(names)-1,max(-1,len(names)-4),-1)]
    return dict(columns=len(names),rank=rank,singular_values=singular.tolist(),cutoff=float(cutoff),
        column_norms=dict(zip(names,np.linalg.norm(jac,axis=0).tolist())),weak_directions=weak,
        condition_ratio=float(singular[0]/singular[-1]) if rank==len(names) else None)


def linear_steps(point,residual,jac):
    jac=matrix(jac);point=np.asarray(point,float);residual=np.asarray(residual,float)
    if (point.shape!=(jac.shape[1],) or residual.shape!=(jac.shape[0],)
            or not np.all(np.isfinite(point)) or not np.all(np.isfinite(residual)) or np.any(abs(point)>1)):
        raise ValueError('finite feasible point and compatible residual required')
    norms=np.linalg.norm(jac,axis=0);scales=np.where(norms>0,norms,1.)
    rank=directions(jac,[str(i) for i in range(jac.shape[1])])['rank']
    rows={}
    for name,scale in (('unscaled',np.ones_like(scales)),('column_scaled',scales)):
        sol=lsq_linear(jac/scale,-residual,bounds=((-1-point)*scale,(1-point)*scale),
            method='bvls',tol=1e-10,max_iter=100)
        if not sol.success or not np.all(np.isfinite(sol.x)):raise ValueError('bounded diagnostic solve unfinished: '+name)
        raw=sol.x/scale;step=np.clip(raw,-1-point,1-point)
        rows[name]=dict(correction=step.tolist(),columns=jac.shape[1],rank=rank,
            scaling=scale.tolist(),linear_cost=float(np.dot(residual+jac@step,residual+jac@step)),
            linear_optimality=float(sol.optimality),roundoff_clip_maximum=float(np.max(abs(raw-step))))
    return rows


def derivative_errors(expected,observed,names):
    expected=matrix(expected);observed=matrix(observed);names=list(names)
    if expected.shape!=observed.shape or expected.shape[1]!=len(names):raise ValueError('matching full Jacobians required')
    result={}
    for i,name in enumerate(names):
        delta=observed[:,i]-expected[:,i];norm=float(np.linalg.norm(expected[:,i]))
        result[name]=dict(maximum_absolute_error=float(np.max(abs(delta))),
            relative_column_error=float(np.linalg.norm(delta)/norm) if norm>0 else None)
    return result
