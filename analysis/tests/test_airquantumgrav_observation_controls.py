# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import math

import numpy as np
import pytest


def library():
    assert importlib.util.find_spec('lll.airquantumgrav_observation_truth') is not None, 'independent observation construction is missing'
    return importlib.import_module('lll.airquantumgrav_observation_truth')


@pytest.mark.parametrize('sign',[-1,1])
def test_observation_channels_apply_bias_and_gain_in_measurement_direction(sign):
    module=library()
    from lll.airquantumgrav_truth import truth
    t=np.array([0.,.2,.7]);case=truth('sphere_rotating',t,latitude_deg=55.,pattern='fast',removal=.35)
    before={k:v.copy() for k,v in case.items()}
    result=module.observe(case,sign=sign)
    w=case['angular_rate_rads'];f=case['specific_force_mps2']
    np.testing.assert_allclose(result['angular_rate_rads'],w*(1+sign*np.array([.002,-.0015,.001]))
        +sign*np.radians([.15,-.2,.25])/3600,rtol=0,atol=1e-16)
    np.testing.assert_allclose(result['specific_force_mps2'],f*(1+sign*np.array([.003,-.002,.004]))
        +sign*np.array([.01,-.02,.015]),rtol=0,atol=2e-15)
    for key in before:assert np.array_equal(before[key],case[key])
    assert result['generated_not_observed']


@pytest.mark.parametrize('model',['sphere_rotating','sphere_still','flat_still'])
@pytest.mark.parametrize('sign',[-1,1])
def test_antenna_truth_is_independent_cartesian_body_displacement(model,sign):
    module=library()
    from lll.airquantumgrav_truth import truth
    case=truth(model,[0.,3.,7.],latitude_deg=-55.,pattern='fast',removal=0.)
    answer=module.antenna(case,sign=sign)
    expected=case['position_world_m']+np.einsum('nij,j->ni',case['body_axes_world'],sign*np.array([1.5,-.7,.4]))
    np.testing.assert_array_equal(answer['position_world_m'],expected)
    np.testing.assert_array_equal(answer['body_axes_world'],case['body_axes_world'])
    assert not np.shares_memory(answer['position_world_m'],case['position_world_m'])


@pytest.mark.parametrize('model',['sphere_rotating','sphere_still','flat_still'])
@pytest.mark.parametrize('sign',[-1,1])
def test_generated_start_corrections_return_true_state_without_navigation_helpers(model,sign):
    module=library()
    from lll.airquantumgrav_truth import truth
    from scipy.spatial.transform import Rotation
    case=truth(model,[0.],latitude_deg=-55.,pattern='fast',removal=.35)
    result=module.start(case,model=model,sign=sign);p=result['parameters'];initial=result['initial']
    c=np.array([initial[k] for k in ('latitude_rad','longitude_rad','height_m')]);phi,h=c[0],c[2]
    if model=='flat_still':mn,me=6371000.,6371000.*(math.pi/2-phi)
    else:
        e2=(1/298.257223563)*(2-1/298.257223563);q=1-e2*math.sin(phi)**2
        mn=6378137.*(1-e2)/q**1.5+h;me=(6378137./q**.5+h)*math.cos(phi)
    position=np.array([p['position_'+a] for a in 'xyz'])
    restored=c+position/np.array([mn,me,-1.])
    np.testing.assert_allclose(restored,case['coordinates'][0],rtol=0,atol=1e-12)
    np.testing.assert_allclose(initial['velocity_ned_mps']+[p['velocity_'+a] for a in 'xyz'],
        case['velocity_local_mps'][0],rtol=0,atol=1e-13)
    rotation=initial['attitude_body_to_ned']@Rotation.from_rotvec([p['attitude_'+a] for a in 'xyz']).as_matrix()
    np.testing.assert_allclose(rotation,case['attitude_body_to_local'][0],rtol=0,atol=5e-16)
    assert result['gravity_mps2']+p['gravity_delta']==pytest.approx(9.81,abs=1e-14)
    assert p['time_offset']==sign*.0007
    assert set(p)=={n+'_'+a for n in ('attitude','velocity','position','gyro_bias','accel_bias','gyro_gain','accel_gain','lever') for a in 'xyz'}|{'time_offset','gravity_delta'}


@pytest.mark.parametrize('fault',['sign','shape','nonfinite','model'])
def test_observation_truth_rejects_unsupported_inputs(fault):
    module=library()
    from lll.airquantumgrav_truth import truth
    case=truth('sphere_still',[0.,1.],latitude_deg=55.,pattern='fast',removal=0.);sign=1;model='sphere_still'
    if fault=='sign':sign=0
    elif fault=='shape':case['body_axes_world']=case['body_axes_world'][:1]
    elif fault=='nonfinite':case['angular_rate_rads'][0,0]=np.nan
    else:model='undeclared'
    with pytest.raises(ValueError):module.start(case,model=model,sign=sign)


def test_observation_truth_does_not_import_navigation_or_calibration_implementation():
    import ast
    from pathlib import Path
    module=library();tree=ast.parse(Path(module.__file__).read_bytes())
    imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
    assert all(n in ('lll.airquantumgrav_truth',) for n in imports)
    assert not any(isinstance(n,ast.Import) and any(a.name not in ('math','numpy') for a in n.names) for n in ast.walk(tree))


def adapter():
    assert importlib.util.find_spec('lll.airquantumgrav_observation_controls') is not None, 'observation study adapter is missing'
    return importlib.import_module('lll.airquantumgrav_observation_controls')


