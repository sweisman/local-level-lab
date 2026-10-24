# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent receiver geometry for training/forecast software controls."""
import math

import numpy as np
import pytest


def conversion():
    from lll import airquantumgrav_observation_truth as module
    assert hasattr(module,'receiver_coordinates'), 'independent antenna coordinate conversion is missing'
    return module.receiver_coordinates


@pytest.mark.parametrize('model',['sphere_rotating','sphere_still','flat_still'])
def test_independent_receiver_coordinates_match_known_nonzero_antenna_geometry(model):
    from lll.airquantumgrav_truth import truth
    from lll.airquantumgrav_observation_truth import antenna
    times=np.array([0.,5.,19.,119.]);answer=antenna(truth(model,times,latitude_deg=-55.,pattern='fast',removal=.35),sign=1)
    coords=conversion()(answer['position_world_m'],model=model)
    phi,longitude,h=coords.T
    if model=='flat_still':
        radius=6371000.*(math.pi/2-phi);z=h
    else:
        e2=(1/298.257223563)*(2-1/298.257223563)
        rn=6378137./np.sqrt(1-e2*np.sin(phi)**2);radius=(rn+h)*np.cos(phi);z=(rn*(1-e2)+h)*np.sin(phi)
    restored=np.column_stack((radius*np.cos(longitude),radius*np.sin(longitude),z))
    np.testing.assert_allclose(restored,answer['position_world_m'],rtol=0,atol=2e-8)
    assert not np.array_equal(coords,answer['coordinates'])


@pytest.mark.parametrize('sign',[-1,1])
def test_independent_receiver_coordinates_recover_oblique_ellipsoid_point(sign):
    e2=(1/298.257223563)*(2-1/298.257223563);n=6378137./math.sqrt(1-e2/2)
    rho=(n+321.)/math.sqrt(2);z=sign*(n*(1-e2)+321.)/math.sqrt(2)
    actual=conversion()([[rho*math.sqrt(3)/2,rho/2,z]],model='sphere_rotating')
    np.testing.assert_allclose(actual[0,:2],[sign*math.pi/4,math.pi/6],atol=1e-14,rtol=0)
    assert actual[0,2]==pytest.approx(321.,abs=5e-8)


@pytest.mark.parametrize('model',['sphere_rotating','sphere_still'])
def test_independent_receiver_coordinates_recover_equator_without_fitted_height(model):
    result=conversion()([[6378260.,0.,0.]],model=model)
    np.testing.assert_allclose(result,[[0.,0.,123.]],atol=1e-9,rtol=0)


@pytest.mark.parametrize('fault',['empty','shape','nonfinite','origin','disc_domain','model'])
def test_independent_receiver_coordinate_failures_are_not_repaired(fault):
    values=[[6378137.,0.,0.]];model='sphere_still'
    if fault=='empty':values=[]
    elif fault=='shape':values=[[1.,2.]]
    elif fault=='nonfinite':values=[[np.nan,0.,0.]]
    elif fault=='origin':values=[[0.,0.,0.]]
    elif fault=='disc_domain':values=[[4*6371000.,0.,0.]];model='flat_still'
    else:model='undeclared'
    with pytest.raises(ValueError):conversion()(values,model=model)


@pytest.mark.parametrize('model',['sphere_rotating','sphere_still','flat_still'])
@pytest.mark.parametrize('sign',[-1,1])
def test_generated_receiver_samples_include_latency_and_antenna_without_fused_navigation(model,sign):
    from lll import airquantumgrav_observation_truth as module
    from lll.airquantumgrav_truth import truth
    assert hasattr(module,'receiver_samples'), 'generated receiver observation API is missing'
    times=np.array([.5,3.5,8.5])
    actual=module.receiver_samples(model,times,latitude_deg=55.,pattern='fast',removal=.35,sign=sign)
    expected=module.antenna(truth(model,times+sign*.0007,latitude_deg=55.,pattern='fast',removal=.35),sign=sign)
    np.testing.assert_array_equal(actual['position_world_m'],expected['position_world_m'])
    np.testing.assert_array_equal(actual['coordinates'],module.receiver_coordinates(expected['position_world_m'],model=model))
    assert 'parameters' not in actual and 'initial' not in actual


def adapter():
    import importlib.util
    assert importlib.util.find_spec('lll.airquantumgrav_training_controls') is not None, 'training study adapter is missing'
    return __import__('lll.airquantumgrav_training_controls',fromlist=['recipe'])


def test_training_matrix_preserves_the_declared_finite_fit_and_forecast_allowance():
    tasks=adapter().tasks()
    assert len(tasks)==len({v['identity'] for v in tasks})==24
    assert sum(v['limits']['native_calls'] for v in tasks)==4824
    assert sum(v['limits']['packet_visits'] for v in tasks)==20666016000
    assert all(v['limits']['native_calls']==201 for v in tasks)
    assert {v['payload']['profile'] for v in tasks}=={False,True}


def short_recipe():
    r=adapter().recipe();r.update(duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2,maximum_evaluations=8)
    return r


def test_generated_training_material_exposes_no_later_position_or_true_start(monkeypatch):
    from lll import airquantumgrav_observation_truth as observation
    module=adapter();r=short_recipe();calls=[];charges=[];original=observation.receiver_samples
    def watched(model,times,**kwargs):
        calls.append(np.array(times));return original(model,times,**kwargs)
    monkeypatch.setattr(observation,'receiver_samples',watched)
    material=module.generated_training(dict(model='sphere_still',latitude_deg=55.,profile=False,start=0),r,
        reserve=lambda **v:charges.append(v))
    assert set(material)=={'theta','dv','dt','rate_times','angular_rate_rads','specific_force_mps2','times','training_gps','training_epochs'}
    assert material['training_gps'].shape==(6,3) and material['theta'].shape==(600,3)
    assert len(calls)==1 and np.array_equal(calls[0],material['times'][:6])
    assert sum(v.get('generated_samples',0) for v in charges)==607
    assert sum(v.get('constructed_intervals',0) for v in charges)==600


