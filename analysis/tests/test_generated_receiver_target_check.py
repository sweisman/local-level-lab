"""Score later generated receiver data without changing the earlier fit."""

import math

import numpy as np
import pytest


def case():
    from lll.airquantumgrav_weighted_controls import fixture_rows
    from lll.airquantumgrav_error_policy import build
    from lll.measurement_noise import receiver_errors
    times=np.array([.5,1.5,2.5,3.5])
    truth=np.array([[.96,-.70,1000.],[.96001,-.69998,1001.],
                    [.96002,-.69996,1002.],[.96003,-.69994,1003.]])
    rows=fixture_rows(truth[:2],times[:2]);working=build(rows,policy_id='reported-short-v1')
    transforms=np.concatenate((working.transforms,
                               np.repeat(working.transforms[-1][None],2,axis=0)))
    noise=receiver_errors(times,working.spec,seed=123,
                          maximum_epochs=4,transforms=transforms)
    measured=[dict(row,latitude_deg=row['latitude_deg']+math.degrees(e[0]),
                   longitude_deg=row['longitude_deg']+math.degrees(e[1]),
                   height_m=row['height_m']+e[2])
              for row,e in zip(rows,noise[:2],strict=True)]
    binding=dict(noise=dict(settings=dict(seed=123),
                            receiver_policy=dict(policy_id='reported-short-v1'),
                            receiver_covariance_source_sha256=working.source_sha256))
    later=truth[2:]+noise[2:]
    diagnostic=dict(prediction_target='receiver_measurement',
                    later_observations_used=False,
                    fixed_parameters=dict(mean=later.tolist()))
    lower=later-np.array([1e-5,1e-5,10.]);upper=later+np.array([1e-5,1e-5,10.])
    bound=dict(prediction_target='receiver_measurement',
               later_observations_used=False,training_epochs=2,prediction_epochs=2,
               lower=lower.ravel().tolist(),upper=upper.ravel().tolist())
    return times,truth,measured,binding,diagnostic,bound


def test_later_receiver_scoring_reproduces_earlier_prefix_and_containment():
    from lll.generated_receiver_target_check import score
    result=score(*case())
    assert result['training_prefix_reproduced'] is True
    assert result['all_later_coordinates_contained'] is True
    assert result['point_horizontal_rms_m'] == pytest.approx(0.,abs=1e-9)
    assert result['mean_full_width_horizontal_m'] > 0
    assert result['empirical_coverage_calibrated'] is False


def test_receiver_scoring_rejects_changed_training_source_and_later_fit_use():
    from lll.generated_receiver_target_check import score
    values=list(case())
    values[2][0]['height_m']+=.01
    with pytest.raises(ValueError,match='earlier receiver'):
        score(*values)
    values=list(case())
    values[4]['later_observations_used']=True
    with pytest.raises(ValueError,match='earlier-only'):
        score(*values)


def test_wide_but_containing_receiver_envelope_is_reported_as_wide():
    from lll.generated_receiver_target_check import score
    values=list(case())
    bound=values[5]
    bound['lower']=(np.array(bound['lower']).reshape(2,3)-
                    np.array([.01,.01,1000.])).ravel().tolist()
    bound['upper']=(np.array(bound['upper']).reshape(2,3)+
                    np.array([.01,.01,1000.])).ravel().tolist()
    narrow=score(*case())
    wide=score(*values)
    assert wide['all_later_coordinates_contained'] is True
    assert wide['mean_full_width_horizontal_m'] > 1000*narrow['mean_full_width_horizontal_m']
