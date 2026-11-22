"""Fixed-time raw gyro aggregation does not inject a field prediction."""

import math
import pytest


def sample(t,rate=.001):
    return dict(gps_time_s=t,angular_rate_rads=[rate,0.,0.],
                acceleration_mps2=[0.,0.,9.8],temperature_c=20.,
                gap_above_1p5_nominal_periods=False)


def test_constant_raw_rate_uses_fixed_gps_time_and_correct_units():
    from lll.esa_ground_imu_rate import summarize_rows
    data=[sample(-.01,99.),sample(0.),sample(.003),sample(.006),sample(.009),
          sample(.012,99.)]
    result=summarize_rows(data,first=0.,last=.01,min_samples=4)
    assert result['samples']==4
    assert result['mean_rate_xyz_deg_per_hour'][0]==pytest.approx(.001*180/math.pi*3600)
    assert result['mean_rate_xyz_deg_per_hour'][1:]==[0.,0.]
    assert result['mean_rate_magnitude_deg_per_hour']==pytest.approx(.001*180/math.pi*3600)
    assert result['uses_model_prediction'] is False


def test_gap_inside_selected_interval_is_rejected():
    from lll.esa_ground_imu_rate import summarize_rows
    with pytest.raises(ValueError,match='gap'):
        summarize_rows([sample(0.),sample(.003),sample(.013)],
                       first=0.,last=.013,min_samples=2)


def test_missing_time_support_is_rejected():
    from lll.esa_ground_imu_rate import summarize_rows
    with pytest.raises(ValueError,match='support'):
        summarize_rows([sample(.1),sample(.103)],
                       first=0.,last=.2,min_samples=2)


def test_coverage_overlap_uses_only_acquisition_timestamps():
    from lll.esa_ground_imu_rate import coverage_overlap
    assert coverage_overlap(100.,2000.,500.,2500.)==(500.,2000.)
    with pytest.raises(ValueError,match='overlap'):
        coverage_overlap(100.,200.,500.,900.)
