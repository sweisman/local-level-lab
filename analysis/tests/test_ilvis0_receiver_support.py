# SPDX-License-Identifier: AGPL-3.0-or-later
"""Receiver-only motion may select one common derivative support."""

import math
import pytest


def policy():
    from lll.ilvis0_receiver_support import SupportPolicy
    return SupportPolicy(half_windows_s=(5., 10.), maximum_gap_s=1.5,
                         minimum_samples=5, minimum_speed_mps=100.,
                         maximum_speed_mps=300.,
                         maximum_course_span_deg=5.,
                         maximum_speed_span_mps=2.,
                         maximum_vertical_rate_span_mps=0.5)


def track():
    times=[float(index) for index in range(41)]
    speed=[200.]*41
    course=[359. if index<20 else 1. for index in range(41)]
    vertical=[0.]*41
    return times,speed,course,vertical


def select(values,target=20.):
    from lll.ilvis0_receiver_support import select_support
    return select_support(*values,target_s=target,policy=policy())


def test_longest_smooth_window_is_common_even_across_course_wrap():
    values=track();before=[list(value) for value in values]
    result=select(values)
    assert result['selected_half_window_s']==10.
    assert result['selected_indices']==(10,30)
    assert [row['accepted'] for row in result['windows']]==[True,True]
    assert result['windows'][1]['course_span_deg']==pytest.approx(2.)
    assert result['scientific_decision']=='abstain'
    assert values==tuple(before)


def test_receiver_maneuver_rejects_long_window_without_changing_short_one():
    times,speed,course,vertical=track();course[12]=10.
    result=select((times,speed,course,vertical))
    assert result['selected_half_window_s']==5.
    assert result['selected_indices']==(15,25)
    assert result['windows'][0]['accepted'] is True
    assert result['windows'][1]['reason']=='course_span'


def test_a_gap_rejects_every_window_and_requires_abstention():
    times,speed,course,vertical=track()
    keep=[index for index in range(41) if index!=19]
    values=tuple([[series[index] for index in keep]
                  for series in (times,speed,course,vertical)])
    result=select(values)
    assert result['selected_half_window_s'] is None
    assert result['selected_indices'] is None
    assert [row['reason'] for row in result['windows']]==['gap','gap']


def test_low_speed_and_missing_symmetric_support_fail_closed():
    times,speed,course,vertical=track();speed=[50.]*41
    result=select((times,speed,course,vertical))
    assert result['selected_indices'] is None
    assert [row['reason'] for row in result['windows']]==['low_speed','low_speed']
    result=select(track(),target=3.)
    assert result['selected_indices'] is None
    assert [row['reason'] for row in result['windows']]==[
        'incomplete_support','incomplete_support']


def test_malformed_receiver_value_has_a_clear_rejection():
    times,speed,course,vertical=track();course[20]=None
    with pytest.raises(ValueError,match='receiver motion samples'):
        select((times,speed,course,vertical))


@pytest.mark.parametrize(('axis','value','reason'),[
    ('speed',205.,'speed_span'),
    ('vertical',1.,'vertical_rate_span'),
])
def test_one_receiver_motion_excursion_rejects_only_its_long_window(
        axis,value,reason):
    times,speed,course,vertical=track()
    {'speed':speed,'vertical':vertical}[axis][12]=value
    result=select((times,speed,course,vertical))
    assert result['selected_half_window_s']==5.
    assert result['windows'][1]['reason']==reason


def test_irregular_supported_cadence_and_insufficient_samples():
    times,speed,course,vertical=track();times[17]=17.2
    assert select((times,speed,course,vertical))['selected_half_window_s']==10.
    indices=(0,10,20,30,40)
    sparse=tuple([[series[index] for index in indices]
                  for series in (times,speed,course,vertical)])
    from lll.ilvis0_receiver_support import SupportPolicy,select_support
    sparse_policy=SupportPolicy(half_windows_s=(5.,10.),maximum_gap_s=11.,
        minimum_samples=5,minimum_speed_mps=100.,maximum_speed_mps=300.,
        maximum_course_span_deg=5.,
        maximum_speed_span_mps=2.,maximum_vertical_rate_span_mps=.5)
    result=select_support(*sparse,target_s=20.,policy=sparse_policy)
    assert result['selected_indices'] is None
    assert [row['reason'] for row in result['windows']]==[
        'sample_count','sample_count']


def _fix(time,latitude,longitude,height=1000.):
    return dict(utc_week_s=time,time1_s=time*1.01+.2,
                latitude_deg=latitude,longitude_deg=longitude,
                orthometric_height_m=height-30.,geoid_separation_m=30.,fix_quality=1)


def test_timestamped_gga_positions_supply_receiver_only_course_and_speed():
    from lll.ilvis0_receiver_support import motion_from_gga_fixes
    radius=6378137.+1000.
    rows=[_fix(float(index),0., math.degrees(200.*index/radius))
          for index in range(11)]
    result=motion_from_gga_fixes(rows,maximum_gap_s=1.5)
    assert result['source']=='primary_receiver_gga'
    assert result['coordinate_metric']=='WGS84 receiver-coordinate interpretation'
    assert result['times_s']==tuple(float(index) for index in range(11))
    assert result['speed_mps']==pytest.approx((200.,)*11,abs=1e-8)
    assert result['course_deg']==pytest.approx((90.,)*11,abs=1e-10)
    assert result['vertical_rate_mps']==pytest.approx((0.,)*11)


