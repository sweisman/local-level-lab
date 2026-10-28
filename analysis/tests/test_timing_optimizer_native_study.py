# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
from types import SimpleNamespace
import pytest


def test_timing_native_definition_is_four_original_cases_with_unexpanded_shared_caps():
    from lll.timing_optimizer_native_study import tasks,configuration,case_recipe
    from lll.structured_noisy_training import limits
    work=tasks();cfg=configuration()
    assert len(work)==4 and len({v['identity'] for v in work})==4
    assert {t['payload']['draw_seed'] for t in work}=={281474977010692,281474977010693}
    assert {t['payload']['case']['start'] for t in work}=={0,1}
    assert all(t['payload']['case']['law']=='point' and t['payload']['case']['profile'] is True
        and t['payload']['case']['model']=='sphere_rotating' for t in work)
    assert sum(t['limits']['native_calls'] for t in work)==239816
    assert all(t['limits']==limits(case_recipe(t['payload']['draw_seed']),'point')[0] for t in work)
    assert (cfg['workers'],cfg['threads'],cfg['maximum_evaluations'],cfg['linear_solves_per_fit'])==(4,1,200,620)
    assert cfg['maximum_wall_s']==3600 and cfg['retries']==0


def gate_fixture():
    from lll.timing_optimizer_native_study import NUMERICAL,GATE_MANIFEST,GATE_SUMMARY
    sources={name:'a'*64 for name in NUMERICAL};env={'same':True}
    report=dict(verified=True,analytical_qualified=True,complete=40,fit_passed=32,controls_correct=8,
        failures=[],pairs=[{'agreement':True} for _ in range(8)],manifest_sha256=GATE_MANIFEST,summary_sha256=GATE_SUMMARY)
    binding=dict(sources=sources,environment=env)
    return report,binding,dict(sources),dict(env)


@pytest.mark.parametrize('change',['source','environment','missing','failure','pair','manifest'])
def test_timing_native_gate_rejects_changed_or_incomplete_analytical_evidence(change):
    from lll.timing_optimizer_native_study import verify_gate
    r,b,s,e=gate_fixture();verify_gate(r,b,s,e)
    if change=='source':s[next(iter(s))]='b'*64
    elif change=='environment':e['same']=False
    elif change=='missing':b['sources']={}
    elif change=='failure':r['fit_passed']=31
    elif change=='pair':r['pairs'][0]['agreement']=False
    else:r['manifest_sha256']='0'*64
    with pytest.raises(ValueError):verify_gate(r,b,s,e)


def test_timing_native_preparation_and_scope_guard_precede_scientific_work(tmp_path):
    from lll.timing_optimizer_native_study import prepare,evaluate
    with pytest.raises(ValueError,match='qualification'):prepare(tmp_path,qualification=None)
    with pytest.raises(ValueError,match='scope'):evaluate({},SimpleNamespace(manifest={'scope':'unapproved'}))
    assert not (tmp_path/'data').exists()


def test_original_calibration_provenance_is_validated_separately_from_computational_case():
    from lll.timing_optimizer_native_study import computational_payload,ORIGINAL_POPULATION,tasks
    case=tasks()[0]['payload'];original=dict(case,role='calibration',population_sha256=ORIGINAL_POPULATION)
    assert computational_payload(original)==case
    for changed in (dict(original,role='validation'),dict(original,population_sha256='0'*64),dict(original,unexpected=True)):
        with pytest.raises(ValueError):computational_payload(changed)


def test_native_timing_frozen_adapter_retains_exact_tasks_without_package_context():
    import importlib.util
    from pathlib import Path
    from lll import timing_optimizer_native_study as live
    spec=importlib.util.spec_from_file_location('_frozen_timing_native_adapter',Path(live.__file__))
    frozen=importlib.util.module_from_spec(spec);spec.loader.exec_module(frozen)
    assert frozen.tasks()==live.tasks() and frozen.configuration()==live.configuration()


