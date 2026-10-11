# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import numpy as np
import pytest


def worker():
    import ilvis0_integration_trial
    return ilvis0_integration_trial


def test_exact_six_identities_and_unchanged_scientific_bounds():
    trial=worker();scope=trial.scope()
    assert len(trial.identities())==len(set(trial.identities()))==6
    assert scope['cases']==trial.clock.base.primary_cases()
    assert scope['maximum_starts']==6 and scope['maximum_per_identity']==1
    assert scope['maximum_evaluations_per_start']==200 and scope['retry_reserve']==0
    assert scope['clock']=='header_elapsed' and scope['increment_convention']=='ordinary_rate_integrals'
    assert scope['mode']=='combined'
    assert all(i.startswith(trial.TARGET+'::') for i in trial.identities())


def test_journal_rejects_retries_extra_starts_and_changed_manifest(tmp_path):
    trial=worker();path=tmp_path/'starts.jsonl'
    for identity in trial.identities():trial.charge(path,identity,'freeze')
    assert len(trial.journal(path,'freeze'))==6
    before=path.read_bytes()
    for identity in (trial.identities()[0],'outside'):
        with pytest.raises(ValueError):trial.charge(path,identity,'freeze')
    with pytest.raises(ValueError):trial.journal(path,'different')
    assert path.read_bytes()==before


@pytest.mark.parametrize('key,value',(('maximum_starts',7),('maximum_per_identity',2),
    ('maximum_evaluations_per_start',201),('retry_reserve',1),('mode','baseline'),('clock','nominal_200Hz')))
def test_scope_rejects_expanded_or_changed_comparison(key,value):
    trial=worker();scope=trial.scope();scope[key]=value
    with pytest.raises(ValueError,match='scope'):trial.check_scope(scope)


def test_native_budget_counts_failed_and_diagnostic_passes():
    trial=worker()
    class Problem:
        bounds=object()
        def residual_tangent(self,*args):raise ValueError('bad numerical input')
        def predict(self,*args):return np.array([1.])
    p=Problem();budget=trial.NativeBudget(p,maximum=3)
    with pytest.raises(ValueError):budget.residual_tangent([], 'model')
    np.testing.assert_array_equal(budget.predict(p,[], 'model'),[1.])
    budget.predict(p,[], 'model')
    assert budget.used==3 and budget.tangents==1 and budget.values==2
    with pytest.raises(trial.clock.base.estimator.EvaluationLimit):budget.predict(p,[], 'model')
    assert budget.used==3


def test_completed_worker_cannot_prepare_or_load_native_kernel(tmp_path,monkeypatch):
    trial=worker();(tmp_path/'completion.json').write_text('{}')
    def forbidden(*args,**kwargs):raise AssertionError('completed comparison cannot restart')
    monkeypatch.setattr(trial,'prepare',forbidden)
    monkeypatch.setattr(trial.candidate,'load_kernel',forbidden)
    with pytest.raises(ValueError,match='completed'):trial.run(tmp_path)


def test_prepare_cli_cannot_fit_or_spawn(monkeypatch,tmp_path):
    trial=worker();prepared=[]
    monkeypatch.setattr(trial,'OUTPUT',tmp_path)
    monkeypatch.setattr(trial.sys,'argv',['trial','--prepare-only'])
    monkeypatch.setattr(trial,'prepare',lambda output:prepared.append(output))
    def forbidden(*args,**kwargs):raise AssertionError('prepare cannot fit or spawn')
    monkeypatch.setattr(trial,'run',forbidden)
    monkeypatch.setattr(trial.subprocess,'Popen',forbidden)
    trial.main();assert prepared==[trial.OUTPUT]


def test_publication_cli_cannot_extract_predict_or_fit(monkeypatch):
    trial=worker();published=[]
    monkeypatch.setattr(trial.sys,'argv',['trial','--package-only'])
    monkeypatch.setattr(trial,'publish',lambda output:published.append(output))
    def forbidden(*args,**kwargs):raise AssertionError('publication must read saved results only')
    monkeypatch.setattr(trial,'run',forbidden)
    monkeypatch.setattr(trial.clock.base.segments,'extract_segment',forbidden)
    monkeypatch.setattr(trial.candidate,'load_kernel',forbidden)
    trial.main();assert published==[trial.OUTPUT]


