# SPDX-License-Identifier: AGPL-3.0-or-later
"""Linear-memory innovations for the declared shared three-axis error family.

Covariance is supplied, not estimated or calibrated. No archive fitting or
physical prediction occurs here. Dense reference code remains unchanged.
"""
import hashlib

import numpy as np
from scipy.linalg import solve_triangular

from .ilvis0_error_model import Spec, factor


class Innovations:
    def __init__(self, times, spec, *, transforms=None, axes=(0,1,2)):
        t=np.array(times,float,copy=True)
        if t.ndim!=1 or not len(t) or not np.all(np.isfinite(t)) or np.any(np.diff(t)<=0.):
            raise ValueError('finite strictly increasing epochs required')
        if not isinstance(spec,Spec): raise ValueError('declared shared-error Spec required')
        axes=tuple(axes)
        if not axes or len(set(axes))!=len(axes) or any(type(x) is not int or x not in (0,1,2) for x in axes):
            raise ValueError('nonempty unique coordinate axes required')
        a=None if transforms is None else np.array(transforms,float,copy=True)
        if a is not None and (a.shape!=(len(t),3,3) or not np.all(np.isfinite(a))
                or np.any(np.linalg.slogdet(a)[0]==0)):
            raise ValueError('finite invertible per-epoch coordinate transforms required')
        self.times=t; self.axes=axes; self.spec=spec; self.transforms=a
        self._q=len(spec.components); self.state_dimension=3*(self._q+2)
        n=len(t); d=len(axes); state_size=self.state_dimension
        self._u=(t-spec.drift_origin_s)/spec.drift_span_s
        self._rho=np.ones((n,self._q))
        self._lower=np.empty((n,d,d)); self._gain=np.empty((n,state_size,d))
        prior=np.zeros((state_size,state_size))
        blocks=[values for _,values in spec.components]+[spec.offset,spec.drift]
        for j,block in enumerate(blocks): prior[3*j:3*j+3,3*j:3*j+3]=block
        identity=np.eye(state_size)
        for i in range(n):
            if i:
                dt=t[i]-t[i-1]; transition=np.ones(state_size)
                for j,(tau,values) in enumerate(spec.components):
                    rho=np.exp(-dt/tau); self._rho[i,j]=rho; transition[3*j:3*j+3]=rho
                prior=prior*transition[:,None]*transition[None,:]
                for j,(tau,values) in enumerate(spec.components):
                    prior[3*j:3*j+3,3*j:3*j+3]+=-np.expm1(-2.*dt/tau)*values
            transform=self._transform(i)
            observation=np.hstack([transform]*(self._q+1)+[self._u[i]*transform])
            white=transform@spec.white@transform.T
            innovation=observation@prior@observation.T+white
            lower=factor((innovation+innovation.T)/2.)
            gain=solve_triangular(lower.T,solve_triangular(lower,observation@prior,lower=True),lower=False).T
            self._lower[i]=lower; self._gain[i]=gain
            # Joseph form preserves latent semidefiniteness without jitter or
            # eigenvalue clipping. Symmetrization removes roundoff skew only.
            update=identity-gain@observation
            prior=update@prior@update.T+gain@white@gain.T
            prior=(prior+prior.T)/2.
        self.log_determinant=float(2.*np.log(np.diagonal(self._lower,axis1=1,axis2=2)).sum())
        if not np.isfinite(self.log_determinant): raise ValueError('unrepresentable innovations determinant')
        digest=hashlib.sha256()
        for value in [t,spec.white,spec.offset,spec.drift,
                np.array([spec.drift_origin_s,spec.drift_span_s]),
                *[np.array([tau]) for tau,_ in spec.components],
                *[block for _,block in spec.components]]:
            digest.update(str(np.shape(value)).encode()+b':')
            digest.update(np.ascontiguousarray(value).tobytes())
        digest.update(b'none' if a is None else a.tobytes())
        self.base_configuration=digest.hexdigest()
        digest.update(bytes(axes)); self.configuration=digest.hexdigest()
        arrays=[self.times,self._u,self._rho,self._lower,self._gain]
        if a is not None: arrays.append(a)
        for value in arrays: value.setflags(write=False)
        self.storage_bytes=sum(value.nbytes for value in arrays)

    def _transform(self,index):
        transform=np.eye(3) if self.transforms is None else self.transforms[index]
        return transform[list(self.axes),:]

    def apply_block(self, values, *, first_epoch, state=None, inverse=False):
        """Apply continuous ordered blocks, returning an explicit serializable state.

        A vector or matrix uses epoch-major retained coordinates in its rows.
        Every matrix column follows the same operator, including zero/rank-
        deficient Jacobian columns. Never restart a later block without state.
        """
        values=np.asarray(values,float); d=len(self.axes)
        if (values.ndim not in (1,2) or not len(values) or len(values)%d
                or not np.all(np.isfinite(values)) or (values.ndim==2 and not values.shape[1])):
            raise ValueError('aligned finite vector or multi-column matrix required')
        columns=1 if values.ndim==1 else values.shape[1]; epochs=len(values)//d
        if type(first_epoch) is not int or first_epoch<0 or first_epoch+epochs>len(self.times):
            raise ValueError('block outside declared epoch support')
        if state is None:
            if first_epoch!=0: raise ValueError('later blocks require continuous saved state')
            mean=np.zeros((self.state_dimension,columns))
        else:
            if (state.get('configuration')!=self.configuration or state.get('next_epoch')!=first_epoch
                    or state.get('columns')!=columns or state.get('inverse') is not bool(inverse)):
                raise ValueError('block configuration, order, columns or direction changed')
            mean=np.array(state['mean'],float,copy=True)
            if mean.shape!=(self.state_dimension,columns) or not np.all(np.isfinite(mean)):
                raise ValueError('invalid saved innovations state')
        blocks=values.reshape(epochs,d,columns); output=np.empty_like(blocks)
        for local,i in enumerate(range(first_epoch,first_epoch+epochs)):
            latent=mean.reshape(self._q+2,3,columns)
            if self._q: latent[:self._q]*=self._rho[i,:,None,None]
            expected=self._transform(i)@(latent[:-1].sum(axis=0)+self._u[i]*latent[-1])
            if inverse:
                innovation=self._lower[i]@blocks[local]
                output[local]=expected+innovation
            else:
                innovation=blocks[local]-expected
                output[local]=solve_triangular(self._lower[i],innovation,lower=True)
            mean+=self._gain[i]@innovation
        if not np.all(np.isfinite(output)) or not np.all(np.isfinite(mean)):
            raise ValueError('unrepresentable innovations or continuation state')
        checkpoint=dict(configuration=self.configuration,next_epoch=first_epoch+epochs,
            columns=columns,inverse=bool(inverse),mean=mean)
        return output.reshape(values.shape),checkpoint

    def whiten(self,values):
        if len(values)!=len(self.times)*len(self.axes): raise ValueError('whole-record vector/matrix required')
        return self.apply_block(values,first_epoch=0)[0]

    def unwhiten(self,values):
        if len(values)!=len(self.times)*len(self.axes): raise ValueError('whole-record vector/matrix required')
        return self.apply_block(values,first_epoch=0,inverse=True)[0]

    def project_to(self,whitened,target):
        """L_subset^-1 S L_full, with no dense factor or projection matrix."""
        if self.axes!=(0,1,2) or not isinstance(target,Innovations) or target.base_configuration!=self.base_configuration:
            raise ValueError('full source and identical covariance/epoch/transform configuration required')
        raw=self.unwhiten(whitened); columns=1 if raw.ndim==1 else raw.shape[1]
        selected=raw.reshape(len(self.times),3,columns)[:,target.axes,:]
        values=selected.reshape(len(self.times)*len(target.axes),columns)
        if raw.ndim==1: values=values.ravel()
        return target.whiten(values)
