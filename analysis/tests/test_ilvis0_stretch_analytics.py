# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent geometry, timing, frame and failure-classification controls."""
import math
import hashlib
import struct

import numpy as np
import pytest

from lll import ilvis0_stretch_analytics as analytics


def fixes(course, latitude=-63., speed=230., seconds=10):
    phi = math.radians(latitude)
    psi = math.radians(course)
    return [dict(time_s=float(t), latitude_rad=phi+t*speed*math.cos(psi)/analytics.RADIUS_M,
                 longitude_rad=t*speed*math.sin(psi)/(analytics.RADIUS_M*math.cos(phi)),
                 height_m=9000.) for t in range(seconds+1)]


@pytest.mark.parametrize('course', [0., 106., 180., 203., 359.])
def test_transport_pitch_and_yaw_are_separate(course):
    report, _ = analytics.trajectory(fixes(course))
    scale = 180/math.pi*3600
    assert report['sphere_transport_across_left_dph'] == pytest.approx(230/analytics.RADIUS_M*scale, rel=1e-3)
    assert report['sphere_transport_along_dph'] == pytest.approx(0., abs=1e-10)
    assert report['disc_transport_across_left_dph'] == 0.
    assert report['disc_transport_along_dph'] == 0.
    assert report['disc_transport_down_dph'] == pytest.approx(-report['mean_longitude_rate_dph'])
    if course == 180:
        assert report['disc_transport_down_dph'] == pytest.approx(0., abs=1e-8)
    if course == 203:
        assert report['mean_east_velocity_mps'] == pytest.approx(230*math.sin(math.radians(203)), rel=1e-3)


def test_longitude_wrap_and_timestamp_errors():
    track = fixes(90., latitude=0.)
    for row in track:
        row['longitude_rad'] = (row['longitude_rad']+math.pi-1e-4+math.pi) % (2*math.pi)-math.pi
    report, _ = analytics.trajectory(track)
    assert report['mean_east_velocity_mps'] == pytest.approx(230., rel=1e-6)
    track[1]['time_s'] = track[0]['time_s']
    with pytest.raises(ValueError, match='timestamp'):
        analytics.trajectory(track)


def test_motion_correction_preserves_added_field_and_crab():
    # Level aircraft heads east, while its ground course is north: 90-degree crab.
    row = dict(roll_deg=0., pitch_deg=0., heading_deg=90.)
    field_ned = np.array([1., 2., 3.])*1e-5
    aircraft_turn = np.array([0., 0., .001])
    rotation = analytics.attitude_matrix(row)
    observed = rotation.T@field_ned+aircraft_turn
    result = analytics.context_corrected(observed, row, aircraft_turn, 0.)
    # Across-left is west; along-track north; down positive.
    np.testing.assert_allclose(result, [-2e-5, 1e-5, 3e-5], atol=1e-14)


def test_no_fused_gyro_channel_is_used_to_remove_motion():
    rows = [dict(time_s=float(i), roll_deg=0., pitch_deg=0., heading_deg=i*.1,
                 angular_rate_x_deg_s=999., angular_rate_y_deg_s=999., angular_rate_z_deg_s=999.,
                 alignment_status=0) for i in range(3)]
    rates = analytics.attitude_rates(rows)
    np.testing.assert_allclose(rates[1], [0., 0., math.radians(.1)], atol=1e-12)


@pytest.mark.parametrize('fit, expected', [
    ({'converged': True}, 'passed'),
    ({'converged': False, 'message': 'maximum evaluations reached'}, 'budget'),
    ({'converged': False, 'message': 'no decreasing feasible nonlinear step'}, 'stall'),
    ({'converged': False, 'message': 'stability verification failed'}, 'stability_check'),
    ({'converged': False, 'error': 'checksum failure'}, 'execution_error'),
    ({'converged': False, 'message': 'stationarity failed'}, 'stationarity_check'),
])
def test_stop_reason_is_not_a_shape_vote(fit, expected):
    assert analytics.stop_reason(fit) == expected


def test_overlapping_time_alone_does_not_establish_same_leg():
    a = dict(segment_id='a', receiver_fixes=fixes(180.))
    b = dict(segment_id='b', receiver_fixes=fixes(180.))
    report = analytics.shared_track(a, b)
    assert report['same_track_candidate']
    assert report['matched_receiver_epochs'] == 11
    for row in b['receiver_fixes']:
        row['longitude_rad'] += .1
    assert not analytics.shared_track(a, b)['same_track_candidate']


def test_rate_summary_uses_sum_of_increments_not_jittered_rate_mean():
    bins = {0: dict(count=200, raw=[0, 0, 0, 100, -200, 300], header_s=1.01,
                   first_s=.005, last_s=1., mount=np.eye(3).tolist())}
    report = analytics.raw_summary(bins, 8)
    factor=2**-18*180/math.pi*3600
    assert report['raw_native_mean_x_dph'] == pytest.approx(100*factor)
    assert report['header_native_mean_x_dph'] == pytest.approx(100*factor/1.01)
    assert report['raw_aircraft_mean_y_dph'] == pytest.approx(-200*factor)


def group4(time, imu_type=8):
    packet=bytearray(68)
    struct.pack_into('<4sHH3dBB6iBBB H',packet,0,b'$GRP',4,60,time,0.,0.,2,0,
                     0,0,0,100,-200,300,0,imu_type,2,0)
    packet[-2:]=b'$#'
    checksum=(-sum(x[0] for x in struct.iter_unpack('<H',packet)))&65535
    struct.pack_into('<H',packet,64,checksum)
    return bytes(packet)


def test_strict_scan_signed_sums_and_corrupt_input(tmp_path):
    path=tmp_path/'sample.013'
    source=b''.join(group4(t) for t in (0.,.005,.010,.015))
    path.write_bytes(source)
    windows=[dict(segment_id='sample',start_s=0.,end_s=.015,imu_type=8,signature='',time_types=2)]
    bins,nav,provenance=analytics.scan_windows(path,hashlib.sha256(source).hexdigest(),0,windows)
    assert nav==[]
    assert provenance['source_bytes']==272
    assert bins['sample'][0]['raw'][3:]==[300,-600,900]
    assert analytics.raw_summary(bins['sample'],8)['native_samples']==3
    corrupt=bytearray(source);corrupt[-20]^=1;path.write_bytes(corrupt)
    with pytest.raises(ValueError,match='checksum'):
        analytics.scan_windows(path,hashlib.sha256(corrupt).hexdigest(),0,windows)


def test_scan_rejects_gap_inside_selected_interval(tmp_path):
    path=tmp_path/'sample.013'
    source=group4(0.)+group4(.02)
    path.write_bytes(source)
    windows=[dict(segment_id='sample',start_s=0.,end_s=.03,imu_type=8,signature='',time_types=2)]
    with pytest.raises(ValueError,match='completeness'):
        analytics.scan_windows(path,hashlib.sha256(source).hexdigest(),0,windows)


def test_pair_differences_use_only_common_seconds():
    left={1:dict(duration_s=1.,raw_aircraft=[1e-5,2e-5,3e-5]),
          2:dict(duration_s=1.,raw_aircraft=[999.,999.,999.])}
    right={1:dict(duration_s=1.,raw_aircraft=[0.,0.,0.])}
    report=analytics.pair_difference(left,right)
    assert report['matched_raw_seconds']==1
    assert report['raw_aircraft_difference_x_dph']==pytest.approx(1e-5*analytics.DPH)

