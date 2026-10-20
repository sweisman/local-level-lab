# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from scipy.stats import chi2


def assess(y,x,**kwargs):
    from lll.ilvis0_reference_scale import fixed_reference_scale
    options=dict(alpha=.01,source_id='shared-training',covariance_id='fixed-shape',
        design_is_fixed=True,error_distribution='gaussian',residual_numerical_allowance=0.)
    options.update(kwargs)
    return fixed_reference_scale(y,x,**options)


def test_scale_bound_uses_residual_dimension_and_lower_quantile():
    x=np.ones((6,1));y=np.array([1.,2.,4.,3.,6.,8.]);result=assess(y,x)
    expected=np.linalg.norm(y-y.mean())/np.sqrt(chi2.ppf(.01,5))
    assert result.scale.upper==pytest.approx(expected)
    assert result.reference_rank==1 and result.scale.residual_degrees_of_freedom==5
    assert result.mean_assumption=='arbitrary_fixed_mean'
    assert result.scale.declared_known_scale is False
    assert result.report()['observational_coverage_qualified'] is False


def test_large_reference_mean_does_not_require_a_polynomial_remainder_bound():
    y=np.linspace(-100.,100.,40)**3;x=np.ones((40,27))
    result=assess(y,x)
    assert result.scale.upper>1.
    assert result.parameter_count==27 and result.reference_rank==1
    assert result.scale.reason=='fixed_reference_noncentral_dominance'


def test_zero_rank_reference_retains_all_noise_dimensions():
    result=assess(np.arange(8.),np.zeros((8,27)))
    assert result.reference_rank==0
    assert result.scale.residual_degrees_of_freedom==8
    assert result.scale.upper==pytest.approx(np.linalg.norm(np.arange(8.))/np.sqrt(chi2.ppf(.01,8)))


def test_declared_numerical_allowance_widens_scale_bound():
    y=np.arange(8.);x=np.ones((8,1));a=assess(y,x);b=assess(y,x,residual_numerical_allowance=.5)
    assert b.scale.upper-a.scale.upper==pytest.approx(.5/np.sqrt(chi2.ppf(.01,7)))


@pytest.mark.parametrize('kwargs,reason',[
    ({'design_is_fixed':False},'data_dependent_reference'),
    ({'error_distribution':'unknown'},'unsupported_error_distribution'),
    ({'residual_numerical_allowance':None},'unsupported_numerical_allowance')])
def test_unsupported_assumptions_return_no_scale_bound(kwargs,reason):
    result=assess(np.arange(8.),np.ones((8,1)),**kwargs)
    assert result.scale.upper is None and result.scale.reason==reason


def test_full_rank_reference_cannot_estimate_a_scale():
    result=assess(np.arange(4.),np.eye(4))
    assert result.scale.upper is None
    assert result.scale.reason=='no_residual_degrees_of_freedom'


@pytest.mark.parametrize('kwargs',[{'alpha':0.},{'residual_numerical_allowance':-.1},{'rank_tolerance':0.},{'source_id':''}])
def test_invalid_configuration_is_rejected(kwargs):
    with pytest.raises(ValueError):assess(np.arange(8.),np.ones((8,1)),**kwargs)


@pytest.mark.parametrize('degrees',[1,3,27,96])
def test_noncentral_reference_lower_tail_never_exceeds_central_quantile(degrees):
    from scipy.stats import ncx2
    threshold=chi2.ppf(.01,degrees)
    for noncentrality in (0.,.1,1.,10.,100.):
        assert ncx2.cdf(threshold,degrees,noncentrality)<=.01+1e-14
