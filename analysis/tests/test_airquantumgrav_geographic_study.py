# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib

import numpy as np
import pytest


def library():return importlib.import_module('lll.airquantumgrav_geographic_controls')


def test_geographic_definition_preserves_complete_matrix_and_finite_work():
    tasks=library().tasks()
    assert len(tasks)==len({t['identity'] for t in tasks})==72
    assert sum(t['limits']['native_calls'] for t in tasks)==144
    assert sum(t['limits']['packet_visits'] for t in tasks)==93312000000
    assert {t['payload']['method'] for t in tasks}=={'left_hold','right_hold','linear_points'}
    assert {t['payload']['latitude_deg'] for t in tasks}=={-55.,55.}
    assert {t['payload']['removal'] for t in tasks}=={0.,.35}
    assert all(t['payload']['maximum_constructed_intervals']==1080000 for t in tasks)


def samples():
    return dict(times=np.array([1.,1.003,1.006]),angular_rate_rads=np.array([[1.,2.,3.],[2.,3.,4.],[3.,4.,5.]]),
        specific_force_mps2=np.array([[4.,5.,6.],[5.,6.,7.],[6.,7.,8.]]))


def test_construct_keeps_original_channels_and_stream_chunk_equivalence():
    module=library();case=samples();before={k:v.copy() for k,v in case.items()};charges=[]
    a=module.construct(case,method='linear_points',rate_hz=300,chunk_size=1,
        reserve=lambda **v:charges.append(v))
    b=module.construct(case,method='linear_points',rate_hz=300,chunk_size=10,reserve=lambda **v:None)
    assert charges==[dict(constructed_intervals=2)] and a['constructed_not_logged_increments']
    for key in ('theta','dv','dt'):assert a[key].tobytes()==b[key].tobytes()
    np.testing.assert_allclose(a['theta'],np.array([[1.5,2.5,3.5],[2.5,3.5,4.5]])*.003,atol=1e-15,rtol=0.)
    for key in case:assert np.array_equal(case[key],before[key])


@pytest.mark.parametrize('fault',['method','gap','reversal','nonfinite'])
def test_construct_rejects_unsupported_inputs_without_repair(fault):
    module=library();case=samples();method='linear_points';charges=[]
    if fault=='method':method='undeclared'
    elif fault=='gap':case['times'][-1]=1.1
    elif fault=='reversal':case['times'][-1]=case['times'][1]
    else:case['angular_rate_rads'][0,0]=np.nan
    with pytest.raises(ValueError):module.construct(case,method=method,rate_hz=300,reserve=lambda **v:charges.append(v))
    if fault in ('method','nonfinite'):assert not charges


@pytest.fixture(scope='module')
def kernel(tmp_path_factory):
    from lll.ilvis0_exploratory import load_kernel
    return load_kernel(tmp_path_factory.mktemp('esa-geographic-kernel'))[0]


@pytest.mark.parametrize('model',['sphere_rotating','sphere_still','flat_still'])
@pytest.mark.parametrize('latitude',[-55.,55.])
@pytest.mark.parametrize('removal',[0.,.35])
def test_native_adapter_matches_independent_short_geometry_and_exact_charges(kernel,model,latitude,removal):
    module=library()
    from lll.airquantumgrav_truth import truth
    times=np.arange(301)/300;case=truth(model,times,latitude_deg=latitude,pattern='slow',removal=removal)
    case['times']=times;charges=[]
    increments=module.construct(case,method='linear_points',rate_hz=300,reserve=lambda **v:None)
    queries=np.array([.25,.5,.75]);answer=truth(model,queries,latitude_deg=latitude,pattern='slow',removal=removal)
    initial=dict(coordinates=case['coordinates'][0],velocity=case['velocity_local_mps'][0],
        rotation=case['attitude_body_to_local'][0])
    prediction=module.propagate(increments,queries,initial,model=model,removal=removal,kernel=kernel,
        reserve=lambda **v:charges.append(v))
    assert charges==[dict(native_calls=1,packet_visits=900)]
    errors=module.position_errors(prediction,answer,model=model)
    assert module.metrics(errors)['maximum_3d_m']<.01


def test_definition_explicitly_includes_both_native_sources():
    from pathlib import Path
    source=library().sources(Path(__file__).resolve().parents[2])
    assert {'analysis/lll/ilvis0_native.c','analysis/lll/ilvis0_tangent.cpp','analysis/lll/airquantumgrav_truth.py'}<=set(source)


