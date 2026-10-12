# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll import ilvis0_geographic_controls as geographic, ilvis0_latitude_controls as latitude
from lll import ilvis0_estimator as estimator, ilvis0_exploratory as explore, ilvis0_shape as shape
import ilvis0_uncertainty_adapter_controls as controls


def api():
    from lll import ilvis0_uncertainty_adapter as adapter
    return adapter


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    path=tmp_path_factory.mktemp('uncertainty-kernels')
    return explore.load_kernel(path)[0],shape.load_tangent(path)[0]


@pytest.mark.parametrize('model',explore.MODELS)
@pytest.mark.parametrize('degrees',(-45.,45.))
def test_native_adapter_checks_all_27_columns_and_off_packet_receiver_epochs(model,degrees,kernels):
    row=controls.run_case(model,degrees,kernels)
    assert row['truth_maximum_position_error_m']<.002
    assert row['maximum_derivative_error_m_per_normalized_parameter']<2e-4
    assert len(row['parameters'])==27 and len(row['derivative_errors_by_parameter'])==27
    assert row['training_epochs']==16 and row['prediction_epochs']==8
    assert row['geometry']['parameters']==27
    assert row['future_probe_shape']==[3,24]
    assert row['native_sweeps']=={'tangent':2,'value':56} and row['all_sweeps_complete']


def test_charge_occurs_before_call_and_failed_work_remains_charged():
    a=api();events=[];budget=a.SweepBudget(1,0,charge_callback=lambda row:events.append(dict(row)))
    def fail():
        assert events[0]['status']=='started'
        raise ValueError('control failure')
    with pytest.raises(ValueError):budget.call('tangent',fail)
    assert budget.counts['tangent']==1 and budget.journal[0]['status']=='failed'
    with pytest.raises(estimator.EvaluationLimit):budget.call('tangent',fail)


def test_physical_longitude_difference_wraps_without_modifying_coordinates():
    a=api();before=np.array([[0.,np.pi-1e-6,10.]])
    after=np.array([[0.,-np.pi+1e-6,12.]])
    original=after.copy()
    np.testing.assert_allclose(a.physical_delta(after,before,[[2.,3.,1.]]),[[0.,6e-6,2.]])
    np.testing.assert_array_equal(after,original)


@pytest.mark.parametrize('limits',[(0,0),(-1,2),(True,2),(1,-1)])
def test_invalid_sweep_allowances_fail(limits):
    with pytest.raises(ValueError):api().SweepBudget(*limits)


def test_training_geometry_does_not_use_future_probe_changes(kernels):
    a=api();f=geographic.fixture('sphere_rotating','nominal');p=geographic.problem(f,*kernels)
    point=geographic.truth_point(f,p)*.5;probes=np.array([point,point+np.eye(6)[0]*1e-4])
    metric=np.tile(f['metric'],(24,1));cov=.01**2*np.eye(72)
    first=a.evaluate(p,f['model'],point,probes,metric,cov,16,a.SweepBudget(1,1))
    # Real supplied-prediction diagnostic: future mean/J/probes can vary arbitrarily.
    predicted,jac,_=p.prediction_tangent(point,f['model'])
    supplied=np.array([p.predict(row,f['model']) for row in probes])
    predicted[16:]+=1.;jac[48:]*=100.;supplied[:,16:]-=1.
    second=a.from_predictions(point,probes,metric,cov,16,list(p.bounds.active),predicted,jac,supplied)
    assert first['geometry']==second['geometry']


def test_outside_parameter_probe_is_rejected_before_native_calls(kernels):
    a=api();f=geographic.fixture('sphere_rotating','nominal');p=geographic.problem(f,*kernels)
    point=geographic.truth_point(f,p);probes=np.array([point,point+10.])
    budget=a.SweepBudget(1,1)
    with pytest.raises(ValueError):a.evaluate(p,f['model'],point,probes,np.tile(f['metric'],(24,1)),np.eye(72),16,budget)
    assert budget.counts=={'tangent':0,'value':0}
