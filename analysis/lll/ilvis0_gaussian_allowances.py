# SPDX-License-Identifier: AGPL-3.0-or-later
"""Simultaneous coordinate allowances under supplied Gaussian error bounds.

No independence is required between coordinates, epochs or a training-derived
scale bound. The supplied marginal variances and scale coverage still need
justification; this module does not establish an aircraft observation law.
"""
from fractions import Fraction as F


def tail_certificate(count,alpha):
    """Certify 2*M*exp(-c^2/2) <= alpha using only rational inequalities.

For x>=0, exp(x) >= sum(x^k/k!, k=0..256). Thus its reciprocal is an
upper bound on exp(-x). The finite integer grid avoids a rounded quantile.
"""
    try:alpha=F(alpha)
    except (ValueError,OverflowError,TypeError):raise ValueError('finite tail probability required') from None
    if type(count) is not int or not 1<=count<=10000000 or not 0<alpha<1:
        raise ValueError('positive finite coordinate count and probability required')
    for critical in range(1,65):
        x=F(critical*critical,2);term=total=F(1)
        for k in range(1,257):term*=x/k;total+=term
        upper=2*count/total
        if upper<=alpha:
            return dict(critical=critical,coordinate_count=count,polynomial_terms=256,
                alpha=str(alpha),tail_upper=str(upper),proof='gaussian_chernoff_positive_exponential_series')
    raise ValueError('tail certificate exceeds its finite supported grid')


def allowances(variance_upper_m2,*,scale,covariance_id,alpha,error_distribution):
    """Return epoch-major metre radii for training AND future coordinates.

Pass the complete declared epoch set once, then select its training/future rows.
Marginal variance upper bounds must describe one common joint error law and
fixed integration origin. The method permits arbitrary correlation but does
not exploit it for sharper intervals. No observed values are accepted.
"""
    return _allowances(variance_upper_m2,scale=scale,covariance_id=covariance_id,alpha=alpha,
        error_distribution=error_distribution,linear=False)


def linear_allowances(variance_upper_m2,*,row_ids,projection_id,scale,covariance_id,alpha,error_distribution):
    """One simultaneous metre-error family of fixed summaries and future rows.

    Each supplied variance belongs to one uniquely named scalar row. Include
    every training summary and future coordinate before taking subsets; the
    shared scale failure budget is added once, without an independence claim.
    Binding the row projection does not itself verify its variance certificate.
    """
    if (not isinstance(row_ids,(tuple,list)) or not row_ids
            or any(not isinstance(v,str) or not v for v in row_ids)
            or len(set(row_ids))!=len(row_ids) or not isinstance(projection_id,str) or not projection_id):
        raise ValueError('unique nonempty fixed row identities and projection identity required')
    result=_allowances(variance_upper_m2,scale=scale,covariance_id=covariance_id,alpha=alpha,
        error_distribution=error_distribution,linear=True,row_count=len(row_ids))
    return dict(result,row_ids=list(row_ids),projection_id=projection_id)


def _allowances(variance_upper_m2,*,scale,covariance_id,alpha,error_distribution,linear,row_count=None):
    import numpy as np
    from lll.ilvis0_bounded_prediction import ScaleBound
    from lll.ilvis0_exact_scale import sqrt_upper
    from lll.ilvis0_saved_prediction_audit import endpoint
    if not isinstance(scale,ScaleBound) or scale.covariance_id!=covariance_id:
        raise ValueError('shared scale and covariance identity must match')
    try:alpha=F(alpha)
    except (ValueError,OverflowError,TypeError):raise ValueError('finite tail probability required') from None
    if not 0<alpha<1 or F(scale.failure_probability)+alpha>=1:
        raise ValueError('positive coordinate budget and combined failure budget below one required')
    base=dict(covariance_id=covariance_id,scale_source_id=scale.source_id,independence_required=False,
        observational_coverage_qualified=False,variance_bounds_established=False,
        scale_bound_validity_established=False,whole_program_roundoff_qualified=False,scientific_decision='abstain')
    def unsupported(reason):return dict(base,supported=False,reason=reason)
    if error_distribution!='gaussian':return unsupported('unsupported_error_distribution')
    if scale.upper is None:return unsupported('unsupported_scale_bound')
    if variance_upper_m2 is None:return unsupported('unsupported_variance_bounds')
    variance=np.array(variance_upper_m2,float,copy=True)
    shape_ok=(variance.ndim==1 and len(variance)==row_count if linear
        else variance.ndim==2 and variance.shape[1]==3 and len(variance)>0)
    if not shape_ok or not np.all(np.isfinite(variance)) or np.any(variance<0.):
        raise ValueError('finite nonnegative complete linear-row variances required' if linear
            else 'finite nonnegative epoch-by-three marginal variance bounds required')
    cert=tail_certificate(int(variance.size),alpha);critical=cert['critical'];radii=[]
    for value in variance.ravel():
        sd=sqrt_upper(F(float(value)))
        radii.append(endpoint(F(float(scale.upper))*critical*F(sd),True))
    result=np.array(radii).reshape(variance.shape);result.setflags(write=False)
    total=F(scale.failure_probability)+F(cert['tail_upper'])
    return dict(base,supported=True,radius_m=result,coordinate_count=int(variance.size),critical=critical,
        tail_certificate=cert,nominal_failure_probability_bound=endpoint(total,True),
        scale_failure_probability=scale.failure_probability,coordinate_failure_budget=str(alpha),
        radius_arithmetic='exact_rational_product_and_outward_binary64_sqrt_and_endpoint')
