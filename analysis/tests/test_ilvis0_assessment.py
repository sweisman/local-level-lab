# SPDX-License-Identifier: AGPL-3.0-or-later
import io
import json
import math
import struct

import numpy as np
import pytest

from lll import applanix as ap, ilvis0_assessment as audit
from test_applanix import packet, imu


def test_group2_layouts_raw_preservation_and_invalid_estimates():
    for size, label in ((76, 'inferred_legacy'), (88, 'documented_v6')):
        body = bytearray(size-12)
        struct.pack_into('<3d', body, 0, 5, 4, 0)
        body[24] = 2
        struct.pack_into('<9f', body, 26, *range(1, 10))
        if size == 88:
            struct.pack_into('<3f', body, 62, 10, 11, 12)
        frame = next(ap.frames(io.BytesIO(packet(2, body))))
        result = audit.navigation_uncertainty(frame)
        assert result['layout_status'].startswith(label)
        assert result['attitude_heading_rms_deg'] == 9
        assert result['usable'] and result['source_kind'] == 'fused_navigation_uncertainty'
        assert bytes.fromhex(result['payload_hex']) == frame.packet[34:-4]
        struct.pack_into('<f', body, 26, float('nan'))
        assert not audit.navigation_uncertainty(next(ap.frames(io.BytesIO(packet(2, body)))))['usable']
    body = bytearray(68)
    result = audit.navigation_uncertainty(next(ap.frames(io.BytesIO(packet(2, body)))))
    assert result['layout_status']=='unsupported_size_preserved' and not result['usable']


def gps_track(climb=0, turn=False, gap=False):
    t = np.arange(240.)
    north = 140*t if not turn else 20000*np.sin(t*140/20000)
    east = 0*t if not turn else 20000*(1-np.cos(t*140/20000))
    rows = [dict(utc_week_s=float(time), latitude_deg=math.degrees(n/6370000),
                 longitude_deg=math.degrees(e/6378137), orthometric_height_m=1000+climb*time,
                 geoid_separation_m=30) for time,n,e in zip(t,north,east)]
    return [r for r in rows if not 80 < r['utc_week_s'] < 130] if gap else rows


def test_gps_only_geometry_never_promotes_orientation_or_hides_gaps():
    straight = audit.gps_geometry(gps_track())
    assert straight['potential_windows'] and not straight['scientific_eligible']
    assert not straight['confirmed_level_flight']
    assert straight['potential_windows'][0]['median_speed_mps'] == pytest.approx(140, rel=.01)
    assert not audit.gps_geometry(gps_track(climb=2))['potential_windows']
    assert not audit.gps_geometry(gps_track(turn=True))['potential_windows']
    for window in audit.gps_geometry(gps_track(gap=True))['potential_windows']:
        assert window['end_s'] <= 80 or window['start_s'] >= 130
    assert not audit.gps_geometry(list(reversed(gps_track())))['potential_windows']


def samples(signs=(1,1,1), wrong_scale=1):
    rng = np.random.default_rng(152)
    gyro = rng.normal(size=(160,3))*1e6
    force = rng.normal(size=(160,3))*1e7
    gravity = rng.normal(size=(160,3))
    return [dict(gyro=g*np.array(signs), gyro_reference=g*audit.ANGLE_SCALE*wrong_scale+.001,
                 force=f*np.array(signs), acceleration_reference=f*audit.VELOCITY_SCALE+9.81*h+.01,
                 gravity=h, error=0, time=i) for i,(g,f,h) in enumerate(zip(gyro,force,gravity))]