def test_disc_error_metric_uses_disc_distance_not_globe_longitude_scale():
    module=library()
    from lll.airquantumgrav_truth import truth
    answer=truth('flat_still',[0.],latitude_deg=-55.,pattern='stationary',removal=0.)
    shifted=answer['coordinates'].copy();shifted[:,1]+=1e-6
    error=module.position_errors(shifted,answer,model='flat_still')
    expected=6371000.*(np.pi/2-np.radians(-55.))*1e-6
    assert np.linalg.norm(error)==pytest.approx(expected,rel=1e-9)


def test_finite_evaluator_reconciles_all_charges_and_persists_its_journal(tmp_path,monkeypatch):
    import json
    from types import SimpleNamespace
    from lll import ilvis0_control_shards as runner
    from lll.studies.journal import Journal
    from lll.studies.artifacts import digest
    module=library();r=module.recipe()
    r.update(duration_s=1.,queries=3,query_start_s=.25,query_step_s=.25,
        maximum_constructed_intervals=900,maximum_generated_samples=905)
    monkeypatch.setattr(module,'recipe',lambda:r)
    monkeypatch.setattr(runner,'_check_continue',lambda *args:None)
    task=next(t for t in module.tasks() if t['payload']['method']=='linear_points')
    recipe_path=tmp_path/'recipe.json';recipe_path.write_text(json.dumps(r))
    environment_path=tmp_path/'environment.json';environment_path.write_text(json.dumps(module.environment()))
    (tmp_path/'manifest.json').write_text('{}');charges=[];saved={};noted=[]
    source_sha=digest((__import__('pathlib').Path(module.__file__).with_name('ilvis0_native.c')).read_bytes())
    context=SimpleNamespace(root=tmp_path,directory=tmp_path/'artifacts'/task['identity'],shard=0,
        manifest=dict(sources={'analysis/lll/ilvis0_native.c':source_sha}),
        input_path=lambda key=None:recipe_path if key is None else environment_path,
        charge=lambda **v:charges.append(v),save=lambda name,v:saved.update({name:v}),note_file=lambda p:noted.append(p))
    result=module.evaluate(task,context)
    assert result['passed'] and sum(v['native_calls'] for v in charges)==2
    assert sum(v['packet_visits'] for v in charges)==2700
    assert result['constructed_intervals']==900 and result['generated_samples']==905
    assert {'compilation.json','rate-300.json','rate-600.json'}==set(saved)
    journal=Journal(noted[0],freeze=digest((tmp_path/'manifest.json').read_bytes()),
        limits={task['identity']:dict(constructed_intervals=900,generated_samples=905)})
    assert journal.count(task['identity'],'constructed_intervals')==900


def test_bad_frozen_recipe_is_rejected_before_compilation_or_charges(tmp_path):
    import json
    from types import SimpleNamespace
    module=library();path=tmp_path/'recipe.json';path.write_text(json.dumps({}))
    context=SimpleNamespace(input_path=lambda:path)
    with pytest.raises(ValueError,match='unchanged frozen'):module.evaluate(module.tasks()[0],context)


def test_geographic_loaders_compile_from_the_declared_isolated_snapshot(tmp_path):
    import importlib.util
    import shutil
    from pathlib import Path
    root=Path(__file__).resolve().parents[2];declared=set(library().sources(root))
    for basename in ('ilvis0_exploratory.py','ilvis0_shape.py','ilvis0_native.c','ilvis0_tangent.cpp'):
        name='analysis/lll/'+basename;assert name in declared
        shutil.copyfile(root/name,tmp_path/basename)
    for label,filename,loader in [('value','ilvis0_exploratory.py','load_kernel'),
                                  ('tangent','ilvis0_shape.py','load_tangent')]:
        spec=importlib.util.spec_from_file_location('lll._esa_isolated_'+label,tmp_path/filename)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        function,meta=getattr(module,loader)(tmp_path/'kernels')
        assert function is not None and meta['source_sha256']


def test_preparation_requires_passing_source_bound_qualification_before_files(tmp_path):
    with pytest.raises(ValueError,match='qualification'):library().prepare(tmp_path,qualification=None)
    assert not (tmp_path/'data').exists()