def test_observation_matrix_has_finite_charges_for_every_identity():
    tasks=adapter().tasks()
    assert len(tasks)==len({v['identity'] for v in tasks})==24
    assert sum(v['limits']['native_calls'] for v in tasks)==96
    assert sum(v['limits']['packet_visits'] for v in tasks)==41472000000
    assert {v['payload']['sign'] for v in tasks}=={-1,1}
    assert all(v['limits']['native_calls']==4 for v in tasks)


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_shape import load_tangent
    directory=tmp_path_factory.mktemp('esa-observation-kernels')
    return load_kernel(directory)[0],load_tangent(directory)[0]


@pytest.mark.parametrize('model',['sphere_rotating','sphere_still','flat_still'])
@pytest.mark.parametrize('latitude',[-55.,55.])
@pytest.mark.parametrize('sign',[-1,1])
def test_known_observation_corrections_match_cartesian_truth_with_all_columns(kernels,model,latitude,sign):
    module=adapter();recipe=module.recipe();recipe.update(duration_s=2.,queries=3,query_start_s=.25,query_step_s=.5)
    charges=[];constructed=[];saved={}
    result=module.calculate(dict(model=model,latitude_deg=latitude,removal=0. if sign<0 else .35,sign=sign),recipe,
        kernel=kernels[0],tangent=kernels[1],reserve=lambda **v:charges.append(v),
        reserve_construction=lambda **v:constructed.append(v),save=lambda k,v:saved.update({k:v}),check_continue=lambda:None)
    assert result['passed'] and result['all_columns_retained']
    assert result['corrected']['maximum_3d_m']<.01
    assert len(saved['corrections.json']['active_parameters'])==27
    assert sum(v['native_calls'] for v in charges)==4
    assert [v['native_kind'] for v in charges]==['tangent','value','value','value']
    assert sum(v['packet_visits'] for v in charges)==7200
    assert sum(v.get('constructed_intervals',0) for v in constructed)==600
    assert sum(v.get('generated_samples',0) for v in constructed)==604
    assert {'corrections.json','forecast.json','comparison.json'}==set(saved)
    assert result['known_corrections_supplied_not_estimated'] and not result['observed_starts']
    assert not result['initialization_estimator_qualified']


def test_observation_prepare_rejects_missing_source_qualification_before_writing(tmp_path):
    with pytest.raises(ValueError,match='qualification'):adapter().prepare(tmp_path,qualification=None)
    assert not (tmp_path/'data').exists()


def test_observation_bad_recipe_rejected_before_native_execution(tmp_path):
    import json
    from types import SimpleNamespace
    module=adapter();path=tmp_path/'recipe.json';path.write_text(json.dumps({}))
    with pytest.raises(ValueError,match='frozen'):
        module.evaluate(module.tasks()[0],SimpleNamespace(input_path=lambda:path))


def test_observation_definition_accepts_actual_runner_assignment_fields():
    from pathlib import Path
    from lll.studies.runtime import Definition
    from lll.ilvis0_control_shards import _tasks
    module=adapter();root=Path(__file__).resolve().parents[2]
    value=dict(id='test-observation-definition',adapter='analysis/lll/airquantumgrav_observation_controls.py',
        sources=module.sources(root),inputs={'recipe':'docs/esa-observation-controls/PLAN.md'},
        tasks=module.tasks(),workers=1,threads=4,maximum_wall_s=7200.)
    assert Definition.from_dict(value,root).id=='test-observation-definition'
    assigned=_tasks(value['tasks'],1)
    assert assigned[0]['native_kind']=='mixed' and assigned[0]['shard']==0


def test_observation_evaluator_preserves_construction_journal_and_actual_native_kinds(tmp_path,monkeypatch):
    import json
    from pathlib import Path
    from types import SimpleNamespace
    from lll import ilvis0_control_shards as runner
    from lll.studies.artifacts import digest
    from lll.studies.journal import Journal
    module=adapter();r=module.recipe();r.update(duration_s=2.,queries=3,query_start_s=.25,query_step_s=.5)
    monkeypatch.setattr(module,'recipe',lambda:r)
    monkeypatch.setattr(runner,'_check_continue',lambda *args:None)
    task=runner._tasks(module.tasks(),1)[0]
    path=tmp_path/'recipe.json';path.write_text(json.dumps(r))
    env=tmp_path/'environment.json';env.write_text(json.dumps(module.environment()))
    (tmp_path/'manifest.json').write_text('{}');saved={};charges=[];noted=[]
    source=Path(module.__file__).parent
    context=SimpleNamespace(root=tmp_path,directory=tmp_path/'artifacts'/task['identity'],shard=0,
        manifest=dict(sources={'analysis/lll/'+n:digest((source/n).read_bytes()) for n in ('ilvis0_native.c','ilvis0_tangent.cpp')}),
        input_path=lambda key=None:path if key is None else env,
        charge=lambda **v:charges.append(v),save=lambda name,v:saved.update({name:v}),note_file=lambda p:noted.append(p))
    result=module.evaluate(task,context)
    assert result['passed'] and len(charges)==4
    assert [v['native_kind'] for v in charges]==['tangent','value','value','value']
    assert sum(v['packet_visits'] for v in charges)==7200
    assert 'compilation.json' in saved and len(noted)==1
    journal=Journal(noted[0],freeze=digest((tmp_path/'manifest.json').read_bytes()),
        limits={task['identity']:dict(constructed_intervals=600,generated_samples=604)})
    assert journal.count(task['identity'],'constructed_intervals')==600
    assert journal.count(task['identity'],'generated_samples')==604
