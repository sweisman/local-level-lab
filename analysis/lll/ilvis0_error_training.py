# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small research controls: training-only REML selection and linear prediction.

No NASA fitting integration, automatic covariance family, active bounds, or
calibrated decisions. A supplied finite covariance list is scored using only
training observations. Prediction includes linear-mean estimation uncertainty,
conditional on each covariance; covariance-selection uncertainty is not integrated.
"""
from dataclasses import dataclass
import math

import numpy as np
from scipy.linalg import solve_triangular

from . import ilvis0_error_model as model

VERSION='ilvis0-error-training-controls-v1'


def readonly(values):
    a=np.array(values,dtype=float,copy=True);a.setflags(write=False)
    return a


def design(values,n,columns=None):
    a=np.array(values,dtype=float,copy=True)
    if (a.ndim!=2 or a.shape[0]!=n or not a.shape[1] or not np.all(np.isfinite(a))
            or (columns is not None and a.shape[1]!=columns)):
        raise ValueError('aligned finite linear design required')
    return a


@dataclass(frozen=True)
class Fit:
    times: object
    values: object
    design: object
    spec: model.Spec
    beta: object
    beta_covariance: object
    quadratic: float
    reml: float


def fit(training_times,training_values,training_design,spec):
    c=model.covariance(training_times,spec);n=len(c)
    y=model.residual(training_values,n);x=design(training_design,n);p=x.shape[1]
    if p>=n:raise ValueError('positive residual degrees of freedom required')
    lower=model.factor(c)
    wy=solve_triangular(lower,y,lower=True);wx=solve_triangular(lower,x,lower=True)
    scales=np.linalg.norm(wx,axis=0)
    if np.any(scales==0):raise ValueError('unidentifiable linear parameters')
    u,s,v=np.linalg.svd(wx/scales,full_matrices=False)
    if s[-1]<=1e-10*s[0]:raise ValueError('unidentifiable or ill-conditioned linear parameters')
    beta=(v.T@((u.T@wy)/s))/scales
    inverse_design=(v.T/s)/scales[:,None]
    beta_covariance=inverse_design@inverse_design.T
    errors=wy-wx@beta;quadratic=float(errors@errors)
    log_cov=2*np.sum(np.log(np.diag(lower)))
    log_information=2*np.sum(np.log(s))+2*np.sum(np.log(scales))
    reml=float(.5*((n-p)*math.log(2*math.pi)+log_cov+log_information+quadratic))
    if not math.isfinite(reml):raise ValueError('nonfinite restricted likelihood')
    return Fit(readonly(training_times),readonly(y),readonly(x),spec,readonly(beta),
        readonly(beta_covariance),quadratic,reml)


def select(training_times,training_values,training_design,candidates):
    """Fixed-list REML comparison; no holdout values accepted, no adaptive search.

    All candidates must share the same mean design and training epochs. Use this
    once on designated development data, not independently for each Earth model.
    Score gaps are descriptive, not confidence levels or calibrated selection tests.
    """
    choices=tuple(candidates)
    ids=[name for name,_ in choices]
    if not ids or any(not isinstance(name,str) or not name for name in ids) or len(set(ids))!=len(ids):
        raise ValueError('nonempty uniquely named covariance candidates required')
    fits={name:fit(training_times,training_values,training_design,spec) for name,spec in choices}
    ordered=sorted(ids,key=lambda name:fits[name].reml)
    winner=ordered[0];gap=None if len(ordered)==1 else fits[ordered[1]].reml-fits[winner].reml
    return dict(selected_id=winner,fit=fits[winner],fits=fits,
        scores=[dict(candidate_id=name,reml=fits[name].reml) for name in ids],
        score_margin=gap,selection_unique=gap is None or gap>1e-8,
        covariance_parameter_uncertainty_included=False)


def predict(fitted,future_times,future_design):
    """Universal linear prediction, retaining error/parameter correlation.

    Predict only later epochs. No future observations are accepted. A supplied
    covariance and unconstrained full-rank linear mean are assumed; nonlinear
    calibration, active bounds and estimated covariance need additional methods.
    """
    future=np.asarray(future_times,dtype=float)
    if future.ndim!=1 or not len(future) or np.any(future<=fitted.times[-1]):
        raise ValueError('future epochs must follow the training block')
    times=np.concatenate((fitted.times,future));c=model.covariance(times,fitted.spec)
    nt=len(fitted.values);npred=3*len(future);xp=design(future_design,npred,len(fitted.beta))
    lower=model.factor(c[:nt,:nt])
    wt=solve_triangular(lower,fitted.design,lower=True)
    cross=solve_triangular(lower,c[:nt,nt:],lower=True)
    wr=solve_triangular(lower,fitted.values-fitted.design@fitted.beta,lower=True)
    mean=xp@fitted.beta+cross.T@wr
    known=c[nt:,nt:]-cross.T@cross;known=(known+known.T)/2
    contrast=xp-cross.T@wt
    parameter=contrast@fitted.beta_covariance@contrast.T;parameter=(parameter+parameter.T)/2
    total=known+parameter;model.factor(total)
    return dict(mean=mean,covariance=total,known_parameter_covariance=known,
        parameter_covariance_contribution=parameter,parameter_uncertainty_included=True,
        covariance_parameter_uncertainty_included=False,active_bounds_supported=False,
        scientific_decision='abstain')


def predict_choices(selection,future_times,future_design):
    """Return covariance-choice sensitivity separately; no averaging or coverage claim."""
    return {name:predict(fitted,future_times,future_design) for name,fitted in selection['fits'].items()}
