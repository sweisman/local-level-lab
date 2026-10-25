# SPDX-License-Identifier: AGPL-3.0-or-later
"""Model-based outer prediction envelopes with bounded nuisance directions.

Inputs are training quantities, declared covariance alternatives and supported
deterministic remainder allowances. This is not an observed-data calibration or
an Earth-model decision. No prediction observations enter these calculations.
"""
from dataclasses import dataclass

import numpy as np
from scipy.stats import chi2,norm


def _alpha(value):
    if not np.isfinite(value) or not 0.<value<1.:raise ValueError('failure allowance must lie strictly between zero and one')
    return float(value)


def _radius(value):
    if value is not None and (not np.isfinite(value) or value<0.):raise ValueError('nonnegative finite remainder radius required')
    return value


def _data(values,design):
    y=np.asarray(values,float);x=np.asarray(design,float)
    if (y.ndim!=1 or not len(y) or x.ndim!=2 or x.shape[0]!=len(y) or not x.shape[1]
            or not np.all(np.isfinite(y)) or not np.all(np.isfinite(x))):
        raise ValueError('finite aligned whitened training values and all design columns required')
    return y,x


def _bounds(values,columns):
    bounds=np.array(values,float,copy=True)
    if bounds.shape!=(columns,2) or not np.all(np.isfinite(bounds)) or np.any(bounds[:,1]<bounds[:,0]):
        raise ValueError('finite ordered bound for every original parameter required')
    bounds.setflags(write=False);return bounds


def _decompose(x,tolerance):
    if not np.isfinite(tolerance) or not 0.<tolerance<1.:raise ValueError('explicit relative numerical rank tolerance required')
    u,s,vt=np.linalg.svd(x,full_matrices=False)
    rank=int(np.sum(s>tolerance*s[0])) if len(s) and s[0]>0. else 0
    ur=u[:,:rank];sr=s[:rank];basis=vt[:rank].T
    retained=(ur*sr)@basis.T
    return ur,sr,basis,rank,float(np.linalg.norm(x-retained,ord=2))


@dataclass(frozen=True)
class ScaleBound:
    upper: object
    failure_probability: float
    source_id: str
    covariance_id: str
    reason: str
    residual_degrees_of_freedom: object=None
    declared_known_scale: bool=False

    def __post_init__(self):
        if self.upper is not None and (not np.isfinite(self.upper) or self.upper<0.):raise ValueError('finite nonnegative scale upper bound required')
        if not 0.<=self.failure_probability<1.:raise ValueError('invalid scale failure allowance')
        if not isinstance(self.source_id,str) or not self.source_id or not isinstance(self.covariance_id,str) or not self.covariance_id:
            raise ValueError('shared calibration source and covariance identity required')


def known_scale(value,*,source_id,covariance_id):
    """Explicit known-scale assumption for software controls or a justified input."""
    return ScaleBound(value,0.,source_id,covariance_id,'declared_known_scale',declared_known_scale=True)


def shared_scale_bound(values,design,*,alpha,source_id,covariance_id,remainder_radius,
                       coefficient_bounds=None,rank_tolerance=1e-10,design_is_fixed=False):
    """One shared training/calibration reference; never separately per candidate.

    If ||whitened mean remainder|| <= B, the residual projection's true noise
    norm is at most ||observed projected residual||+B. Invert a lower chi-square
    quantile with its residual degrees of freedom. No independence from later
    training estimates is needed for the subsequent union-bound accounting.
    """
    alpha=_alpha(alpha);_radius(remainder_radius);y,x=_data(values,design)
    if remainder_radius is None:return ScaleBound(None,alpha,source_id,covariance_id,'unsupported_remainder')
    if design_is_fixed is not True:
        return ScaleBound(None,alpha,source_id,covariance_id,'data_dependent_scale_reference')
    u,s,basis,rank,discarded=_decompose(x,rank_tolerance);degrees=len(y)-rank
    if degrees<=0:return ScaleBound(None,alpha,source_id,covariance_id,'no_residual_degrees_of_freedom',degrees)
    extra=0.
    if rank<x.shape[1] and discarded>0. and coefficient_bounds is None:
        return ScaleBound(None,alpha,source_id,covariance_id,'unbounded_discarded_reference_response',degrees)
    if coefficient_bounds is not None:
        bounds=_bounds(coefficient_bounds,x.shape[1])
        extra=discarded*float(np.linalg.norm(np.max(abs(bounds),axis=1)))
    residual=y-u@(u.T@y)
    denominator=float(np.sqrt(chi2.ppf(alpha,degrees)))
    upper=(float(np.linalg.norm(residual))+remainder_radius+extra)/denominator
    return ScaleBound(upper,alpha,source_id,covariance_id,'shared_training_calibration',degrees)


