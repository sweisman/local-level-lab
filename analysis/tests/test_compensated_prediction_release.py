# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fresh cohorts reuse the existing executor, score and statistical policy."""
import copy
import pytest


@pytest.mark.parametrize('role,count,first,last,hours',[
    ('calibration',7176,281474977010656,281474977010954,120),
    ('validation',4344,281474977110656,281474977110836,72)])
def test_compensated_cohort_is_fresh_complete_and_finite(role,count,first,last,hours):
    from lll.compensated_prediction_release import recipe,tasks,EXCLUDED_SEEDS
    from lll.prediction_calibration_study import recipe as old
    r=recipe(role);rows=tasks(role,'a'*64)
    assert len(rows)==count and len({t['identity'] for t in rows})==count
    assert r['seeds']==list(range(first,last+1)) and r['maximum_wall_s']==hours*3600
    assert r['workers']==4 and r['threads']==1 and r['maximum_evaluations']==200 and r['retries']==0
    assert not set(r['seeds'])&set(EXCLUDED_SEEDS)
    assert set(old('calibration')['seeds']+old('validation')['seeds'])<=set(EXCLUDED_SEEDS)
    assert all(t['limits']['native_calls']==59954 and t['limits']['packet_visits']==376512753 for t in rows)
    assert {t['payload']['draw_seed'] for t in rows}==set(r['seeds'])


def test_compensated_population_binds_mean_provider_without_changing_noise_or_physics():
    from lll.compensated_prediction_release import population,case_recipe,recipe,REQUIRED_SOURCES
    from lll.prediction_calibration_study import _configured
    sources={k:'a'*64 for k in REQUIRED_SOURCES};env={'fixture':'one-thread'}
    p=population(sources,env);q=copy.deepcopy(sources)
    assert p['descriptor']['mean_arithmetic']=='compensated-coordinate-tangent-v1'
    assert p['descriptor']['recipe']['workers']==4
    assert all('seed' not in v for v in p['descriptor']['recipe']['noise_by_law'].values())
    seed=recipe('calibration')['seeds'][0];actual=case_recipe(seed);old=_configured(seed)
    assert all(actual[k]==v for k,v in old.items() if k!='workers')
    q['analysis/lll/ilvis0_coordinate_precision.py']='b'*64
    assert population(q,env)['sha256']!=p['sha256']
    assert population(sources,{'fixture':'changed'})['sha256']!=p['sha256']
    with pytest.raises(ValueError):case_recipe(281474976810726)


def test_compensated_handoff_requires_its_own_cohort_and_validation_policy():
    from lll import compensated_prediction_release as protocol
    from lll.prediction_calibration_report import build_handoff,check_handoff
    r=protocol.recipe('calibration')
    report=dict(verified=True,role='calibration',total=7176,returned_outcomes=7176,
        population_sha256='a'*64,manifest_sha256='b'*64,summary_sha256='c'*64,
        validation_policy=protocol.recipe('validation'),draws=[dict(seed=seed,role='calibration',
            population_sha256='a'*64,maximum_score=float(i)) for i,seed in enumerate(r['seeds'])])
    handoff=build_handoff(report,protocol=protocol)
    assert handoff['calibration']['threshold']==298.
    assert check_handoff(handoff,population_sha256='a'*64,protocol=protocol)==handoff
    with pytest.raises(ValueError):check_handoff(handoff,population_sha256='a'*64)


def test_compensated_release_requires_qualification_before_inputs(tmp_path):
    from lll.compensated_prediction_release import prepare
    with pytest.raises(ValueError):prepare(tmp_path,role='calibration',qualification=None)
    assert not (tmp_path/'data').exists()


def test_compensated_validation_requires_calibration_before_preparation(tmp_path):
    from lll.compensated_prediction_release import prepare
    with pytest.raises(ValueError,match='calibration'):
        prepare(tmp_path,role='validation',qualification='not-yet-qualified')
    assert not (tmp_path/'data').exists()


