# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import math

import pytest

from lll import airquantumgrav_increments as adapter


def row(t,angular=(1.,2.,3.),accel=(0.,0.,-9.81),number=1):
    return dict(gps_time_s=t,angular_rate_rads=list(angular),acceleration_mps2=list(accel),
        temperature_c=20.,line_number=number)


@pytest.mark.parametrize('method',['left_hold','right_hold','linear_points'])
def test_constant_channels_and_original_rows_are_preserved(method):
    a=row(100.);b=row(100.003,number=2);original=copy.deepcopy([a,b])
    interval=list(adapter.intervals([a,b],method=method))[0]
    dt=b['gps_time_s']-a['gps_time_s']
    assert interval['dt_s']==dt
    assert interval['dtheta_rad']==[x*dt for x in a['angular_rate_rads']]
    assert interval['dv_mps']==[x*dt for x in a['acceleration_mps2']]
    assert interval['raw_left']==a and interval['raw_right']==b and [a,b]==original
    assert interval['increment_origin']=='constructed_from_reported_rates'
    assert interval['instrument_sampling_phase_established'] is False


def test_linear_points_matches_analytic_integrals_and_labels_alignment():
    a=row(100.,angular=(1.,0.,0.));b=row(100.004,angular=(3.,0.,0.),number=2)
    interval=list(adapter.intervals([a,b],method='linear_points',alignment_s=.001))[0]
    assert interval['dtheta_rad'][0]==2.*(100.004-100.)
    assert interval['interval_start_gps_s']==100.001
    assert interval['raw_left']['gps_time_s']==100.
    assert interval['quadrature_hypothesis']=='linear_points'


def test_stream_continuation_has_no_missing_or_duplicate_interval():
    rows=[row(100.+i*.003,number=i+1) for i in range(5)]
    stream=adapter.IntervalStream(method='right_hold')
    a=list(stream.push(rows[:2]));b=list(stream.push(rows[2:]))
    assert a+b==list(adapter.intervals(rows,method='right_hold'))
    assert len(a+b)==4


@pytest.mark.parametrize('times',[(100.,100.),(100.,99.),(100.,100.02)])
def test_reversals_duplicates_and_gaps_are_rejected(times):
    with pytest.raises(ValueError):list(adapter.intervals([row(t) for t in times],method='left_hold'))


def test_single_record_has_no_preceding_measurement_and_unknown_method_rejected():
    assert list(adapter.intervals([row(10.)],method='right_hold'))==[]
    with pytest.raises(ValueError):list(adapter.intervals([row(10.)],method='guess'))


@pytest.mark.parametrize('method',['left_hold','right_hold','linear_points'])
def test_analytic_sine_error_inside_supplied_derivative_bound(method):
    t=1.2;h=.003;frequency=3.
    a=row(t,angular=(math.sin(frequency*t),0.,0.));b=row(t+h,angular=(math.sin(frequency*(t+h)),0.,0.))
    result=list(adapter.intervals([a,b],method=method))[0]
    exact=(math.cos(frequency*t)-math.cos(frequency*(t+h)))/frequency
    allowance=adapter.integral_error_bound(result['dt_s'],method=method,first_derivative_bound=frequency,
        second_derivative_bound=frequency**2)
    assert abs(result['dtheta_rad'][0]-exact)<=allowance+1e-15


def test_bad_input_does_not_replace_previous_valid_row():
    stream=adapter.IntervalStream(method='left_hold');assert list(stream.push([row(10.)]))==[]
    with pytest.raises(ValueError):list(stream.push([row(9.)]))
    good=list(stream.push([row(10.003)]))
    assert len(good)==1 and good[0]['raw_left']['gps_time_s']==10.