def test_cli_requires_an_explicit_action(monkeypatch):
    trial=worker();monkeypatch.setattr(trial.sys,'argv',['trial'])
    with pytest.raises(SystemExit):trial.main()


def test_snapshot_paths_preserve_duplicate_basenames():
    trial=worker()
    a=trial.snapshot_path(trial.OUTPUT,str((trial.ROOT/'docs/a/PLAN.md').resolve()))
    b=trial.snapshot_path(trial.OUTPUT,str((trial.ROOT/'docs/b/PLAN.md').resolve()))
    assert a!=b
    assert a==trial.OUTPUT/'source-freeze/docs/a/PLAN.md'


def test_qualification_environment_normalizes_labels_but_rejects_version_changes():
    trial=worker();current=trial.clock.base.runtime.numerical_environment()
    qualified={name:current[name] for name in ('python','numpy','scipy')}
    qualified.update(threads=current['thread_settings'],matplotlib='report-only')
    trial.check_qualification_environment(qualified)
    qualified['numpy']='different'
    with pytest.raises(ValueError,match='environment'):trial.check_qualification_environment(qualified)


def test_receipt_sources_and_artifacts_use_their_declared_roots(tmp_path):
    trial=worker();receipt={'sources':{'analysis/tests/a.py':'source'},'inputs':{'fits.csv':'artifact'}}
    assert trial.receipt_hashes(receipt,'sources',tmp_path)=={str(trial.ROOT/'analysis/tests/a.py'):'source'}
    assert trial.receipt_hashes(receipt,'inputs',tmp_path)=={str(tmp_path/'fits.csv'):'artifact'}
    receipt['inputs']={'../other.csv':'escape'}
    with pytest.raises(ValueError):trial.receipt_hashes(receipt,'inputs',tmp_path)


def test_synthetic_plumbing_keeps_same_clock_and_counts_predictions(tmp_path,monkeypatch):
    trial=worker();base=trial.clock.base
    from lll import ilvis0_geographic_controls as control
    f=control.fixture('sphere_rotating','nominal')
    values=np.zeros((len(f['dt']),15));values[:,2]=f['dt'];values[:,9:12]=f['theta'];values[:,12:15]=f['dv']
    sigma=np.tile(.01/f['metric'],len(f['gps_times']));cov=np.diag(sigma**2)
    covs={'h1_v3_tau60':cov,'h10_v30_tau300':cov}
    kernel=trial.candidate.load_kernel(tmp_path/'kernel')[0]
    monkeypatch.setattr(base.corpus,'initialize',lambda *args:(f['initial'],9.81))
    def known_calibration(problem,model,**kwargs):
        point=control.truth_point(f,problem);r,j,b=problem.residual_tangent(point,model)
        return dict(converged=True,model=model,normalized_parameters=point.tolist(),parameters=problem.bounds.decode(point),
            residual_sum_squares=float(r@r),evaluations=1,active_bounds=[],scientific_decision='abstain')
    monkeypatch.setattr(base.shape,'fit_shape_candidate',known_calibration)
    case=dict(case_id='test',profile=False,limits=control.LIMITS)
    provenance={'first_interval_start_utc_s':1000.}
    result=trial.fit_one(tmp_path,'synthetic',case,'sphere_rotating',values,f['gps_times'],f['gps'],
        provenance,covs,1/f['metric'],kernel)
    assert result['converged'] and result['evaluations']==3
    assert result['actual_tangent_sweeps']==1 and result['diagnostic_predictions']==2
    assert result['clock_hypothesis']=='header_elapsed'
    assert result['integration_mode']=='combined'
    assert max(result['original_integration_fixed_parameter_rms_neu_m'])>100*max(result['residual_rms_neu_m'])
    assert (tmp_path/result['residual_file']).exists()


@pytest.mark.parametrize('maximum',(0,201,1.5,True))
def test_invalid_native_allowance_is_rejected(maximum):
    trial=worker()
    with pytest.raises(ValueError):trial.NativeBudget(object(),maximum=maximum)


def test_interrupted_start_is_retained_without_retry(tmp_path):
    trial=worker();identity=trial.identities()[0];trial.charge(tmp_path/'starts.jsonl',identity,'freeze')
    result=trial.checked_cache(tmp_path,identity,'freeze')
    assert not result['converged'] and 'no retry' in result['error']
    assert result['charged_native_sweep_allowance']==200 and result['evaluations'] is None
    assert trial.checked_cache(tmp_path,identity,'freeze')==result
    assert len(trial.journal(tmp_path/'starts.jsonl','freeze'))==1


