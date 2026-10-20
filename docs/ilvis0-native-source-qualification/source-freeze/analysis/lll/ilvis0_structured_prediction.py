# SPDX-License-Identifier: AGPL-3.0-or-later
"""Conditional error forecasts without future observations or dense covariance.

The covariance is supplied. Bounded calibration and covariance-estimation
uncertainty are not included here. Frozen innovations code is reused unchanged.
"""
import numpy as np

from .ilvis0_structured_covariance import Innovations


class Forecast:
    def __init__(self,training,future_times,*,transforms=None):
        if not isinstance(training,Innovations):raise ValueError('qualified training innovations operator required')
        times=np.array(future_times,float,copy=True)
        if (times.ndim!=1 or not len(times) or not np.all(np.isfinite(times))
                or np.any(np.diff(times)<=0.) or times[0]<=training.times[-1]):
            raise ValueError('strictly increasing future epochs must follow training')
        transform=None if transforms is None else np.asarray(transforms,float)
        if training.transforms is not None and transform is None:
            raise ValueError('explicit future coordinate transforms required')
        if transform is not None and (transform.shape!=(len(times),3,3)
                or not np.all(np.isfinite(transform)) or np.any(np.linalg.slogdet(transform)[0]==0)):
            raise ValueError('finite invertible future coordinate transforms required')
        self.training=training;self.times=times
        spec=training.spec;q=len(spec.components);size=training.state_dimension;d=len(training.axes)
        prior=np.zeros((size,size));mean_root=np.zeros((size,size));identity=np.eye(size)
        blocks=[values for _,values in spec.components]+[spec.offset,spec.drift]
        for j,block in enumerate(blocks):prior[3*j:3*j+3,3*j:3*j+3]=block
        # Reconstruct the final state covariance from the frozen gain sequence.
        # Also propagate the covariance root of the response to whitened training
        # errors. QR avoids subtracting two nearly equal covariance matrices.
        for i,time in enumerate(training.times):
            if i:
                transition=np.ones(size)
                for j,(tau,values) in enumerate(spec.components):
                    transition[3*j:3*j+3]=training._rho[i,j]
                prior=prior*transition[:,None]*transition[None,:]
                mean_root=mean_root*transition[:,None]
                for j,(tau,values) in enumerate(spec.components):
                    dt=time-training.times[i-1]
                    prior[3*j:3*j+3,3*j:3*j+3]+=-np.expm1(-2.*dt/tau)*values
            a=training._transform(i)
            h=np.hstack([a]*(q+1)+[training._u[i]*a])
            gain=training._gain[i];white=a@spec.white@a.T
            update=identity-gain@h
            prior=update@prior@update.T+gain@white@gain.T
            prior=(prior+prior.T)/2.
            responses=np.hstack((mean_root,gain@training._lower[i]))
            mean_root=np.linalg.qr(responses.T,mode='reduced')[1].T
        response=np.empty((len(times),d,size));variance=np.empty((len(times),d));norm=np.empty_like(variance)
        cumulative=np.ones(size);previous=training.times[-1]
        for i,time in enumerate(times):
            dt=time-previous;transition=np.ones(size)
            for j,(tau,values) in enumerate(spec.components):
                transition[3*j:3*j+3]=np.exp(-dt/tau)
            prior=prior*transition[:,None]*transition[None,:]
            for j,(tau,values) in enumerate(spec.components):
                prior[3*j:3*j+3,3*j:3*j+3]+=-np.expm1(-2.*dt/tau)*values
            cumulative*=transition
            a=(np.eye(3) if transform is None else transform[i])[list(training.axes),:]
            u=(time-spec.drift_origin_s)/spec.drift_span_s
            h=np.hstack([a]*(q+1)+[u*a]);response[i]=h*cumulative[None,:]
            variance[i]=np.diag(h@prior@h.T+a@spec.white@a.T)
            norm[i]=np.linalg.norm(response[i]@mean_root,axis=1)
            previous=time
        if (not np.all(np.isfinite(response)) or not np.all(np.isfinite(variance))
                or np.any(variance<=0.) or not np.all(np.isfinite(norm))):
            raise ValueError('unrepresentable conditional prediction geometry')
        self._response=response;self.variance=variance.ravel();self.training_response_norm=norm.ravel()
        for value in (self.times,self._response,self.variance,self.training_response_norm):value.setflags(write=False)
        self.storage_bytes=sum(value.nbytes for value in
            (self.times,self._response,self.variance,self.training_response_norm))
        self.covariance_estimation_uncertainty_included=False
        self.parameter_uncertainty_included=False

    def mean(self,training_values):
        """Conditional error mean, using training values only; all columns kept."""
        values=np.asarray(training_values,float);training=self.training;d=len(training.axes)
        if (values.ndim not in (1,2) or len(values)!=len(training.times)*d
                or not np.all(np.isfinite(values)) or (values.ndim==2 and not values.shape[1])):
            raise ValueError('finite complete training vector or multi-column matrix required')
        checkpoint=None
        for first in range(0,len(training.times),1024):
            last=min(len(training.times),first+1024)
            _,checkpoint=training.apply_block(values[first*d:last*d],first_epoch=first,state=checkpoint)
        columns=checkpoint['columns']
        output=np.einsum('ndq,qk->ndk',self._response,checkpoint['mean']).reshape(-1,columns)
        if not np.all(np.isfinite(output)):raise ValueError('unrepresentable conditional error mean')
        return output.ravel() if values.ndim==1 else output
