# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib
from types import SimpleNamespace

import pytest


def test_native_reference_count_preserves_four_and_accepts_explicit_six():
    from lll.timing_optimizer_native_study import reference_count
    assert reference_count(SimpleNamespace())==4
    assert reference_count(SimpleNamespace(expected_point_count=6))==6
    for bad in (True,0,-1,1.5,'6'):
        with pytest.raises(ValueError):reference_count(SimpleNamespace(expected_point_count=bad))


def test_native_reference_replay_audit_requires_all_six_and_preserves_four_default():
    from lll.timing_optimizer_native_report import replays_exact
    points=[dict(identity=str(i)) for i in range(6)];ids=[p['identity'] for p in points]
    assert replays_exact(points,ids,expected_count=6)
    assert not replays_exact(points,ids[:-1],expected_count=6)
    assert not replays_exact(points,ids[:-1]+[ids[0]],expected_count=6)
    assert replays_exact(points[:4],ids[:4]) and not replays_exact(points,ids)


def test_feasible_native_has_six_unchanged_cases_and_exact_finite_caps():
    from lll import timing_optimizer_native_study as old
    m=importlib.import_module('lll.timing_feasible_native_study');rows=m.tasks();cfg=m.configuration()
    assert len(rows)==6 and len({r['identity'] for r in rows})==6
    assert [r['payload'] for r in rows[:4]]==[r['payload'] for r in old.tasks()]
    assert [m.column_count(r['payload']['case']) for r in rows]==[27,27,27,27,26,26]
    assert {r['payload']['draw_seed'] for r in rows[4:]}=={281474977210667}
    assert {r['payload']['case']['start'] for r in rows[4:]}=={0,1}
    assert sum(r['limits']['native_calls'] for r in rows)==359724
    assert sum(r['limits']['packet_visits'] for r in rows)==2259076518
    assert (cfg['workers'],cfg['threads'],cfg['maximum_fits'],cfg['maximum_wall_s'])==(4,1,6,5400.)
    assert cfg['maximum_evaluations']==200 and cfg['linear_solves_per_fit']==620 and cfg['retries']==0


@pytest.mark.parametrize('change',[None,'count','pairs','source','environment','manifest','failed'])
def test_feasible_native_requires_new_full_analytical_gate(change):
    from lll.timing_optimizer_native_study import NUMERICAL
    m=importlib.import_module('lll.timing_feasible_native_study')
    sources={k:'a'*64 for k in NUMERICAL};env={'same':True};binding=dict(sources=copy.deepcopy(sources),environment=env)
    r=dict(verified=True,analytical_qualified=True,complete=44,fit_passed=36,controls_correct=8,
        failures=[],pairs=[dict(agreement=True) for _ in range(9)],
        manifest_sha256=m.GATE_MANIFEST,summary_sha256=m.GATE_SUMMARY)
    if change=='count':r['complete']=40
    elif change=='pairs':r['pairs'].pop()
    elif change=='source':binding['sources'][NUMERICAL[0]]='b'*64
    elif change=='environment':binding['environment']={}
    elif change=='manifest':r['manifest_sha256']='c'*64
    elif change=='failed':r['analytical_qualified']=False
    if change is None:m.verify_gate(r,binding,sources,env)
    else:
        with pytest.raises(ValueError):m.verify_gate(r,binding,sources,env)


def test_feasible_native_keeps_original_cohorts_separate():
    m=importlib.import_module('lll.timing_feasible_native_study')
    for t in m.tasks():
        p=t['payload'];old=dict(p,role='calibration',population_sha256=m.POPULATIONS[p['draw_seed']])
        assert m.computational_payload(old)==p
        old['population_sha256']='0'*64
        with pytest.raises(ValueError):m.computational_payload(old)