def test_timing_native_bound_protocol_keeps_original_start_and_failed_fit(monkeypatch):
    from pathlib import Path
    from lll.timing_optimizer_native_study import protocol
    from lll.studies.artifacts import digest
    from lll import ilvis0_training_forecast as training,ilvis0_timing_stop as solver
    raw=b'def train_and_forecast(start):\n from lll.ilvis0_training_forecast import fit_training\n return fit_training("problem","model",start=start,maximum_evaluations=200,reserve=lambda **kw:None,stopping="near_zero")\n'
    source='analysis/lll/airquantumgrav_prediction.py';own='analysis/lll/timing_optimizer_native_study.py'
    class Context:
        manifest={'sources':{source:digest(raw),own:digest(Path('analysis/lll/timing_optimizer_native_study.py').read_bytes())}}
        def save(self,*a):pass
    seen=[];start=[.001,-.001]
    def fit(p,m,**kw):
        assert kw['start'] is start and kw['stopping']=='near_zero'
        return kw['solver_provider'](p,m,start=kw['start'],maximum_evaluations=kw['maximum_evaluations'])
    def solve(p,m,**kw):
        assert kw['start'] is start and kw['maximum_evaluations']==200
        kw['reserve_linear']();seen.append(1)
        return dict(converged=False,stability_policy={'old':True})
    monkeypatch.setattr(training,'fit_training',fit);monkeypatch.setattr(solver,'fit_candidate',solve)
    bound=protocol(Context(),reserve_linear=lambda:None,check_continue=lambda:None,
        raw=raw,expected_sha256=digest(raw))
    result=bound(start)
    assert seen==[1] and result['converged'] is False
    assert result['ordinary_stability_policy']=={'old':True}


@pytest.mark.parametrize('failure',[False,True])
def test_timing_native_worker_delegates_shared_runner_and_preserves_linear_charges(tmp_path,monkeypatch,failure):
    import json
    from pathlib import Path
    from lll import timing_optimizer_native_study as worker,structured_noisy_study as shared
    from lll import airquantumgrav_inventory as inventory
    from lll.studies import source_binding
    from lll.studies.artifacts import encoded
    from lll.studies.journal import Journal
    from lll import ilvis0_control_shards as shards
    task=worker.tasks()[0];gate,binding,sources,env=gate_fixture()
    points=[dict(identity='original-'+str(i),payload=dict(t['payload'],role='calibration',
        population_sha256=worker.ORIGINAL_POPULATION),saved_converged=i<2,
        artifacts={'input-binding.json':{'unchanged':True}}) for i,t in enumerate(worker.tasks())]
    manifest=dict(scope=worker.SCOPE,sources=sources);(tmp_path/'manifest.json').write_bytes(encoded(manifest))
    values={'configuration':worker.configuration(),'qualification-environment':env,'qualification-request':{'sources':sources},
        'analytical-gate':gate,'analytical-binding':binding,'points':points}
    for name,value in values.items():(tmp_path/(name+'.json')).write_bytes(encoded(value))
    notes=[]
    class Context:
        root=tmp_path;directory=tmp_path/'artifacts'
        def input_path(self,key):return tmp_path/(key+'.json')
        def save(self,name,value):(self.directory/name).write_bytes(encoded(value))
        def note_file(self,path):notes.append(path)
    ctx=Context();ctx.manifest=manifest
    monkeypatch.setattr(inventory,'environment',lambda:env)
    monkeypatch.setattr(source_binding,'verify',lambda *a,**kw:None)
    monkeypatch.setattr(shards,'_check_continue',lambda *a:None)
    def protocol(context,*,reserve_linear,check_continue):
        def training():reserve_linear()
        return training
    monkeypatch.setattr(worker,'protocol',protocol)
    seen=[]
    def run(work,context,**kw):
        assert work==task and kw['payload']==task['payload']['case']
        kw['training_provider']();seen.append(True)
        if failure:raise RuntimeError('controlled failure')
        ctx.save('fit.json',{'linear_solves':1});ctx.save('input-binding.json',{'unchanged':True})
        return dict(passed=False,scientific_decision='abstain')
    monkeypatch.setattr(shared,'run_case',run)
    if failure:
        with pytest.raises(RuntimeError,match='controlled failure'):worker.evaluate(task,ctx)
    else:
        result=worker.evaluate(task,ctx)
        assert result['passed'] is False and not result['original_labels_changed']
    assert seen==[True] and notes==[ctx.directory/'timing-linear.sqlite']
    from lll.studies.artifacts import digest
    journal=Journal(notes[0],freeze=digest((tmp_path/'manifest.json').read_bytes()),
        limits={task['identity']:{'linear_solves':620}})
    assert journal.count(task['identity'],'linear_solves')==1
