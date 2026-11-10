# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fresh release metadata and source bridge; never launches a campaign."""
import copy
from dataclasses import replace
from types import SimpleNamespace
import pytest

from test_feasible_prediction_release import published_gate


def release():
    from lll.host_prediction_release import release
    return release


@pytest.mark.parametrize('role,count,first,last,hours',[
    ('calibration',7176,281474977610656,281474977610954,240),
    ('validation',4344,281474977710656,281474977710836,144)])
def test_host_release_cohorts_and_caps_are_complete_and_disjoint(role,count,first,last,hours):
    from lll import feasible_prediction_release as previous
    p=release();r=p.recipe(role);tasks=p.tasks(role,'a'*64)
    assert r['seeds']==list(range(first,last+1)) and len(tasks)==count
    assert (r['workers'],r['threads'],r['maximum_evaluations'],r['maximum_wall_s'],r['retries'])==(4,1,200,hours*3600,0)
    assert r['require_uninterrupted_cohort'] is True
    assert not set(r['seeds'])&set(p.EXCLUDED_SEEDS)
    assert not set(r['seeds'])&set(p.recipe('validation' if role=='calibration' else 'calibration')['seeds'])
    for phase in ('calibration','validation'):assert set(previous.recipe(phase)['seeds'])<=set(p.EXCLUDED_SEEDS)
    assert sum(t['limits']['native_calls'] for t in tasks)==(430229904 if role=='calibration' else 260440176)
    assert p.identity(role)=='prediction-'+role+'-host-20261030'


def test_host_release_preserves_the_qualified_physics_noise_and_stopping():
    from lll import prediction_calibration_study as original,feasible_prediction_release as previous
    p=release();seed=p.recipe('calibration')['seeds'][0]
    assert p.case_recipe(seed)==dict(original._configured(seed),workers=4)
    sources={n:'a'*64 for n in p.REQUIRED_SOURCES};env={'fixed':True}
    before=previous.population(sources,env)['descriptor'];after=p.population(sources,env)['descriptor']
    assert {k:v for k,v in after.items() if k not in ('version','execution_lifetime','interruption_reporting')}=={
        k:v for k,v in before.items() if k!='version'}
    assert after['linear_initialization']=='feasible_anchor' and after['linear_solves_per_fit']==620
    assert p.population(dict(sources,**{'analysis/lll/studies/prediction_release.py':'b'*64}),env)['sha256']!=p.population(sources,env)['sha256']
    for bad in (True,previous.recipe('calibration')['seeds'][0]):
        with pytest.raises(ValueError):p.case_recipe(bad)


@pytest.mark.parametrize('change',[None,'numeric_source','missing_source','reporting_source',
    'old_reporting_hash','environment','report','completion','binding_includes_updated_source'])
def test_host_release_source_bridge_accepts_only_the_exact_reporting_update(published_gate,change):
    p=release();report,binding=copy.deepcopy(published_gate);current=dict(binding['sources'])
    for name,old,new in p.reporting_updates:
        assert binding['sources'].pop(name)==old;current[name]=new
    if change=='numeric_source':current['analysis/lll/timing_cells.py']='0'*64
    elif change=='missing_source':binding['sources'].pop(next(iter(binding['sources'])))
    elif change=='reporting_source':current[p.reporting_updates[0][0]]='0'*64
    elif change=='old_reporting_hash':p=replace(p,reporting_updates=((p.reporting_updates[0][0],'0'*64,p.reporting_updates[0][2]),))
    elif change=='environment':binding['environment']={}
    elif change=='report':report['cases']=47
    elif change=='completion':binding['completion']['summary_sha256']='0'*64
    elif change=='binding_includes_updated_source':binding['sources'][p.reporting_updates[0][0]]=p.reporting_updates[0][1]
    if change is None:p.verify_optimizer_gate(report,binding,current,published_gate[1]['environment'])
    else:
        with pytest.raises(ValueError):p.verify_optimizer_gate(report,binding,current,published_gate[1]['environment'])


def test_host_release_cannot_exempt_a_numerical_file_from_qualification():
    p=release()
    with pytest.raises(ValueError):replace(p,reporting_updates=(('analysis/lll/timing_cells.py','a'*64,'b'*64),))


