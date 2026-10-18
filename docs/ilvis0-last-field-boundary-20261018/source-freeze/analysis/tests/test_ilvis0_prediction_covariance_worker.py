# SPDX-License-Identifier: AGPL-3.0-or-later
import json
from pathlib import Path

import numpy as np
import pytest


def api():
    import ilvis0_prediction_covariance_worker as worker
    return worker


def ledger(tmp_path):
    from lll.ilvis0_sweep_journal import Ledger
    return Ledger(tmp_path,'freeze',['a','b'],fit_limit=2,diagnostic_limit=1)


def test_native_call_is_durably_charged_before_failure_and_not_retried(tmp_path):
    book=ledger(tmp_path);book.start('a')
    def failure():
        rows=book.read('sweeps')
        assert rows[-1]['identity']=='a' and rows[-1]['phase']=='fit'
        raise ValueError('native control failure')
    with pytest.raises(ValueError):book.call('a','fit','tangent',failure)
    assert book.count('a','fit')==1
    with pytest.raises(ValueError,match='retry'):book.start('a')
    book.call('a','fit','value',lambda:3)
    with pytest.raises(Exception,match='allowance'):book.call('a','fit','value',failure)
    assert book.count('a','fit')==2


def test_separate_diagnostic_limit_and_unknown_start_cannot_spend(tmp_path):
    book=ledger(tmp_path)
    with pytest.raises(ValueError):book.call('a','fit','tangent',lambda:1)
    with pytest.raises(ValueError):book.start('outside')
    book.start('a');book.call('a','diagnostic','value',lambda:1)
    with pytest.raises(Exception,match='allowance'):book.call('a','diagnostic','value',lambda:2)
    assert book.count('a','fit')==0


def test_corrupt_and_changed_freeze_journals_are_rejected(tmp_path):
    book=ledger(tmp_path);book.start('a')
    path=tmp_path/'starts.jsonl';row=json.loads(path.read_text());row['manifest_sha256']='changed'
    path.write_text(json.dumps(row)+'\n')
    with pytest.raises(ValueError):book.read('starts')
    path.write_text('{"partial":')
    with pytest.raises(ValueError):book.read('starts')


def test_reopened_ledger_retains_interrupted_charge(tmp_path):
    book=ledger(tmp_path);book.start('a');book.call('a','fit','tangent',lambda:1)
    resumed=ledger(tmp_path)
    assert resumed.count('a','fit')==1
    with pytest.raises(ValueError,match='retry'):resumed.start('a')
    resumed.start('b')
    assert len(resumed.read('starts'))==2


def test_axis_probes_record_infeasible_directions_and_keep_center():
    points,omitted=api().axis_probes(np.array([-1.,0.,.999]),.01)
    np.testing.assert_array_equal(points[0],[-1.,0.,.999])
    assert points.shape==(5,3) and np.all(abs(points)<=1.)
    assert omitted==[{'parameter':0,'direction':-1},{'parameter':2,'direction':1}]


def test_completed_worker_refuses_before_authorization_or_native_work(tmp_path):
    (tmp_path/'completion.json').write_text('{}')
    with pytest.raises(ValueError,match='completed'):api().run(tmp_path)


def test_worker_refuses_without_explicit_finite_allowance_before_data_access(tmp_path):
    with pytest.raises(ValueError,match='authorization'):api().run(tmp_path)
    assert not (tmp_path/'starts.jsonl').exists()


def test_output_lock_rejects_duplicate_worker(tmp_path):
    w=api()
    with w.worker_lock(tmp_path):
        with pytest.raises(BlockingIOError):
            with w.worker_lock(tmp_path):pass


def test_publication_does_not_launch_or_refit(monkeypatch,tmp_path):
    w=api();seen=[]
    monkeypatch.setattr(w.sys,'argv',['worker','--package-only'])
    monkeypatch.setattr(w,'publish',lambda output:seen.append(output))
    monkeypatch.setattr(w,'run',lambda *a:pytest.fail('publication cannot run fits'))
    monkeypatch.setattr(w.subprocess,'Popen',lambda *a,**k:pytest.fail('publication cannot launch'))
    w.main();assert seen==[w.OUTPUT]


def test_software_control_uses_real_native_calls_and_saved_prediction(tmp_path):
    report=api().software_control(tmp_path)
    assert report['maximum_truth_error_m']<.002
    assert report['fit_native_sweeps']>=4 and report['diagnostic_native_sweeps']==13
    assert report['training_epochs']==16 and report['prediction_epochs']==8
    assert report['observed_fit_starts']==0 and report['archive_records_loaded']==0
    assert report['prefix_agreement'] and report['epochs_written']==24
    assert Path(report['residual_path']).exists()