def test_training_weights_use_training_coordinate_metric_and_fixed_sigma_only():
    covariance=adapter().training_covariance(np.array([[0.,0.,600.],[0.,1.,900.]]),'flat_still',sigma_m=.01)
    want=np.tile([(.01/6371000.)**2,(.01/(6371000.*math.pi/2))**2,.0001],2)
    np.testing.assert_allclose(np.diag(covariance),want,rtol=1e-15,atol=0)
    assert np.count_nonzero(covariance)==6


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_shape import load_tangent
    directory=tmp_path_factory.mktemp('esa-training-kernels')
    return load_kernel(directory)[0],load_tangent(directory)[0]


@pytest.mark.parametrize('profile',[False,True])
def test_later_positions_open_after_saved_forecast_and_cannot_change_training_fit(kernels,monkeypatch,profile):
    import io
    from lll import airquantumgrav_observation_truth as observation
    module=adapter();r=short_recipe();original=observation.receiver_samples;current={};snapshots=[]
    def watched(model,times,**kwargs):
        answer=original(model,times,**kwargs)
        if len(times)==r['queries']:
            assert 'forecast.json' in current['saved']
            answer['position_world_m'][6:,0]+=current['change']
            answer['coordinates']=observation.receiver_coordinates(answer['position_world_m'],model=model)
        else:assert len(times)==6
        return answer
    monkeypatch.setattr(observation,'receiver_samples',watched)
    for change in (0.,100.):
        current.clear();current.update(saved={},change=change);charges=[];constructed=[];binary={}
        result=module.calculate(dict(model='flat_still',latitude_deg=55.,profile=profile,start=0),r,
            kernel=kernels[0],tangent=kernels[1],reserve=lambda **v:charges.append(v),
            reserve_construction=lambda **v:constructed.append(v),save=lambda name,value:current['saved'].update({name:value}),
            save_bytes=lambda name,value:binary.update({name:value}),check_continue=lambda:None)
        assert len(current['saved']['fit.json']['active_parameters'])==26+int(profile)
        assert len(charges)==result['evaluations']+1<=9
        assert sum(v.get('generated_samples',0) for v in constructed)==616
        assert sum(v.get('constructed_intervals',0) for v in constructed)==600
        with np.load(io.BytesIO(binary['raw-inputs.npz']),allow_pickle=False) as arrays:
            assert arrays['theta'].shape==(600,3) and arrays['angular_rate_rads'].shape==(601,3)
        snapshots.append((current['saved']['fit.json'],current['saved']['forecast.json'],binary['raw-inputs.npz'],result))
    np.testing.assert_allclose(snapshots[0][0]['normalized_parameters'],snapshots[1][0]['normalized_parameters'],atol=1e-14,rtol=0)
    np.testing.assert_array_equal(snapshots[0][1]['coordinates'],snapshots[1][1]['coordinates'])
    assert snapshots[0][2]==snapshots[1][2]
    assert snapshots[1][3]['prediction']['horizontal_rms_m']>snapshots[0][3]['prediction']['horizontal_rms_m']+50


def test_training_preparation_requires_software_qualification_before_any_write(tmp_path):
    with pytest.raises(ValueError,match='qualification'):adapter().prepare(tmp_path,qualification=None)
    assert not (tmp_path/'data').exists()


def test_training_bad_recipe_rejected_before_loading_or_charging(tmp_path):
    import json
    from types import SimpleNamespace
    module=adapter();path=tmp_path/'recipe.json';path.write_text(json.dumps({}))
    with pytest.raises(ValueError,match='frozen'):module.evaluate(module.tasks()[0],SimpleNamespace(input_path=lambda:path))


def test_changed_earlier_scoring_positions_are_rejected_after_forecast(kernels,monkeypatch):
    from lll import airquantumgrav_observation_truth as observation
    r=short_recipe();original=observation.receiver_samples;saved={}
    def changed(model,times,**kwargs):
        answer=original(model,times,**kwargs)
        if len(times)==r['queries']:
            assert 'forecast.json' in saved
            answer['coordinates'][0,2]+=1.
        return answer
    monkeypatch.setattr(observation,'receiver_samples',changed)
    with pytest.raises(ValueError,match='earlier'):
        adapter().calculate(dict(model='sphere_still',latitude_deg=55.,profile=False,start=0),r,
            kernel=kernels[0],tangent=kernels[1],reserve=lambda **v:None,reserve_construction=lambda **v:None,
            save=lambda k,v:saved.update({k:v}),save_bytes=lambda *v:None,check_continue=lambda:None)


def test_training_definition_and_isolated_dependencies_cover_native_inputs():
    from pathlib import Path
    from lll.studies.runtime import Definition
    from lll.ilvis0_control_shards import _tasks
    root=Path(__file__).resolve().parents[2];module=adapter();sources=module.sources(root)
    assert {'analysis/lll/ilvis0_native.c','analysis/lll/ilvis0_tangent.cpp','analysis/lll/ilvis0_control_shards.py'}<=set(sources)
    value=dict(id='test-training-definition',adapter='analysis/lll/airquantumgrav_training_controls.py',sources=sources,
        inputs={'recipe':'docs/esa-training-forecast-controls/PLAN.md'},tasks=module.tasks(),workers=1,threads=4,maximum_wall_s=7200.)
    assert Definition.from_dict(value,root).id=='test-training-definition'
    assert len(_tasks(value['tasks'],1))==24
