# SPDX-License-Identifier: AGPL-3.0-or-later
import math
import numpy as np
import pytest
from lll.ilvis0_background_plot import trace
from lll.ilvis0_gyro_prediction import OMEGA


def fixture(course,latitude=0.,rate=0.):
    geometry=dict(latitude_rad=np.full(2,latitude),courses={'sphere_rotating':np.full(2,course)})
    support=dict(utc_seconds=[100,101],receiver_indices=[0,1],durations_s=[.5,1.],
        raw_aircraft=[[0.,-rate,0.],[0.,-rate,0.]])
    return geometry,support


@pytest.mark.parametrize('course,expected',[(0.,0.),(math.pi/2,1.),(math.pi,0.),(-math.pi/2,-1.)])
def test_independent_cardinal_projection_signs_and_actual_durations(course,expected):
    rows=trace(*fixture(course))
    field=sum(r['assumed_background_increment_deg'] for r in rows)
    assert field==pytest.approx(expected*OMEGA*1.5*180/math.pi,abs=1e-16)
    assert rows[-1]['corrected_nose_down_deg']==pytest.approx(-field)


def test_only_background_is_removed_with_no_transport_subtraction_or_fused_channels():
    background=OMEGA*math.cos(.7);transport=2e-5
    geometry,support=fixture(math.pi/2,.7,background+transport)
    support['fused_context_corrected']=[[100.]*3]*2
    geometry['latitude_rate_rads']=np.full(2,-100.)
    rows=trace(geometry,support)
    assert rows[-1]['corrected_nose_down_deg']==pytest.approx(transport*1.5*180/math.pi)
    assert rows[-1]['raw_nose_down_deg']==pytest.approx((background+transport)*1.5*180/math.pi)


def test_missing_second_is_preserved_as_a_gap_and_invalid_data_rejected():
    geometry,support=fixture(math.pi/2);support['utc_seconds'][1]=103
    rows=trace(geometry,support)
    assert rows[1]['gap_before'] and rows[1]['elapsed_s']==4
    support['durations_s'][0]=0.
    with pytest.raises(ValueError):trace(geometry,support)