def test_host_release_reads_pinned_optimizer_evidence_and_checks_current_math(monkeypatch,published_gate):
    from pathlib import Path
    from lll import airquantumgrav_inventory as inventory,feasible_prediction_release as previous
    from lll.studies.artifacts import digest,encoded
    root=Path(__file__).resolve().parents[2];p=release()
    frozen_environment=published_gate[1]['environment']
    if inventory.environment()!=frozen_environment:
        with pytest.raises(ValueError,match='environment changed'):
            p.optimizer_report(root)
    monkeypatch.setattr(inventory,'environment',lambda:frozen_environment)
    report=p.optimizer_report(root)
    assert digest(encoded(report))==previous.GATE_REPORT_SHA256
    assert report['cases']==48 and report['start_pairs']==24 and report['original_input_replays']==4
    read=Path.read_bytes;target=root/'analysis/lll/timing_cells.py'
    monkeypatch.setattr(Path,'read_bytes',lambda path:b'changed mathematical source' if path==target else read(path))
    with pytest.raises(ValueError):p.optimizer_report(root)


def test_host_release_cannot_reuse_any_declared_cohort():
    from lll import feasible_prediction_release as previous
    with pytest.raises(ValueError):replace(release(),first_seeds=(previous.recipe('calibration')['seeds'][0],281474977710656))


def test_host_release_validation_requires_its_own_complete_handoff(tmp_path):
    from lll.prediction_calibration_report import build_handoff,check_handoff
    from lll import feasible_prediction_release as previous
    p=release()
    with pytest.raises(ValueError):p.prepare(tmp_path,role='validation',qualification='not-ready')
    assert not (tmp_path/'data').exists()
    value=dict(verified=True,role='calibration',total=7176,returned_outcomes=7176,
        population_sha256='a'*64,manifest_sha256='b'*64,summary_sha256='c'*64,
        validation_policy=p.recipe('validation'),draws=[dict(seed=s,role='calibration',
            population_sha256='a'*64,maximum_score=float(i)) for i,s in enumerate(p.recipe('calibration')['seeds'])])
    handoff=build_handoff(value,protocol=p.policy())
    assert handoff['calibration']['threshold']==298.
    with pytest.raises(ValueError):check_handoff(handoff,population_sha256='a'*64,protocol=previous.policy())
    value['cohort_interrupted']=True
    with pytest.raises(ValueError):build_handoff(value,protocol=p.policy())


@pytest.mark.parametrize('role,gib',[('calibration',55),('validation',35)])
def test_host_release_disk_and_recovery_guards_precede_launch(tmp_path,monkeypatch,role,gib):
    import shutil
    from lll import ilvis0_control_shards as runner
    from lll.studies import recovery
    p=release();seen=[]
    monkeypatch.setattr(shutil,'disk_usage',lambda _:SimpleNamespace(free=gib*2**30-1))
    monkeypatch.setattr(runner,'launch',lambda *args,**kw:seen.append((args,kw)) or {'started':True})
    with pytest.raises(ValueError,match='free disk'):p.launch(tmp_path,role=role,reserved_threads=0)
    assert not seen and not list(tmp_path.iterdir())
    monkeypatch.setattr(shutil,'disk_usage',lambda _:SimpleNamespace(free=gib*2**30))
    for state in ('closed','owned','cohort_unavailable','deadline_exhausted','stop_requested'):
        monkeypatch.setattr(recovery,'inspect',lambda *args,**kw:dict(state=state))
        with pytest.raises(ValueError):p.launch(tmp_path,role=role,reserved_threads=0)
        assert not seen
    monkeypatch.setattr(recovery,'inspect',lambda *args,**kw:dict(state='uncharged_work_available'))
    assert p.launch(tmp_path,role=role,reserved_threads=0)=={'started':True}
    assert seen==[((tmp_path/'data'/p.identity(role),),{'reserved_threads':0})]


def test_host_release_uses_the_shared_preparer_and_qualified_executor(tmp_path,monkeypatch):
    from lll import compensated_prediction_release as shared,prediction_calibration_study as executor
    from lll.timing_optimizer_native_study import timing_case_context
    from lll.studies.artifacts import encoded
    p=release();seen=[]
    monkeypatch.setattr(shared,'prepare',lambda root,**kw:seen.append(kw) or {'prepared':True})
    assert p.prepare(tmp_path,role='calibration',qualification='checked')=={'prepared':True}
    assert seen[0]['definition'] is p
    monkeypatch.setattr(type(p),'verify_optimizer_gate',lambda *args:None)
    class Input:
        def __init__(self,value):self.value=value
        def read_bytes(self):return encoded(self.value)
    class Context:
        manifest={'sources':{}}
        def input_path(self,key):return Input(p.source_updates if key=='parent-source-updates' else {})
    def evaluate(task,context,**kw):
        assert kw['case_context'] is timing_case_context
        assert kw['protocol'].recipe('calibration')==p.recipe('calibration')
        return {'passed':False}
    monkeypatch.setattr(executor,'evaluate',evaluate)
    assert p.evaluate({},Context())=={'passed':False}
