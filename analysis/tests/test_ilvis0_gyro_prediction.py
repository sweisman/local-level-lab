# SPDX-License-Identifier: AGPL-3.0-or-later
import math
import numpy as np
import pytest


def module():
    from lll import ilvis0_gyro_prediction
    return ilvis0_gyro_prediction


@pytest.mark.parametrize('course',[0.,math.pi/2,math.pi,3*math.pi/2])
def test_level_transport_pitch_follows_negative_speed_over_radius(course):
    g=module();phi=.7;v=210.;radius=6371000.
    pd=v*math.cos(course)/radius;ld=v*math.sin(course)/(radius*math.cos(phi))
    vector=g.geographic_vector('sphere_still',phi,pd,ld,removal=0.)
    right=g.right_axis(course,roll=0.,pitch=0.)
    assert vector@right==pytest.approx(-v/radius)
    assert g.geographic_vector('flat_still',phi,pd,ld,removal=0.)@right==pytest.approx(0.,abs=1e-15)


def test_background_and_upstream_removal_are_separate_and_common():
    g=module();phi=-.8;pd=2e-5;ld=1e-5
    standard=np.array([g.OMEGA*math.cos(phi),0.,-g.OMEGA*math.sin(phi)])
    rotating=g.geographic_vector('sphere_rotating',phi,pd,ld,removal=0.)
    still=g.geographic_vector('sphere_still',phi,pd,ld,removal=0.)
    np.testing.assert_allclose(rotating-still,standard,atol=1e-18)
    for model in g.MODELS:
        a=g.geographic_vector(model,phi,pd,ld,removal=0.)
        b=g.geographic_vector(model,phi,pd,ld,removal=1.)
        np.testing.assert_allclose(a-b,standard,atol=1e-18)


def test_tilt_projection_and_course_motion_have_independent_known_limits():
    g=module();roll=.1
    np.testing.assert_allclose(g.right_axis(0.,roll=roll,pitch=0.),[0.,math.cos(roll),math.sin(roll)])
    assert g.course_pitch_rate(.03,roll=roll,pitch=0.)==pytest.approx(.03*math.sin(roll))
    assert g.course_pitch_rate(200.,roll=0.,pitch=.2)==0.


def fixes():
    return [dict(time_s=float(i),latitude_rad=-.8+1e-5*i,longitude_rad=2.+2e-5*i,height_m=9000.) for i in range(5)]


def bins():
    return {str(i):dict(duration_s=1.,raw_aircraft=[0.,-1e-4,0.],fused_context_corrected=[900.,800.,700.]) for i in range(4)}


def test_receiver_geometry_uses_each_candidate_metric_and_preserves_dateline():
    g=module();rows=fixes();rows[0]['longitude_rad']=math.pi-2e-5
    for i in range(1,5):rows[i]['longitude_rad']=-math.pi+(i-1)*2e-5
    series=g.receiver_geometry(rows)
    np.testing.assert_allclose(series['longitude_rate_rads'],2e-5,atol=1e-14)
    assert not np.allclose(series['courses']['sphere_still'],series['courses']['flat_still'])
    assert len(series['times_s'])==4


def test_matched_raw_angles_ignore_fused_channels_and_keep_sign():
    g=module();geometry=g.receiver_geometry(fixes());raw=bins()
    support=g.matched_bins(raw,geometry,recorded_mount_available=True)
    row=g.summarize(geometry,support,model='sphere_still',crab_deg=0.,roll_deg=0.,pitch_deg=0.,removal=0.)
    assert row['observed_nose_down_dph']==pytest.approx(1e-4*g.DPH)
    assert row['observed_nose_down_deg']==pytest.approx(4e-4*180./math.pi)
    for b in raw.values():b['fused_context_corrected']=[-1e30]*3
    again=g.summarize(geometry,g.matched_bins(raw,geometry,recorded_mount_available=True),
        model='sphere_still',crab_deg=0.,roll_deg=0.,pitch_deg=0.,removal=0.)
    assert row==again
    assert row['scientific_decision']=='abstain'


def test_matching_rejects_ties_without_interpolating_and_reports_missing_mount():
    g=module()
    assert g.nearest_unique(np.array([0.,1.]),.5,.55) is None
    assert g.nearest_unique(np.array([0.,1.]),.49,.55)==0
    result=g.matched_bins(bins(),g.receiver_geometry(fixes()),recorded_mount_available=False)
    assert result['supported'] is False and result['reason']=='recorded_mount_unavailable'


@pytest.mark.parametrize('bad',['reversed','gap','nonfinite','pole'])
def test_invalid_receiver_support_is_rejected(bad):
    rows=fixes()
    if bad=='reversed':rows[2]['time_s']=rows[1]['time_s']
    elif bad=='gap':rows[2]['time_s']+=3.
    elif bad=='nonfinite':rows[2]['height_m']=float('nan')
    else:rows[2]['latitude_rad']=math.pi/2
    with pytest.raises(ValueError):module().receiver_geometry(rows)
