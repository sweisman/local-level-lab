# SPDX-License-Identifier: AGPL-3.0-or-later
import math
import hashlib
import io
import struct
import numpy as np
import pytest
from lll import ilvis0_forward as f
from test_applanix import packet
from test_ilvis0_installation import message


def test_interval_integrals_against_independent_high_order_quadrature():
    nodes,weights=np.polynomial.legendre.leggauss(80);u=(nodes+1)/2;weights/=2
    for theta in ([0.,0.,0.],[1e-9,2e-9,-3e-9],[.12,-.24,.33],[1.,-.8,.4]):
        r,j,k=f.interval_matrices(theta)
        assert np.allclose(r.T@r,np.eye(3),atol=1e-13)
        # Independent rotation construction using axis eigenvectors is unnecessary;
        # quadrature checks both integration weights against the exponential itself.
        actual=[f.exp(np.array(theta)*s) for s in u]
        assert np.allclose(j,sum(w*a for w,a in zip(weights,actual)),atol=1e-12)
        assert np.allclose(k,sum(w*(1-s)*a for w,s,a in zip(weights,u,actual)),atol=1e-12)


def test_rotation_log_roundtrip_near_zero_and_pi_and_invalid_inputs():
    for v in ([1e-12,0,0],[.12,-.2,.3],[0,math.pi,0],[math.pi/np.sqrt(3)]*3):
        assert np.allclose(f.exp(f.log(f.exp(v))),f.exp(v),atol=1e-9)
    with pytest.raises(ValueError):f.log(np.diag([1,1,-1]))
    with pytest.raises(ValueError):f.exp([float('nan'),0,0])


def test_constant_force_and_clock_hypotheses():
    p=f.Preintegration()
    for i in range(200):p.step([0,0,0],[.005,0,0],.006)
    r=p.result()
    assert r['rotated_specific_force_integral_mps']==pytest.approx([1,0,0])
    assert r['specific_force_position_integral_m_by_clock']['header_elapsed']==pytest.approx([.6,0,0])
    assert r['specific_force_position_integral_m_by_clock']['nominal_200Hz']==pytest.approx([.5,0,0])
    assert not r['gravity_removed'] and not r['earth_rate_removed']


def test_composition_matches_packet_level_integration():
    all_steps=f.Preintegration();a=f.Preintegration();b=f.Preintegration()
    for i in range(400):
        theta=[.001,-.0003,.0004];dv=[.0002,.0001,-.049]
        all_steps.step(theta,dv,.005+(i%2)*1e-5)
        (a if i<200 else b).step(theta,dv,.005+(i%2)*1e-5)
    for clock in ('header_elapsed','nominal_200Hz'):
        composed=f.compose(a.result(),b.result(),clock);expected=all_steps.result()
        assert np.allclose(composed['delta_rotation'],expected['delta_rotation'],atol=1e-12)
        assert np.allclose(composed['rotated_specific_force_integral_mps'],expected['rotated_specific_force_integral_mps'],atol=1e-12)
        assert np.allclose(composed['specific_force_position_integral_m_by_clock'][clock],expected['specific_force_position_integral_m_by_clock'][clock],atol=1e-12)


def test_noncommuting_short_corrections_survive_zero_angle_sum():
    p=f.Preintegration()
    for theta in ([.01,0,0],[0,.01,0],[-.01,0,0],[0,-.01,0]):p.step(theta,[0,0,0],.005)
    r=p.result()
    assert np.linalg.norm(r['summed_body_angle_increments_rad'])==0
    assert r['finite_rotation_difference_from_summed_angles_rad']>9e-5


def test_one_second_tenth_degree_pitch_return_preserves_rotated_gravity():
    p=f.Preintegration();c=np.eye(3);g=np.array([0,0,-9.80665]);amplitude=np.deg2rad(.1)
    for i in range(200):
        theta=np.array([0.,amplitude/100*(1 if i<100 else -1),0.])
        middle=c@f.exp(theta/2);dv=middle.T@g*.005
        p.step(theta,dv,.005);c=c@f.exp(theta)
    r=p.result()
    assert np.linalg.norm(f.log(r['delta_rotation']))<1e-12
    assert np.allclose(r['rotated_specific_force_integral_mps'],g,atol=1e-9)
    assert r['rotated_force_difference_from_unrotated_sum_mps']>.008


