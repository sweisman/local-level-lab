# SPDX-License-Identifier: AGPL-3.0-or-later
import math
import pytest
from lll.ilvis0_gyro_prediction import OMEGA


def fixture(course=math.pi/2,latitude=.7):
    geometry=dict(latitude_rad=[latitude,latitude],latitude_rate_rads=[math.cos(course)]*2,
        longitude_rate_rads=[math.sin(course)/math.cos(latitude)]*2)
    support=dict(utc_seconds=[100,101],receiver_indices=[0,1],durations_s=[.5,1.],
        raw_aircraft=[[.001,-.002,.003]]*2)
    field=OMEGA*math.cos(latitude)*math.sin(course);transport=2e-5
    cache={str(s):dict(duration_s=d,raw_aircraft=g,
        fused_context_corrected=[field+transport,.001,.002])
        for s,d,g in zip(support['utc_seconds'],support['durations_s'],support['raw_aircraft'])}
    return geometry,support,cache,transport


@pytest.mark.parametrize('course',[0.,math.pi/2,math.pi,-math.pi/2])
def test_known_field_is_removed_and_transport_is_retained(course):
    from lll.ilvis0_motion_plot import trace
    geometry,support,cache,transport=fixture(course)
    rows=trace(geometry,support,cache)
    assert rows[-1]['residual_across_track_deg']==pytest.approx(transport*1.5*180/math.pi,abs=1e-15)
    assert rows[-1]['raw_pitch_deg']==pytest.approx(.002*1.5*180/math.pi)


def test_missing_attitude_support_is_explicit_not_raw_or_zero_substitution():
    from lll.ilvis0_motion_plot import trace
    geometry,support,cache,_=fixture();del cache['101']['fused_context_corrected']
    rows=trace(geometry,support,cache)
    assert rows[0]['supported'] and not rows[1]['supported']
    assert rows[1]['residual_across_track_deg'] is None
    assert rows[1]['unsupported_reason']=='navigation_attitude_correction_unavailable'


def test_cache_mismatch_and_nonfinite_motion_are_rejected():
    from lll.ilvis0_motion_plot import trace
    geometry,support,cache,_=fixture();cache['100']['raw_aircraft']=[0.,0.,0.]
    with pytest.raises(ValueError):trace(geometry,support,cache)
    geometry,support,cache,_=fixture();cache['100']['fused_context_corrected'][0]=float('nan')
    with pytest.raises(ValueError):trace(geometry,support,cache)


def test_no_model_transport_or_fused_gyro_rate_is_subtracted():
    from lll.ilvis0_motion_plot import trace
    geometry,support,cache,transport=fixture()
    geometry['transport_pitch_rate']=[1e10]*2
    for row in cache.values():row['angular_rate_y_deg_s']=1e10
    rows=trace(geometry,support,cache)
    assert rows[-1]['residual_across_track_deg']==pytest.approx(transport*1.5*180/math.pi)


def test_original_time_origin_and_gaps_are_preserved():
    from lll.ilvis0_motion_plot import trace
    geometry,support,cache,_=fixture();support['utc_seconds'][1]=104;cache['104']=cache.pop('101')
    rows=trace(geometry,support,cache)
    assert rows[1]['elapsed_s']==5 and rows[1]['gap_before']
