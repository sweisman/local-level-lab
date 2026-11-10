# SPDX-License-Identifier: AGPL-3.0-or-later
"""Linear-memory innovations for an explicitly supplied linear Gaussian law.

Matrices are fixed inputs, not fitted to the residual being whitened. This
component establishes neither an archive error law nor parameter uncertainty.
"""
import hashlib


class LinearInnovations:
    def __init__(self,steps,*,epoch_count,state_dimension,observation_dimension,
                 initial_loading,maximum_bytes,design_is_fixed,error_distribution,
                 observation_form='after_transition',white_error_may_be_singular=False):
        if (type(epoch_count) is not int or not 1<=epoch_count<=100000
                or type(state_dimension) is not int or not 1<=state_dimension<=40
                or type(observation_dimension) is not int or not 1<=observation_dimension<=3
                or type(maximum_bytes) is not int or maximum_bytes<1):
            raise ValueError('finite epoch, state, observation and storage limits required')
        n,k,d=epoch_count,state_dimension,observation_dimension
        storage=n*(k*k+2*k*d+d*d)*8
        if storage>maximum_bytes:raise ValueError('declared operator storage allowance exceeded')
        if design_is_fixed is not True or error_distribution!='gaussian':
            raise ValueError('explicit fixed-design Gaussian error assumption required')
        if observation_form not in ('after_transition','before_transition_shared_noise'):
            raise ValueError('explicit supported observation timing/noise form required')
        if type(white_error_may_be_singular) is not bool:
            raise ValueError('explicit singular white-error policy required')
        import numpy as np
        from scipy.linalg import solve_triangular
        from lll.ilvis0_error_model import factor
        self.epoch_count=n;self.state_dimension=k;self.observation_dimension=d
        self.observation_form=observation_form
        self.storage_bytes=storage;self.error_law_calibrated=False;self.parameter_uncertainty_included=False
        self._transition=np.empty((n,k,k));self._observation=np.empty((n,d,k))
        self._lower=np.empty((n,d,d));self._gain=np.empty((n,k,d))
        digest=hashlib.sha256(b'linear-gaussian-innovations-v2:'+observation_form.encode())
        if white_error_may_be_singular:digest.update(b':semidefinite-white-allowed')
        def matrix(value,shape=None,rows=None):
            a=np.array(value,dtype=float,copy=True)
            if (a.ndim!=2 or not np.all(np.isfinite(a)) or (shape is not None and a.shape!=shape)
                    or (rows is not None and (a.shape[0]!=rows or a.shape[1]>40))):
                raise ValueError('finite aligned transition, observation and noise-loading matrices required')
            digest.update(str(a.shape).encode()+b':'+a.astype('<f8',copy=False).tobytes())
            return a
        initial=matrix(np.zeros((k,0)) if initial_loading is None else initial_loading,rows=k)
        prior=initial@initial.T;iterator=iter(steps)
        for i in range(n):
            try:step=next(iterator)
            except StopIteration as error:raise ValueError('complete declared state-space steps required') from error
            keys={'transition','process_loading','observation','white_loading'}
            if observation_form=='before_transition_shared_noise':keys.add('observation_process_loading')
            if not isinstance(step,dict) or set(step)!=keys:
                raise ValueError('exact declared state/observation error specification required')
            f=matrix(step['transition'],shape=(k,k));b=matrix(step['process_loading'],rows=k)
            h=matrix(step['observation'],shape=(d,k));loading=matrix(step['white_loading'],rows=d)
            if observation_form=='after_transition':shared=h@b;h=h@f
            else:shared=matrix(step['observation_process_loading'],shape=(d,b.shape[1]))
            white=loading@loading.T
            if not white_error_may_be_singular:
                factor(white)  # Preserve the historical positive-white default.
            # white=loading@loading.T is positive semidefinite by construction.
            # Even in this explicit mode the complete innovation must remain
            # positive definite. Never add a floor to force invertibility.
            innovation=h@prior@h.T+shared@shared.T+white
            lower=factor((innovation+innovation.T)/2)
            cross=f@prior@h.T+b@shared.T
            gain=solve_triangular(lower.T,solve_triangular(lower,cross.T,lower=True),lower=False).T
            self._transition[i]=f;self._observation[i]=h;self._lower[i]=lower;self._gain[i]=gain
            update=f-gain@h;noise=b-gain@shared
            prior=update@prior@update.T+noise@noise.T+gain@white@gain.T;prior=(prior+prior.T)/2
            if not np.all(np.isfinite(prior)):raise ValueError('unrepresentable state covariance')
        try:next(iterator)
        except StopIteration:pass
        else:raise ValueError('more state-space steps than declared')
        self.log_determinant=float(2*np.log(np.diagonal(self._lower,axis1=1,axis2=2)).sum())
        if not np.isfinite(self.log_determinant):raise ValueError('unrepresentable innovations determinant')
        self.configuration=digest.hexdigest()
        for value in (self._transition,self._observation,self._lower,self._gain):value.setflags(write=False)

    def apply_block(self,values,*,first_epoch,state=None,inverse=False):
        import numpy as np
        from scipy.linalg import solve_triangular
        values=np.asarray(values,dtype=float);d=self.observation_dimension
        if (values.ndim not in (1,2) or not len(values) or len(values)%d
                or not np.all(np.isfinite(values)) or (values.ndim==2 and not 1<=values.shape[1]<=512)
                or type(inverse) is not bool):
            raise ValueError('finite epoch-aligned residual vector or complete column matrix required')
        columns=1 if values.ndim==1 else values.shape[1];epochs=len(values)//d
        if type(first_epoch) is not int or first_epoch<0 or first_epoch+epochs>self.epoch_count:
            raise ValueError('block outside declared epoch support')
        if state is None:
            if first_epoch!=0:raise ValueError('later blocks require saved continuous state')
            mean=np.zeros((self.state_dimension,columns))
        else:
            if (not isinstance(state,dict) or state.get('configuration')!=self.configuration
                    or state.get('next_epoch')!=first_epoch or state.get('columns')!=columns
                    or state.get('inverse') is not inverse):
                raise ValueError('block order, configuration, columns or direction changed')
            mean=np.array(state.get('mean'),dtype=float,copy=True)
            if mean.shape!=(self.state_dimension,columns) or not np.all(np.isfinite(mean)):
                raise ValueError('finite aligned checkpoint state required')
        blocks=values.reshape(epochs,d,columns);output=np.empty_like(blocks)
        for local,i in enumerate(range(first_epoch,first_epoch+epochs)):
            expected=self._observation[i]@mean
            if inverse:
                innovation=self._lower[i]@blocks[local];output[local]=expected+innovation
            else:
                innovation=blocks[local]-expected
                output[local]=solve_triangular(self._lower[i],innovation,lower=True)
            mean=self._transition[i]@mean+self._gain[i]@innovation
        if not np.all(np.isfinite(output)) or not np.all(np.isfinite(mean)):
            raise ValueError('unrepresentable innovations or checkpoint')
        checkpoint=dict(configuration=self.configuration,next_epoch=first_epoch+epochs,columns=columns,
            inverse=inverse,mean=mean.tolist())
        return output.reshape(values.shape),checkpoint

    def conditional_marginals(self,*,state=None):
        """Future means/covariance given earlier residuals and fixed parameters.

        Later innovations have zero conditional mean, but remain random. Their
        effects on later innovations-driven means must be propagated as well
        as the saved innovation variances. No later observations are accepted.
        """
        import numpy as np
        from lll.ilvis0_error_model import factor
        k=self.state_dimension;d=self.observation_dimension
        if state is None:first=0;mean=np.zeros((k,1))
        else:
            first=state.get('next_epoch') if isinstance(state,dict) else None
            if (type(first) is not int or not 0<=first<=self.epoch_count
                    or state.get('configuration')!=self.configuration or state.get('columns')!=1
                    or state.get('inverse') is not False):
                raise ValueError('same-configuration earlier forward vector checkpoint required')
            mean=np.array(state.get('mean'),dtype=float,copy=True)
            if mean.shape!=(k,1) or not np.all(np.isfinite(mean)):
                raise ValueError('finite complete earlier checkpoint mean required')
        count=self.epoch_count-first;means=np.empty((count,d));covariances=np.empty((count,d,d))
        uncertain_mean=np.zeros((k,k))
        for local,i in enumerate(range(first,self.epoch_count)):
            f=self._transition[i];h=self._observation[i];gain=self._gain[i]
            innovation=self._lower[i]@self._lower[i].T
            covariance=h@uncertain_mean@h.T+innovation;covariance=(covariance+covariance.T)/2
            factor(covariance)
            means[local]=(h@mean)[:,0];covariances[local]=covariance
            mean=f@mean
            uncertain_mean=f@uncertain_mean@f.T+gain@innovation@gain.T;uncertain_mean=(uncertain_mean+uncertain_mean.T)/2
            if not np.all(np.isfinite(uncertain_mean)):raise ValueError('unrepresentable future error covariance')
        if not np.all(np.isfinite(means)):raise ValueError('unrepresentable conditional future mean')
        return dict(mean=means,covariance=covariances,conditioning_epochs=first,forecast_epochs=count,
            later_observations_used=False,parameter_uncertainty_included=False,error_law_calibrated=False)

    def whiten(self,values):
        if len(values)!=self.epoch_count*self.observation_dimension:raise ValueError('complete record required')
        return self.apply_block(values,first_epoch=0)[0]

    def unwhiten(self,values):
        if len(values)!=self.epoch_count*self.observation_dimension:raise ValueError('complete record required')
        return self.apply_block(values,first_epoch=0,inverse=True)[0]

    def prefix(self,epoch_count):
        return PrefixInnovations(self,epoch_count)