def test_fixed_scales_independent_axis_discovery_and_holdout_mapping(monkeypatch):
    monkeypatch.setattr(audit.il, 'matched_samples', lambda *a,**k:(samples((1,-1,-1)),160))
    result = audit.validate_imu21('dummy')
    assert result['accepted']
    assert result['mapping']==dict(permutation=[0,1,2], signs=[1,-1,-1])
    assert result['gyro']['axes'][1]['source_axis']=='y'
    assert result['gyro']['axes'][1]['sign']==-1
    assert audit.VELOCITY_SCALE==.3048*2**-21
    assert audit.ANGLE_SCALE==2**-28
    wrong = audit.validate_imu21('dummy', dict(permutation=[0,1,2], signs=[1,1,1]))
    assert not wrong['accepted'] and not wrong['mapping_matches_fixed']
    monkeypatch.setattr(audit.il, 'matched_samples', lambda *a,**k:(samples(wrong_scale=1.006),160))
    assert not audit.validate_imu21('dummy')['accepted']


def test_fine_alignment_units_diagnostic_remains_scientifically_blocked(monkeypatch):
    def matched(*a,**k):
        return (samples(),160) if k.get('alignment_statuses')==(1,) else ([],0)
    monkeypatch.setattr(audit.il, 'matched_samples', matched)
    result = audit.validate_imu21('dummy')
    assert result['accepted'] and result['reference_status']=='fine_alignment_decoder_diagnostic_only'
    assert not result['earth_model_eligible']


def test_native_export_uses_actual_dt_preserves_signs_and_flags(monkeypatch):
    rows = [dict(imu(time=t), imu_type=21) for t in (1,1.005,1.015,1.010)]
    monkeypatch.setattr(audit.il, 'groups', lambda *a:iter(rows))
    monkeypatch.setattr(audit.ap, 'group4', lambda row:row)
    result = list(audit.physical_rows('dummy'))
    assert result[1]['raw_dtheta_y']==-3
    assert result[1]['dtheta_y_rad']==-3*2**-28
    assert result[1]['dv_y_mps']==-.3048*2**-21
    assert result[1]['angular_rate_y_rads']==pytest.approx(-3*2**-28/.005)
    assert result[0]['angular_rate_y_rads'] is None
    assert result[2]['angular_rate_y_rads'] is None
    assert result[3]['angular_rate_y_rads'] is None


def test_representatives_require_actual_dates_and_distinct_hashes():
    def row(task,date,hash):
        return dict(task_id=task, timing=dict(dates=[date]), screen=dict(state='retain'),
                    inspection=dict(versions={'v':1}, imu_types={'21':1}, rate_codes={'2':1}, source_sha256=hash))
    rows = [row('a','2009-01-01','h1'),row('b','2009-01-02','h1'),row('c','2009-01-01','h2')]
    assert audit.select_configurations(rows)[0]['representatives']==['a']
    rows.append(row('d','2009-01-03','h3'))
    assert audit.select_configurations(rows)[0]['representatives']==['a','d']


def test_resume_does_not_touch_sources_and_rejects_changed_inputs(tmp_path,monkeypatch):
    corpus, prior = tmp_path/'corpus', tmp_path/'prior'
    corpus.mkdir(); prior.mkdir()
    record = dict(task_id='one', filename='sample.013')
    (corpus/'records.jsonl').write_text(json.dumps(record)+'\n')
    (prior/'cleanup.jsonl').write_text('')
    context = dict(task_id='one', filename='sample.013', screen=dict(state='unresolved'),
                   inspection=dict(versions={'v':1}, imu_types={'6':1}, rate_codes={'2':1}, source_sha256='original'))
    (prior/'summary.json').write_text(json.dumps(dict(results=[context])))
    source = corpus/'one'/'decoded'/'sample.013.gz'; source.parent.mkdir(parents=True)
    source.write_bytes(b'original')
    calls = []
    def diagnostics(*a):
        calls.append(a)
        return dict(gps=dict(potential_windows=[]), earth_model_eligible=False), []
    monkeypatch.setattr(audit, 'read_diagnostics', diagnostics)
    output = tmp_path/'assessment'
    assert audit.run(corpus,prior,output)['unresolved_files']==1
    assert audit.run(corpus,prior,output)['unresolved_files']==1 and len(calls)==1
    assert source.read_bytes()==b'original'
    (prior/'cleanup.jsonl').write_text('changed')
    with pytest.raises(ValueError,match='mismatch'):
        audit.run(corpus,prior,output)
