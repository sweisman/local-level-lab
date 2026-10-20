# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
from functools import partial
import math

import numpy as np
import pytest

from lll import airquantumgrav_selection as selection

verified_select=partial(selection.select,source_integrity_verified=True)


def rows(n=2501,step=.5,speed=60.):
    return [dict(sequence=i,gps_week=2269,time_s=1000+i*step,latitude_deg=65.,longitude_deg=-50.,height_m=1500.,
        north_mps=speed,east_mps=0.,up_mps=0.,position_variance_m2=[1.,1.,4.],pdop=2.,satellites=12,
        utc_date='06/07/2023',utc_time='12:00:00') for i in range(n)]


def test_entire_supported_run_is_selected_with_durable_summaries():
    result=verified_select(rows(),imu_support=(999.,2300.))
    assert len(result['eligible'])==1
    run=result['eligible'][0]
    assert run['duration_s']==1240. and run['distance_m']==74400.
    assert run['mean_course_deg']==0. and run['mean_latitude_deg']==65.
    assert result['gyro_used_for_selection'] is False


def test_threshold_equalities_pass():
    result=verified_select(rows(n=2421,speed=50.),imu_support=(999.,2300.))
    assert result['eligible'][0]['duration_s']==1200.
    assert result['eligible'][0]['distance_m']==60000.


@pytest.mark.parametrize('key,value,reason',[
    ('north_mps',49.,'speed'),('pdop',4.01,'receiver_quality'),('satellites',7,'receiver_quality'),
    ('position_variance_m2',[0.,1.,1.],'receiver_quality'),
    ('position_variance_m2',[25.01,1.,1.],'receiver_quality')])
def test_quality_and_speed_failures_are_preserved(key,value,reason):
    data=rows(n=100);data[50][key]=value
    result=verified_select(data,imu_support=(999.,2300.))
    assert reason in result['epoch_reasons'][50]
    assert not result['eligible']


def test_gap_splits_without_interpolating_or_bridging():
    data=rows()
    for r in data[1250:]:r['time_s']+=1.
    result=verified_select(data,imu_support=(999.,2400.))
    assert len(result['blocks'])==2 and not result['eligible']
    assert len(result['rejected_runs'])==2


@pytest.mark.parametrize('kind',['duplicate','reversal','week'])
def test_time_and_week_errors_are_rejected(kind):
    data=rows(n=50)
    if kind=='week':data[25]['gps_week']+=1
    else:data[25]['time_s']=data[24]['time_s']-(.1 if kind=='reversal' else 0.)
    with pytest.raises(ValueError):verified_select(data,imu_support=(999.,2300.))


def test_heading_wrap_is_not_a_maneuver():
    data=rows(n=100)
    for i,r in enumerate(data):
        angle=math.radians(359.9+i*.002)
        r.update(north_mps=60.*math.cos(angle),east_mps=60.*math.sin(angle))
    result=verified_select(data,imu_support=(999.,2300.))
    assert 'maneuver_margin' not in result['epoch_reasons'][50]


def test_maneuver_exclusion_includes_window_support_and_margin():
    data=rows(n=401)
    for r in data[190:211]:r['up_mps']=2.
    result=verified_select(data,imu_support=(999.,2300.))
    assert 'maneuver_margin' in result['epoch_reasons'][150]
    assert 'maneuver_margin' in result['epoch_reasons'][250]
    assert 'maneuver_margin' not in result['epoch_reasons'][100]


def test_nonuniform_timestamps_use_actual_time_and_distance():
    data=rows(n=100)
    for i,r in enumerate(data):r['time_s']+=.02*math.sin(i*.2)
    result=verified_select(data,imu_support=(999.,2300.))
    run=result['rejected_runs'][0]
    assert math.isclose(run['distance_m'],60.*run['duration_s'],rel_tol=1e-14)


def test_zero_speed_and_imu_support_are_explicit_exclusions():
    data=rows(n=100);data[50]['north_mps']=0.
    result=verified_select(data,imu_support=(1010.,1035.))
    assert 'speed' in result['epoch_reasons'][50]
    assert 'imu_support' in result['epoch_reasons'][5]
    assert not result['eligible']


def test_unsupported_integrity_cannot_be_selected():
    with pytest.raises(ValueError):verified_select(rows(n=100),imu_support=(999.,2300.),source_integrity_verified=False)