class Region:
    def __init__(self,values,design,bounds,*,scale,covariance_id,remainder_radius,alpha,
                 rank_tolerance=1e-10,design_is_fixed=False):
        y,x=_data(values,design);self.bounds=_bounds(bounds,x.shape[1]);self.parameter_count=x.shape[1]
        if not isinstance(scale,ScaleBound) or scale.covariance_id!=covariance_id:
            raise ValueError('shared scale must match the declared covariance alternative')
        self.scale=scale;self.covariance_id=covariance_id;self.alpha=_alpha(alpha)
        if type(design_is_fixed) is not bool:raise ValueError('explicit boolean design-origin flag required')
        self.design_is_fixed=design_is_fixed
        self.original_remainder_radius=_radius(remainder_radius)
        self.supported=scale.upper is not None and remainder_radius is not None
        self.reason='supported' if self.supported else 'unsupported_scale_or_remainder'
        if not self.supported:return
        u,s,basis,rank,discarded=_decompose(x,rank_tolerance)
        self.rank=rank;self.basis=basis;self.singular=s
        self.discarded_response_bound=discarded*float(np.linalg.norm(np.max(abs(self.bounds),axis=1)))
        self.center=basis@((u.T@y)/s) if rank else np.zeros(x.shape[1])
        # A Jacobian learned from these observations has a data-dependent
        # projection. Its projected noise is bounded by the full noise norm;
        # it cannot use the fixed-design rank-degree chi-square shortcut.
        self.noise_degrees_of_freedom=(rank if design_is_fixed else len(y)) if rank else 0
        noise=scale.upper*np.sqrt(chi2.ppf(1.-self.alpha,self.noise_degrees_of_freedom)) if rank else 0.
        self.radius=float(noise+remainder_radius+self.discarded_response_bound)
        if not np.isfinite(self.radius) or not np.all(np.isfinite(self.center)):raise ValueError('unrepresentable training region')
        for value in (self.basis,self.singular,self.center):value.setflags(write=False)

    def support(self,directions):
        l=np.asarray(directions,float)
        if l.ndim!=2 or l.shape[1]!=self.parameter_count or not len(l) or not np.all(np.isfinite(l)):
            raise ValueError('finite prediction directions for every original parameter required')
        if not self.supported:return dict(supported=False,reason=self.reason)
        lo,hi=self.bounds.T
        box_low=np.minimum(l*lo,l*hi).sum(axis=1);box_high=np.maximum(l*lo,l*hi).sum(axis=1)
        coefficients=l@self.basis;null=l-coefficients@self.basis.T
        center=l@self.center
        half=self.radius*np.linalg.norm(coefficients/self.singular,axis=1) if self.rank else np.zeros(len(l))
        lower=np.maximum(box_low,center-half+np.minimum(null*lo,null*hi).sum(axis=1))
        upper=np.minimum(box_high,center+half+np.maximum(null*lo,null*hi).sum(axis=1))
        if not np.all(np.isfinite(lower)) or not np.all(np.isfinite(upper)):raise ValueError('unrepresentable prediction support')
        return dict(supported=True,lower=lower,upper=upper,empty=bool(np.any(lower>upper)),
            parameter_count=self.parameter_count,training_rank=self.rank,
            joint_parameter_feasibility_established=False,scientific_decision='abstain')


