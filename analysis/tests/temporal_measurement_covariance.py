# SPDX-License-Identifier: AGPL-3.0-or-later
"""Conditional temporal-covariance sensitivity; no statistical decisions or fitting."""
import numpy as np
from scipy.signal import lfilter
from scipy.sparse import csr_matrix, diags

POLICY = dict(version='temporal-shared-input-sensitivity-1',
    gps_correlation_seconds=[0.,1.,5.,15.,60.,300.],
    imu_correlation_seconds=[0.,1.,5.,15.,60.,300.],
    temporal_kernel='exp(-abs(t_i-t_j)/tau); tau=0 means independent input seconds',
    latent_factor='Principal symmetric root of dimensionless channel correlation times marginal scales',
    imu_latent_frame='Physical sensor axes mapped into recovered reference orientation at each second',
    gaps='Covariance may persist over elapsed gaps; no missing data, filter support or derivative rows added',
    scope='Six saved states, fixed support and marginal error scales, 36 scenarios each; no optimization',
    production_enabled=False,decisions_enabled=False)


def correlation_root(S):
    """Unit-independent channel standardization; no arbitrary eigenvector matching."""
    sigma=np.sqrt(np.maximum(np.diagonal(S,axis1=1,axis2=2),0.))
    denominator=sigma[:,:,None]*sigma[:,None,:]
    correlation=np.divide(S,denominator,out=np.zeros_like(S),where=denominator>0)
    correlation=(correlation+correlation.transpose(0,2,1))/2
    values,vectors=np.linalg.eigh(correlation)
    if values.min() < -1e-8:raise ValueError('input covariance is not positive semidefinite')
    root=(vectors*np.sqrt(np.maximum(values,0.))[:,None,:])@vectors.transpose(0,2,1)
    return sigma[:,:,None]*root


def latent_responses(jacobians,S,rotations):
    """Preserve within-second blocks; carry IMU correlation in physical sensor axes."""
    if S.shape[1:]!=(11,11) or rotations.shape!=(len(S),3,3):raise ValueError('eleven channels and per-second mount rotations required')
    if np.any(S[:,:5,5:]) or np.any(S[:,5:,:5]):raise ValueError('this sensitivity policy assumes no GPS/IMU cross covariance')
    Q=np.zeros_like(S);Q[:,:5,:5]=correlation_root(S[:,:5,:5])
    R=np.zeros((len(S),6,6));R[:,:3,:3]=rotations;R[:,3:,3:]=rotations
    sensor=R.transpose(0,2,1)@S[:,5:,5:]@R
    Q[:,5:,5:]=R@correlation_root(sensor)
    # Sparse response for each standardized latent error, retaining all cross-axis
    # and gyro/auxiliary shared-input paths in the observation Jacobian.
    responses=[]
    for j in range(11):
        response=csr_matrix(jacobians[0].shape)
        for i,B in enumerate(jacobians):
            if np.any(Q[:,i,j]):response=response+B@diags(Q[:,i,j])
        responses.append(response.tocsr())
    return responses,Q


def temporal_product(values,t,tau):
    """Apply exponential covariance without forming a dense timestamp matrix."""
    values=np.asarray(values,float);t=np.asarray(t,float)
    if values.shape[1]!=len(t) or len(t)<1 or not np.isfinite(t).all() or np.any(np.diff(t)<=0):raise ValueError('increasing finite times and matching columns required')
    if not np.isfinite(tau) or tau<0:raise ValueError('nonnegative finite correlation duration required')
    if tau==0:return values.copy()
    steps=np.diff(t)
    if len(steps)==0:return values.copy()
    if np.max(abs(steps-steps[0]))<1e-7:
        rho=np.exp(-steps[0]/tau)
        forward=lfilter([1.],[1.,-rho],values,axis=1)
        backward=lfilter([1.],[1.,-rho],values[:,::-1],axis=1)[:,::-1]
    else:
        # Exact elapsed-time recurrence across irregular timestamps and gaps.
        forward=values.copy();backward=values.copy();rho=np.exp(-steps/tau)
        for i in range(1,len(t)):forward[:,i]+=rho[i-1]*forward[:,i-1]
        for i in range(len(t)-2,-1,-1):backward[:,i]+=rho[i]*backward[:,i+1]
    return forward+backward-values


def temporal_covariance(responses,t,tau):
    covariance=np.zeros((responses[0].shape[0],responses[0].shape[0]))
    for response in responses:
        if not response.nnz:continue
        transformed=temporal_product(response.toarray(),t,tau)
        covariance+=response@transformed.T
    return (covariance+covariance.T)/2


def scenario_metrics(covariance,residual_response,parameter_response,n):
    after=residual_response@covariance@residual_response.T
    parameters=parameter_response@covariance@parameter_response.T
    from lll.calib import RAD2DPH
    return dict(fixed_parameter_sigma_dph=float(np.sqrt(np.maximum(np.diag(covariance)[:n],0.).mean())*RAD2DPH),
        local_fit_residual_sigma_dph=float(np.sqrt(np.maximum(np.diag(after),0.).mean())*RAD2DPH),
        local_k_sampling_sd=np.sqrt(np.maximum(np.diag(parameters)[:3],0.)).tolist())
