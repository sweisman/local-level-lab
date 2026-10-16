# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
import hashlib
import struct
from test_applanix import packet
from lll import ilvis0_corpus_modeling as corpus
from lll import ilvis0_excitation_controls as controls, ilvis0_gps_sensitivity as sensitivity
from lll import ilvis0_exploratory as explore


def test_broyden_control_checks_actual_stationarity(tmp_path):
    base,point,_=controls.fixture(2.,'steady_orientation',sensitivity.assumptions()[0],
        truth={'gyro_bias_y':2e-6},limits={'gyro_bias_y':1e-5})
    result=corpus.bounded_fit(base,'flat_still',maximum_evaluations=100)
    assert result['evaluations']<=100
    assert result['converged']
    assert abs(result['parameters']['gyro_bias_y']-2e-6)<1e-8
    assert result['exact_projected_gradient_relative']<=result['stationarity_tolerance']
    assert result['scientific_decision']=='abstain'


def test_short_budget_does_not_claim_convergence():
    base,_,_=controls.fixture(2.,'brief_pitch',sensitivity.assumptions()[0],truth={'gyro_bias_y':2e-6})
    result=corpus.bounded_fit(base,'flat_still',maximum_evaluations=40)
    assert result['evaluations']<=40
    assert result['scientific_decision']=='abstain'
    assert not result['converged'] or result['exact_projected_gradient_relative']<=1e-4


def test_extract_rejects_unknown_units_before_scan():
    context={'timing':{'accepted':True},'inspection':{'imu_types':{'999':1}}}
    with pytest.raises(ValueError,match='unsupported/mixed'):corpus.extract('unused',context)


def test_extract_rejects_unknown_clock_before_scan():
    with pytest.raises(ValueError,match='UTC'):corpus.extract('unused',{'timing':{'accepted':False}})


def test_scale_families_stay_distinct():
    assert corpus.SCALES[8]==(2.**-18,2.**-14)
    assert corpus.SCALES[21]==(2.**-28,.3048*2.**-21)
    assert corpus.SCALES[6][0]!=corpus.SCALES[8][0]
    assert corpus.SCALES[6][1]!=corpus.SCALES[21][1]


def test_antipodal_force_initializer_is_proper_rotation():
    times=np.arange(1.,12.)
    gps=np.column_stack((.5+times*1e-5,np.zeros(len(times)),np.ones(len(times))*100))
    values=np.zeros((100,15));values[:,14]=.05
    initial,_=corpus.initialize(times,gps,values,'sphere_still')
    r=initial['attitude_body_to_ned']
    assert np.allclose(r.T@r,np.eye(3))
    assert np.linalg.det(r)==pytest.approx(1.)


def fixture_file(tmp_path,corrupt=False):
    packets=[]
    for k in range(24001):
        t=k*.005
        body=bytearray(56);struct.pack_into('<3d',body,0,t,t,0);body[24]=2
        struct.pack_into('<6i',body,26,0,0,-804,0,0,0);body[51]=8;body[52]=2
        packets.append(packet(4,body))
        if k%200==0:
            seconds=k//200;stamp=f'000{seconds//60}{seconds%60:02d}.00'
            text=f'GPGGA,{stamp},3000.000,N,00000.000,E,1,9,1.0,100,M,0,M,,'
            checksum=0
            for b in text.encode():checksum^=b
            sentence=f'${text}*{checksum:02X}\r\n'.encode()
            receiver=bytearray(34+len(sentence))
            while (len(receiver)+12)%4:receiver.append(0)
            struct.pack_into('<3d',receiver,0,t,t,0);receiver[24]=2
            struct.pack_into('<H',receiver,26,1);struct.pack_into('<H',receiver,32,len(sentence))
            receiver[34:34+len(sentence)]=sentence;packets.append(packet(10001,receiver))
    raw=b''.join(packets);path=tmp_path/'controlled.013';path.write_bytes(raw if not corrupt else raw[:-1])
    context={'timing':{'accepted':True,'gps_minus_utc_s':15},
             'inspection':{'imu_types':{'8':24001},'source_sha256':hashlib.sha256(raw).hexdigest()}}
    return path,context


def test_corpus_extract_native_gps_only_and_hash(tmp_path):
    path,context=fixture_file(tmp_path)
    values,times,gps,provenance=corpus.extract(path,context)
    assert len(values)>23000 and len(times)>110
    assert not provenance['group1_observations_used']
    assert not provenance['steady_level_flight_established']
    assert values[0,14]==pytest.approx(-804*2**-14)
    assert np.all(np.diff(times)>0)
    context['inspection']['source_sha256']='a'*64
    with pytest.raises(ValueError,match='hash'):corpus.extract(path,context)


def test_corpus_corrupt_original_is_rejected(tmp_path):
    path,context=fixture_file(tmp_path,corrupt=True)
    with pytest.raises(ValueError,match='truncated'):corpus.extract(path,context)


def test_corpus_resume_hash_and_attempts(tmp_path):
    from ilvis0_corpus_modeling_worker import cached,save,charge
    target=tmp_path/'result.json';save(target,{'value':1},'a'*64)
    assert cached(target,'a'*64)=={'value':1}
    target.write_text(target.read_text().replace('"value": 1','"value": 2'))
    with pytest.raises(ValueError,match='hash'):cached(target,'a'*64)
    starts=tmp_path/'starts.jsonl';tasks=['file::sphere_still']
    charge(starts,tasks[0],'a'*64,tasks);charge(starts,tasks[0],'a'*64,tasks)
    with pytest.raises(ValueError,match='allowance'):charge(starts,tasks[0],'a'*64,tasks)
    with pytest.raises(ValueError,match='corrupt'):charge(starts,tasks[0],'b'*64,tasks)


def test_carried_interrupted_start_stays_charged(tmp_path):
    from ilvis0_corpus_modeling_worker import charge
    prior=[{'identity':'file::sphere_still'}];tasks=['file::sphere_still']
    path=tmp_path/'starts.jsonl'
    charge(path,tasks[0],'a'*64,tasks,prior)
    with pytest.raises(ValueError,match='allowance'):charge(path,tasks[0],'a'*64,tasks,prior)


def test_recorded_result_writer_wraps_longitude_and_counts():
    from ilvis0_corpus_modeling_worker import recorded_diagnostics
    class Problem:
        gps=np.zeros((2,3))
        def predict(self,point,model):return np.tile([1.,2*np.pi+.01,3.],(2,1))
        def whiten(self,delta):return delta.ravel()
    p=Problem();result=recorded_diagnostics(p,p,p,[],'sphere_still',np.ones((2,3)))
    assert result['diagnostic_predictions']==2
    assert result['residual_rms_neu_m']==pytest.approx([1.,.01,3.])
    assert result['header_fixed_parameter_rms_neu_m']==pytest.approx([1.,.01,3.])
