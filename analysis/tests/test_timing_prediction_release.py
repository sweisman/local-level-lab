# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import pytest


@pytest.mark.parametrize('role,count,first,last,hours',[
    ('calibration',7176,281474977210656,281474977210954,240),
    ('validation',4344,281474977310656,281474977310836,144)])
def test_timing_release_cohorts_are_separate_complete_and_finite(role,count,first,last,hours):
    from lll import timing_prediction_release as release,compensated_prediction_release as previous
    from lll import prediction_calibration_study as original
    r=release.recipe(role);rows=release.tasks(role,'a'*64)
    assert r['seeds']==list(range(first,last+1)) and len(rows)==count
    assert len({t['identity'] for t in rows})==count
    assert (r['workers'],r['threads'],r['maximum_evaluations'],r['maximum_wall_s'],r['retries'])==(4,1,200,hours*3600,0)
    assert not set(r['seeds'])&set(release.EXCLUDED_SEEDS)
    assert not set(r['seeds'])&set(release.recipe('validation' if role=='calibration' else 'calibration')['seeds'])
    for p in (original,previous):
        assert set(p.recipe('calibration')['seeds']+p.recipe('validation')['seeds'])<=set(release.EXCLUDED_SEEDS)
    assert sum(t['limits']['native_calls'] for t in rows)==(430229904 if role=='calibration' else 260440176)
    assert sum(t['limits']['packet_visits'] for t in rows)==(2701855515528 if role=='calibration' else 1635571399032)
    assert {t['payload']['role'] for t in rows}=={role}


def test_timing_release_population_binds_method_without_changing_inputs():
    from lll import timing_prediction_release as r,prediction_calibration_study as original
    sources={k:'a'*64 for k in r.REQUIRED_SOURCES};env={'one_thread':True}
    p=r.population(sources,env)
    assert p['descriptor']['timing_method']=='native-clock-local-cells-v3'
    assert p['descriptor']['linear_solves_per_fit']==620
    seed=r.recipe('calibration')['seeds'][0];old=original._configured(seed);new=r.case_recipe(seed)
    assert new==dict(old,workers=4)
    changed=copy.deepcopy(sources);changed['analysis/lll/ilvis0_timing_stop.py']='b'*64
    assert r.population(changed,env)['sha256']!=p['sha256']
    assert r.population(sources,{'changed':True})['sha256']!=p['sha256']
    with pytest.raises(ValueError):r.case_recipe(281474977010692)


def test_timing_release_cannot_allow_changes_to_qualified_numerics_or_integrator():
    from lll import timing_prediction_release as release
    from lll.timing_optimizer_native_study import NUMERICAL
    from lll.coordinate_optimizer_study import ARITHMETIC
    assert not set(NUMERICAL+ARITHMETIC)&set(release.allowed_parent_updates)


@pytest.mark.parametrize('change',[None,'source','environment','count','pair','manifest','binding'])
def test_timing_release_requires_complete_hash_bound_optimizer_gate(change):
    from lll import timing_prediction_release as r
    from lll.timing_optimizer_native_study import NUMERICAL
    sources={k:'a'*64 for k in NUMERICAL};env={'same':True};binding=dict(sources=copy.deepcopy(sources),environment=env,
        completion=dict(manifest_sha256=r.GATE_MANIFEST,summary_sha256=r.GATE_SUMMARY))
    report=dict(verified=True,native_qualified=True,complete=48,selected=48,failures=[],
        rows=[dict(passed=True) for _ in range(48)],pairs=[dict(passed=True) for _ in range(24)],
        original_binding_replays_exact=True,manifest_sha256=r.GATE_MANIFEST,summary_sha256=r.GATE_SUMMARY)
    if change=='source':sources[next(iter(sources))]='b'*64
    elif change=='environment':env={'changed':True}
    elif change=='count':report['complete']=47
    elif change=='pair':report['pairs'][0]['passed']=False
    elif change=='manifest':report['manifest_sha256']='c'*64
    elif change=='binding':report['original_binding_replays_exact']=False
    if change is None:r.verify_optimizer_gate(report,binding,sources,env)
    else:
        with pytest.raises(ValueError,match='optimizer qualification'):r.verify_optimizer_gate(report,binding,sources,env)


def test_timing_release_handoff_cannot_use_either_earlier_cohort():
    from lll import timing_prediction_release as r,compensated_prediction_release as previous
    from lll.prediction_calibration_report import build_handoff,check_handoff
    report=dict(verified=True,role='calibration',total=7176,returned_outcomes=7176,population_sha256='a'*64,
        manifest_sha256='b'*64,summary_sha256='c'*64,validation_policy=r.recipe('validation'),
        draws=[dict(seed=s,role='calibration',population_sha256='a'*64,maximum_score=float(i)) for i,s in enumerate(r.recipe('calibration')['seeds'])])
    handoff=build_handoff(report,protocol=r.policy())
    assert handoff['calibration']['threshold']==298.
    assert check_handoff(handoff,population_sha256='a'*64,protocol=r.policy())==handoff
    with pytest.raises(ValueError):check_handoff(handoff,population_sha256='a'*64,protocol=previous.policy())


