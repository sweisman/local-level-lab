# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def _material():
    from lll.ilvis0_receipt_journal import digest
    from lll.ilvis0_witness_search import recipe
    initial=[.25 if i==25 else .05*(i%3-1) for i in range(27)]
    config=dict(model=0,profile=False,limits=[1.]*27,initial_c=[0.,0.,0.],
        initial_v=[0.,0.,0.],initial_r=[[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]],gravity=9.81,radius=6371000.)
    problem=dict(binding=dict(case_sha256='a'*64,source_sha256='b'*64,
        configuration_sha256=digest(config),model=0,profile=False),
        training_s=recipe()['training_s'],future_s=438.,observations=[[0.,0.,0.]]*5,
        allowance_m=[[1.,1.,1.]]*5,numerical_error_m=[1e-5]*3,targets_m=[20.,20.,50.],
        coordinate_scale=[1.,1.,1.],physical_lower=[-1.]*27,physical_upper=[1.]*27,
        future_observations_used=False)
    records=[dict(point=initial,status=0,time_s=t,prediction=[0.,0.,0.]) for t in recipe()['training_s']]
    bundle=dict(problem=problem,initial=initial,initial_records=records)
    case=dict(configuration=config,theta=[[0.,0.,0.]]*96000,dv=[[0.,0.,0.]]*96000,dt=[.005]*96000)
    spec=dict(model=0,profile=False,sign=1,compiler='test compiler',case_key='case')
    return bundle,case,spec


def test_recipe_freezes_the_original_observations_and_finite_allowance():
    from lll.ilvis0_witness_search import recipe,validate_recipe
    value=recipe();validate_recipe(value)
    assert value['packets']==96000 and value['training_s']==[2.,10.,30.,180.,290.]
    assert value['search_batches']==32 and value['verification_batches']==1
    assert value['future_s']==438. and value['maximum_identity_seconds']==1800.
    with pytest.raises(ValueError):validate_recipe(dict(value,search_batches=33))


@pytest.mark.parametrize('changed', ['configuration','initial','observations','clock','history'])
def test_bundle_validation_rejects_changed_original_problem(changed):
    from lll.ilvis0_witness_search import validate_bundle
    bundle,case,spec=_material();validate_bundle(bundle,case,spec)
    if changed=='configuration':case['configuration']['gravity']=10.
    elif changed=='initial':bundle['initial_records'][0]['point']=[0.]*27
    elif changed=='observations':bundle['problem']['observations']=[[10.,0.,0.]]*5
    elif changed=='clock':case['configuration']['limits'][25]=.1
    else:case['dt'].pop()
    with pytest.raises(ValueError):validate_bundle(bundle,case,spec)


def test_case_matrix_requires_every_distinct_model_and_processing_case():
    from lll.ilvis0_witness_search import case_matrix
    tasks=[dict(identity=f'{m}-{int(p)}',payload=dict(model=m,profile=p))
        for m in range(3) for p in (False,True)]
    assert len(case_matrix(tasks))==6
    with pytest.raises(ValueError):case_matrix(tasks[:-1]+[tasks[0]])


def test_adapter_supports_the_study_runners_standalone_loader():
    import importlib.util
    from lll import ilvis0_witness_search as candidate
    spec=importlib.util.spec_from_file_location('_standalone_witness_candidate',candidate.__file__)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    bundle,case,payload=_material()
    assert module.validate_bundle(bundle,case,payload)==bundle['problem']


@pytest.mark.parametrize('bad_hash',[False,True])
def test_parent_reader_requires_closed_and_hash_matched_complete_cases(tmp_path,monkeypatch,bad_hash):
    import hashlib
    import json
    from lll import ilvis0_witness_search as candidate
    from lll.studies import artifacts
    summary=json.dumps(dict(completed=5,results=[])).encode();manifest=b'{}'
    completion=json.dumps(dict(manifest_sha256='a'*64 if bad_hash else hashlib.sha256(manifest).hexdigest(),
        summary_sha256=hashlib.sha256(summary).hexdigest())).encode()
    rows={'parent/completion.json':completion,'parent/manifest.json':manifest,'parent/summary.json':summary}
    class Store:
        def __init__(self,root):pass
        def catalog(self):return {}
        def _read(self,name,catalog):return rows[name]
    monkeypatch.setattr(artifacts,'ArchiveStore',Store)
    with pytest.raises(ValueError):candidate.closed_cases(tmp_path,'parent')


@pytest.mark.parametrize('bad_binding',[False,True])
def test_worker_charges_search_and_final_replay_and_rejects_changed_source(tmp_path,monkeypatch,bad_binding):
    import hashlib
    import numpy as np
    from lll import ilvis0_witness_search as candidate
    from lll import ilvis0_control_shards as runner,ilvis0_shape,ilvis0_density_native_probes,ilvis0_truth_probes
    from lll.ilvis0_receipt_journal import encoded
    bundle,case,spec=_material();spec['bundle_key']='bundle'
    paths={}
    for key,value in (('recipe',candidate.recipe()),('case',case)):
        p=tmp_path/(key+'.json');p.write_bytes(encoded(value));paths[key]=p
    sha=hashlib.sha256(paths['case'].read_bytes()).hexdigest()
    bundle['problem']['binding']['case_sha256']='c'*64 if bad_binding else sha
    paths['bundle']=tmp_path/'bundle.json';paths['bundle'].write_bytes(encoded(bundle))
    class Context:
        root=tmp_path/'study';shard=0
        manifest=dict(sources={'analysis/lll/ilvis0_tangent.cpp':'b'*64},inputs={'case':dict(sha256=sha)})
        def __init__(self):self.charges=[];self.saved={}
        def input_path(self,key=None):return paths[key or 'recipe']
        def charge(self,**value):self.charges.append(value)
        def save(self,name,value):self.saved[name]=value
    context=Context()
    monkeypatch.setattr(runner,'_check_continue',lambda *args:None)
    monkeypatch.setattr(ilvis0_shape,'load_tangent',lambda directory:(None,dict(compiler='test compiler',source_sha256='b'*64)))
    def query(kernel,config,theta,dv,dt,times,point,reserve,save=lambda record:None):
        assert len(context.charges)>=1
        reserve(len(times),len(dt)*len(times))
        raw=dict(status=0,prediction=np.zeros((6,3)),jacobian=np.zeros((6,3,27)))
        save(raw)
        return dict(raw,classification=dict(counter_verified=True))
    monkeypatch.setattr(ilvis0_density_native_probes,'query',query)
    def search(problem,initial,oracle,**kwargs):
        kwargs['reserve']();kwargs['save']('proposal',dict(index=1,point=initial))
        raw=oracle(initial)
        record=dict(binding=problem['binding'],times_s=problem['training_s']+[problem['future_s']],
            point=initial,status=0,prediction=raw['prediction'].tolist())
        return dict(native_queries=1,best_point=initial,best_record=record,optimizer_success=False,
            stopping_reason='test stop')
    monkeypatch.setattr(ilvis0_truth_probes,'search_witness',search)
    task=dict(identity='case-0-0-positive',payload=spec)
    if bad_binding:
        with pytest.raises(ValueError,match='source'):candidate.evaluate(task,context)
        assert context.charges==[]
    else:
        result=candidate.evaluate(task,context)
        assert result['passed'] and result['native_evaluations']==2
        assert context.charges==[dict(native_calls=1,packet_visits=576000)]*2
        assert 'selected-before-verification.json' in context.saved
        assert 'verified-witness.json' in context.saved
