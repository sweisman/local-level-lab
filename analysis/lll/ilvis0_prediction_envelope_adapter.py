# SPDX-License-Identifier: AGPL-3.0-or-later
"""Training-only interface for supplied native means and global error assumptions.

No integration, fitting, future observations or automatic physical decisions.
Declaring a global remainder does not demonstrate its validity for an archive.
"""
from dataclasses import dataclass
import hashlib
import json
from types import MappingProxyType

import numpy as np

from .ilvis0_bounded_prediction import Region,ScaleBound,predict,union
from .ilvis0_structured_covariance import Innovations
from .ilvis0_structured_prediction import Forecast


def _vector(value,size=None):
    x=np.array(value,float,copy=True)
    if x.ndim!=1 or not len(x) or (size is not None and x.shape!=(size,)) or not np.all(np.isfinite(x)):
        raise ValueError('aligned finite parameter or coordinate vector required')
    x.setflags(write=False);return x


def _identity(value):
    if not isinstance(value,str) or not value:raise ValueError('explicit nonempty provenance identity required')
    return value


@dataclass(frozen=True)
class Frame:
    origin:object
    matrix:object
    source_id:str

    def __post_init__(self):
        origin=_vector(self.origin,3);matrix=np.array(self.matrix,float,copy=True)
        if matrix.shape!=(3,3) or not np.all(np.isfinite(matrix)) or np.linalg.slogdet(matrix)[0]==0.:
            raise ValueError('fixed invertible finite coordinate transform required')
        matrix.setflags(write=False);_identity(self.source_id)
        object.__setattr__(self,'origin',origin);object.__setattr__(self,'matrix',matrix)

    def positions(self,values):
        x=np.asarray(values,float)
        if x.ndim!=2 or x.shape[1]!=3 or not len(x) or not np.all(np.isfinite(x)):
            raise ValueError('finite three-coordinate observations or predictions required')
        result=(x-self.origin)@self.matrix.T
        if not np.all(np.isfinite(result)):raise ValueError('unrepresentable fixed-frame positions')
        return result

    def jacobian(self,values):
        x=np.asarray(values,float)
        if x.ndim!=2 or not len(x) or len(x)%3 or not x.shape[1] or not np.all(np.isfinite(x)):
            raise ValueError('finite epoch-major Jacobian with all columns required')
        result=np.einsum('ab,nbp->nap',self.matrix,x.reshape(-1,3,x.shape[1])).reshape(x.shape)
        if not np.all(np.isfinite(result)):raise ValueError('unrepresentable fixed-frame Jacobian')
        return result


@dataclass(frozen=True)
class Remainder:
    candidate_id:str
    configuration:str
    center:object
    lower:object
    upper:object
    training_radii:object
    future_bounds:object
    source_id:str
    scope:str

    def __post_init__(self):
        for value in (self.candidate_id,self.configuration,self.source_id):_identity(value)
        if self.scope!='global_parameter_box':raise ValueError('explicit global parameter-box scope required; samples are not bounds')
        center=_vector(self.center);lower=_vector(self.lower,len(center));upper=_vector(self.upper,len(center))
        if np.any(lower>upper) or np.any(center<lower) or np.any(center>upper):raise ValueError('center must belong to complete parameter box')
        radii=dict(self.training_radii)
        for key,value in radii.items():
            _identity(key)
            if value is not None and (not np.isfinite(value) or value<0.):raise ValueError('nonnegative global training bound required')
        future=None if self.future_bounds is None else _vector(self.future_bounds)
        if future is not None and np.any(future<0.):raise ValueError('nonnegative future-coordinate bounds required')
        for key,value in dict(center=center,lower=lower,upper=upper,training_radii=MappingProxyType(radii),future_bounds=future).items():
            object.__setattr__(self,key,value)