def test_timing_release_validation_requires_handoff_before_preparation(tmp_path):
    from lll.timing_prediction_release import prepare
    with pytest.raises(ValueError,match='calibration'):prepare(tmp_path,role='validation',qualification='not-yet-qualified')
    assert not (tmp_path/'data').exists()


def test_timing_release_delegates_shared_campaign_and_counted_scope(monkeypatch):
    from lll import timing_prediction_release as r,prediction_calibration_study as shared
    from lll.timing_optimizer_native_study import timing_case_context
    from lll.coordinate_optimizer_study import kernels
    from lll.studies.artifacts import encoded
    class Input:
        def read_bytes(self):return encoded({})
    class Context:
        manifest={'sources':{}}
        def input_path(self,key):return Input()
    task={};context=Context();seen=[]
    monkeypatch.setattr(r,'verify_optimizer_gate',lambda *a:None)
    def evaluate(t,c,**kw):
        assert t is task and c is context
        assert kw['case_context'] is timing_case_context and kw['kernel_provider'] is kernels
        assert kw['protocol'].audit_fit is r.audit_fit
        seen.append(True);return {'passed':False}
    monkeypatch.setattr(shared,'evaluate',evaluate)
    assert r.evaluate(task,context)=={'passed':False} and seen==[True]


@pytest.mark.parametrize('columns',[26,27])
def test_timing_release_audit_checks_real_journal_and_full_profile_columns(tmp_path,columns):
    from test_timing_optimizer_native_report import fixture
    from lll.timing_prediction_release import audit_fit
    from lll.studies.journal import Journal
    f=fixture()
    if columns==26:
        f['active_parameters'].pop();f['normalized_parameters'].pop()
        for row in f['local_linearization']['jacobian']:row.pop()
        for c in f['stability_probe']['cells']:c['point'].pop()
    j=Journal(tmp_path/'timing.sqlite',freeze='a'*64,limits={'case':{'linear_solves':620}})
    j.start('case');j.reserve('case','linear_solves');j.reserve('case','linear_solves')
    class Study:
        completion={'manifest_sha256':'a'*64}
        def artifact(self,identity,name,*,raw=False):
            assert identity=='case'
            if name=='fit.json':return f
            assert name=='timing-linear.sqlite' and raw
            return j.path.read_bytes()
    result=audit_fit(Study(),'case',{'profile':columns==27})
    assert result['passed'] and result['columns']==columns and result['linear_solves']==2
    j.reserve('case','linear_solves')
    with pytest.raises(ValueError,match='accounting'):audit_fit(Study(),'case',{'profile':columns==27})


def test_timing_release_prepare_delegates_to_shared_preparer(monkeypatch,tmp_path):
    from lll import timing_prediction_release as release,compensated_prediction_release as shared
    seen=[]
    def prepare(root,**kwargs):
        assert root is tmp_path and kwargs['definition'] is release
        assert kwargs['role']=='calibration' and kwargs['qualification']=='checked'
        seen.append(True);return {'prepared':True}
    monkeypatch.setattr(shared,'prepare',prepare)
    assert release.prepare(tmp_path,role='calibration',qualification='checked')=={'prepared':True}
    assert seen==[True]


@pytest.mark.parametrize('role,gib',[('calibration',55),('validation',35)])
def test_timing_release_disk_preflight_precedes_any_worker_or_charge(tmp_path,monkeypatch,role,gib):
    from types import SimpleNamespace
    from lll import timing_prediction_release as r,ilvis0_control_shards as runner
    import shutil
    minimum=gib*2**30;seen=[]
    assert r.recipe(role)['minimum_free_bytes']==minimum
    monkeypatch.setattr(shutil,'disk_usage',lambda path:SimpleNamespace(free=minimum-1))
    monkeypatch.setattr(runner,'launch',lambda *a,**kw:seen.append((a,kw)))
    with pytest.raises(ValueError,match='free disk'):r.launch(tmp_path,role=role,reserved_threads=0)
    assert not seen and not list(tmp_path.iterdir())
    monkeypatch.setattr(shutil,'disk_usage',lambda path:SimpleNamespace(free=minimum))
    r.launch(tmp_path,role=role,reserved_threads=0)
    assert seen==[((tmp_path/'data'/r.identity(role),),{'reserved_threads':0})]
