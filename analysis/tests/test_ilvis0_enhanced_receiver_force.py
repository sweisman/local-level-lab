"""Primary-receiver enhanced positions can enter the same gyro-free bridge."""

import math

import numpy as np
import pytest

from lll.ilvis0_error_model import Spec
from lll.ilvis0_joint_receiver_force import assess_candidates_structured
from lll.ilvis0_receiver_support import SupportPolicy, motion_from_enhanced_positions


def _inputs():
    week = 1900
    origin = week*604800.
    radius = 6378137. + 1000.
    rows = [dict(gps_week=week, gps_milliseconds=i*1000,
                 latitude_deg=0., longitude_deg=math.degrees(200.*i/radius),
                 ellipsoid_height_m=1000., velocity_north_mps=0.,
                 velocity_east_mps=200., velocity_up_mps=0.,
                 position_solution_mode=5)
            for i in range(31)]
    policy = SupportPolicy(
        half_windows_s=(5.,), maximum_gap_s=1.5,
        minimum_samples=5, minimum_speed_mps=100.,
        maximum_speed_mps=300., maximum_course_span_deg=5.,
        maximum_speed_span_mps=5., maximum_vertical_rate_span_mps=.5)
    spec = Spec(white=np.diag([1e-16, 1e-16, .09]),
                drift_origin_s=origin, drift_span_s=30.)
    return rows, policy, spec, origin


def test_enhanced_position_motion_uses_receiver_velocity_and_gps_time():
    rows, policy, _, origin = _inputs()
    motion = motion_from_enhanced_positions(rows, maximum_gap_s=policy.maximum_gap_s)
    assert motion['source'] == 'primary_receiver_enhanced_position'
    assert motion['times_s'][0] == origin
    assert motion['times_s'][-1] == origin+30.
    assert motion['speed_mps'][10] == 200.
    assert motion['course_deg'][10] == 90.
    text_rows = [dict(row, gps_week=str(row['gps_week']),
                      gps_milliseconds=str(row['gps_milliseconds']))
                 for row in rows]
    assert motion_from_enhanced_positions(
        text_rows, maximum_gap_s=policy.maximum_gap_s)['times_s'] == motion['times_s']


def test_enhanced_position_structured_force_keeps_source_and_common_support():
    rows, policy, spec, origin = _inputs()
    result = assess_candidates_structured(
        rows, spec, targets_s=[origin+15.], policy=policy, degree=2,
        background_rate_rads=7.292115e-5, gravity_mps2=9.8,
        disc_radius_m=6371000.,
        source_kind='primary_receiver_enhanced_position')
    assert result['source'] == 'primary_receiver_enhanced_position'
    assert result['selected_indices'] == [(10, 20)]
    assert result['supported_target_indices'] == [0]
    assert result['joint_covariance_mps4'].shape == (3, 3)
    assert result['gyro_observations_used'] is False
    assert result['scientific_decision'] == 'abstain'


def test_enhanced_position_rejects_bad_epoch_and_gap():
    rows, policy, _, _ = _inputs()
    bad = [dict(row) for row in rows]
    bad[4]['gps_milliseconds'] = -1
    with pytest.raises(ValueError):
        motion_from_enhanced_positions(bad, maximum_gap_s=policy.maximum_gap_s)
    bad = [dict(row) for row in rows]
    bad[4]['gps_week'] = 1900.5
    with pytest.raises(ValueError):
        motion_from_enhanced_positions(bad, maximum_gap_s=policy.maximum_gap_s)
    bad = [dict(row) for row in rows]
    bad[4]['gps_milliseconds'] = 5000
    with pytest.raises(ValueError):
        motion_from_enhanced_positions(bad, maximum_gap_s=policy.maximum_gap_s)