@pytest.mark.parametrize('declared',[4,6])
def test_six_reference_worker_checks_inventory_before_native_work_and_keeps_charges(tmp_path,monkeypatch,declared):
    import json
    from lll import timing_optimizer_native_study as worker,structured_noisy_study as shared
    from lll import airquantumgrav_inventory as inventory,ilvis0_control_shards as shards
    from lll.studies import source_binding
    from lll.studies.artifacts import encoded,digest
    from lll.studies.journal import Journal
    m=importlib.import_module('lll.timing_feasible_native_study');task=m.tasks()[4]
    env={'same':True};sources={k:'a'*64 for k in worker.NUMERICAL}
    gate=dict(verified=True,analytical_qualified=True,complete=44,fit_passed=36,controls_correct=8,
        failures=[],pairs=[dict(agreement=True) for _ in range(9)],
        manifest_sha256=m.GATE_MANIFEST,summary_sha256=m.GATE_SUMMARY)
    points=[dict(identity='old-'+str(i),payload=dict(t['payload'],role='calibration',
        population_sha256=m.POPULATIONS[t['payload']['draw_seed']]),saved_converged=i<2,
        artifacts={'input-binding.json':{'fixed':True}}) for i,t in enumerate(m.tasks())]
    manifest=dict(scope=m.SCOPE,sources=sources);(tmp_path/'manifest.json').write_bytes(encoded(manifest))
    values={'configuration':m.configuration(),'qualification-environment':env,
        'qualification-request':{'sources':sources},'analytical-gate':gate,
        'analytical-binding':dict(sources=sources,environment=env),'points':points}
    for name,value in values.items():(tmp_path/(name+'.json')).write_bytes(encoded(value))
    notes=[];calls=[]
    class Context:
        root=tmp_path;directory=tmp_path/'artifacts'
        def input_path(self,key):return tmp_path/(key+'.json')
        def save(self,name,value):(self.directory/name).write_bytes(encoded(value))
        def note_file(self,path):notes.append(path)
    context=Context();context.manifest=manifest
    monkeypatch.setattr(m,'expected_point_count',declared)
    monkeypatch.setattr(inventory,'environment',lambda:env)
    monkeypatch.setattr(source_binding,'verify',lambda *a,**k:None)
    monkeypatch.setattr(shards,'_check_continue',lambda *a:None)
    monkeypatch.setattr(worker,'protocol',lambda context,**kw:kw['reserve_linear'])
    def run(t,c,**kw):
        calls.append(True);assert kw['payload']['profile'] is False
        kw['training_provider']();c.save('fit.json',{'linear_solves':1})
        c.save('input-binding.json',{'fixed':True})
        return dict(passed=False,scientific_decision='abstain')
    monkeypatch.setattr(shared,'run_case',run)
    if declared==4:
        with pytest.raises(ValueError,match='original regression input binding'):m.evaluate(task,context)
        assert not calls and not notes
    else:
        out=m.evaluate(task,context);assert out['original_binding_replays']==1 and out['passed'] is False
        replay=json.loads((context.directory/'original-binding-replay.json').read_bytes())
        assert replay['original_identity']=='old-4' and replay['original_fit_converged'] is False
        assert notes==[context.directory/'timing-linear.sqlite']
        journal=Journal(notes[0],freeze=digest((tmp_path/'manifest.json').read_bytes()),
            limits={task['identity']:{'linear_solves':620}})
        assert journal.count(task['identity'],'linear_solves')==1


def test_native_auditor_reference_count_survives_original_point_variable_shadowing(monkeypatch):
    from lll import timing_optimizer_native_report as reporter,compensated_prediction_release as release
    from lll import structured_noisy_publication as publication,coordinate_optimizer_report as pairs
    from lll import airquantumgrav_inventory as inventory
    from lll.studies import closed
    spec=dict(start=0,profile=False,law='increment',model='sphere_rotating')
    task=dict(identity='unit',payload=dict(draw_seed=7,case=spec))
    fit=dict(linear_solves=0,converged=True,stability_probe={},residual_sum_squares=1.,evaluations=1,
             active_parameters=['time_offset'],normalized_parameters=[0.])
    point=dict(identity='old',payload=task['payload'],saved_converged=False,artifacts={})
    values={'configuration':{},'qualification-environment':{'unit':True},
            'analytical-gate':{},'analytical-binding':{},'points':[point]}
    artifacts={'fit.json':fit,'forecast.json':{},'training-observations.json':{},'input-binding.json':{},
        'original-binding-replay.json':dict(exact=True,original_labels_changed=False,
            original_identity='old',original_fit_converged=False)}
    class Saved:
        manifest=dict(scope='unit',tasks=[task],sources={});tasks={'unit':task};rows={'unit':{}}
        completion=dict(manifest_sha256='a'*64,summary_sha256='b'*64);summary=dict(elapsed_s=0.)
        def input(self,name):return values[name]
        def envelope(self,identity):return dict(artifacts={},result=dict(passed=True,
            prediction=dict(horizontal_rms_m=0.,vertical_rms_m=0.)))
        def artifact(self,identity,name):return artifacts[name]
        def close(self):pass
    monkeypatch.setattr(closed,'ClosedStudy',lambda *a:Saved())
    monkeypatch.setattr(release,'native_bindings',lambda s:{})
    monkeypatch.setattr(publication,'inspect_case',lambda *a,**k:dict(converged=True,accurate=True))
    monkeypatch.setattr(publication,'native_cache_entries',lambda *a,**k:{})
    monkeypatch.setattr(pairs,'compare_starts',lambda v:dict(passed=True))
    monkeypatch.setattr(inventory,'environment',lambda:{'unit':True})
    monkeypatch.setattr(reporter,'audit_verification',lambda *a,**k:dict(cells=0,passed=True))
    policy=SimpleNamespace(SCOPE='unit',configuration=lambda:{},tasks=lambda:[task],
        verify_gate=lambda *a:None,case_recipe=lambda s:{'limits':{'time_offset':.01}},computational_payload=lambda p:p,
        expected_point_count=1,column_count=lambda s:26)
    r=reporter.inspect('.', 'unused-unit-input',definition=policy)
    assert r['native_qualified'] and r['original_binding_replays_exact']
    assert r['rows'][0]['original_fit_converged'] is False
