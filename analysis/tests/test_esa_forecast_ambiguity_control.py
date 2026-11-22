"""A withheld forecast can hide motion behind an assumed IMU error."""

import math

import numpy as np
import pytest


def test_future_motion_and_sensor_error_have_the_same_recorded_input():
    from lll.esa_forecast_ambiguity_control import paired_forecasts

    case=paired_forecasts(training_s=2,future_s=120,rate_hz=20,
                          speed_mps=80.,rate_dph=1.)
    turning=case['turning'];straight=case['straight']
    for name in ('measured_gyro_rads','measured_force_mps2',
                 'training_receiver_position_m'):
        assert np.array_equal(turning[name],straight[name])
    assert np.array_equal(case['imu_time_s'][0:41],np.arange(-40,1)/20)
    assert case['future_receiver_time_s'][-1]==120.
    assert turning['true_gyro_rads'][-1,2]>0
    assert straight['true_gyro_rads'][-1,2]==0
    rate=math.radians(1.)/3600
    expected_y=80*(1-math.cos(rate*120))/rate
    assert case['end_separation_m']==pytest.approx(expected_y,rel=1e-7)
    assert case['end_separation_m']>2.7


def test_future_ambiguity_requires_bounded_physical_inputs():
    from lll.esa_forecast_ambiguity_control import paired_forecasts

    with pytest.raises(ValueError,match='finite positive'):
        paired_forecasts(speed_mps=float('nan'))
    with pytest.raises(ValueError,match='finite positive'):
        paired_forecasts(rate_dph=0.)


def test_report_confirms_exact_observation_match_and_no_aircraft_reads():
    from lll.esa_forecast_ambiguity_control import summarize_control

    report=summarize_control(training_s=2,future_s=120,rate_hz=20)
    assert report['recorded_imu_identical'] is True
    assert report['training_receiver_identical'] is True
    assert report['future_receiver_withheld'] is True
    assert report['original_reads']==0
    assert report['protected_reads']==0
    assert report['end_separation_m']>2.7
    assert len(report['source_sha256'])==64
    assert report['scientific_decision']=='abstain'