def predict(region,nominal_mean,contrasts,*,conditional_variance,training_response_norm,
            future_remainder_bounds,alpha,prediction_ids):
    """Simultaneous coordinate envelope; no prediction observations accepted.

    nominal_mean = future intercept + conditional training-error mean.
    contrasts = future design - conditional response to training design.
    Gaussian marginal bounds use Bonferroni, retaining arbitrary correlation.
    Training remainder acts through the supplied whitened-response row norms.
    """
    alpha=_alpha(alpha);mean=np.asarray(nominal_mean,float);variance=np.asarray(conditional_variance,float)
    response=np.asarray(training_response_norm,float);ids=tuple(prediction_ids)
    if (mean.ndim!=1 or not len(mean) or not np.all(np.isfinite(mean)) or len(ids)!=len(mean)
            or len(set(ids))!=len(ids) or variance.shape!=mean.shape or response.shape!=mean.shape
            or not np.all(np.isfinite(variance)) or np.any(variance<0.)
            or not np.all(np.isfinite(response)) or np.any(response<0.)):
        raise ValueError('aligned finite prediction geometry and unique coordinate identities required')
    if future_remainder_bounds is None:return dict(supported=False,reason='unsupported_future_remainder')
    remainder=np.asarray(future_remainder_bounds,float)
    if remainder.shape!=mean.shape or not np.all(np.isfinite(remainder)) or np.any(remainder<0.):
        raise ValueError('nonnegative finite future mean-error allowance per coordinate required')
    support=region.support(contrasts)
    if not support['supported'] or support['empty']:
        return dict(supported=False,reason=support.get('reason','empty_outer_parameter_support'))
    total=alpha+region.alpha+region.scale.failure_probability
    if total>=1.:raise ValueError('total error allowance must be below one')
    critical=float(norm.isf(alpha/(2.*len(mean))))
    noise=region.scale.upper*critical*np.sqrt(variance)
    bias=remainder+response*region.original_remainder_radius
    lower=mean+support['lower']-noise-bias;upper=mean+support['upper']+noise+bias
    if not np.all(np.isfinite(lower)) or not np.all(np.isfinite(upper)):raise ValueError('unrepresentable prediction envelope')
    return dict(supported=True,lower=lower,upper=upper,prediction_ids=ids,
        covariance_id=region.covariance_id,scale_source_id=region.scale.source_id,
        nominal_failure_probability_bound=total,gaussian_critical_value=critical,
        conditional_noise_half_width=noise,deterministic_remainder_half_width=bias,
        parameter_count=region.parameter_count,training_rank=region.rank,
        observational_coverage_calibrated=False,global_remainder_assumption_verified=False,
        scientific_decision='abstain')


def union(alternatives):
    """Cover the stated finite family; do not discard unsupported alternatives."""
    if not alternatives:raise ValueError('nonempty predeclared covariance family required')
    unsupported=[name for name,value in alternatives.items() if not value.get('supported')]
    if unsupported:return dict(supported=False,reason='unsupported_covariance_alternatives',unsupported_ids=sorted(unsupported))
    rows=list(alternatives.values());reference=rows[0]
    for name,row in alternatives.items():
        if (name!=row['covariance_id'] or tuple(row['prediction_ids'])!=tuple(reference['prediction_ids'])
                or row['scale_source_id']!=reference['scale_source_id']):
            raise ValueError('same prediction coordinates and shared calibration source required across family')
    return dict(supported=True,lower=np.minimum.reduce([r['lower'] for r in rows]),
        upper=np.maximum.reduce([r['upper'] for r in rows]),prediction_ids=reference['prediction_ids'],
        covariance_ids=sorted(alternatives),scale_source_id=reference['scale_source_id'],
        nominal_failure_probability_bound=max(r['nominal_failure_probability_bound'] for r in rows),
        outside_declared_family_coverage_established=False,observational_coverage_calibrated=False,
        scientific_decision='abstain')