@dataclass(frozen=True,init=False)
class Family:
    training_times:object
    future_times:object
    specifications:object
    scales:object
    frame:Frame
    parameter_names:tuple
    assessment_id:str
    configuration:str
    _operators:object
    _forecasts:object

    def __init__(self,training_times,future_times,specifications,scales,*,frame,parameter_names,assessment_id):
        specifications=dict(specifications);scales=dict(scales);names=tuple(parameter_names)
        if not specifications or set(scales)!=set(specifications):raise ValueError('complete shared covariance/scale family required')
        if not isinstance(frame,Frame):raise ValueError('explicit frozen common coordinate frame required')
        _identity(assessment_id)
        if not names or len(set(names))!=len(names):raise ValueError('unique complete native parameter order required')
        for name in names:_identity(name)
        for name,scale in scales.items():
            _identity(name)
            if not isinstance(scale,ScaleBound) or scale.covariance_id!=name:raise ValueError('shared scale identity must match each covariance')
        if len({v.source_id for v in scales.values()})!=1:raise ValueError('one shared scale source required across family')
        operators={name:Innovations(training_times,spec) for name,spec in specifications.items()}
        forecasts={name:Forecast(operators[name],future_times) for name in specifications}
        first=next(iter(operators));times=operators[first].times;future=forecasts[first].times
        configuration=dict(assessment_id=assessment_id,parameter_names=names,frame_source=frame.source_id,
            frame_origin=frame.origin.tolist(),frame_matrix=frame.matrix.tolist(),future_times=future.tolist(),
            covariance_configurations={name:op.configuration for name,op in operators.items()},
            scales={name:dict(upper=None if v.upper is None else float(v.upper),failure_probability=v.failure_probability,
                source_id=v.source_id) for name,v in scales.items()})
        digest=hashlib.sha256(json.dumps(configuration,sort_keys=True,allow_nan=False).encode()).hexdigest()
        fields=dict(training_times=times,future_times=future,specifications=MappingProxyType(specifications),scales=MappingProxyType(scales),
            frame=frame,parameter_names=names,assessment_id=assessment_id,configuration=digest,
            _operators=MappingProxyType(operators),_forecasts=MappingProxyType(forecasts))
        for name,value in fields.items():object.__setattr__(self,name,value)

    def envelope(self,*,candidate_id,training_observations,center_parameters,training_prediction,future_prediction,
                 training_jacobian,future_jacobian,lower,upper,remainder=None):
        _identity(candidate_id);p=len(self.parameter_names);nt=len(self.training_times);nf=len(self.future_times)
        center=_vector(center_parameters,p);lower=_vector(lower,p);upper=_vector(upper,p)
        if np.any(lower>upper) or np.any(center<lower) or np.any(center>upper):raise ValueError('fitted center outside complete physical box')
        observed=self.frame.positions(training_observations);train=self.frame.positions(training_prediction)
        future=self.frame.positions(future_prediction)
        jt=self.frame.jacobian(training_jacobian);jp=self.frame.jacobian(future_jacobian)
        if observed.shape!=(nt,3) or train.shape!=(nt,3) or future.shape!=(nf,3) or jt.shape!=(3*nt,p) or jp.shape!=(3*nf,p):
            raise ValueError('prediction times, native parameter columns and observations disagree')
        if remainder is not None:
            if (not isinstance(remainder,Remainder) or remainder.candidate_id!=candidate_id
                    or remainder.configuration!=self.configuration or not np.array_equal(remainder.center,center)
                    or not np.array_equal(remainder.lower,lower) or not np.array_equal(remainder.upper,upper)
                    or (remainder.future_bounds is not None and remainder.future_bounds.shape!=(3*nf,))
                    or set(remainder.training_radii)-set(self.specifications)):
                raise ValueError('global remainder identity, center, box or configuration mismatch')
        y=(observed-train).ravel();alternatives={};degrees={};ranks={}
        ids=tuple(f'{time:.17g}-axis-{axis}' for time in self.future_times for axis in range(3))
        for name,operator in self._operators.items():
            forecast=self._forecasts[name];radius=None if remainder is None else remainder.training_radii.get(name)
            region=Region(operator.whiten(y),operator.whiten(jt),np.column_stack((lower-center,upper-center)),
                scale=self.scales[name],covariance_id=name,remainder_radius=radius,alpha=.02,design_is_fixed=False)
            mean=future.ravel()+forecast.mean(y);directions=jp-forecast.mean(jt)
            alternatives[name]=predict(region,mean,directions,conditional_variance=forecast.variance,
                training_response_norm=forecast.training_response_norm,
                future_remainder_bounds=None if remainder is None else remainder.future_bounds,alpha=.02,prediction_ids=ids)
            degrees[name]=getattr(region,'noise_degrees_of_freedom',None);ranks[name]=getattr(region,'rank',None)
        result=union(alternatives)
        result.update(candidate_id=candidate_id,configuration=self.configuration,assessment_id=self.assessment_id,
            frame_source_id=self.frame.source_id,parameter_count=p,parameter_names=self.parameter_names,
            training_rank_by_covariance=ranks,noise_degrees_of_freedom_by_covariance=degrees,
            global_bound_validity_established=False,observational_coverage_calibrated=False,
            native_integration_qualified=False,scientific_decision='abstain')
        return result
