# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import pytest


def test_timing_matrix_keeps_all_old_computational_cases_and_exact_caps():
    from lll import timing_optimizer_matrix_study as matrix,coordinate_optimizer_study as original
    rows=matrix.tasks();old=original.tasks();cfg=matrix.configuration()
    assert len(rows)==48 and len({r['identity'] for r in rows})==48
    assert [{k:v for k,v in r.items() if k!='input_key'} for r in rows]==[
        {k:v for k,v in r.items() if k!='input_key'} for r in old]
    assert all(r['input_key']=='points' for r in rows)
    assert sum(r['limits']['native_calls'] for r in rows)==2877792
    assert sum(r['limits']['packet_visits'] for r in rows)==18072612144
    assert (cfg['workers'],cfg['threads'],cfg['maximum_wall_s'],cfg['maximum_fits'])==(4,1,7200.,48)
    assert cfg['maximum_evaluations']==200 and cfg['linear_solves_per_fit']==620 and cfg['retries']==0
    keys={matrix.pair_key(r) for r in rows}
    assert len(keys)==24 and all({r['payload']['case']['start'] for r in rows if matrix.pair_key(r)==k}=={0,1} for k in keys)


@pytest.mark.parametrize('change',[None,'count','pairs','source','environment','manifest','failed','replays'])
def test_timing_matrix_requires_complete_same_source_native_regression(change):
    from lll import timing_optimizer_matrix_study as m
    from lll.timing_optimizer_native_study import NUMERICAL
    sources={n:'a'*64 for n in NUMERICAL};env={'same':True};binding=dict(sources=copy.deepcopy(sources),environment=env)
    r=dict(verified=True,native_qualified=True,selected=4,complete=4,failures=[],original_binding_replays_exact=True,
        rows=[dict(passed=True) for _ in range(4)],pairs=[dict(passed=True) for _ in range(2)],
        manifest_sha256=m.GATE_MANIFEST,summary_sha256=m.GATE_SUMMARY)
    if change=='count':r['complete']=3
    elif change=='pairs':r['pairs'].pop()
    elif change=='source':binding['sources'][next(iter(sources))]='b'*64
    elif change=='environment':binding['environment']={}
    elif change=='manifest':r['manifest_sha256']='c'*64
    elif change=='failed':r['rows'][0]['passed']=False
    elif change=='replays':r['original_binding_replays_exact']=False
    if change is None:m.verify_gate(r,binding,sources,env)
    else:
        with pytest.raises(ValueError,match='native qualification'):m.verify_gate(r,binding,sources,env)


def test_matrix_worker_uses_shared_execution_and_explicit_optional_original_matches(monkeypatch):
    from lll import timing_optimizer_matrix_study as m,timing_optimizer_native_study as shared
    seen=[];task={};context=object()
    def run(t,c,*,definition):
        assert t is task and c is context;seen.append(definition);return {'delegated':True}
    monkeypatch.setattr(shared,'run_task',run)
    assert m.evaluate(task,context)=={'delegated':True} and seen==[m]
    assert m.require_original_match is False
    original={'draw_seed':281474976810725,'case':{},'role':'calibration','population_sha256':m.ORIGINAL_POPULATION}
    assert m.computational_payload(original)==dict(draw_seed=281474976810725,case={})
    original['population_sha256']='0'*64
    with pytest.raises(ValueError):m.computational_payload(original)


@pytest.mark.parametrize('columns',[26,27])
def test_native_matrix_audit_keeps_all_declared_profile_columns(columns):
    from test_timing_optimizer_native_report import fixture
    from lll.timing_optimizer_native_report import audit_verification
    f=fixture()
    if columns==26:
        f['active_parameters'].pop();f['normalized_parameters'].pop()
        for row in f['local_linearization']['jacobian']:row.pop()
        for cell in f['stability_probe']['cells']:
            cell['point'].pop()
            # The fixture shares its baseline Jacobian with the cell.
    assert audit_verification(f,expected_columns=columns)['columns']==columns
    with pytest.raises(ValueError):audit_verification(f,expected_columns=53-columns)


@pytest.mark.parametrize('matched',[False,True])
def test_matrix_shared_worker_preserves_original_matches_and_charges(tmp_path,monkeypatch,matched):
    import json
    from lll import timing_optimizer_matrix_study as policy,timing_optimizer_native_study as worker
    from lll import structured_noisy_study as shared,airquantumgrav_inventory as inventory,ilvis0_control_shards as shards
    from lll.studies import source_binding
    from lll.studies.artifacts import encoded,digest
    from lll.studies.journal import Journal
    work=policy.tasks();task=work[0] if matched else work[5];env={'fixed':True};sources={}
    points=[dict(identity='old-'+str(i),payload=dict(t['payload'],role='calibration',population_sha256=policy.ORIGINAL_POPULATION),
        saved_converged=False,artifacts={'input-binding.json':{'fixed':True}}) for i,t in enumerate(work[:4])]
    manifest=dict(scope=policy.SCOPE,sources=sources);(tmp_path/'manifest.json').write_bytes(encoded(manifest))
    values={'configuration':policy.configuration(),'qualification-environment':env,'qualification-request':{'sources':sources},
        'analytical-gate':{},'analytical-binding':{},'points':points}
    for k,v in values.items():(tmp_path/(k+'.json')).write_bytes(encoded(v))
    notes=[]
    class Context:
        root=tmp_path;directory=tmp_path/'artifacts'
        def input_path(self,key):return tmp_path/(key+'.json')
        def save(self,name,value):(self.directory/name).write_bytes(encoded(value))
        def note_file(self,path):notes.append(path)
    context=Context();context.manifest=manifest
    monkeypatch.setattr(inventory,'environment',lambda:env)
    monkeypatch.setattr(source_binding,'verify',lambda *a,**kw:None)
    monkeypatch.setattr(shards,'_check_continue',lambda *a:None)
    monkeypatch.setattr(policy,'verify_gate',lambda *a:None)
    monkeypatch.setattr(worker,'protocol',lambda context,**kw:kw['reserve_linear'])
    def run(t,c,**kwargs):
        assert kwargs['r']==policy.case_recipe(task['payload']['draw_seed'])
        kwargs['training_provider']();c.save('fit.json',{'linear_solves':1});c.save('input-binding.json',{'fixed':True})
        return dict(passed=False,scientific_decision='abstain')
    monkeypatch.setattr(shared,'run_case',run)
    result=policy.evaluate(task,context);replay=json.loads((context.directory/'original-binding-replay.json').read_bytes())
    assert result['passed'] is False and result['original_binding_replays']==int(matched)
    assert replay['matched_identities']==(['old-0'] if matched else [])
    assert replay['original_fit_converged'] is (False if matched else None)
    assert notes==[context.directory/'timing-linear.sqlite']
    journal=Journal(notes[0],freeze=digest((tmp_path/'manifest.json').read_bytes()),limits={task['identity']:{'linear_solves':620}})
    assert journal.count(task['identity'],'linear_solves')==1