class PrefixInnovations:
    """Earlier-only projection sharing the parent's read-only storage.

    The identity and determinant contain only earlier matrices. Forward and
    inverse operations never consume later residuals. Use the full parent
    explicitly for later conditional predictions; this view has no future data.
    """
    def __init__(self,parent,epoch_count):
        import numpy as np
        if (not isinstance(parent,LinearInnovations) or type(epoch_count) is not int
                or not 1<=epoch_count<=parent.epoch_count):
            raise ValueError('supported positive earlier epoch count required')
        self.parent=parent;self.epoch_count=epoch_count
        self.state_dimension=parent.state_dimension;self.observation_dimension=parent.observation_dimension
        self.shares_parent_storage=True;self.storage_bytes=parent.storage_bytes
        self.error_law_calibrated=False;self.parameter_uncertainty_included=False
        digest=hashlib.sha256(b'linear-innovations-prefix-v1:'+parent.observation_form.encode())
        for values in (parent._transition,parent._observation,parent._lower,parent._gain):
            prefix=values[:epoch_count].astype('<f8',copy=False)
            digest.update(str(prefix.shape).encode()+b':')
            digest.update(memoryview(prefix).cast('B'))
        self.configuration=digest.hexdigest()
        self.log_determinant=float(2*np.log(np.diagonal(parent._lower[:epoch_count],axis1=1,axis2=2)).sum())

    def whiten(self,values):
        if len(values)!=self.epoch_count*self.observation_dimension:
            raise ValueError('complete training prefix required')
        return self.parent.apply_block(values,first_epoch=0)[0]

    def unwhiten(self,values):
        if len(values)!=self.epoch_count*self.observation_dimension:
            raise ValueError('complete training prefix required')
        return self.parent.apply_block(values,first_epoch=0,inverse=True)[0]
