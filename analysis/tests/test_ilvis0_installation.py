# SPDX-License-Identifier: AGPL-3.0-or-later
import io
import gzip
import json
import struct
import numpy as np
import pytest
from lll import applanix as ap, ilvis0_installation as audit
from test_applanix import packet


def message(group=1, angles=(0,0,90), ref_angles=(0,0,0)):
    size=80 if group==1 else 92
    body=bytearray(size-12)
    struct.pack_into('<H',body,0,65535)
    body[2:5]=bytes((2,1,1))
    struct.pack_into('<3f',body,5,.14,.035,-.12)
    offset=29 if group==1 else 53
    struct.pack_into('<6f',body,offset,*(angles+ref_angles))
    return next(ap.frames(io.BytesIO(packet(group,body,tag=b'$MSG'))))


def test_legacy_and_documented_layouts_preserve_raw_and_have_distinct_authority():
    old=audit.installation_message(message())
    assert old['usable'] and old['layout_status'].startswith('empirically_inferred')
    assert old['candidate_reference_to_imu_m']==pytest.approx([.14,.035,-.12])
    assert np.allclose(old['imu_to_aircraft_rotation'],[[0,-1,0],[1,0,0],[0,0,1]],atol=1e-14)
    modern=audit.installation_message(message(20))
    assert modern['usable'] and modern['layout_status']=='documented_V6_MSG20'
    assert bytes.fromhex(old['packet_hex'])==message().packet
    other=ap.Frame(0,'$MSG',1,message(20).packet)
    assert not audit.installation_message(other)['usable']


def test_composed_rotations_explain_axis_change_and_reject_invalid_fields():
    rotated=audit.installation_message(message(angles=(90,90,0)))
    assert np.allclose(rotated['imu_to_aircraft_rotation'],[[0,1,0],[0,0,-1],[-1,0,0]],atol=1e-14)
    assert np.linalg.det(np.array(rotated['imu_to_aircraft_rotation']))==pytest.approx(1)
    assert not audit.installation_message(message(angles=(float('nan'),0,0)))['usable']
    assert not audit.installation_message(message(angles=(181,0,0)))['usable']


def samples(jitter=True):
    rng=np.random.default_rng(1316)
    raw=rng.normal(size=(160,6))*20
    raw[:,2]-=1450
    gravity=rng.normal(size=(160,3))*.1
    gravity[:,2]+=1
    matrix=audit.rotation((0,0,90))
    force=raw[:,:3]@matrix.T/audit.PERIOD_S
    gyro=raw[:,3:]@matrix.T/audit.PERIOD_S
    dt=.005+rng.normal(size=len(raw))*1e-5 if jitter else np.full(len(raw),.005)
    return [dict(time=float(i),source_packet_offset=200+i,raw_increments=r.tolist(),dt=float(d),
                 gravity=g.tolist(),acceleration_reference=(f*audit.VELOCITY_SCALE+9.81*g+.001).tolist(),
                 gyro_reference=(w*audit.ANGLE_SCALE+.0001).tolist())
            for i,(r,d,g,f,w) in enumerate(zip(raw,dt,gravity,force,gyro))]


def test_header_jitter_is_diagnostic_not_silently_replaced():
    setting=audit.installation_message(message()); setting['packet_offset']=100
    result=audit.compare_rates(samples(),[setting])
    assert result['cases']['fixed_200Hz_period_hypothesis']['accelerometer']['accepted']
    assert result['cases']['fixed_200Hz_period_hypothesis']['gyro']['accepted']
    assert not result['cases']['measured_header_interval']['accelerometer']['accepted']
    assert result['residual_improvement_factors'][2]>100
    assert not result['automatic_decoder_enabled'] and not result['scientific_eligible']
    assert result['header_intervals_preserved']


def test_samples_before_recorded_settings_do_not_inherit_later_mount():
    setting=audit.installation_message(message()); setting['packet_offset']=280
    result=audit.compare_rates(samples(False),[setting])
    assert result['before_first_recorded_setting']==80
    assert result['samples']==80
    assert result['cases']['measured_header_interval']['accelerometer']['accepted']
    setting['packet_offset']=500
    assert audit.compare_rates(samples(),[setting])['samples']==0


def test_full_scan_rejects_hash_mismatch_and_corrupt_packets(tmp_path):
    source=tmp_path/'bad.013'
    source.write_bytes(message().packet)
    with pytest.raises(ValueError,match='SHA-256'):
        audit.read_context(source,'wrong')
    data=bytearray(message().packet); data[18]^=1; source.write_bytes(data)
    with pytest.raises(ValueError,match='checksum'):
        audit.read_context(source,'wrong')


def test_sparse_navigation_cannot_support_a_high_rate_lever_correction():
    nav=[dict(time1_s=float(i),**{f'angular_rate_{a}_deg_s':0 for a in 'xyz'}) for i in range(160)]
    setting=audit.installation_message(message()); setting['packet_offset']=0
    result=audit.lever_comparison(nav,samples(),[setting])
    assert all(not c['supported'] for c in result['comparisons'])


def test_resume_preserves_original_and_checks_cached_artifacts(tmp_path,monkeypatch):
    corpus,prior=tmp_path/'corpus',tmp_path/'prior'
    corpus.mkdir();prior.mkdir()
    source=corpus/'a/decoded/a.013.gz';source.parent.mkdir(parents=True);source.write_bytes(b'preserved')
    (corpus/'records.jsonl').write_text(json.dumps(dict(task_id='a',filename='a.013'))+'\n')
    artifact=prior/'samples.json.gz'
    with gzip.open(artifact,'wt') as stream:json.dump(dict(samples=samples()),stream)
    row=dict(task_id='a',filename='a.013',matched_artifact=artifact.name,
             matched_artifact_sha256=audit.il.sha256(artifact),provenance=dict(source_sha256='original'))
    (prior/'summary.json').write_text(json.dumps(dict(state='complete',results=[row])))
    (prior/'manifest.json').write_text('{}')
    (prior/'axis-change-supplement.json').write_text(json.dumps(dict(results=[dict(task_id='a',
        chronological_first_half_mapping=dict(permutation=[1,0,2],signs=[-1,1,1]))])))
    setting=audit.installation_message(message());setting['packet_offset']=0
    calls=[]
    def read(*args):
        calls.append(args)
        return [],[setting],{},{}
    monkeypatch.setattr(audit,'read_context',read)
    monkeypatch.setattr(audit,'lever_comparison',lambda *args:{})
    output=tmp_path/'output'
    assert audit.run(corpus,prior,output)['errors']==0
    assert audit.run(corpus,prior,output)['errors']==0 and len(calls)==1
    assert source.read_bytes()==b'preserved'
    artifact.write_bytes(b'changed')
    with pytest.raises(ValueError,match='mismatch'):
        audit.run(corpus,prior,output)
