# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll import ilvis0_geographic_controls as controls
from lll import ilvis0_exploratory as explore, ilvis0_shape as shape


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    path=tmp_path_factory.mktemp('geographic-kernels')
    return explore.load_kernel(path)[0],shape.load_tangent(path)[0]


@pytest.mark.parametrize('model',explore.MODELS)
@pytest.mark.parametrize('clock',('nominal','variable'))
def test_independent_increments_predict_external_receiver_track(model,clock,kernels):
    f=controls.fixture(model,clock)
    p=controls.problem(f,*kernels)
    point=controls.truth_point(f,p)
    predicted,jac,boundaries=p.prediction_tangent(point,model)
    assert controls.position_error(f,predicted)<.002
    assert np.max(abs(predicted-p.predict(point,model)))<1e-8
    assert boundaries==0
    assert np.all(np.isfinite(jac))
    assert f['gps_times'][0]>p.bounds.limits['time_offset']
    assert f['gps_times'][-1]+p.bounds.limits['time_offset']<p.ends[-1]


def test_generator_obeys_external_time_and_known_geographic_metrics():
    globe=controls.fixture('sphere_rotating','nominal')
    disc=controls.fixture('flat_still','nominal')
    assert np.all(globe['dt']==.005)
    assert np.all(globe['gps'][:,0]==0)
    assert np.all(globe['gps'][:,2]==1000)
    t=globe['gps_times']+globe['truth']['time_offset']
    np.testing.assert_allclose(globe['gps'][:,1],220*t/6379137.,atol=1e-15)
    t=disc['gps_times']+disc['truth']['time_offset']
    np.testing.assert_allclose(disc['gps'][:,1],220*t/(6371000*np.pi/2),atol=1e-15)
    # Gravity/Coriolis increments differ even though both physical tracks are level.
    assert np.max(abs(globe['dv']-disc['dv']))>1e-5


def test_invalid_models_and_clocks_do_not_generate_controls():
    with pytest.raises(ValueError): controls.fixture('unknown','nominal')
    with pytest.raises(ValueError): controls.fixture('flat_still','unknown')


def test_external_receiver_times_expose_an_uncorrected_clock_scale(kernels):
    f=controls.fixture('sphere_rotating','nominal')
    altered=dict(f,dt=f['dt']*1.00005)
    p=controls.problem(altered,*kernels)
    assert controls.position_error(f,p.predict(controls.truth_point(f,p),f['model']))>.01


def test_actual_tangent_derivatives_agree_with_separate_value_differences(kernels):
    f=controls.fixture('sphere_rotating','variable'); p=controls.problem(f,*kernels)
    point=controls.truth_point(f,p)*.8
    _,jac,_=p.prediction_tangent(point,f['model'])
    for k in range(len(point)):
        step=np.eye(len(point))[k]*1e-3
        fd=(p.predict(point+step,f['model'])-p.predict(point-step,f['model'])).ravel()/2e-3
        # Convert coordinates to metres before comparing small angular derivatives.
        assert np.max(abs((fd-jac[:,k]).reshape(-1,3)*f['metric']))<2e-5


def test_bounded_nonlinear_fit_recovers_predictions_from_poor_initialization(kernels):
    f=controls.fixture('sphere_rotating','nominal')
    row=controls.run_fit(f,*kernels,strategy='original',start_id='opposed')
    assert row['fit']['converged']
    assert row['maximum_position_error_m']<.002
    assert row['actual_tangent_sweeps']==row['fit']['evaluations']
    assert row['actual_value_sweeps']==2
    assert row['actual_tangent_sweeps']+row['actual_value_sweeps']<=200
    assert row['observed_fit_starts']==0