def test_dated_applanix_gga_mapping_feeds_receiver_motion_without_packet_time():
    from lll.ilvis0_followup import mapped_context
    from lll.ilvis0_receiver_support import motion_from_gga_fixes
    radius=6378137.+1000.
    gga=[dict(time1_s=18.+float(i)+.2,time_types=1,sod=float(i),
              latitude_deg=0.,longitude_deg=math.degrees(200.*i/radius),
              orthometric_height_m=970.,geoid_separation_m=30.,fix_quality=1)
         for i in range(11)]
    _,fixes=mapped_context([],gga,dict(accepted=True,gps_minus_utc_s=18))
    result=motion_from_gga_fixes(fixes,maximum_gap_s=1.5)
    assert result['times_s']==tuple(float(i) for i in range(11))
    assert result['speed_mps']==pytest.approx((200.,)*11,abs=1e-8)
    assert result['ellipsoidal_height_m']==pytest.approx((1000.,)*11)


def test_receiver_motion_crosses_dateline_without_false_speed():
    from lll.ilvis0_receiver_support import motion_from_gga_fixes
    radius=6378137.+1000.
    rows=[_fix(float(index),0.,((179.99+math.degrees(200.*index/radius)+180.)%360.)-180.)
          for index in range(15)]
    result=motion_from_gga_fixes(rows,maximum_gap_s=1.5)
    assert result['speed_mps']==pytest.approx((200.,)*15,abs=1e-6)
    assert result['course_deg']==pytest.approx((90.,)*15,abs=1e-9)


def test_receiver_motion_uses_vertical_rate_and_meridian_metric():
    from lll.ilvis0_receiver_support import motion_from_gga_fixes
    meridian=6378137.*(1.-0.00669437999014)+1008.
    rows=[_fix(float(index),math.degrees(150.*index/meridian),0.,1000.+2.*index)
          for index in range(9)]
    result=motion_from_gga_fixes(rows,maximum_gap_s=1.5)
    assert result['speed_mps'][4]==pytest.approx(150.,rel=1e-6)
    assert result['course_deg'][4]==pytest.approx(0.,abs=1e-10)
    assert result['vertical_rate_mps']==pytest.approx((2.,)*9)
    assert result['ellipsoidal_height_m'][4]==pytest.approx(1008.)
    assert result['height_convention']=='GGA orthometric_height_m + geoid_separation_m'


def test_timed_gga_motion_feeds_one_common_support_selection():
    from lll.ilvis0_receiver_support import (
        SupportPolicy,motion_from_gga_fixes,select_support)
    radius=6378137.+1000.
    rows=[_fix(float(index),0.,math.degrees(200.*index/radius))
          for index in range(11)]
    motion=motion_from_gga_fixes(rows,maximum_gap_s=1.5)
    chosen=select_support(motion['times_s'],motion['speed_mps'],
        motion['course_deg'],motion['vertical_rate_mps'],target_s=5.,
        policy=SupportPolicy(half_windows_s=(5.,),maximum_gap_s=1.5,
            minimum_samples=5,minimum_speed_mps=100.,
            maximum_speed_mps=300.,
            maximum_course_span_deg=5.,maximum_speed_span_mps=2.,
            maximum_vertical_rate_span_mps=.5))
    assert chosen['selected_indices']==(0,10)
    assert chosen['scientific_decision']=='abstain'


@pytest.mark.parametrize('change',[
    {'utc_week_s':1.},
    {'fix_quality':0},
    {'orthometric_height_m':None},
    {'geoid_separation_m':None},
    {'latitude_deg':90.},
])
def test_receiver_motion_rejects_unusable_fixes(change):
    from lll.ilvis0_receiver_support import motion_from_gga_fixes
    rows=[_fix(float(index),0.,.001*index) for index in range(5)]
    rows[2].update(change)
    with pytest.raises(ValueError,match='receiver fixes'):
        motion_from_gga_fixes(rows,maximum_gap_s=1.5)


def test_receiver_motion_rejects_a_missing_fix_before_differencing():
    from lll.ilvis0_receiver_support import motion_from_gga_fixes
    rows=[_fix(float(index),0.,.001*index) for index in (0,1,2,4,5)]
    with pytest.raises(ValueError,match='receiver fixes'):
        motion_from_gga_fixes(rows,maximum_gap_s=1.5)


def test_packet_timestamp_never_replaces_missing_gga_measurement_time():
    from lll.ilvis0_receiver_support import motion_from_gga_fixes
    rows=[_fix(float(index),0.,.001*index) for index in range(5)]
    rows[2].pop('utc_week_s')
    with pytest.raises(ValueError,match='receiver fixes'):
        motion_from_gga_fixes(rows,maximum_gap_s=1.5)


def test_impossible_speed_fails_the_common_support_policy():
    times,speed,course,vertical=track()
    speed=[350.]*len(speed)
    result=select((times,speed,course,vertical))
    assert result['selected_indices'] is None
    assert [row['reason'] for row in result['windows']]==[
        'high_speed','high_speed']
