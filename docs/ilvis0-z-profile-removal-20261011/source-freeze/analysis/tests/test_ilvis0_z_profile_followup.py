# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def worker(study='removal'):
    import ilvis0_z_profile_followup as w
    w.configure(study)
    return w


@pytest.mark.parametrize('study,target,profile', [
    ('removal','570b37d23af5e245dd461051',True),
    ('replication','d9d91c8edba5721931856fc9',False)])
def test_separate_exact_finite_scopes(study,target,profile):
    w=worker(study); scope=w.scope()
    assert len(scope['identities'])==len(set(scope['identities']))==27
    assert all(i.startswith(target+'::') for i in scope['identities'])
    assert scope['cases'][0]['profile'] is profile
    assert scope['maximum_native_sweeps']==5400 and scope['retry_reserve']==0
    assert scope['study']==study


def test_predeclared_recording_selection_and_completion_are_metadata_only():
    w=worker('replication'); chosen,reference=w.selection_and_reference()
    assert chosen['segment']['segment_id']=='d9d91c8edba5721931856fc9'
    assert chosen['segment']['duration_s']==439.
    assert chosen['segment']==reference['segment']
    assert chosen['filename']=='ILVIS0_applanix_57289_610_LVIS_38614965.013'


def test_removal_case_starts_at_zero_removal_not_half():
    w=worker()
    class B: active=('position_x','earth_removal','velocity_x')
    class P: bounds=B()
    np.testing.assert_array_equal(w.initial_point(P()),[0.,-1.,0.])


def test_removal_journal_never_reuses_other_stage_or_retries(tmp_path):
    w=worker(); identity=w.identities()[0]
    w.charge(tmp_path/'starts.jsonl',identity,'freeze')
    with pytest.raises(ValueError): w.charge(tmp_path/'starts.jsonl',identity,'freeze')
    w.configure('replication')
    with pytest.raises(ValueError): w.journal(tmp_path/'starts.jsonl','freeze')


def test_nonrun_modes_are_safe_and_busy_lock_blocks_prepare(tmp_path,monkeypatch):
    w=worker(); monkeypatch.setattr(w,'OUTPUT',tmp_path)
    monkeypatch.setattr(w.sys,'argv',['worker','--study','removal','--detach'])
    monkeypatch.setattr(w,'configure',lambda study:None)
    def forbidden(*args,**kwargs): raise AssertionError('busy worker cannot prepare or spawn')
    monkeypatch.setattr(w,'prepare',forbidden)
    with (tmp_path/'worker.lock').open('a') as lock:
        w.fcntl.flock(lock,w.fcntl.LOCK_EX|w.fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError): w.main()


def test_completed_followup_cannot_run_again(tmp_path,monkeypatch):
    w=worker();(tmp_path/'completion.json').write_text('{}')
    monkeypatch.setattr(w,'prepare',lambda *a:pytest.fail('completed study cannot prepare'))
    with pytest.raises(ValueError,match='completed'):w.run(tmp_path)


@pytest.mark.parametrize('study', ['removal','replication'])
def test_native_followup_keeps_fixed_coordinates_and_processing_case(tmp_path,monkeypatch,study):
    w=worker(study)
    from lll import ilvis0_geographic_controls as control
    f=control.fixture('sphere_rotating','nominal')
    theta=f['theta'].copy()
    theta[:,2]=(theta[:,2]-f['truth']['gyro_bias_z']*f['dt'])/(1+f['truth']['gyro_gain_z'])
    values=np.zeros((len(f['dt']),15))
    values[:,2]=f['dt'];values[:,9:12]=theta;values[:,12:15]=f['dv']
    cov=np.diag(np.tile(.01/f['metric'],len(f['gps_times']))**2)
    case=dict(w.scope()['cases'][0],limits=control.LIMITS)
    monkeypatch.setattr(w,'scope',lambda:{'cases':[case]})
    monkeypatch.setattr(w.base.corpus,'initialize',lambda *a:(f['initial'],9.81))
    kernel=w.base.explore.load_kernel(tmp_path/'kernel')[0]
    tangent=w.base.shape.load_tangent(tmp_path/'kernel')[0]
    identity=next(i for i in w.identities() if i.split('::')[2]=='sphere_rotating' and w.coordinate(i)==(0,0))
    result=w.fit_one(tmp_path,identity,values,f['gps_times'],f['gps'],
        {'first_interval_start_utc_s':0.},{'h1_v3_tau60':cov},1/f['metric'],kernel,tangent)
    assert 'error' not in result,result
    assert result['parameters']['gyro_gain_z']==result['parameters']['gyro_bias_z']==0
    assert ('earth_removal' in result['free_coordinate_order']) is case['profile']
    assert result['evaluations']==result['actual_tangent_sweeps']+2<=200
    assert max(result['residual_rms_neu_m'])<.002
    assert result['scientific_decision']=='abstain'


def test_missing_and_mismatched_authorization_rejects_compute(tmp_path):
    w=worker();(tmp_path/'manifest.json').write_text('{}')
    with pytest.raises(FileNotFoundError):w.check_authorization(tmp_path)
    (tmp_path/'authorization.json').write_text('{"maximum_starts":28}')
    with pytest.raises(ValueError):w.check_authorization(tmp_path)


def test_reference_snapshot_is_part_of_freeze(tmp_path,monkeypatch):
    w=worker();(tmp_path/'selection.json.gz').write_bytes(b'selection')
    (tmp_path/'reference.json').write_text('{}')
    manifest=dict(w.scope(),sources={},inputs={},environment={},
        selection_sha256=w.base.il.sha256(tmp_path/'selection.json.gz'),
        reference_sha256=w.base.il.sha256(tmp_path/'reference.json'))
    w.base.follow.atomic_json(tmp_path/'manifest.json',manifest)
    monkeypatch.setattr(w.base.runtime,'check_environment',lambda *a:None)
    assert w.verify(tmp_path)==manifest
    (tmp_path/'reference.json').write_text('{"changed":true}')
    with pytest.raises(ValueError,match='reference snapshot'):w.verify(tmp_path)
