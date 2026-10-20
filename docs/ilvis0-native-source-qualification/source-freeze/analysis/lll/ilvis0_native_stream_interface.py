# SPDX-License-Identifier: AGPL-3.0-or-later
"""Native prediction source for a separately supplied training-only fit/seed.

Future positions and fused navigation are absent from this API. Provenance
labels do not prove an externally supplied seed/center was training-only.
"""
import hashlib
import json

import numpy as np

from .ilvis0_shape import PARAMETERS
from .ilvis0_streaming import Stream
from .ilvis0_prediction_envelope_adapter import Frame,Family

VERSION='ilvis0-native-structured-source-v1'


def _times(values):
    result=np.array(values,float,copy=True)
    if result.ndim!=1 or not len(result) or not np.all(np.isfinite(result)) or np.any(np.diff(result)<=0.):
        raise ValueError('nonempty finite strictly ordered query times required')
    result.setflags(write=False);return result


class NativeSource:
    def __init__(self,directory,configuration,*,training_times,future_times,parameter_names,
                 frame,seed_source_id,center_source_id):
        names=tuple(parameter_names);train=_times(training_times);future=_times(future_times)
        if (names!=PARAMETERS or future[0]<=train[-1] or not isinstance(frame,Frame)
                or not isinstance(seed_source_id,str) or not seed_source_id
                or not isinstance(center_source_id,str) or not center_source_id
                or configuration.get('tangent',True) is not True):
            raise ValueError('full native order, fixed frame, separate support and explicit source identities required')
        self._stream=Stream(directory,**dict(configuration,tangent=True))
        self.training_times=train;self.future_times=future;self.parameter_names=names;self.frame=frame
        self._times=np.r_[train,future];self._query=0;self._positions=[];self._jacobians=[];self._boundaries=0
        self._configuration=self._stream.checkpoint()['config']
        self._sources=dict(seed_source_id=seed_source_id,center_source_id=center_source_id)

    def push(self,theta,dv,dt,*,packet_offset,elapsed_s):
        periods=np.asarray(dt,float)
        if periods.ndim!=1:raise ValueError('one-dimensional packet periods required')
        end=self._stream.elapsed_s
        for period in periods:end+=float(period)
        stop=self._query
        while stop<len(self._times) and self._times[stop]+self._stream.time_offset<=end:stop+=1
        # A block-end query is evaluated now, in its original left interval.
        result=self._stream.push(theta,dv,periods,self._times[self._query:stop],
            packet_offset=packet_offset,elapsed_s=elapsed_s)
        self._positions.append(result['positions']);self._jacobians.append(result['jacobian'].reshape(-1,27))
        self._query=stop;self._boundaries+=result['boundaries']

    def finish(self):
        if self._query!=len(self._times):raise ValueError('native training/future predictions incomplete')
        out=np.concatenate(self._positions);jac=np.vstack(self._jacobians);nt=len(self.training_times)
        receipt=dict(version=VERSION,input_configuration=self._configuration,
            kernel=self._stream.identity,training_times=self.training_times.tolist(),future_times=self.future_times.tolist(),
            parameter_names=list(self.parameter_names),frame_source_id=self.frame.source_id,
            frame_origin=self.frame.origin.tolist(),frame_matrix=self.frame.matrix.tolist(),
            packet_count=self._stream.packet_count,elapsed_s=self._stream.elapsed_s,
            boundaries=self._boundaries,seed_training_provenance_verified=False,
            center_training_provenance_verified=False,global_remainder_available=False,
            future_positions_read=False,fused_navigation_read=False,**self._sources)
        receipt['configuration_sha256']=hashlib.sha256(json.dumps(receipt,sort_keys=True,allow_nan=False).encode()).hexdigest()
        receipt=json.loads(json.dumps(receipt,allow_nan=False))
        return dict(training_prediction=out[:nt].copy(),future_prediction=out[nt:].copy(),
            training_jacobian=jac[:3*nt].copy(),future_jacobian=jac[3*nt:].copy(),receipt=receipt)

    def envelope(self,family,*,candidate_id,training_observations,lower,upper,remainder=None):
        expected=('sphere_rotating','sphere_still','flat_still')[self._configuration['model']]
        if candidate_id!=expected:raise ValueError('candidate label does not match native physical model')
        if (not isinstance(family,Family) or family.parameter_names!=self.parameter_names
                or not np.array_equal(family.training_times,self.training_times)
                or not np.array_equal(family.future_times,self.future_times)
                or family.frame.source_id!=self.frame.source_id
                or not np.array_equal(family.frame.origin,self.frame.origin)
                or not np.array_equal(family.frame.matrix,self.frame.matrix)):
            raise ValueError('native source and uncertainty family dependencies differ')
        supplied=self.finish()
        result=family.envelope(candidate_id=candidate_id,training_observations=training_observations,
            center_parameters=np.array(self._configuration['point']),
            training_prediction=supplied['training_prediction'],future_prediction=supplied['future_prediction'],
            training_jacobian=supplied['training_jacobian'],future_jacobian=supplied['future_jacobian'],
            lower=lower,upper=upper,remainder=remainder)
        result['native_source_receipt']=supplied['receipt']
        return result
