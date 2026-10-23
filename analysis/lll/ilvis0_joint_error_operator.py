# SPDX-License-Identifier: AGPL-3.0-or-later
"""Linear-memory receiver plus accumulated IMU error, under a supplied law.

The inertial model is the separately checked constant-coupling linear SDE.
No fitting, aircraft error calibration, nonlinear propagation guarantee or
physical decision is performed. Calibration uncertainty remains external.
"""
import hashlib
import math

import numpy as np
from scipy.linalg import solve_triangular

from .ilvis0_error_model import Spec,component,factor
from .ilvis0_inertial_error import transition,process_covariance,_coupling


def _times(values):
    times=np.array(values,float,copy=True)
    if (times.ndim!=1 or not len(times) or not np.all(np.isfinite(times))
            or np.any(np.diff(times)<=0.)):
        raise ValueError('finite strictly increasing epochs required')
    return times


def _finite(values):
    if not np.all(np.isfinite(values)):raise ValueError('unrepresentable joint error propagation')
    return values


class Operator:
    def __init__(self,times,spec,*,origin_s,accel_psd,gyro_psd,coupling):
        self.times=_times(times);self.origin_s=float(origin_s)
        if not isinstance(spec,Spec) or not math.isfinite(self.origin_s) or self.times[0]<self.origin_s:
            raise ValueError('declared receiver Spec and fixed noise origin at or before observations required')
        self.spec=spec;self.accel_psd=component(accel_psd);self.gyro_psd=component(gyro_psd)
        self.coupling=np.array(_coupling(coupling),copy=True)
        self._q=len(spec.components);self._receiver_size=3*(self._q+2)
        self.state_dimension=self._receiver_size+9;size=self.state_dimension;n=len(self.times)
        self._lower=np.empty((n,3,3));self._gain=np.empty((n,size,3));self._dt=np.diff(np.r_[self.origin_s,self.times])
        prior=np.zeros((size,size));root=np.zeros_like(prior);identity=np.eye(size)
        for j,values in enumerate([v for _,v in spec.components]+[spec.offset,spec.drift]):
            prior[3*j:3*j+3,3*j:3*j+3]=values
        for i,time_s in enumerate(self.times):
            f,prior=self._advance(prior,self._dt[i]);root=f@root
            h=self._observation(time_s);cross=h@prior
            innovation=cross@h.T+spec.white;lower=factor((innovation+innovation.T)/2.)
            gain=solve_triangular(lower.T,solve_triangular(lower,cross,lower=True),lower=False).T
            self._lower[i]=lower;self._gain[i]=gain
            update=identity-gain@h
            prior=update@prior@update.T+gain@spec.white@gain.T
            prior=(prior+prior.T)/2.
            root=np.linalg.qr(np.hstack((root,gain@lower)).T,mode='reduced')[1].T
            _finite(prior);_finite(root)
        self._final_covariance=prior;self._mean_root=root
        self.log_determinant=float(2.*np.log(np.diagonal(self._lower,axis1=1,axis2=2)).sum())
        if not math.isfinite(self.log_determinant):raise ValueError('unrepresentable innovation determinant')
        digest=hashlib.sha256(b'ilvis0-joint-error-operator-v1')
        arrays=[self.times,self._dt,self.coupling,self.accel_psd,self.gyro_psd,spec.white,spec.offset,spec.drift,
            np.array([self.origin_s,spec.drift_origin_s,spec.drift_span_s]),
            *[np.array([tau]) for tau,_ in spec.components],*[v for _,v in spec.components]]
        for value in arrays:
            digest.update(str(value.shape).encode()+b':'+np.ascontiguousarray(value).tobytes())
        self.configuration=digest.hexdigest()
        for value in (self.times,self._dt,self.coupling,self._lower,self._gain,prior,root):value.setflags(write=False)
        self.storage_bytes=sum(v.nbytes for v in (self.times,self._dt,self.coupling,self._lower,self._gain,prior,root,
            self.accel_psd,self.gyro_psd))
        self.parameter_uncertainty_included=False;self.observational_coverage_qualified=False

    def _transition(self,dt):
        f=np.eye(self.state_dimension)
        for j,(tau,_) in enumerate(self.spec.components):f[3*j:3*j+3,3*j:3*j+3]*=np.exp(-dt/tau)
        f[self._receiver_size:,self._receiver_size:]=transition(dt,self.coupling)
        return f

    def _advance(self,prior,dt):
        f=self._transition(dt);result=f@prior@f.T
        for j,(tau,values) in enumerate(self.spec.components):
            result[3*j:3*j+3,3*j:3*j+3]+=-np.expm1(-2.*dt/tau)*values
        result[self._receiver_size:,self._receiver_size:]+=process_covariance(
            dt,self.accel_psd,self.gyro_psd,self.coupling)
        return f,_finite((result+result.T)/2.)

    def _observation(self,time_s):
        h=np.zeros((3,self.state_dimension));eye=np.eye(3)
        for j in range(self._q+1):h[:,3*j:3*j+3]=eye
        h[:,3*(self._q+1):self._receiver_size]=eye*((time_s-self.spec.drift_origin_s)/self.spec.drift_span_s)
        h[:,self._receiver_size:self._receiver_size+3]=eye
        return h

    def _blocks(self,values):
        values=np.asarray(values,float);n=len(self.times)
        if (values.ndim not in (1,2) or len(values)!=3*n or not np.all(np.isfinite(values))
                or (values.ndim==2 and not values.shape[1])):
            raise ValueError('complete finite epoch-major vector or matrix required')
        columns=1 if values.ndim==1 else values.shape[1]
        return values,values.reshape(n,3,columns),columns

    def _apply(self,values,*,inverse=False):
        values,blocks,columns=self._blocks(values)
        output=np.empty_like(blocks);mean=np.zeros((self.state_dimension,columns))
        for i,time_s in enumerate(self.times):
            mean=self._transition(self._dt[i])@mean
            if inverse:
                innovation=self._lower[i]@blocks[i]
                output[i]=self._observation(time_s)@mean+innovation
            else:
                innovation=blocks[i]-self._observation(time_s)@mean
                output[i]=solve_triangular(self._lower[i],innovation,lower=True)
            mean+=self._gain[i]@innovation
        return _finite(output.reshape(values.shape)),_finite(mean)

    def whiten(self,values):
        return self._apply(values)[0]

    def unwhiten(self,values):
        """Apply the implicit joint covariance factor L; no dense factor is formed."""
        return self._apply(values,inverse=True)[0]

    def unwhiten_transpose(self,values):
        """Apply L.T by a reverse state recursion, retaining every cross covariance."""
        values,blocks,columns=self._blocks(values)
        output=np.empty_like(blocks);adjoint=np.zeros((self.state_dimension,columns))
        for i in range(len(self.times)-1,-1,-1):
            output[i]=self._lower[i].T@(blocks[i]+self._gain[i].T@adjoint)
            adjoint=self._transition(self._dt[i]).T@(adjoint+self._observation(self.times[i]).T@blocks[i])
        return _finite(output.reshape(values.shape))

    def project_covariance(self,weights):
        """Covariance of declared linear summaries, using O(n*k+k*k) workspace.

        Rows are fixed observation weights; this neither estimates the law nor
        includes nonlinear calibration or covariance-parameter uncertainty.
        """
        weights=np.asarray(weights,float)
        if (weights.ndim!=2 or not weights.shape[0] or weights.shape[1]!=3*len(self.times)
                or not np.all(np.isfinite(weights))):
            raise ValueError('finite nonempty summary rows over all observation coordinates required')
        factor=self.unwhiten_transpose(weights.T);covariance=factor.T@factor
        return _finite((covariance+covariance.T)/2.)

    def forecast(self,future_times):
        return _Forecast(self,future_times)


