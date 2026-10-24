# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
import math

import numpy as np
import pytest


def library():
    assert importlib.util.find_spec('lll.airquantumgrav_error_policy') is not None, 'versioned receiver error policy is missing'
    return __import__('lll.airquantumgrav_error_policy',fromlist=['build'])


def rows():
    return [dict(time_s=100.+i*.5,gps_week=2200,latitude_deg=0.,longitude_deg=10.,height_m=0.,
        position_variance_m2=[4.,9.,16.],position_cross_covariance_m2=[1.,.5,-.25]) for i in range(4)]


@pytest.mark.parametrize('policy',['reported-short-v1','reported-persistent-v1'])
def test_policy_preserves_reported_cross_axes_and_upward_height(policy):
    module=library();raw=rows();before=copy.deepcopy(raw);model=module.build(raw,policy_id=policy)
    scale=1. if policy=='reported-short-v1' else 3.
    expected=np.array([[4.0025,1.,.5],[1.,9.0025,-.25],[.5,-.25,16.0225]])*scale**2
    np.testing.assert_allclose(model.marginal_neu[0],expected,atol=1e-14,rtol=0)
    dense=model.dense(maximum_epochs=4)
    metric=np.diag([6335439.3272928195,6378137.,1.])
    np.testing.assert_allclose(metric@dense[:3,:3]@metric,expected,atol=1e-12,rtol=1e-14)
    assert dense[0,2]>0 and dense[1,2]<0
    assert raw==before
    assert not model.times.flags.writeable and not model.transforms.flags.writeable
    assert model.descriptor['receiver_covariance_calibrated'] is False


@pytest.mark.parametrize('policy,tau,scale',[('reported-short-v1',1.,1.),('reported-persistent-v1',60.,3.)])
def test_time_correlation_has_the_declared_share_and_actual_elapsed_time(policy,tau,scale):
    raw=rows()[:2];raw[1]['time_s']=103.25
    for row in raw:row['position_cross_covariance_m2']=[0.,0.,0.]
    model=library().build(raw,policy_id=policy);dense=model.dense(maximum_epochs=2)
    metric=np.diag([6335439.3272928195,6378137.,1.])
    want=np.diag([4.0025,9.0025,16.0225])*scale**2*.95*math.exp(-3.25/tau)
    np.testing.assert_allclose(metric@dense[:3,3:6]@metric,want,atol=1e-12,rtol=1e-14)


@pytest.mark.parametrize('policy',['reported-short-v1','reported-persistent-v1'])
def test_structured_whitening_matches_dense_for_residuals_and_all_27_columns(policy):
    raw=rows();raw[1]['position_variance_m2']=[5.,8.,17.];raw[2]['latitude_deg']=-55.;raw[3]['height_m']=600.
    model=library().build(raw,policy_id=policy);dense=model.dense(maximum_epochs=4);operator=model.operator()
    values=np.arange(12*27,dtype=float).reshape(12,27)/100
    values*=np.tile([1e-7,1e-7,1.],4)[:,None];values[:,3]=0.
    want=np.linalg.solve(np.linalg.cholesky(dense),values)
    np.testing.assert_allclose(operator.whiten(values),want,rtol=5e-12,atol=2e-7)
    np.testing.assert_allclose(operator.unwhiten(operator.whiten(values)),values,rtol=1e-12,atol=1e-11)
    assert operator.whiten(values).shape==(12,27)
    np.testing.assert_array_equal(operator.whiten(values)[:,3],np.zeros(12))


def test_outcome_and_gyro_metadata_cannot_change_weights_or_binding():
    raw=rows();a=library().build(raw,policy_id='reported-short-v1')
    changed=copy.deepcopy(raw)
    for row in changed:row.update(preferred_model='disc',gyro_mean=1000.,fit_cost=-1.)
    b=library().build(changed,policy_id='reported-short-v1')
    np.testing.assert_array_equal(a.transforms,b.transforms)
    assert a.configuration==b.configuration and a.source_sha256==b.source_sha256


@pytest.mark.parametrize('fault',['negative_covariance','singular_covariance','cross_covariance','time','week','nonfinite','pole','shape','policy'])
def test_unsupported_reported_data_are_rejected_without_repair(fault):
    raw=rows();policy='reported-short-v1'
    if fault=='negative_covariance':raw[0]['position_variance_m2'][0]=-.001
    elif fault=='singular_covariance':raw[0]['position_variance_m2'][0]=0.;raw[0]['position_cross_covariance_m2']=[0.,0.,0.]
    elif fault=='cross_covariance':raw[0]['position_cross_covariance_m2'][0]=100.
    elif fault=='time':raw[1]['time_s']=raw[0]['time_s']
    elif fault=='week':raw[1]['gps_week']+=1
    elif fault=='nonfinite':raw[0]['height_m']=np.nan
    elif fault=='pole':raw[0]['latitude_deg']=90.
    elif fault=='shape':raw[0]['position_cross_covariance_m2']=[0.]
    else:policy='unfrozen'
    with pytest.raises(ValueError):library().build(raw,policy_id=policy)


@pytest.mark.parametrize('cap',[None,0,3,2049])
def test_dense_allocation_requires_a_sufficient_finite_explicit_cap(cap):
    model=library().build(rows(),policy_id='reported-short-v1')
    with pytest.raises(ValueError):model.dense(maximum_epochs=cap)


def test_reported_covariance_quality_check_preserves_the_original_matrix():
    module=library();raw=rows()[0];before=copy.deepcopy(raw)
    assert hasattr(module,'reported_covariance'), 'shared covariance quality check is missing'
    result=module.reported_covariance(raw)
    np.testing.assert_array_equal(result,[[4.,1.,.5],[1.,9.,-.25],[.5,-.25,16.]])
    assert raw==before
    raw['position_cross_covariance_m2'][0]=100.
    with pytest.raises(ValueError):module.reported_covariance(raw)