def test_forward_inverse_joint_factor_with_coriolis_and_tilt():
    c=f.exp([.1,.2,.3]);v=np.array([120.,20.,-1.]);theta=[.001,.0002,-.0004];dv=[.003,.002,-.049]
    earth=[6e-5,0,-4e-5];transport=[1e-5,-2e-5,3e-5];gravity=[0,0,9.8];dt=.005
    c1,v1,_=f.local_step(c,v,theta,dv,dt,earth,transport,gravity)
    got=f.predicted_increments(c,c1,v,v1,dt,earth,transport,gravity,earth_retention=1,transport_retention=1)
    assert np.allclose(got[0],theta,atol=1e-13)
    assert np.allclose(got[1],dv,atol=1e-13)


def test_earth_processing_hypothesis_can_erase_stationary_earth_gyro_term():
    e=np.array([6e-5,0,-4e-5]);c=np.eye(3);v=np.zeros(3);dt=.005
    raw=f.predicted_increments(c,c,v,v,dt,e,np.zeros(3),[0,0,9.8],earth_retention=1,transport_retention=1)
    removed=f.predicted_increments(c,c,v,v,dt,e,np.zeros(3),[0,0,9.8],earth_retention=0,transport_retention=1)
    assert np.allclose(raw[0],e*dt,atol=1e-15)
    assert np.linalg.norm(removed[0])<1e-15
    with pytest.raises(ValueError,match='retention'):
        f.predicted_increments(c,c,v,v,dt,e,[0,0,0],[0,0,9.8],earth_retention=None,transport_retention=1)


def test_stationary_raw_sensor_gravity_and_earth_rate_hold_local_state():
    c=np.eye(3);v=np.zeros(3);e=np.array([6e-5,0,-4e-5]);g=np.array([0,0,9.8])
    for i in range(200):c,v,_=f.local_step(c,v,e*.005,-g*.005,.005,e,[0,0,0],g)
    assert np.allclose(c,np.eye(3),atol=1e-12) and np.linalg.norm(v)<1e-10


def test_model_metrics_and_disc_scale_are_explicit():
    phi=.8;rate=[1e-5,2e-5,-.1]
    globe=f.coordinate_kinematics('sphere_rotating',phi,1000,rate)
    assert np.allclose(globe['transport_rate_ned_rads'],f.models.transport_rate(phi,1000,*globe['velocity_ned_mps'][:2]))
    disc=f.coordinate_kinematics('flat_still',phi,1000,rate,disc_radius_m=6e6)
    assert disc['transport_rate_ned_rads']==pytest.approx([0,0,-rate[1]])
    assert not np.allclose(disc['velocity_ned_mps'],globe['velocity_ned_mps'])
    with pytest.raises(ValueError,match='explicit'):f.coordinate_kinematics('flat_still',phi,1000,rate)


def test_calibration_bounds_and_antenna_motion_are_enforced():
    b=f.CalibrationBounds(.001,.01,.001,.01);zero=[0,0,0]
    theta,dv=f.apply_calibration([.1,0,0],[0,0,.2],.005,zero,zero,zero,zero,zero,b)
    assert theta==pytest.approx([.1,0,0]) and dv==pytest.approx([0,0,.2])
    with pytest.raises(ValueError,match='outside'):b.validate([.002,0,0],zero,zero,zero,zero)
    with pytest.raises(ValueError,match='mounting'):b.validate(zero,zero,zero,zero,[.02,0,0])
    p,v=f.antenna_offsets(np.eye(3),[0,0,.1],[2,0,0])
    assert p==pytest.approx([2,0,0]) and v==pytest.approx([0,.2,0])


def test_receiver_endpoint_association_retains_time_offsets_and_rejects_duplicates():
    fixes=[dict(time1_s=10.+i,time_types=2,sod=10.+i,latitude_deg=60,longitude_deg=-30) for i in range(3)]
    factors=[dict(first_interval_start_s=10.002,last_time_s=10.998)]
    assert f.gps_endpoints(factors,fixes,15)==3
    assert factors[0]['receiver_start']['epoch_minus_factor_endpoint_s']==pytest.approx(-.002)
    assert factors[0]['receiver_end']['epoch_minus_factor_endpoint_s']==pytest.approx(.002)
    assert not factors[0]['receiver_epoch_coincidence_assumed']
    with pytest.raises(ValueError,match='duplicate'):f.gps_endpoints(factors,[fixes[0]]*2,15)


