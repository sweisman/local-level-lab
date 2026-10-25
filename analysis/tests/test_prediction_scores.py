# SPDX-License-Identifier: AGPL-3.0-or-later
import math
import pytest


def test_prediction_score_uses_entire_block_and_every_coordinate():
    from lll.prediction_scores import maximum_score
    r=maximum_score([[1.,-2.,3.],[4.,-10.,1.]],[[1.,1.,1.],[2.,2.,2.]],maximum_epochs=40)
    assert r['maximum_standardized_error']==5.
    assert r['worst_epoch_index']==1 and r['worst_coordinate']=='longitude'
    assert r['maximum_by_coordinate']==dict(latitude=2.,longitude=5.,height=3.)
    assert r['confidence_calibrated'] is False and r['calibration_uncertainty_included'] is False


def test_prediction_score_is_invariant_to_consistent_coordinate_units():
    from lll.prediction_scores import maximum_score
    e=[[1e-7,2e-7,1.],[2e-7,-1e-7,2.]];s=[[1e-8,2e-8,.1]]*2
    a=maximum_score(e,s,maximum_epochs=40)
    factors=[180/math.pi,180/math.pi,100.]
    b=maximum_score([[x*f for x,f in zip(v,factors)] for v in e],
        [[x*f for x,f in zip(v,factors)] for v in s],maximum_epochs=40)
    assert a['maximum_standardized_error']==pytest.approx(b['maximum_standardized_error'])


@pytest.mark.parametrize('sigma',[[[0.,1.,1.]],[[-1.,1.,1.]],[[math.nan,1.,1.]],[[True,1.,1.]]])
def test_prediction_score_rejects_invalid_standard_deviations_without_floor(sigma):
    from lll.prediction_scores import maximum_score
    with pytest.raises(ValueError):maximum_score([[1.,2.,3.]],sigma,maximum_epochs=40)


@pytest.mark.parametrize('patch',[{'errors':[]},{'errors':[[1.,2.]]},
    {'standard_deviations':[[1.,1.,1.]]*2},{'maximum_epochs':0}])
def test_prediction_score_rejects_incomplete_or_unbounded_input(patch):
    from lll.prediction_scores import maximum_score
    args=dict(errors=[[1.,2.,3.]],standard_deviations=[[1.,1.,1.]],maximum_epochs=40);args.update(patch)
    with pytest.raises(ValueError):maximum_score(**args)


def test_coordinate_score_wraps_longitude_and_preserves_radian_height_covariance_units():
    from lll.prediction_scores import coordinate_score
    true=[[.5,math.pi-1e-7,100.]];predicted=[[.5+1e-7,-math.pi+1e-7,100.2]]
    covariance=[[[1e-16,0.,0.],[0.,1e-16,0.],[0.,0.,.01]]]
    r=coordinate_score(predicted,true,covariance,maximum_epochs=40)
    assert r['maximum_standardized_error']==pytest.approx(20.,rel=1e-7)
    assert r['standardized_errors'][0][2]==pytest.approx(2.)
    assert r['coordinate_units']==['radian','radian','metre']


@pytest.mark.parametrize('covariance',[
    [[[1.,2.,0.],[2.,1.,0.],[0.,0.,1.]]],
    [[[1.,.2,0.],[0.,1.,0.],[0.,0.,1.]]],
    [[[1.,0.,0.],[0.,1.,0.],[0.,0.,0.]]]])
def test_coordinate_score_rejects_invalid_covariance_without_repair(covariance):
    from lll.prediction_scores import coordinate_score
    with pytest.raises(ValueError):coordinate_score([[.1,.2,1.]],[[.1,.2,1.]],covariance,maximum_epochs=40)
