# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib
from pathlib import Path

import pytest


def release():return importlib.import_module('lll.feasible_prediction_release')


@pytest.mark.parametrize('role,count,first,last,hours',[
    ('calibration',7176,281474977410656,281474977410954,240),
    ('validation',4344,281474977510656,281474977510836,144)])
def test_feasible_release_has_disjoint_complete_cohorts_and_unchanged_caps(role,count,first,last,hours):
    from lll import timing_prediction_release as old,compensated_prediction_release as older
    from lll import prediction_calibration_study as original
    p=release();r=p.recipe(role);rows=p.tasks(role,'a'*64)
    assert r['seeds']==list(range(first,last+1)) and len(rows)==count
    assert (r['workers'],r['threads'],r['maximum_evaluations'],r['maximum_wall_s'],r['retries'])==(4,1,200,hours*3600,0)
    assert not set(r['seeds'])&set(p.EXCLUDED_SEEDS)
    assert not set(r['seeds'])&set(p.recipe('validation' if role=='calibration' else 'calibration')['seeds'])
    for prior in (original,older,old):
        for phase in ('calibration','validation'):assert set(prior.recipe(phase)['seeds'])<=set(p.EXCLUDED_SEEDS)
    assert sum(t['limits']['native_calls'] for t in rows)==(430229904 if role=='calibration' else 260440176)
    assert sum(t['limits']['packet_visits'] for t in rows)==(2701855515528 if role=='calibration' else 1635571399032)
    assert len({t['identity'] for t in rows})==count and p.identity(role)!=old.identity(role)


def test_feasible_release_binds_corrected_method_without_changing_physics_or_noise():
    from lll import prediction_calibration_study as original
    p=release();sources={n:'a'*64 for n in p.REQUIRED_SOURCES};env={'fixed':True};pop=p.population(sources,env)
    assert pop['descriptor']['linear_initialization']=='feasible_anchor'
    assert pop['descriptor']['linear_nonworsening_required'] is True
    assert pop['descriptor']['linear_solves_per_fit']==620
    seed=p.recipe('calibration')['seeds'][0]
    assert p.case_recipe(seed)==dict(original._configured(seed),workers=4)
    assert p.allowed_parent_updates==frozenset()
    assert p.population(dict(sources,**{'analysis/lll/timing_cells.py':'b'*64}),env)['sha256']!=pop['sha256']
    for bad in (True,281474977210667,281474977010692):
        with pytest.raises(ValueError):p.case_recipe(bad)


@pytest.fixture(scope='module')
def published_gate():
    import json
    from lll.studies.artifacts import ArchiveStore
    from lll.studies.closed import ClosedStudy
    root=Path(__file__).resolve().parents[2];a=ArchiveStore(root)
    report=json.loads(a.read('docs/timing-matrix-combined/artifacts/verified-report.json'));a.close()
    s=ClosedStudy(root,'docs/timing-matrix-completion')
    try:return report,dict(sources=s.manifest['sources'],environment=s.input('qualification-environment'),completion=s.completion)
    finally:s.close()


@pytest.mark.parametrize('change',[None,'source','source_missing','environment','count','pair','report_hash','completion','replays'])
def test_feasible_release_requires_exact_combined_gate_and_complete_source_binding(published_gate,change):
    p=release();report,binding=copy.deepcopy(published_gate);sources=dict(binding['sources']);env=copy.deepcopy(binding['environment'])
    if change=='source':sources[next(iter(sources))]='0'*64
    elif change=='source_missing':binding['sources'].pop(next(iter(binding['sources'])))
    elif change=='environment':env={}
    elif change=='count':report['cases']=47
    elif change=='pair':report['pairs'][0]['passed']=False
    elif change=='report_hash':report['native_calls']=1
    elif change=='completion':binding['completion']['summary_sha256']='0'*64
    elif change=='replays':report['original_input_replays']=3
    if change is None:p.verify_optimizer_gate(report,binding,sources,env)
    else:
        with pytest.raises(ValueError,match='optimizer qualification'):p.verify_optimizer_gate(report,binding,sources,env)


def test_feasible_release_validation_requires_its_own_complete_handoff(tmp_path):
    from lll.prediction_calibration_report import build_handoff,check_handoff
    from lll import timing_prediction_release as old
    p=release()
    with pytest.raises(ValueError,match='calibration'):p.prepare(tmp_path,role='validation',qualification='not-ready')
    assert not (tmp_path/'data').exists()
    report=dict(verified=True,role='calibration',total=7176,returned_outcomes=7176,population_sha256='a'*64,
        manifest_sha256='b'*64,summary_sha256='c'*64,validation_policy=p.recipe('validation'),
        draws=[dict(seed=s,role='calibration',population_sha256='a'*64,maximum_score=float(i)) for i,s in enumerate(p.recipe('calibration')['seeds'])])
    handoff=build_handoff(report,protocol=p.policy())
    assert check_handoff(handoff,population_sha256='a'*64,protocol=p.policy())==handoff
    with pytest.raises(ValueError):check_handoff(handoff,population_sha256='a'*64,protocol=old.policy())


def test_feasible_release_delegates_same_preparer_executor_and_counted_scope(monkeypatch,tmp_path):
    from lll import compensated_prediction_release as shared,prediction_calibration_study as executor
    from lll.timing_optimizer_native_study import timing_case_context
    p=release();seen=[]
    monkeypatch.setattr(shared,'prepare',lambda root,**kw:seen.append((root,kw)) or {'prepared':True})
    assert p.prepare(tmp_path,role='calibration',qualification='checked')=={'prepared':True}
    assert seen[0][1]['definition'] is p
    monkeypatch.setattr(p,'verify_optimizer_gate',lambda *a:None)
    from lll.studies.artifacts import encoded
    class Input:
        def read_bytes(self):return encoded({})
    class Context:
        manifest={'sources':{}}
        def input_path(self,key):return Input()
    def evaluate(t,c,**kw):
        assert kw['case_context'] is timing_case_context and kw['protocol'].recipe is p.recipe
        return {'passed':False}
    monkeypatch.setattr(executor,'evaluate',evaluate)
    assert p.evaluate({},Context())=={'passed':False}


@pytest.mark.parametrize('role,gib',[('calibration',55),('validation',35)])
def test_feasible_release_disk_check_precedes_launch_and_charges(monkeypatch,tmp_path,role,gib):
    import shutil
    from types import SimpleNamespace
    from lll import ilvis0_control_shards as runner
    p=release();seen=[]
    monkeypatch.setattr(shutil,'disk_usage',lambda path:SimpleNamespace(free=gib*2**30-1))
    monkeypatch.setattr(runner,'launch',lambda *a,**kw:seen.append(a) or {'started':True})
    with pytest.raises(ValueError,match='free disk'):p.launch(tmp_path,role=role,reserved_threads=0)
    assert not seen and not list(tmp_path.iterdir())
    monkeypatch.setattr(shutil,'disk_usage',lambda path:SimpleNamespace(free=gib*2**30))
    assert p.launch(tmp_path,role=role,reserved_threads=0)=={'started':True}
    assert seen==[(tmp_path/'data'/p.identity(role),)]