def context(tmp_path,monkeypatch,role='calibration'):
    from types import SimpleNamespace
    from lll import compensated_prediction_release as release,airquantumgrav_inventory
    from lll.studies.artifacts import encoded,digest
    env={'fixture':'one-thread'};monkeypatch.setattr(airquantumgrav_inventory,'environment',lambda:env)
    raw=b'# frozen release fixture\n';sources={n:digest(raw) for n in release.REQUIRED_SOURCES}
    for name in sources:
        p=tmp_path/'source-freeze'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    pop=release.population(sources,env)
    manifest=dict(scope=release.SCOPE,sources=sources,tasks=release.tasks(role,pop['sha256']))
    (tmp_path/'manifest.json').write_bytes(encoded(manifest));paths={}
    gate=dict(complete=48,selected=48,failures=[],candidate_qualified=True,rows=[{'passed':True}]*48,
        pairs=[{'passed':True}]*24,original_binding_replays=4,original_binding_replays_exact=True)
    values={'recipe':release.recipe(role),'population':pop,'qualification-environment':env,
        'optimizer-gate':gate,'optimizer-binding':dict(environment=env,sources=sources)}
    for key,value in values.items():
        p=tmp_path/(key+'.json');p.write_bytes(encoded(value));paths[key]=p
    task=manifest['tasks'][0];directory=tmp_path/'artifacts'/task['identity']
    def input_path(key=None):
        if (key or 'recipe') not in paths:raise ValueError('missing frozen input')
        return paths[key or 'recipe']
    def save(name,value):
        directory.mkdir(parents=True,exist_ok=True);(directory/name).write_bytes(encoded(value))
    ctx=SimpleNamespace(root=tmp_path,manifest=manifest,directory=directory,input_path=input_path,save=save)
    return task,ctx,paths


@pytest.mark.parametrize('change',['seed','source','environment','gate','validation'])
def test_compensated_worker_rejects_changed_or_unreleased_work(tmp_path,monkeypatch,change):
    from lll.compensated_prediction_release import evaluate
    import json
    role='validation' if change=='validation' else 'calibration'
    task,ctx,paths=context(tmp_path,monkeypatch,role)
    if change=='seed':task=dict(task,payload=dict(task['payload'],draw_seed=1))
    elif change=='source':
        name=next(iter(ctx.manifest['sources']));(ctx.root/'source-freeze'/name).write_text('# changed\n')
    elif change=='environment':paths['qualification-environment'].write_text('{}')
    elif change=='gate':
        d=json.loads(paths['optimizer-gate'].read_text());d['complete']=47;paths['optimizer-gate'].write_text(json.dumps(d))
    with pytest.raises(ValueError):evaluate(task,ctx)
    assert not ctx.directory.exists()


