# SPDX-License-Identifier: AGPL-3.0-or-later
"""Local delta/cubature comparison; not calibrated probabilistic coverage."""
import math

import numpy as np

VERSION='ilvis0-local-scalar-response-v1'


def local_response(function,mean,covariance,*,step=.01):
    mean=np.asarray(mean,float);covariance=np.asarray(covariance,float)
    n=len(mean) if mean.ndim==1 else 0
    if (not n or not np.all(np.isfinite(mean)) or covariance.shape!=(n,n)
            or not np.all(np.isfinite(covariance))
            or not np.allclose(covariance,covariance.T,rtol=1e-12,atol=0.)
            or not math.isfinite(step) or step<=0.):
        raise ValueError('finite mean, symmetric covariance and positive step required')
    variances=np.diag(covariance)
    if np.any(variances<=0.):raise ValueError('positive definite covariance required')
    scales=np.sqrt(variances)
    correlation=covariance/scales[:,None]/scales[None,:]
    try:root=scales[:,None]*np.linalg.cholesky(correlation)
    except np.linalg.LinAlgError as error:
        raise ValueError('positive definite covariance required; no repair') from error
    calls=0
    def value(point):
        nonlocal calls
        calls+=1;result=float(function(point.copy()))
        if not math.isfinite(result):raise ValueError('nonfinite nonlinear response')
        return result
    center=value(mean)
    gradients=[]
    for factor in (1.,2.):
        gradient=[]
        for i in range(n):
            displacement=root[:,i]*(step*factor)
            gradient.append((value(mean+displacement)-value(mean-displacement))/(2*step*factor))
        gradients.append(np.array(gradient))
    linear_sigma=float(np.linalg.norm(gradients[0]))
    disagreement=float(np.linalg.norm(gradients[0]-gradients[1])/
        max(np.linalg.norm(gradients[0]),np.linalg.norm(gradients[1]),1e-15))
    sampled=np.array([value(mean+sign*math.sqrt(n)*root[:,i]) for i in range(n) for sign in (-1.,1.)])
    cubature_mean=float(np.mean(sampled));cubature_sigma=float(np.std(sampled))
    return dict(version=VERSION,center=center,linear_sigma=linear_sigma,
        cubature_mean=cubature_mean,cubature_sigma=cubature_sigma,mean_shift=cubature_mean-center,
        relative_gradient_disagreement=disagreement,evaluations=calls,
        covariance_calibrated=False,cubature_is_exact_distribution=False,scientific_decision='abstain')
