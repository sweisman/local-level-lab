# SPDX-License-Identifier: AGPL-3.0-or-later
"""Training-only controls: timing, selection and native work accounting."""
import importlib.util

import numpy as np
import pytest


def implementation():
    name='lll.ilvis0_training_forecast'
    assert importlib.util.find_spec(name) is not None, 'training-only pipeline missing'
    return __import__(name,fromlist=['initialize_training'])


def test_initial_gravity_uses_measured_integration_periods():
    times=np.arange(1.,10.)
    gps=np.c_[np.full(9,.4),times*1e-5,np.full(9,100.)]
    dt=np.tile([.004,.0065],1000)
    theta=np.zeros((len(dt),3));dv=np.c_[dt*.03,np.zeros(len(dt)),-dt*9.8]
    initial,gravity=implementation().initialize_training(times,gps,theta=theta,dv=dv,dt=dt,
        model='sphere_still',maximum_interval_s=.0075,clock='header_elapsed')
    assert gravity==pytest.approx(np.hypot(.03,9.8),abs=1e-12)
    assert np.linalg.det(initial['attitude_body_to_ned'])==pytest.approx(1.)


@pytest.mark.parametrize('change',['nominal_clock','gap','nonfinite','too_few_early_epochs'])
def test_initialization_rejects_unsupported_training_data(change):
    times=np.arange(1.,10.);gps=np.c_[np.full(9,.4),times*1e-5,np.full(9,100.)]
    dt=np.full(2200,.005);theta=np.zeros((len(dt),3));dv=np.c_[dt*0,dt*0,-dt*9.8]
    clock='header_elapsed'
    if change=='nominal_clock':clock='nominal_200Hz';dt[0]=.004
    elif change=='gap':dt[0]=.01
    elif change=='nonfinite':dv[0,0]=np.nan
    else:times[1:]+=11
    with pytest.raises(ValueError):implementation().initialize_training(times,gps,theta=theta,dv=dv,dt=dt,
        model='sphere_still',maximum_interval_s=.0075,clock=clock)


def test_primary_selection_uses_passing_training_cost_and_fixed_start_order():
    fits=[dict(converged=True,residual_sum_squares=2.,prediction_error=1.),
          dict(converged=False,residual_sum_squares=.01,prediction_error=0.),
          dict(converged=True,residual_sum_squares=2.,prediction_error=0.)]
    assert implementation().primary_index(fits)==0
    fits[0]['prediction_error']=999.
    assert implementation().primary_index(fits)==0
    assert implementation().primary_index([dict(converged=False,residual_sum_squares=0.)]) is None
    with pytest.raises(ValueError):implementation().primary_index([dict(converged=True,residual_sum_squares=np.nan)])


@pytest.mark.parametrize('stopping',['ordinary','near_zero'])
def test_fit_reserves_every_actual_native_call_and_keeps_all_columns(tmp_path,stopping):
    from lll.ilvis0_shape import TangentProblem,load_tangent
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_estimator import Bounds
    dt=np.full(80,.005);theta=np.zeros((80,3));dv=np.c_[dt*0,dt*0,-9.81*dt]
    times=np.linspace(.02,.3,9);gps=np.tile([.4,.2,100.],(9,1))
    initial=dict(latitude_rad=.4,longitude_rad=.2,height_m=100.,velocity_ned_mps=np.zeros(3),
        attitude_body_to_ned=np.eye(3))
    problem=TangentProblem(theta,dv,dt,times,gps,np.eye(27),initial,Bounds({'accel_bias_x':.1}),
        fit_earth_removal=False,kernel=load_kernel(tmp_path)[0],tangent_kernel=load_tangent(tmp_path)[0],
        clock_hypothesis='nominal_200Hz',processing_hypothesis='unsubtracted_increment_hypothesis',
        maximum_interval_s=.0075,gravity_mps2=9.81,disc_radius_m=6371000.)
    charges=[]
    options={} if stopping=='ordinary' else dict(stopping=stopping)
    fit=implementation().fit_training(problem,'flat_still',start=[.1],maximum_evaluations=20,
        reserve=lambda **v:charges.append(v),**options)
    assert fit['converged'] and fit['evaluations']==len(charges)<=20
    assert all(v==dict(native_calls=1,packet_visits=80*9) for v in charges)
    assert fit['active_parameters']==['accel_bias_x']
    assert fit['prediction_receiver_positions_used_in_training'] is False
    assert fit['scientific_decision']=='abstain'
    if stopping=='near_zero':assert fit['near_zero_probe']['fresh_evaluations']==2


