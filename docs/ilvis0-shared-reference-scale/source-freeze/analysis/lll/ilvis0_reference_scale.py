# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared training scale upper bound under a declared fixed Gaussian reference.

An arbitrary deterministic mean produces a noncentral residual norm. Its
central lower quantile remains conservative; no Earth-candidate residual or
withheld observation is used. Covariance shape is supplied, not estimated here.
"""
from dataclasses import dataclass

import numpy as np
from scipy.stats import chi2

from .ilvis0_bounded_prediction import ScaleBound


@dataclass(frozen=True)
class Assessment:
    scale:ScaleBound
    reference_rank:int
    parameter_count:int
    observation_count:int
    residual_norm:object
    numerical_allowance:object
    mean_assumption:str='arbitrary_fixed_mean'

    def report(self):
        return dict(scale_upper=self.scale.upper,failure_probability=self.scale.failure_probability,
            source_id=self.scale.source_id,covariance_id=self.scale.covariance_id,reason=self.scale.reason,
            residual_degrees_of_freedom=self.scale.residual_degrees_of_freedom,reference_rank=self.reference_rank,
            parameter_count=self.parameter_count,observation_count=self.observation_count,residual_norm=self.residual_norm,
            numerical_allowance=self.numerical_allowance,mean_assumption=self.mean_assumption,
            covariance_shape_established=False,observational_coverage_qualified=False,scientific_decision='abstain')


def fixed_reference_scale(values,reference,*,alpha,source_id,covariance_id,design_is_fixed,
                          error_distribution,residual_numerical_allowance,rank_tolerance=1e-10):
    """Assess supplied whitened training data with one fixed reference projection.

    Gaussian errors and a deterministic, error-independent reference are required.
    The numerical allowance must upper-bound any residual-norm understatement;
    zero is an explicit exact-arithmetic assumption for generated controls.
    """
    y=np.asarray(values,float);x=np.asarray(reference,float)
    if (y.ndim!=1 or not len(y) or x.ndim!=2 or x.shape[0]!=len(y) or not x.shape[1]
            or not np.all(np.isfinite(y)) or not np.all(np.isfinite(x))):
        raise ValueError('aligned finite whitened values and complete fixed reference required')
    if (not np.isfinite(alpha) or not 0.<alpha<1. or not np.isfinite(rank_tolerance) or not 0.<rank_tolerance<1.
            or not isinstance(source_id,str) or not source_id or not isinstance(covariance_id,str) or not covariance_id
            or type(design_is_fixed) is not bool):
        raise ValueError('explicit valid fixed-reference configuration required')
    if residual_numerical_allowance is not None and (not np.isfinite(residual_numerical_allowance) or residual_numerical_allowance<0.):
        raise ValueError('finite nonnegative residual numerical allowance required')
    def result(reason,upper=None,rank=0,residual=None,degrees=None):
        scale=ScaleBound(upper,float(alpha),source_id,covariance_id,reason,degrees)
        return Assessment(scale,rank,x.shape[1],len(y),residual,residual_numerical_allowance)
    if not design_is_fixed:return result('data_dependent_reference')
    if error_distribution!='gaussian':return result('unsupported_error_distribution')
    if residual_numerical_allowance is None:return result('unsupported_numerical_allowance')
    u,s,_=np.linalg.svd(x,full_matrices=False)
    rank=int(np.sum(s>rank_tolerance*s[0])) if len(s) and s[0]>0. else 0
    degrees=len(y)-rank
    if degrees<=0:return result('no_residual_degrees_of_freedom',rank=rank,degrees=degrees)
    basis=u[:,:rank];residual=float(np.linalg.norm(y-basis@(basis.T@y)))
    denominator=float(np.sqrt(chi2.ppf(alpha,degrees)))
    if not np.isfinite(denominator) or denominator<=0.:
        return result('unrepresentable_reference_quantile',rank=rank,residual=residual,degrees=degrees)
    upper=(residual+residual_numerical_allowance)/denominator
    if not np.isfinite(upper):return result('unrepresentable_scale_bound',rank=rank,residual=residual,degrees=degrees)
    return result('fixed_reference_noncentral_dominance',upper=upper,rank=rank,residual=residual,degrees=degrees)
