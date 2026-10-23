# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F

import numpy as np
import pytest
from scipy.stats import norm

from lll.ilvis0_bounded_prediction import known_scale,ScaleBound


@pytest.mark.parametrize('count,alpha',[(3,.05),(1317,.02),(192240,.01),(6,1e-12)])
def test_tail_certificate_is_an_exact_upper_bound(count,alpha):
    from lll.ilvis0_gaussian_allowances import tail_certificate
    cert=tail_certificate(count,alpha)
    c=cert['critical'];x=F(c*c,2);term=total=F(1)
    for k in range(1,257):term*=x/k;total+=term
    assert F(cert['tail_upper'])==2*count/total<=F(alpha)
    assert 2*count*norm.sf(c)<=float(F(cert['tail_upper']))


def test_all_epochs_and_axes_share_one_probability_budget_and_outward_radius():
    from lll.ilvis0_gaussian_allowances import allowances
    scale=known_scale(.3,source_id='training-only',covariance_id='joint-law')
    variance=np.array([[.1,1.,2.],[4.,0.,.005]])
    result=allowances(variance,scale=scale,covariance_id='joint-law',alpha=.01,error_distribution='gaussian')
    assert result['supported'] and result['coordinate_count']==6
    assert result['scale_source_id']=='training-only'
    assert not result['independence_required'] and not result['observational_coverage_qualified']
    for v,r in zip(variance.ravel(),result['radius_m'].ravel()):
        assert F(float(r))**2>=F(.3)**2*result['critical']**2*F(float(v))
    assert not result['radius_m'].flags.writeable


def test_training_estimated_scale_probability_is_added_without_independence():
    from lll.ilvis0_gaussian_allowances import allowances
    scale=ScaleBound(2.,.01,'shared-training','joint-law','assumed-upper-bound')
    result=allowances(np.ones((439,3)),scale=scale,covariance_id='joint-law',alpha=.02,error_distribution='gaussian')
    exact=F(.01)+F(result['tail_certificate']['tail_upper'])
    assert F(result['nominal_failure_probability_bound'])>=exact
    assert result['nominal_failure_probability_bound']<=.03
    assert result['coordinate_count']==1317


@pytest.mark.parametrize('variance,scale,distribution,reason',[
    (None,known_scale(1.,source_id='x',covariance_id='law'),'gaussian','unsupported_variance_bounds'),
    (np.ones((2,3)),ScaleBound(None,.01,'x','law','unknown'),'gaussian','unsupported_scale_bound'),
    (np.ones((2,3)),known_scale(1.,source_id='x',covariance_id='law'),'unknown','unsupported_error_distribution'),
])
def test_missing_assumptions_remain_unsupported(variance,scale,distribution,reason):
    from lll.ilvis0_gaussian_allowances import allowances
    result=allowances(variance,scale=scale,covariance_id='law',alpha=.02,error_distribution=distribution)
    assert not result['supported'] and result['reason']==reason


@pytest.mark.parametrize('variance',[np.ones(3),np.empty((0,3)),np.ones((2,2)),np.array([[1.,-1.,0.]]),np.array([[np.inf,1.,1.]])])
def test_malformed_or_negative_variance_is_not_repaired(variance):
    from lll.ilvis0_gaussian_allowances import allowances
    with pytest.raises(ValueError):allowances(variance,scale=known_scale(1.,source_id='x',covariance_id='law'),
        covariance_id='law',alpha=.02,error_distribution='gaussian')


def test_scale_identity_and_total_budget_are_enforced():
    from lll.ilvis0_gaussian_allowances import allowances
    for covariance_id,scale in [('other',known_scale(1.,source_id='x',covariance_id='law')),
        ('law',ScaleBound(1.,.99,'x','law','assumed'))]:
        with pytest.raises(ValueError):allowances(np.ones((2,3)),scale=scale,covariance_id=covariance_id,
            alpha=.02,error_distribution='gaussian')


def test_declared_linear_rows_share_budget_with_future_coordinates():
    from lll.ilvis0_gaussian_allowances import linear_allowances
    ids=['training:mean:north','training:trend:east','future:438:north','future:438:east','future:438:up']
    variance=np.array([.1,0.,2.,4.,.5]);scale=ScaleBound(2.,.01,'training','law','assumed')
    result=linear_allowances(variance,row_ids=ids,projection_id='fixed-moments-and-future',
        scale=scale,covariance_id='law',alpha=.02,error_distribution='gaussian')
    assert result['supported'] and result['coordinate_count']==5 and result['row_ids']==ids
    assert result['projection_id']=='fixed-moments-and-future'
    assert result['tail_certificate']['coordinate_count']==5
    assert not result['independence_required'] and not result['observational_coverage_qualified']
    assert not result['radius_m'].flags.writeable and result['radius_m'][1]==0.
    for v,r in zip(variance,result['radius_m'],strict=True):
        assert F(float(r))**2>=4*result['critical']**2*F(float(v))
    assert F(result['nominal_failure_probability_bound'])>=F(.01)+F(result['tail_certificate']['tail_upper'])


@pytest.mark.parametrize('variance,ids,projection',[
    ([1.,2.],['same','same'],'p'),([1.,2.],['one'],'p'),
    ([1.],[''],'p'),([1.],['one'],''),([[1.,2.]],['one','two'],'p'),
    ([float('nan')],['one'],'p'),([-1.],['one'],'p')])
def test_linear_allowances_reject_unbound_or_malformed_rows(variance,ids,projection):
    from lll.ilvis0_gaussian_allowances import linear_allowances
    with pytest.raises(ValueError):linear_allowances(variance,row_ids=ids,projection_id=projection,
        scale=known_scale(1.,source_id='x',covariance_id='law'),covariance_id='law',alpha=.02,
        error_distribution='gaussian')