def test_unknown_stopping_policy_is_rejected_before_any_charge():
    charges=[]
    with pytest.raises(ValueError,match='stopping'):
        implementation().fit_training(None,'control',start=[],maximum_evaluations=20,
            reserve=lambda **v:charges.append(v),stopping='unknown')
    assert not charges


def test_near_zero_control_definition_preserves_geometry_and_allowances():
    from lll.ilvis0_forecast_controls import recipe,control_tasks
    old=recipe();new=recipe(stopping='near_zero')
    assert {k:v for k,v in new.items() if k!='stopping'}==old
    tasks=control_tasks(stopping='near_zero')
    assert len(tasks)==24 and all(t['payload']['stopping']=='near_zero' for t in tasks)
    assert sum(t['limits']['native_calls'] for t in tasks)==14424


def test_near_zero_preparation_requires_software_qualification_before_creating_files(tmp_path):
    from lll.ilvis0_forecast_controls import prepare
    with pytest.raises(ValueError,match='software qualification'):
        prepare(tmp_path,identity='missing-software-proof',stopping='near_zero')
    assert not (tmp_path/'data').exists()


@pytest.mark.parametrize('model',range(3))
@pytest.mark.parametrize('profile',[False,True])
@pytest.mark.parametrize('clock',['header_elapsed','nominal_200Hz'])
def test_closed_form_control_has_explicit_units_and_independent_truth(model,profile,clock):
    name='lll.ilvis0_forecast_controls'
    assert importlib.util.find_spec(name) is not None, 'closed-form forecast controls missing'
    controls=__import__(name,fromlist=['case_arrays'])
    case=controls.case_arrays(model,profile,clock)
    assert case['dt'].shape==(4800,) and case['gps'].shape==(23,3)
    assert np.sum(case['dt'])==pytest.approx(24.)
    assert case['gps'][:,0]==pytest.approx(0.)
    assert case['gps'][:,2]==pytest.approx(20.)
    rate=np.diff(case['gps'][:,1])/np.diff(case['times'])
    radius=6378137.+20 if model<2 else 6371000.*np.pi/2
    assert rate==pytest.approx(220./radius)
    earth=np.array([7.292115e-5 if model==0 else 0.,0.,0.])
    transport=np.array([220./radius,0.,0.]) if model<2 else np.array([0.,0.,-220./radius])
    removal=np.array([.35*7.292115e-5 if profile else 0.,0.,0.])
    rotation=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]])
    assert case['theta']/case['dt'][:,None]==pytest.approx(np.tile(rotation.T@(earth+transport-removal),(4800,1)))
    force=rotation.T@(np.cross(2*earth+transport,[0.,220.,0.])-[0.,0.,9.81])
    assert case['dv']/case['dt'][:,None]==pytest.approx(np.tile(force,(4800,1)))


def test_control_tasks_pass_shared_engine_validation_before_preparation():
    from lll.ilvis0_forecast_controls import control_tasks
    from lll.ilvis0_control_shards import _tasks
    tasks=control_tasks()
    assert len(_tasks(tasks,1))==24
    assert sum(t['limits']['native_calls'] for t in tasks)==14424
    assert all(t['limits']['bound_calls']==t['limits']['bound_steps']==0 for t in tasks)


def test_adapter_supports_the_shared_workers_standalone_loader(tmp_path):
    from pathlib import Path
    path=Path(__file__).parents[1]/'lll/ilvis0_forecast_controls.py'
    spec=importlib.util.spec_from_file_location('_standalone_forecast_controls',path)
    adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
    input_=tmp_path/'recipe.json';input_.write_text('{}')
    context=type('Context',(),{'input_path':lambda self:input_})()
    with pytest.raises(ValueError,match='recipe differs'):adapter.evaluate({},context)