def test_full_task_writes_hashed_epochs_and_all_parameter_geometry(tmp_path):
    from lll import ilvis0_geographic_controls as geographic
    from lll.ilvis0_sweep_journal import Ledger
    w=api();f=geographic.fixture('sphere_rotating','nominal')
    kernels=(w.base.explore.load_kernel(tmp_path/'kernel')[0],w.base.shape.load_tangent(tmp_path/'kernel')[0])
    limits=dict(geographic.LIMITS)
    book=Ledger(tmp_path,'software',['fixture'])
    values=np.column_stack((np.zeros((len(f['dt']),2)),f['dt'],np.zeros((len(f['dt']),6)),f['theta'],f['dv']))
    cov=np.diag(np.tile(.01/f['metric'],24)**2)
    task=dict(identity='fixture',model='sphere_rotating',covariance='software',processing_case='software')
    fit=w.fit_task(tmp_path,task,dict(profile=False,limits=limits),values,f['gps_times'],f['gps'],
        cov,kernels,book,16,dict(first_interval_start_utc_s=0.))
    assert 'error' not in fit,fit.get('error')
    assert fit['fit_native_sweeps']<=200 and fit['diagnostic_native_sweeps']<=55
    assert fit['evaluations']==book.count('fixture','fit')
    assert fit['initialization_gps_epochs']==16
    assert fit['prediction_receiver_positions_used_in_training'] is False
    assert fit['uncertainty_geometry']['parameters']==6
    for file_key,hash_key in (('residual_file','residual_sha256'),('geometry_file','geometry_sha256')):
        assert w.base.il.sha256(tmp_path/fit[file_key])==fit[hash_key]


def test_changed_or_expanded_allowance_refused(tmp_path):
    w=api();(tmp_path/'manifest.json').write_text('{}')
    auth=dict(manifest_sha256=w.base.il.sha256(tmp_path/'manifest.json'),maximum_starts=12,
        maximum_native_sweeps=3061,retries=0,approval='explicit_user_approval')
    (tmp_path/'authorization.json').write_text(json.dumps(auth))
    with pytest.raises(ValueError,match='authorization'):w.authorization(tmp_path)
    auth['maximum_native_sweeps']=3060
    (tmp_path/'authorization.json').write_text(json.dumps(auth));w.authorization(tmp_path)
    (tmp_path/'manifest.json').write_text('{"changed":true}')
    with pytest.raises(ValueError,match='authorization'):w.authorization(tmp_path)


def test_prediction_profile_cannot_turn_failed_fit_into_preference():
    w=api();tasks=[];fits={}
    for cov in ('h1_v3_tau10','h1_v3_tau300'):
        for case in ('bias1_unsubtracted','bias1_profiled_removal'):
            for model,cost in [('sphere_rotating',1.),('sphere_still',2.),('flat_still',3.)]:
                identity=cov+'::'+case+'::'+model
                tasks.append(dict(identity=identity,covariance=cov,processing_case=case))
                fits[identity]=dict(model=model,converged=model!='flat_still',residual_sum_squares=cost,
                    prediction_diagnostics={'prediction':{'conditional_cost':cost}})
    result=w.profiles(tasks,fits,'prediction')
    assert result['conditional_shape_preference']=='unresolved'
    assert result['rotation_diagnostics'] is None


def completed_fixture(tmp_path):
    from lll.ilvis0_sweep_journal import Ledger
    w=api();(tmp_path/'manifest.json').write_text('{}')
    identities=[f'control-{i}' for i in range(12)]
    book=Ledger(tmp_path,w.base.il.sha256(tmp_path/'manifest.json'),identities)
    results={}
    for identity in identities:
        book.start(identity);book.call(identity,'fit','value',lambda:1)
        results[identity]=dict(fit_native_sweeps=1,diagnostic_native_sweeps=0)
    summary=dict(starts=12,native_sweeps=12,results=results)
    completion=dict(starts=12,native_sweeps=12,journal_hashes={
        name:w.base.il.sha256(tmp_path/name) for name in ('starts.jsonl','sweeps.jsonl')})
    return dict(proposal=dict(identities=identities)),summary,completion


def test_completion_reconciles_every_saved_fit_with_durable_charges(tmp_path):
    w=api();manifest,summary,completion=completed_fixture(tmp_path)
    w.check_accounting(tmp_path,manifest,summary,completion)
    summary['results']['control-0']['fit_native_sweeps']=2
    with pytest.raises(ValueError,match='accounting'):w.check_accounting(tmp_path,manifest,summary,completion)


def test_publication_rejects_changed_journal_even_if_total_counts_match(tmp_path):
    w=api();manifest,summary,completion=completed_fixture(tmp_path)
    path=tmp_path/'sweeps.jsonl';path.write_text(path.read_text().replace('"value"','"tangent"'))
    with pytest.raises(ValueError):w.check_accounting(tmp_path,manifest,summary,completion)