def test_joint_navigation_predictor_recovers_controlled_translation_and_tiny_pitch():
    initial=dict(attitude_body_to_ned=np.eye(3),velocity_ned_mps=[.5,0,0],latitude_rad=.8,longitude_rad=0.,height_m=20.)
    dt=.005;gravity=np.array([0.,0.,9.80665]);acceleration=np.array([.2,0,0]);c=np.eye(3);increments=[]
    amplitude=np.deg2rad(.1)
    for i in range(200):
        theta=np.array([0.,amplitude/100*(1 if i<100 else -1),0.])
        middle=c@f.exp(theta/2)
        increments.append((theta,middle.T@(acceleration-gravity)*dt,dt));c=c@f.exp(theta)
    states=list(f.forward_window(initial,increments,'flat_still',gravity,
        processing_hypothesis='unsubtracted_increment_hypothesis',disc_radius_m=6e6))
    assert len(states)==200
    assert states[-1]['velocity_ned_mps']==pytest.approx([.7,0,0],abs=1e-10)
    assert states[-1]['latitude_rad']==pytest.approx(.8+.6/6e6,abs=1e-13)
    assert states[-1]['height_m']==pytest.approx(20.,abs=1e-10)
    assert np.rad2deg(f.log(states[99]['attitude_body_to_ned']))[1]==pytest.approx(.1)
    assert np.linalg.norm(f.log(states[-1]['attitude_body_to_ned']))<1e-12
    with pytest.raises(ValueError,match='explicit'):
        list(f.forward_window(initial,increments,'flat_still',gravity,processing_hypothesis=None,disc_radius_m=6e6))


def test_globe_metric_navigation_stationary_control_and_inverse_coordinate_mapping():
    initial=dict(attitude_body_to_ned=np.eye(3),velocity_ned_mps=[0,0,0],latitude_rad=.8,longitude_rad=0.,height_m=20.)
    earth=f.models.earth_rate_sphere(.8);g=np.array([0,0,9.8]);dt=.005
    states=list(f.forward_window(initial,[(earth*dt,-g*dt,dt)]*200,'sphere_rotating',g,
        processing_hypothesis='unsubtracted_increment_hypothesis'))
    assert np.linalg.norm(states[-1]['velocity_ned_mps'])<1e-9
    assert states[-1]['latitude_rad']==pytest.approx(.8,abs=1e-14)
    assert np.allclose(states[-1]['attitude_body_to_ned'],np.eye(3),atol=1e-12)
    for model,radius in (('sphere_still',None),('flat_still',6e6)):
        rate=np.array([1e-5,2e-5,-.1]);v=f.coordinate_kinematics(model,.8,20,rate,radius)['velocity_ned_mps']
        assert np.allclose(f.coordinate_rates(model,.8,20,v,radius),rate)


def test_strict_source_packet_correspondence_and_hash_before_accepted_output(tmp_path):
    setup=message();signature=setup.packet[10:-4].hex();raw=bytearray(setup.packet)
    raw_values=[-1,2,-3,4,-5,6]
    for i in range(401):
        body=bytearray(56);struct.pack_into('<3d',body,0,.001+i*.005,0.,0.)
        body[24]=2;struct.pack_into('<6i',body,26,*raw_values);body[51]=6;body[52]=2
        raw.extend(packet(4,body))
    path=tmp_path/'control.013';path.write_bytes(raw);sha=hashlib.sha256(raw).hexdigest()
    expected=[dict(utc_second=1,complete_diagnostic_block=True,samples=200,
        raw_increment_sums=[200*v for v in raw_values],installation_signature=signature)]
    factors,provenance=f.preintegrate_file(path,sha,expected,0)
    assert provenance['raw_imu_packets']==401 and len(factors)==1
    assert factors[0]['samples']==200 and factors[0]['raw_increment_sums']==expected[0]['raw_increment_sums']
    assert not provenance['group1_observations_used']
    with pytest.raises(ValueError,match='SHA-256'):f.preintegrate_file(path,'0'*64,expected,0)
    with pytest.raises(ValueError,match='correspondence'):
        f.preintegrate_file(path,sha,[dict(expected[0],samples=199)],0)
    path.write_bytes(raw[:-1])
    with pytest.raises(ValueError,match='truncated'):f.preintegrate_file(path,sha,expected,0)


def test_resume_rejects_corrupted_artifacts_or_wrong_task_and_promotion(tmp_path):
    p=tmp_path/'factors.json.gz';f.observation.gzip_json(p,dict(factors=[]))
    report=dict(version=f.VERSION,task_id='a',scientific_eligible=False,earth_model_fit_attempts=0,
        factors_sha256=f.il.sha256(p),provenance=dict(source_sha256='s'))
    f.verify_factor_report(report,p,'a','s')
    with pytest.raises(ValueError,match='invalid'):f.verify_factor_report(report,p,'b','s')
    with pytest.raises(ValueError,match='invalid'):f.verify_factor_report(dict(report,scientific_eligible=True),p,'a','s')
    p.write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='mismatch'):f.verify_factor_report(report,p,'a','s')
