# SPDX-License-Identifier: AGPL-3.0-or-later
import hashlib
import json
import numpy as np
import pytest
from lll import applanix as ap, ilvis0_observation as obs
from test_applanix import packet


def row(time, offset=0):
    return dict(time1_s=time,time_types=2,packet_offset=offset,imu_type=6,rate_code=2,
                data_status=0,imu_status=0,**dict(zip(ap.RAW_FIELDS,[-1,2,-3,4,-5,6])))


def setting(signature='a'):
    return dict(usable=True,signature=signature,imu_to_aircraft_rotation=np.eye(3).tolist())


def test_integer_increment_accumulation_and_clock_hypotheses_preserve_jitter():
    a=obs.IncrementBlocks(0)
    for i in range(400):
        a.feed(row(.001+i*.005+(i%2)*.00002,i*68),setting())
    a.finish()
    assert len(a.blocks)==2
    assert not a.blocks[0]['complete_diagnostic_block']
    b=a.blocks[1]
    assert b['complete_diagnostic_block'] and b['samples']==200
    assert b['raw_increment_sums']==[-200,400,-600,800,-1000,1200]
    assert b['dtheta_sum_rad_hypothesis'][0]==800*obs.installation.ANGLE_SCALE
    assert b['angular_rate_native_rads_by_clock_hypothesis']['header_elapsed'][0]==pytest.approx(800*obs.installation.ANGLE_SCALE/b['header_interval_sum_s'])
    assert b['first_packet_offset']==200*68


def test_gaps_and_mount_changes_are_flagged_without_bridging_or_repair():
    a=obs.IncrementBlocks(0)
    for i in range(400):
        if i==230:
            continue
        a.feed(row(.001+i*.005),setting('a' if i<300 else 'b'))
    a.finish()
    assert set(a.blocks[1]['flags'])=={'unsupported_increment_interval','installation_change_inside_block'}
    assert not a.blocks[1]['angular_rate_native_rads_by_clock_hypothesis']
    assert a.blocks[1]['samples']==199


def test_time_reversals_types_and_unsupported_sensor_are_rejected():
    a=obs.IncrementBlocks(0);a.feed(row(1),None)
    with pytest.raises(ValueError,match='non-increasing'):
        a.feed(row(1),None)
    with pytest.raises(ValueError,match='basis'):
        a.feed(dict(row(1.005),time_types=1),None)
    with pytest.raises(ValueError,match='configuration'):
        a.feed(dict(row(1.005),imu_type=21),None)


def test_projection_handles_dependent_columns_and_preserves_orthogonal_signal():
    y=np.array([1.,-1.,1.,-1.])
    residual,rank=obs.projection(y,np.column_stack([np.ones(4),2*np.ones(4),np.zeros(4)]))
    assert rank==1 and np.allclose(residual,y)
    assert np.linalg.norm(obs.projection(y,np.eye(4))[0])<1e-14


def test_each_motion_run_gets_its_own_bias_and_drift():
    t=np.arange(20,dtype=float);segment=np.repeat([0,1],10)
    anchor=np.zeros((20,3))
    y=np.column_stack([np.where(segment==0,1.+t,100.-t),np.ones(20),np.zeros(20)]).ravel()
    x=obs.nuisance_matrix(t,anchor,segment,'constant_and_linear_drift')
    assert np.linalg.norm(obs.projection(y,x)[0])<1e-10
    assert np.linalg.norm(obs.projection(y,obs.nuisance_matrix(t,anchor,segment,'constant_bias'))[0])>1


def test_geometry_depends_on_receiver_positions_and_completeness_not_gyro(monkeypatch):
    # Reduce only the unit-test envelope; production keeps the complete preregistered grid.
    monkeypatch.setitem(obs.POLICY,'attitude_envelope_deg',[0])
    monkeypatch.setitem(obs.POLICY,'crab_envelope_deg',[0])
    fixes=[dict(utc_week_s=float(i),latitude_deg=60+i*.001,longitude_deg=-30+i*.002) for i in range(20)]
    blocks=[dict(complete_diagnostic_block=True,first_time_s=float(i),last_time_s=i+.99,
                 installation_signature='a',raw_increment_sums=[0]*6) for i in range(20)]
    first=obs.geometry(fixes,blocks)
    for b in blocks:
        b['raw_increment_sums']=[10**12]*6
    assert obs.geometry(fixes,blocks)==first
    assert first['moving_samples']>10 and not first['raw_rate_values_used_in_geometry']
    assert first['unconstrained_aircraft_motion']['retained_fraction_all_pairs']==0
    assert not first['conditional_geometry']['decision_enabled']
    assert obs.geometry([fixes[0]]*3,blocks)['samples']==0


def test_longitude_wrap_and_missing_receiver_epochs_are_not_interpolated(monkeypatch):
    monkeypatch.setattr(obs,'contrast_envelope',lambda *args:dict(samples=len(args[0])))
    fixes=[dict(utc_week_s=float(i),latitude_deg=60.,longitude_deg=(179.995+i*.001+180)%360-180) for i in range(25) if i not in (10,11,12,13)]
    blocks=[dict(complete_diagnostic_block=True,first_time_s=float(i),last_time_s=i+.99,
                 installation_signature='a') for i in range(25)]
    result=obs.geometry(fixes,blocks)
    assert result['samples']<21
    assert result['speed_proxy_range_mps'][1]<100


def test_resume_checks_compressed_increment_integrity_and_scientific_flags(tmp_path):
    artifact=tmp_path/'b.json.gz';obs.gzip_json(artifact,dict(raw=[-1,2]))
    report=dict(version=obs.VERSION,scientific_eligible=False,earth_model_fit_attempts=0,
                blocks_sha256=obs.il.sha256(artifact))
    obs.verify_report(report,artifact)
    original=artifact.read_bytes();obs.gzip_json(artifact,dict(raw=[-1,2]));assert artifact.read_bytes()==original
    artifact.write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='hash'):
        obs.verify_report(report,artifact)
    with pytest.raises(ValueError,match='invalid'):
        obs.verify_report(dict(report,scientific_eligible=True),artifact)


def test_scan_rejects_source_hash_and_corruption_before_geometry(tmp_path):
    path=tmp_path/'sample.013';path.write_bytes(packet(7,bytes(4)))
    with pytest.raises(ValueError,match='SHA-256'):
        obs.scan(path,'0'*64,15)
    path.write_bytes(b'bad')
    with pytest.raises(ValueError,match='header'):
        obs.scan(path,hashlib.sha256(b'bad').hexdigest(),15)
