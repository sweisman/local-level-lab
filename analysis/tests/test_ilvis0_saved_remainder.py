# SPDX-License-Identifier: AGPL-3.0-or-later
from copy import deepcopy
import pytest
from test_ilvis0_saved_prediction_audit import joint_future_fixture


def saved_fixture():
    region,saved=joint_future_fixture();saved['bound'].update(
        time_s=saved['time_s'],
        position_unshared_remainder=[.125]*3,force_unshared_remainder=[0.]*3,
        lever_unshared_remainder=[0.]*3)
    return region,saved


def test_saved_remainder_rebuilds_all_columns_and_reserves_each_exact_check(monkeypatch):
    from lll import ilvis0_saved_remainder as candidate
    from lll import ilvis0_direct_interface as interface
    region,saved=saved_fixture();before=deepcopy(saved);new=deepcopy(saved['bound'])
    new['unshared_remainder']=[.0625]*3;charges={};artifacts={}
    monkeypatch.setattr(interface,'matched_bounds',lambda old,updated:dict(passed=True))
    def reserve(**values):
        for key,value in values.items():charges[key]=charges.get(key,0)+value
    result=candidate.rebuild_prediction(region,saved,new,reserve=reserve,
        save=lambda name,value:artifacts.update({name:value}))
    assert saved==before
    assert result['audit']['width_m']==[10.8125,.4375,.1875]
    assert charges==dict(matched_comparisons=1,lp_proposals=6,exact_supports=24)
    assert artifacts['future.json']['bound']==new
    assert list(artifacts).index('future.json')<list(artifacts).index('independent-audit.json')


def test_saved_remainder_rejects_changed_maps_before_support_calls(monkeypatch):
    from lll import ilvis0_saved_remainder as candidate
    from lll import ilvis0_direct_interface as interface
    region,saved=saved_fixture();charges=[]
    monkeypatch.setattr(interface,'matched_bounds',lambda *_:dict(passed=False))
    with pytest.raises(ValueError,match='matched'):
        candidate.rebuild_prediction(region,saved,saved['bound'],
            reserve=lambda **values:charges.append(values),save=lambda *_:None)
    assert charges==[dict(matched_comparisons=1)]


@pytest.mark.parametrize('change',['domain','time','source','future'])
def test_saved_remainder_rejects_mixed_inputs_before_any_work(change):
    from lll import ilvis0_saved_remainder as candidate
    region,saved=saved_fixture();new=deepcopy(saved['bound']);charges=[]
    new['time_s']=saved['time_s']
    if change=='domain':saved['upper']=[2.]*51
    elif change=='time':new['time_s']+=1.
    elif change=='source':new['source_id']='wrong'
    else:region['future_truth_used']=True
    with pytest.raises(ValueError):
        candidate.rebuild_prediction(region,saved,new,
            reserve=lambda **values:charges.append(values),save=lambda *_:None)
    assert not charges


def worker_context(tmp_path):
    import json
    from types import SimpleNamespace
    from lll.ilvis0_saved_remainder import recipe,limits
    values=dict(main=dict(identity='case',model=0,profile=False,reference=dict(binding='reference'),
        prior_width_m=[1000.]*3),case={},truth=dict(identity='case',reference_binding='reference',
        known_truth_retained=True,maximum_exact_training_slack='-1',future_truth_m=['0']*3))
    for key,value in values.items():(tmp_path/(key+'.json')).write_text(json.dumps(value))
    manifest=dict(limits=dict(maximum_wall_s=120))
    (tmp_path/'manifest.json').write_text(json.dumps(manifest));saved={};noted=[];opened=[]
    def input_path(key='main'):
        opened.append(key);return tmp_path/(key+'.json')
    context=SimpleNamespace(root=tmp_path,directory=tmp_path/'artifacts',manifest=manifest,input_path=input_path,
        save=lambda key,value:saved.update({key:value}),note_file=lambda path:noted.append(path),
        charge=lambda **values:None)
    task=dict(identity='case',payload=dict(recipe(),model=0,profile=False,limits=limits(),
        case_key='case',truth_key='truth',compiler='test-compiler'))
    return task,context,saved,noted,opened


@pytest.mark.parametrize('width,useful',[(1.,True),(100.,False)])
def test_worker_preserves_width_gate_and_opens_truth_only_after_prediction(tmp_path,monkeypatch,width,useful):
    from lll import ilvis0_saved_remainder as candidate
    task,context,saved,noted,opened=worker_context(tmp_path)
    def calculate(material,case,spec,*,reserve,charge,save,**_):
        assert 'truth' not in opened
        reserve(**{k:v for k,v in candidate.limits().items() if k!='truth_audits'})
        future=dict(envelope=dict(lower=[-width/2]*3,upper=[width/2]*3))
        save('future.json',future)
        return dict(future=future,audit=dict(passed=True,width_m=[width]*3),
            conditional_remainder=dict(original_remainder=10.,remainder_upper=2.))
    monkeypatch.setattr(candidate,'calculate',calculate)
    result=candidate.evaluate(task,context)
    assert result['passed'] is useful and result['numerical_checks_passed']
    assert result['future_truth_contained'] and result['work']==candidate.limits()
    assert opened==['main','case','truth'] and noted
    assert list(saved).index('future.json')<list(saved).index('truth-audit.json')