def test_uncharged_cache_cannot_be_used(tmp_path):
    trial=worker();identity=trial.identities()[0]
    trial.clock.base.save(tmp_path/(identity.replace('::','-')+'.json'),{'converged':True},'freeze')
    with pytest.raises(ValueError,match='uncharged'):trial.checked_cache(tmp_path,identity,'freeze')


def test_corrupt_saved_residual_cannot_be_reused(tmp_path):
    trial=worker();identity=trial.identities()[0];trial.charge(tmp_path/'starts.jsonl',identity,'freeze')
    path=tmp_path/'residual.csv.gz';path.write_bytes(b'original')
    result=dict(residual_file=path.name,residual_sha256=trial.clock.base.il.sha256(path))
    trial.clock.base.save(tmp_path/(identity.replace('::','-')+'.json'),result,'freeze')
    path.write_bytes(b'corruption')
    with pytest.raises(ValueError):trial.checked_cache(tmp_path,identity,'freeze')


def test_busy_worker_prevents_detach_before_preparation(tmp_path,monkeypatch):
    trial=worker();monkeypatch.setattr(trial,'OUTPUT',tmp_path)
    monkeypatch.setattr(trial.sys,'argv',['trial','--detach'])
    def forbidden(*args,**kwargs):raise AssertionError('busy worker cannot prepare or spawn')
    monkeypatch.setattr(trial,'prepare',forbidden);monkeypatch.setattr(trial.subprocess,'Popen',forbidden)
    with (tmp_path/'worker.lock').open('a') as lock:
        trial.fcntl.flock(lock,trial.fcntl.LOCK_EX|trial.fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):trial.main()


def test_publication_reads_only_audited_saved_results(tmp_path,monkeypatch):
    trial=worker();base=trial.clock.base;guide=tmp_path/'public'
    monkeypatch.setattr(trial,'GUIDE',guide)
    def forbidden(*args,**kwargs):raise AssertionError('publication cannot predict, fit or load native code')
    monkeypatch.setattr(trial.candidate,'load_kernel',forbidden)
    monkeypatch.setattr(base.shape,'fit_shape_candidate',forbidden)
    monkeypatch.setattr(base.segments,'extract_segment',forbidden)
    monkeypatch.setattr(trial,'verify',lambda output:{})
    base.follow.atomic_json(tmp_path/'manifest.json',{'sources':{}})
    digest=base.il.sha256(tmp_path/'manifest.json');rows=[]
    for case in base.primary_cases():
        fits=[]
        for index,model in enumerate(base.explore.MODELS):
            identity=trial.TARGET+'::'+case['case_id']+'::'+model
            trial.charge(tmp_path/'starts.jsonl',identity,digest)
            fit=dict(model=model,case_id=case['case_id'],converged=True,solver_reported_success=True,
                exact_projected_gradient_relative=1e-8,residual_sum_squares=float(index+1),
                residual_rms_neu_m=[.1,.2,.3],active_bounds=[],evaluations=3,
                parameters={'gyro_gain_z':0.,'gyro_bias_z':0.})
            base.save(tmp_path/(identity.replace('::','-')+'.json'),fit,digest);fits.append(fit)
        rows.append(dict(case_id=case['case_id'],fits=fits))
    summary=dict(cases=rows,header_reference={'cases':rows},
        integration_robustness_profile=base.shape.hierarchical_profile(rows))
    base.follow.atomic_json(tmp_path/'summary.json',summary)
    base.follow.atomic_json(tmp_path/'completion.json',dict(state='complete',starts=6,
        manifest_sha256=digest,summary_sha256=base.il.sha256(tmp_path/'summary.json')))
    (tmp_path/'selection.json.gz').write_bytes(b'frozen selection');(tmp_path/'source-freeze').mkdir()
    trial.publish(tmp_path)
    receipt=base.load(guide/'evidence-receipt.json');trial.clock.audit.verify_artifacts(guide,receipt)
    assert 'rotating globe' in (guide/'README.md').read_text()
    assert len((guide/'comparison.csv').read_text().splitlines())==7