class _Forecast:
    def __init__(self,operator,times):
        self.times=_times(times);self._operator=operator
        if self.times[0]<=operator.times[-1]:raise ValueError('future epochs must follow all training epochs')
        prior=np.array(operator._final_covariance,copy=True);cumulative=np.eye(operator.state_dimension)
        previous=operator.times[-1];n=len(self.times)
        self._response=np.empty((n,3,operator.state_dimension));self.variance=np.empty((n,3))
        self.training_response_norm=np.empty((n,3))
        for i,time_s in enumerate(self.times):
            f,prior=operator._advance(prior,time_s-previous);cumulative=f@cumulative
            h=operator._observation(time_s);self._response[i]=h@cumulative
            self.variance[i]=np.diag(h@prior@h.T+operator.spec.white)
            self.training_response_norm[i]=np.linalg.norm(self._response[i]@operator._mean_root,axis=1)
            previous=time_s
        self.variance=self.variance.ravel();self.training_response_norm=self.training_response_norm.ravel()
        if np.any(self.variance<=0.):raise ValueError('positive conditional coordinate variances required')
        for v in (self.times,self._response,self.variance,self.training_response_norm):_finite(v);v.setflags(write=False)
        self.storage_bytes=sum(v.nbytes for v in (self.times,self._response,self.variance,self.training_response_norm))
        self.parameter_uncertainty_included=False;self.observational_coverage_qualified=False

    def mean(self,training_values):
        values=np.asarray(training_values,float);_,state=self._operator._apply(values)
        output=np.einsum('ndq,qk->ndk',self._response,state).reshape(3*len(self.times),state.shape[1])
        return _finite(output.ravel() if values.ndim==1 else output)
