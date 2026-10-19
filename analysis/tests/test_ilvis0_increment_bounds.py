# SPDX-License-Identifier: AGPL-3.0-or-later
import itertools

import numpy as np
import pytest

from lll.ilvis0_increment_bounds import magnitude_bounds


def calculate(counts,periods,uncertainty=1.):
    return magnitude_bounds(np.array(counts,dtype=np.int32),np.array(periods,float),
        scale_mps_per_count=1.,count_uncertainty=uncertainty,period_hypothesis='declared test period')


def test_exact_counts_and_periods_recover_increment_magnitude():
    result=calculate([[3,4,0],[0,0,-5]],[[1,1],[1,1]],0.)
    np.testing.assert_array_equal(result['packet_force_lower_mps2'],[5.,5.])
    np.testing.assert_array_equal(result['packet_force_upper_mps2'],[5.,5.])
    assert result['time_weighted_magnitude_lower_mps2']==5.
    assert result['time_weighted_magnitude_upper_mps2']==5.


def test_box_extrema_include_sign_crossing_and_period_uncertainty():
    result=calculate([[-3,4,0]],[[.5,1.]])
    assert result['packet_force_lower_mps2'][0]==pytest.approx(np.sqrt(13.))
    assert result['packet_force_upper_mps2'][0]==pytest.approx(np.sqrt(42.)/.5)
    for delta in itertools.product((-1.,0.,1.),repeat=3):
        value=np.linalg.norm(np.array([-3,4,0])+delta)
        assert result['packet_force_lower_mps2'][0]<=value<=result['packet_force_upper_mps2'][0]


def test_duration_weighted_magnitudes_are_not_mean_packet_rates_or_summed_vector():
    result=calculate([[1,0,0],[-1,0,0]],[[1,1],[3,3]],0.)
    assert result['time_weighted_magnitude_lower_mps2']==.5
    assert result['time_weighted_magnitude_upper_mps2']==.5
    assert result['aggregation']=='sum of packet increment norms / total integration duration'


def test_repetition_does_not_shrink_deterministic_quantization_bound():
    one=calculate([[3,4,0]],[[1,1]])
    many=calculate([[3,4,0]]*100,[[1,1]]*100)
    for key in ('time_weighted_magnitude_lower_mps2','time_weighted_magnitude_upper_mps2'):
        assert many[key]==pytest.approx(one[key])
    assert not many['continuous_force_upper_bound_established']
    assert not many['statistical_coverage_calibrated']
    assert many['scientific_decision']=='abstain'


def test_binary_scale_and_distinct_clock_hypotheses_are_explicit():
    result=magnitude_bounds(np.array([[8192,0,0]],np.int32),np.array([[.005,.005]]),
        scale_mps_per_count=2**-14,count_uncertainty=0.,period_hypothesis='nominal 200 Hz')
    assert result['packet_force_lower_mps2'][0]==100.
    assert result['period_hypothesis']=='nominal 200 Hz'
    result=magnitude_bounds(np.array([[8192,0,0]],np.int32),np.array([[.01,.01]]),
        scale_mps_per_count=2**-14,count_uncertainty=0.,period_hypothesis='header elapsed time')
    assert result['packet_force_lower_mps2'][0]==50.


@pytest.mark.parametrize('argument,value',[
    ('counts',np.ones((2,3),float)),('counts',np.ones((2,3),bool)),
    ('counts',np.empty((0,3),np.int32)),('counts',np.array([[2**32,0,0]])),
    ('period_bounds_s',np.zeros((2,2))),('period_bounds_s',np.array([[1.,.5],[1.,1.]])),
    ('period_bounds_s',np.array([[1.,np.nan],[1.,1.]])),
    ('period_bounds_s',np.ones((2,))),('count_uncertainty',-.1),
    ('count_uncertainty',np.inf),('scale_mps_per_count',0.),('period_hypothesis','')
])
def test_invalid_or_missing_support_fails_closed(argument,value):
    arguments=dict(counts=np.ones((2,3),np.int32),period_bounds_s=np.ones((2,2)),
        scale_mps_per_count=1.,count_uncertainty=1.,period_hypothesis='declared')
    arguments[argument]=value
    with pytest.raises(ValueError):magnitude_bounds(**arguments)
