# SPDX-License-Identifier: AGPL-3.0-or-later
import hashlib
import struct
import numpy as np
import pytest

from lll import ilvis0_clock_audit as audit


def test_timestamp_drift_does_not_establish_increment_period():
    times=100000.+np.arange(2001)*.005*1.00005
    row=audit.timing_statistics(times,.005)
    assert row['intervals']==2000
    assert row['elapsed_minus_nominal_s']==pytest.approx(.0005,abs=1e-10)
    assert row['mean_period_error_ppm']==pytest.approx(50.,abs=1e-4)
    assert row['integration_period_identified'] is False


def test_fixed_period_packet_jitter_has_zero_net_drift_but_variable_intervals():
    times=np.arange(2001)*.005
    times[1:-1]+=.0002*(-1.)**np.arange(1,2000)
    row=audit.timing_statistics(times,.005)
    assert row['elapsed_minus_nominal_s']==pytest.approx(0.)
    assert row['interval_std_us']>300
    assert row['interval_lag_one_correlation']<-.99


@pytest.mark.parametrize('times',[[0.,.005,.005],[0.,.005,.004],
    [0.,float('nan'),.01],[0.,.005,.025]])
def test_invalid_or_gapped_science_timing_is_rejected(times):
    with pytest.raises(ValueError): audit.timing_statistics(times,.005)


@pytest.mark.parametrize('kind',['fixed_period_jitter','variable_period','clock_scale'])
def test_independently_generated_clock_controls_recover_the_known_period(kind):
    row=audit.clock_control(kind)
    assert row['passed']
    assert row['correct_clock_max_velocity_error_mps']<1e-10
    assert row['correct_clock_max_angle_error_rad']<1e-10
    assert row['wrong_clock_max_velocity_error_mps']>1e-5
    assert row['wrong_clock_max_angle_error_rad']>1e-7


def test_variable_rotation_separates_gain_offset_but_not_free_clock_scale():
    row=audit.calibration_control(varying=True)
    assert row['known_clock_rank']==2 and row['free_clock_rank']==2
    assert row['free_clock_parameters']==3
    assert row['least_squares_prediction_error']<1e-12
    assert row['qr_prediction_error']<1e-12
    assert row['passed']


def test_constant_rotation_does_not_separate_gain_and_offset():
    row=audit.calibration_control(varying=False)
    assert row['known_clock_rank']==row['free_clock_rank']==1
    assert row['unique_gain_and_offset_recovered'] is False
    assert row['passed']


def test_stationary_gravity_effect_matches_independent_closed_form_clock_scale():
    n=2400; period=.005; epsilon=50e-6; gravity=9.81
    times=np.arange(n+1)*period*(1+epsilon)
    row=audit.stationary_timing_effect(times,period)
    assert row['header_final_velocity_mps']==pytest.approx(gravity*epsilon*n*period,abs=1e-10)
    assert row['header_final_height_m']==pytest.approx(.5*gravity*epsilon*(n*period)**2*(1+epsilon),abs=1e-10)
    assert row['mean_gravity_correction_mps2']==pytest.approx(gravity/(1+epsilon)-gravity)
    assert row['mean_corrected_max_height_m']<1e-10
    assert row['uses_observed_accelerometer_values'] is False


def packet(time,secondary,rate=2,time_types=2):
    data=bytearray(68)
    struct.pack_into('<4sHH3dBB6i',data,0,b'$GRP',4,60,time,secondary,0.,time_types,0,
        -1,2,-3,4,-5,6)
    data[59]=21; data[60]=rate; data[-2:]=b'$#'
    checksum=-sum(v[0] for v in struct.iter_unpack('<H',data))&65535
    struct.pack_into('<H',data,64,checksum)
    return bytes(data)


def sample(tmp_path,data=None):
    data=data or b''.join(packet(1.+i*.005,3.+i*.005) for i in range(3))
    path=tmp_path/'control.013'; path.write_bytes(data)
    context=dict(timing=dict(gps_minus_utc_s=0),inspection=dict(source_sha256=hashlib.sha256(data).hexdigest()))
    segment=dict(start_s=1.,end_s=1.01,raw_guard_s=0.,signature='',imu_type=21,time_types=2,segment_id='control')
    return path,context,segment


def test_strict_selected_scan_reproduces_offsets_and_both_clocks(tmp_path):
    report,rows=audit.scan_selected(*sample(tmp_path))
    assert report['intervals']==2
    assert report['first_packet_offset']==68 and report['last_packet_offset']==136
    assert report['secondary_timing']['intervals']==2
    assert report['primary_minus_secondary_elapsed_s']==pytest.approx(0.,abs=1e-12)
    assert rows[0]['raw_dv_x']==-1 and rows[0]['raw_dtheta_y']==-5


@pytest.mark.parametrize('damage',['checksum','truncation','hash','rate','time_basis'])
def test_selected_scan_rejects_corruption_or_configuration_change(tmp_path,damage):
    path,context,segment=sample(tmp_path)
    if damage=='checksum':
        data=bytearray(path.read_bytes()); data[40]^=1; path.write_bytes(data)
    elif damage=='truncation': path.write_bytes(path.read_bytes()[:-1])
    elif damage=='hash': context['inspection']['source_sha256']='0'*64
    else:
        path.write_bytes(packet(1.,3.)+packet(1.005,3.005,rate=1 if damage=='rate' else 2,
            time_types=1 if damage=='time_basis' else 2)+packet(1.01,3.01))
    with pytest.raises(ValueError): audit.scan_selected(path,context,segment)