def test_worker_keeps_charged_failure_and_does_not_open_truth_or_retry(tmp_path,monkeypatch):
    from lll import ilvis0_saved_remainder as candidate
    from lll.studies.journal import inspect_snapshot
    from lll.studies.artifacts import digest
    task,context,saved,noted,opened=worker_context(tmp_path)
    def failure(*_,reserve,**__):
        reserve(reference_setups=1);raise ValueError('deliberate software rejection')
    monkeypatch.setattr(candidate,'calculate',failure)
    with pytest.raises(ValueError,match='deliberate'):candidate.evaluate(task,context)
    assert 'truth' not in opened and noted
    assert inspect_snapshot(noted[0].read_bytes(),digest((tmp_path/'manifest.json').read_bytes()))['starts']==1
    with pytest.raises(ValueError,match='already charged'):candidate.evaluate(task,context)


def test_actual_short_saved_pipeline_reuses_training_and_native_values(tmp_path,monkeypatch):
    from pathlib import Path
    import numpy as np
    from lll import ilvis0_saved_remainder as candidate
    from lll.ilvis0_sharded_native import plain
    from test_ilvis0_staged_native import test_native_stages_keep_prior_constraints_and_then_predict_without_future_observations as baseline
    from test_ilvis0_regrouped_history import native
    class Capture:
        def __init__(self):self.saved={};self.calls=[]
        def reserve(self,**_):pass
        def before_bound(self,_):pass
        def save(self,name,value):self.saved[name]=plain(value)
        def native(self,kernel,config,theta,dv,dt,time_s,point):
            value,jac=native(kernel,config,theta,dv,dt,time_s,point)
            self.calls.append((time_s,np.array(point),value,jac));return value,jac
    capture=Capture();baseline(tmp_path/'base',runtime=capture)
    records=capture.saved;region=records['stage-02-region.json'];ref=records['reference.json']
    center=next((v,j) for t,p,v,j in capture.calls if t==.13 and not np.any(p))
    saved=dict(parameter_count=51,reference=ref,bound=records['future-bound.json'],envelope=records['future.json'],
        nominal=center[0].tolist(),jacobian=center[1].tolist(),fixed_center=region['center'][:27],
        lower=region['lower'],upper=region['upper'],time_s=.13)
    bundle=dict(training=dict(region=region),reference=ref,lower=region['lower'],upper=region['upper'])
    material=dict(saved=saved,proof_input=bundle,conditioning_certificate=records['stage-02-certificate.json'])
    metadata=records['compilation.json'];expected={}
    for kind,value in metadata.items():
        if kind!='native':expected.update({'analysis/lll/'+p:h for p,h in value['sources'].items()})
    spec=dict(packets=32,training_rows=24,future_s=.13,model=0,profile=True,
        compiler=metadata['arithmetic']['compiler'],maximum_bound_seconds=30.)
    charges={};operations=[];artifacts={}
    def reserve(**values):
        for key,value in values.items():charges[key]=charges.get(key,0)+value
    result=candidate.calculate(material,records['case.json'],spec,reserve=reserve,
        charge=lambda **v:operations.append(v),save=lambda k,v:artifacts.update({k:v}),
        kernel_directory=tmp_path/'base/kernels',source_directory=Path(candidate.__file__).parent,
        expected_sources=expected)
    assert result['audit']['passed'] and charges['exact_supports']==30
    assert operations==[dict(bound_calls=1,bound_steps=288)]
    assert result['conditional_remainder']['remainder_upper']<=result['conditional_remainder']['original_remainder']
    assert result['future']['nominal']==saved['nominal'] and result['future']['jacobian']==saved['jacobian']
    assert len(region['inequality_design'])==24 and result['matched']['passed']


@pytest.mark.parametrize('rows',[0,12])
def test_preparer_rejects_missing_or_duplicated_short_control_coverage(tmp_path,rows):
    from lll.ilvis0_saved_remainder import saved_inputs
    from lll.studies.artifacts import encoded,digest
    directory=tmp_path/'data/qualification';directory.mkdir(parents=True)
    def write(name,value):
        raw=encoded(value);(directory/name).write_bytes(raw);return digest(raw)
    manifest=write('manifest.json',dict(sources={}))
    entries=[]
    for i in range(rows):
        result=dict(passed=True,all_probes_contained=True,maps_preserved=True,
            remainders_nonwidening=True,force_remainder_reduced=True,model=0,profile=False,scope='physical')
        name=f'control-{i}.json'
        entries.append(dict(artifact=name,artifact_sha256=write(name,dict(result=result))))
    summary=write('summary.json',dict(passed=True,completed=12,results=entries))
    write('completion.json',dict(manifest_sha256=manifest,summary_sha256=summary))
    with pytest.raises(ValueError,match='twelve|coverage'):
        saved_inputs(tmp_path,'data/nonexistent-parent','data/qualification')
