# SPDX-License-Identifier: AGPL-3.0-or-later
import math
import numpy as np
import pytest
from lll import esa_position_assessment as assessment


def test_covariance_fields_preserve_north_east_up_cross_terms():
    row=dict(position_variance_m2=[1.,4.,9.],position_cross_covariance_m2=[-.2,.3,-.4])
    assert assessment.position_covariance(row)==[[1.,-.2,.3],[-.2,4.,-.4],[.3,-.4,9.]]


def test_window_support_requires_bracketing_epochs_and_preserves_gaps():
    t=np.arange(21)*.5;s=np.arange(21)
    assert assessment.window_indices(t,s,10)==(0,21)
    assert assessment.window_indices(t,s,0) is None
    s[9:]+=1
    assert assessment.window_indices(t,s,10) is None


def test_export_precision_is_verified_without_changing_the_text():
    lines=['SeqNum Latitude Longitude H-Ell\n','00000000 64.1234567890 -51.1234567890 123.456\n']
    assert list(assessment.precision_checked(lines))==lines
    with pytest.raises(ValueError):list(assessment.precision_checked(['00000000 64.12345 -51.1234567890 123.456\n']))
    with pytest.raises(ValueError,match='before decoding'):
        list(assessment.precision_checked(lines+lines[1:],maximum_records=1))


def test_window_budget_saves_before_work_and_stage_allowances_cannot_be_reused():
    events=[];budget=assessment.Windows(1,lambda k,v:events.append((k,v)),lambda:None)
    claim=budget.begin(10)
    assert events[0][1]['windows']==1
    claim('position');claim('point');claim('residual')
    with pytest.raises(ValueError):claim('position')
    with pytest.raises(ValueError):budget.begin(11)


def test_independent_residual_fit_reproduces_cubics_without_claiming_correlated_noise():
    t=np.linspace(-5.,5.,21);chart=np.column_stack((t**3,t*t,t))
    result=assessment.residual_diagnostic(t,chart,center_s=0.)
    assert max(result['rms_m'])<1e-12 and result['lag1']==[None,None,None]


def test_complete_receiver_window_has_no_instantaneous_or_eligibility_claim():
    t=np.arange(21)*.5;phi=math.radians(64.);height=1000.
    east=(6378137./math.sqrt(1-6.69437999014e-3*math.sin(phi)**2)+height)*math.cos(phi)
    rows=[dict(time_s=float(v),sequence=i,latitude_deg=64.,longitude_deg=math.degrees(-.5+60.*v/east),height_m=height,
        north_mps=0.,east_mps=60.,up_mps=0.,position_variance_m2=[.0001]*3,
        position_cross_covariance_m2=[0.]*3,velocity_covariance_m2_s2=np.eye(3).tolist()) for i,v in enumerate(t)]
    events=[];budget=assessment.Windows(1,lambda k,v:events.append(v),lambda:None)
    result=assessment.assess_window(rows,t,np.arange(21),10,
        dict(airborne_supported='True',trend_rate_deg_s='.003'),claim=budget.begin(10))
    assert result['supported'] and result['airborne_supported']
    assert abs(result['position_course_rate_deg_s'])<1e-8
    assert max(abs(v) for v in result['position_minus_reported_ne_mps'])<1e-7
    assert result['position']['instantaneous_motion_supported'] is False
    assert result['eligibility_policy_changed'] is False and result['scientific_decision']=='abstain'
    assert budget.calls==dict(position=1,point=1,residual=1)