def test_compensated_frozen_worker_uses_shared_executor_and_qualified_provider(tmp_path,monkeypatch):
    import importlib.util,json,sys
    from pathlib import Path
    from lll import structured_noisy_study,independent_noisy_study
    from lll.coordinate_optimizer_study import kernels
    path=Path(__file__).resolve().parents[1]/'lll/compensated_prediction_release.py'
    spec=importlib.util.spec_from_file_location('_frozen_compensated_release',path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module
    try:
        spec.loader.exec_module(module);task,ctx,_=context(tmp_path,monkeypatch);seen=[]
        def run(t,c,*,r,payload,kernel_provider):
            assert t is task and c is ctx and kernel_provider is kernels
            assert payload==task['payload']['case'] and r['noise_by_law']['increment']['seed']==task['payload']['draw_seed']
            seen.append(True);c.save('fit.json',{'residual_sum_squares':3.})
            return dict(passed=False,converged=False,native_calls=0,scientific_decision='abstain')
        monkeypatch.setattr(structured_noisy_study,'run_case',run)
        monkeypatch.setattr(independent_noisy_study,'score_saved_case',lambda *a,**kw:{'maximum_standardized_error':7.})
        result=module.evaluate(task,ctx)
        marker=json.loads((ctx.directory/'family-outcome.json').read_text())
        assert seen==[True] and result['passed'] is False and marker['converged'] is False
        assert marker['seed']==module.recipe('calibration')['seeds'][0]
    finally:sys.modules.pop(spec.name,None)


def test_original_calibration_defaults_match_frozen_reference_exactly():
    from pathlib import Path
    from lll import prediction_calibration_study as current
    from lll.studies.closed import ClosedStudy,load_python_reference
    from lll.studies.artifacts import encoded
    s=ClosedStudy(Path.cwd(),'docs/compensated-optimizer-qualification')
    try:
        name='analysis/lll/prediction_calibration_study.py';sha=s.manifest['sources'][name]
        old=load_python_reference(s.read('source-freeze/'+name,sha,raw=True),name='lll._release_original_'+sha,sha256=sha)
        sources={n:'a'*64 for n in old.REQUIRED_SOURCES};env={'fixture':True}
        assert encoded(current.population(sources,env))==encoded(old.population(sources,env))
        for role in ('calibration','validation'):
            assert encoded(current.recipe(role))==encoded(old.recipe(role))
            assert encoded(current.tasks(role,'a'*64))==encoded(old.tasks(role,'a'*64))
            seed=old.recipe(role)['seeds'][0]
            assert encoded(current.case_recipe(seed))==encoded(old.case_recipe(seed))
    finally:s.close()


def test_modern_tangent_cache_entries_use_metadata_paths():
    from lll.structured_noisy_publication import native_cache_entries
    from lll.studies.artifacts import encoded
    tm=dict(source_file='coordinate-precision-key.cpp',binary_file='coordinate-precision-key.so',
        source_sha256='a'*64,binary_sha256='b'*64,compiler='c++',compiler_executable='/usr/bin/c++',
        flags=[],cache_sha256='c'*64)
    nm=dict(tm,source_file='noise-step-key.cpp',binary_file='noise-step-key.so')
    metadata={'coordinate-precision-key.json':tm,'noise-step-key.json':nm}
    class Saved:
        tasks={'case':{'shard':0}};rows={'case':{}}
        def envelope(self,identity):return {'result':{'converged':True}}
        def artifact(self,identity,name):return {'tangent':tm,'noise_bridge':nm}
        def read(self,path,**kw):
            name=path.rsplit('/',1)[-1]
            if name=='builds.sqlite':return b'journal'
            return encoded(metadata[name])
    entries=native_cache_entries(Saved())
    assert len(entries)==7
    assert 'shards/000/kernels/coordinate-precision-key.so' in entries
    assert 'shards/000/kernels/coordinate-precision-key.json' in entries
    assert not any('wide-tangent' in name for name in entries)


def test_compensated_partial_report_uses_new_cohort_and_cannot_supply_handoff(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from lll import compensated_prediction_release as release,structured_noisy_publication,airquantumgrav_inventory
    from lll.prediction_calibration_report import inspect,build_handoff
    from lll.studies import closed
    from lll.studies.artifacts import digest
    raw=b'frozen report fixture';sources={n:digest(raw) for n in release.REQUIRED_SOURCES};env={'fixture':True}
    pop=release.population(sources,env);matrix={t['identity']:t for t in release.tasks('calibration',pop['sha256'])}
    identity=next(iter(matrix))
    class Saved:
        def __init__(self,*a):
            self.manifest=dict(scope=release.SCOPE,sources=sources);self.tasks=matrix;self.rows={identity:{}}
            self.summary=dict(completed=1,elapsed_s=1.,charged={})
            self.completion=dict(manifest_sha256='b'*64,summary_sha256='c'*64)
        def input(self,key):return {'recipe':release.recipe('calibration'),'population':pop,
            'qualification-environment':env,'validation-policy':release.recipe('validation')}[key]
        def read(self,*a,**kw):return raw
        def envelope(self,identity):return {'result':{'passed':False,'reason':'unavailable'},'artifacts':{}}
        def close(self):pass
    monkeypatch.setattr(closed,'ClosedStudy',Saved)
    monkeypatch.setattr(airquantumgrav_inventory,'environment',lambda:env)
    monkeypatch.setattr(structured_noisy_publication,'inspect_case',lambda *a,**kw:None)
    policy=release.policy();policy.native_bindings=lambda s:{}
    report=inspect(tmp_path,'data/partial',protocol=policy)
    assert report['returned_outcomes']==1 and report['total']==7176 and report['calibration'] is None
    assert report['draws'][0]['seed']==release.recipe('calibration')['seeds'][0]
    with pytest.raises(ValueError):build_handoff(report,protocol=policy)


@pytest.mark.parametrize('change',['count','pair','binding','environment'])
def test_compensated_parent_qualification_rejects_missing_or_changed_evidence(change):
    from lll.compensated_prediction_release import verify_optimizer_gate
    report=dict(complete=48,selected=48,failures=[],candidate_qualified=True,rows=[{'passed':True}]*48,
        pairs=[{'passed':True}]*24,original_binding_replays=4,original_binding_replays_exact=True)
    binding=dict(environment={'fixture':True},sources={'source':'a'*64});current={'source':'a'*64};env={'fixture':True}
    if change=='count':report['complete']=47
    elif change=='pair':report['pairs']=[{'passed':False}]+report['pairs'][1:]
    elif change=='binding':current['source']='b'*64
    else:env={}
    with pytest.raises(ValueError):verify_optimizer_gate(report,binding,current,env)


def test_compensated_publication_uses_its_qualified_sources_plan_and_protocol(tmp_path,monkeypatch):
    import json
    from types import SimpleNamespace
    from lll import prediction_calibration_report,ilvis0_control_publication
    from lll.studies import qualification
    from lll import airquantumgrav_inventory
    seen=[];env={'fixture':True}
    policy=SimpleNamespace(qualification_sources=lambda root:['new-release.py'],plan='docs/fresh-plan.md')
    report=dict(role='calibration',native_assets={},calibration=None,validation=None,returned_outcomes=1)
    data=tmp_path/'data/fresh';data.mkdir(parents=True)
    for name in ('manifest.json','authorization.json','start.json','start.seal.json','summary.json','completion.json'):
        (data/name).write_text('{}')
    frozen=data/'source-freeze/docs/fresh-plan.md';frozen.parent.mkdir(parents=True)
    frozen.write_text('# Exact frozen plan\n')
    manifest=dict(sources={'docs/fresh-plan.md':'fixture'},inputs={},allocation={'workers':0})
    monkeypatch.setattr(ilvis0_control_publication.runner,'verify',lambda data:manifest)
    monkeypatch.setattr(ilvis0_control_publication.runner,'verify_completion',lambda data:dict(results=[]))
    real_package=ilvis0_control_publication.publish
    def checked(root,request,**kw):
        assert kw['sources']==['new-release.py'];seen.append('qualified');return b'request',b'tests'
    def inspect(root,prefix,*,protocol):
        assert protocol is policy;seen.append('inspected');return report
    def package(data,public,text,*,plan):
        real_package(data,public,text,plan=plan);seen.append('packaged')
    monkeypatch.setattr(qualification,'checked',checked)
    monkeypatch.setattr(airquantumgrav_inventory,'environment',lambda:env)
    monkeypatch.setattr(prediction_calibration_report,'inspect',inspect)
    monkeypatch.setattr(prediction_calibration_report,'render',lambda r:'# release\n')
    monkeypatch.setattr(prediction_calibration_report,'result_csv',lambda r:'identity\n')
    monkeypatch.setattr(ilvis0_control_publication,'publish',package)
    monkeypatch.setattr(ilvis0_control_publication,'check',lambda *a:None)
    result=prediction_calibration_report.publish(tmp_path,'data/fresh',qualification='request',
        output='docs/fresh',protocol=policy)
    assert seen==['qualified','inspected','packaged','inspected']
    assert result['optimizer_starts']==0 and result['returned']==1
    assert (tmp_path/'docs/fresh/PLAN.md').read_bytes()==frozen.read_bytes()
