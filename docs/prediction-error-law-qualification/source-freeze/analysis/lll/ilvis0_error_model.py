# SPDX-License-Identifier: AGPL-3.0-or-later
"""Research-only shared error covariance; no estimation, archive fits or decisions.

Dense matrices use epoch-major north/east/up order. Component matrices are in
metres squared in a common frame. Explicit transforms can change frames/units.
Whitening and prediction assume a supplied covariance and known residual mean;
they do not include uncertainty in estimated calibration or covariance parameters.
"""
from dataclasses import dataclass
import math

import numpy as np
from scipy.linalg import solve_triangular

VERSION='ilvis0-shared-error-controls-v1'


def symmetric(values,size=None):
    a=np.array(values,dtype=float,copy=True)
    if (a.ndim!=2 or a.shape[0]!=a.shape[1] or not len(a)
            or (size is not None and a.shape!=(size,size)) or not np.all(np.isfinite(a))):
        raise ValueError('finite square covariance required')
    if not np.allclose(a,a.T,rtol=1e-12,atol=0):
        raise ValueError('symmetric covariance required')
    return (a+a.T)/2


def factor(values):
    """Cholesky with diagonal equilibration, no jitter/eigenvalue clipping."""
    a=symmetric(values);d=np.diag(a)
    if np.any(d<=0):raise ValueError('positive definite covariance required')
    scales=np.sqrt(d);normalized=a/scales[:,None]/scales[None,:]
    try:lower=np.linalg.cholesky(normalized)*scales[:,None]
    except np.linalg.LinAlgError as e:raise ValueError('positive definite covariance required') from e
    if not np.all(np.isfinite(lower)):raise ValueError('nonfinite covariance factor')
    return lower


def component(values,positive=False):
    a=symmetric(np.zeros((3,3)) if values is None else values,size=3)
    if positive:factor(a)
    else:
        eigenvalues=np.linalg.eigvalsh(a)
        tolerance=32*np.finfo(float).eps*np.max(np.abs(eigenvalues))
        if np.min(eigenvalues)<-tolerance:raise ValueError('positive semidefinite component required')
    # Tiny roundoff eigenvalues are not clipped; final covariance must factor.
    a.setflags(write=False)
    return a


@dataclass(frozen=True)
class Spec:
    white: object
    components: tuple=()
    offset: object=None
    drift: object=None
    drift_origin_s: float=0.
    drift_span_s: float=1.

    def __post_init__(self):
        if (not math.isfinite(self.drift_origin_s) or not math.isfinite(self.drift_span_s)
                or self.drift_span_s<=0):raise ValueError('finite full-record drift origin/positive span required')
        if len(self.components)>2:raise ValueError('at most two correlation components supported')
        converted=[];previous=0.
        for tau,values in self.components:
            if not math.isfinite(tau) or tau<=previous:raise ValueError('positive strictly ordered time scales required')
            converted.append((float(tau),component(values)));previous=tau
        object.__setattr__(self,'white',component(self.white,positive=True))
        object.__setattr__(self,'offset',component(self.offset))
        object.__setattr__(self,'drift',component(self.drift))
        object.__setattr__(self,'components',tuple(converted))


def covariance(times,spec,transforms=None):
    """Use actual timestamps; drift origin/span are never inferred from a subset."""
    t=np.asarray(times,dtype=float)
    if t.ndim!=1 or not len(t) or not np.all(np.isfinite(t)) or np.any(np.diff(t)<=0):
        raise ValueError('strictly increasing finite epochs required')
    n=len(t);u=(t-spec.drift_origin_s)/spec.drift_span_s
    c=np.kron(np.eye(n),spec.white)+np.kron(np.ones((n,n)),spec.offset)
    c+=np.kron(np.outer(u,u),spec.drift)
    for tau,values in spec.components:
        c+=np.kron(np.exp(-np.abs(t[:,None]-t[None,:])/tau),values)
    if transforms is not None:
        a=np.asarray(transforms,dtype=float)
        if a.shape!=(n,3,3) or not np.all(np.isfinite(a)) or np.any(np.linalg.slogdet(a)[0]==0):
            raise ValueError('finite invertible per-epoch transforms required')
        c=np.einsum('iab,ibjc,jdc->iajd',a,c.reshape(n,3,n,3),a).reshape(3*n,3*n)
    c=(c+c.T)/2
    factor(c)  # Reject loss of positive definiteness rather than repairing it.
    return c


def residual(values,n):
    r=np.asarray(values,dtype=float)
    if r.shape!=(n,) or not np.all(np.isfinite(r)):raise ValueError('aligned finite residual vector required')
    return r


def whiten(values,cov):
    lower=factor(cov);r=residual(values,len(lower))
    innovations=solve_triangular(lower,r,lower=True)
    quadratic=float(innovations@innovations)
    logdet=float(2*np.sum(np.log(np.diag(lower))))
    return dict(innovations=innovations,quadratic=quadratic,log_determinant=logdet,
        negative_log_likelihood=.5*(quadratic+logdet+len(r)*math.log(2*math.pi)))


def indices(values,n):
    i=np.asarray(values)
    if (i.ndim!=1 or not len(i) or i.dtype.kind not in 'iu' or len(np.unique(i))!=len(i)
            or np.any(i<0) or np.any(i>=n)):raise ValueError('nonempty unique integer indices required')
    return i


def condition(cov,training,prediction,training_residual):
    """Gaussian residual prediction conditional only on the supplied training errors.

    Build the complete covariance before splitting, preserving offsets, drift and
    cross-boundary dependence. Does not estimate a trajectory or read held-out errors.
    """
    c=symmetric(cov);factor(c);n=len(c)
    train=indices(training,n);test=indices(prediction,n)
    if np.intersect1d(train,test).size:raise ValueError('training/prediction indices must be disjoint')
    r=residual(training_residual,len(train));lower=factor(c[np.ix_(train,train)])
    whitened=solve_triangular(lower,r,lower=True)
    cross=solve_triangular(lower,c[np.ix_(train,test)],lower=True)
    mean=cross.T@whitened
    conditional=c[np.ix_(test,test)]-cross.T@cross
    conditional=(conditional+conditional.T)/2
    factor(conditional)
    return dict(mean=mean,covariance=conditional,parameter_uncertainty_included=False)
