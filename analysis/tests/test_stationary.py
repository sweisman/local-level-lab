# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from lll.format import Session, validate_manifest
from lll import stationary


def capture(rate=12.,drift=2.,latitude=5.):
    phases=[]; times=[]; values=[]
    for i,pos in enumerate('ABBAABBA'):
        start=i*120_000_000_000
        t=start+np.arange(120)*1_000_000_000
        phases.append(dict(name=f'ground.{pos}.{i+1}',start_ns=int(start),end_ns=int(start+120e9),still_s=120.))
        times.extend(t); values.extend(80+drift*t/1e9/3600+(rate if pos=='A' else -rate))
    t=np.array(times,dtype=np.int64); g=np.array(values)/stationary.RAD2DPH
    return Session(dict(kind='stationary',phases=phases,stationary={'protocol':stationary.PROTOCOL,'latitude_deg':latitude,'axis':'x'}),
        {'gyro':dict(t_ns=t,x=g,y=g*0,z=g*0),'accel':dict(t_ns=t,x=g*0,y=g*0,z=g*0+9.81)})


def test_signed_reversal_is_recovered_with_linear_drift_without_latitude_prior():
    a=stationary.summarize(capture(latitude=5.)); b=stationary.summarize(capture(latitude=80.))
    assert a['signed_rate_dph']==pytest.approx(12.)
    assert a['linear_offset_change_dph_per_hour']==pytest.approx(2.)
    assert a==b and a['scientific_decision']=='abstain'
    assert 'p_value' not in a and 'expected_rate' not in a


def test_null_and_negative_rates_are_not_turned_into_positive_magnitudes():
    assert stationary.summarize(capture(rate=0.))['signed_rate_dph']==pytest.approx(0.,abs=1e-10)
    assert stationary.summarize(capture(rate=-3.))['signed_rate_dph']==pytest.approx(-3.)


def test_missing_orientation_and_link_gap_withhold_rate():
    sess=capture(); sess.manifest['phases']=sess.manifest['phases'][:1]
    assert stationary.summarize(sess)['signed_rate_dph'] is None
    sess=capture(); sess.streams['gyro']['t_ns'][50]=sess.streams['gyro']['t_ns'][49]
    assert stationary.summarize(sess)['signed_rate_dph'] is None


def test_stationary_manifest_rejects_invalid_location_and_orientation():
    m=dict(schema_version=3,data_license='CC0-1.0',session_id='test',install_id='test',
        device={},phases=[],clock={'elapsed_ns':0,'utc_ms':0},imu={'variant':'spp'})
    m.update(kind='stationary',stationary={'protocol':'stationary-reversal-v1','axis':'z','latitude_deg':200})
    errors=validate_manifest(m,['manifest.json','imu.bin.gz'])
    assert any('stationary' in e for e in errors)
    m['stationary'].update(axis='x',latitude_deg=-45.,block_minutes=30.)
    assert validate_manifest(m,['manifest.json','imu.bin.gz'])==[]


def test_incomplete_saved_block_is_not_accepted_as_a_complete_recording():
    sess=capture(); sess.manifest['stationary']['block_minutes']=10
    assert stationary.summarize(sess)['signed_rate_dph'] is None


def test_sparse_endpoints_or_accel_timestamp_reversal_withhold_rate():
    sess=capture(); sess.streams['gyro']={k:v[::20] for k,v in sess.streams['gyro'].items()}
    assert stationary.summarize(sess)['signed_rate_dph'] is None
    sess=capture(); sess.streams['accel']['t_ns']=sess.streams['accel']['t_ns'].copy()
    sess.streams['accel']['t_ns'][50]=sess.streams['accel']['t_ns'][49]
    assert stationary.summarize(sess)['signed_rate_dph'] is None


def test_unknown_protocol_is_not_silently_decoded_as_the_current_one():
    sess=capture(); sess.manifest['stationary']['protocol']='unknown'
    assert stationary.summarize(sess)['signed_rate_dph'] is None


def test_actual_analysis_and_html_use_stationary_path_without_flight_fit(tmp_path):
    from lll.format import write_session
    from lll.witmotion import spp_packets
    from lll.analyze import analyze
    from lll.report import session_report
    m=dict(schema_version=3,data_license='CC0-1.0',session_id='test',install_id='test',
        device={},phases=[],clock={'elapsed_ns':0,'utc_ms':0},imu={'variant':'spp'},
        kind='stationary',stationary={'protocol':stationary.PROTOCOL,'axis':'x'})
    chunk=spp_packets(0x51,[[0,0,2048,0]]).tobytes()+spp_packets(0x52,[[0,0,0,0]]).tobytes()
    path=tmp_path/'stationary.zip'; write_session(path,m,{},imu=(np.array([1]),[chunk]))
    result=analyze(path)
    assert 'no_flight_phase' not in result['flags'] and 'fit' not in result
    assert result['stationary']['signed_rate_dph'] is None
    assert result['scientific_decision']=='abstain'
    assert 'Latitude and the expected Earth rate were not supplied' in session_report(result)
