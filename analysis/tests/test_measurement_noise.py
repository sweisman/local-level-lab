# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent timing/units/covariance controls for synthetic measurement noise."""
import pytest


def test_component_streams_are_reproducible_independent_and_do_not_touch_global_rng():
    import numpy as np
    from lll.measurement_noise import stream
    np.random.seed(812);before=np.random.get_state()
    a=stream(12,'gyro.white').standard_normal(50)
    assert np.array_equal(a,stream(12,'gyro.white').standard_normal(50))
    assert not np.array_equal(a,stream(12,'receiver.white').standard_normal(50))
    assert all(np.array_equal(x,y) for x,y in zip(before,np.random.get_state(),strict=True))


def test_white_increment_units_and_nonuniform_intervals_match_independent_draws():
    import numpy as np
    from lll.measurement_noise import stream,white_increments
    dt=np.array([.002,.005,.01]);psd=np.diag([1.,4.,9.]);before=dt.copy()
    expected=stream(11,'white').standard_normal((3,3))*np.sqrt(dt[:,None])*[1.,2.,3.]
    actual=white_increments(dt,psd,rng=stream(11,'white'),maximum_steps=3)
    assert np.allclose(actual,expected,rtol=1e-15,atol=0) and np.array_equal(dt,before)
    # PSD is rate squared times seconds. Increments scale with sqrt(dt), not dt.
    assert np.allclose(actual/np.sqrt(dt[:,None]),expected/np.sqrt(dt[:,None]))


@pytest.mark.parametrize('ratio',[1e-8,1e-5,.01,.1,1.,10.])
def test_integrated_ou_moments_match_high_precision_independent_integrals(ratio):
    import decimal
    from lll.measurement_noise import ou_moments
    with decimal.localcontext() as context:
        context.prec=75
        x=decimal.Decimal(str(ratio));tau=decimal.Decimal('17');rho=(-x).exp();one=decimal.Decimal(1)
        expected=[rho,one-rho*rho,tau*(one-rho)**2,
            tau*tau*(2*x-3+4*rho-(-2*x).exp())]
    actual=ou_moments([float(tau)*ratio],tau_s=float(tau))
    for key,value in zip(('rho','state_variance','state_integral_covariance','integral_variance'),expected,strict=True):
        assert actual[key][0]==pytest.approx(float(value),rel=2e-12,abs=1e-24)


def test_ou_integration_keeps_state_increment_correlation_and_stationary_variance():
    import numpy as np
    from lll.measurement_noise import stream,ou_increments
    # Independent stationary-OU formula for an interval of length T=2, tau=3.
    t=2.;tau=3.;rho=np.exp(-t/tau);variance=2*tau*(t-tau*(1-rho))
    rng=stream(8,'ensemble');values=[]
    for _ in range(4096):
        sample=ou_increments([t],np.eye(3),tau_s=tau,rng=rng,maximum_steps=1)
        values.append([sample['increments'][0,0],sample['states'][0,0],sample['states'][1,0]])
    covariance=np.cov(np.array(values),rowvar=False,bias=True)
    expected=np.array([[variance,tau*(1-rho),tau*(1-rho)],[tau*(1-rho),1.,rho],[tau*(1-rho),rho,1.]])
    assert np.allclose(covariance,expected,rtol=.085,atol=.04)


def test_ou_path_can_continue_without_redrawing_bias_or_resetting_noise_origin():
    import numpy as np
    from lll.measurement_noise import stream,ou_increments
    dt=[.003,.005,.002,.01];covariance=np.diag([.2,.3,.4])
    whole=ou_increments(dt,covariance,tau_s=10.,rng=stream(11,'bias'),maximum_steps=4)
    rng=stream(11,'bias')
    left=ou_increments(dt[:2],covariance,tau_s=10.,rng=rng,maximum_steps=2)
    right=ou_increments(dt[2:],covariance,tau_s=10.,rng=rng,initial=left['states'][-1],maximum_steps=2)
    assert np.array_equal(whole['increments'],np.concatenate((left['increments'],right['increments'])))
    assert np.array_equal(whole['states'],np.concatenate((left['states'],right['states'][1:])))


def test_zero_noise_preserves_measurements_and_does_not_repair_invalid_covariance():
    import numpy as np
    from lll.measurement_noise import stream,white_increments,ou_increments
    assert not white_increments([.005]*3,np.zeros((3,3)),rng=stream(1,'zero'),maximum_steps=3).any()
    result=ou_increments([.005]*3,np.zeros((3,3)),tau_s=10.,rng=stream(1,'bias'),maximum_steps=3)
    assert not result['states'].any() and not result['increments'].any()
    with pytest.raises(ValueError):white_increments([.005],np.diag([1.,-1e-30,1.]),rng=stream(1,'bad'),maximum_steps=1)


@pytest.mark.parametrize('dt,cap',[([0.],1),([-1.],1),([float('nan')],1),([.01,.01],1),([.01],True)])
def test_increment_noise_rejects_invalid_timing_or_work_allowance_before_draw(dt,cap):
    from lll.measurement_noise import white_increments
    class NoDraw:
        def standard_normal(self,*args):raise AssertionError('invalid data consumed randomness')
    with pytest.raises(ValueError):white_increments(dt,[[1,0,0],[0,1,0],[0,0,1]],rng=NoDraw(),maximum_steps=cap)


def test_receiver_noise_preserves_prefix_across_later_times_and_fixed_drift_origin():
    import numpy as np
    from lll.measurement_noise import receiver_errors
    from lll.ilvis0_error_model import Spec
    spec=Spec(white=np.eye(3),components=((4.,.3*np.eye(3)),),offset=.4*np.eye(3),
        drift=.2*np.eye(3),drift_origin_s=0.,drift_span_s=10.)
    times=np.array([1.,2.,5.,9.,20.]);before=times.copy()
    whole=receiver_errors(times,spec,seed=22,maximum_epochs=5)
    prefix=receiver_errors(times[:3],spec,seed=22,maximum_epochs=3)
    assert np.array_equal(whole[:3],prefix) and np.array_equal(times,before)
    assert not np.array_equal(whole,receiver_errors(times,spec,seed=23,maximum_epochs=5))


def test_receiver_draws_reproduce_independent_cross_axis_and_time_covariance():
    import numpy as np
    from lll.measurement_noise import receiver_errors
    from lll.ilvis0_error_model import Spec
    times=np.array([0.,2.]);matrix=np.array([[1.,.2,-.1],[.2,2.,.3],[-.1,.3,3.]])
    spec=Spec(white=.1*matrix,components=((3.,.6*matrix),),offset=.2*matrix,
        drift=.1*matrix,drift_origin_s=-1.,drift_span_s=10.)
    values=np.array([receiver_errors(times,spec,seed=i,maximum_epochs=2).ravel() for i in range(4096)])
    # This expectation uses the written covariance law, not the whitening implementation.
    u=(times+1)/10
    expected=np.kron(.1*np.eye(2)+.6*np.exp(-abs(times[:,None]-times[None,:])/3)+.2+.1*np.outer(u,u),matrix)
    assert np.max(abs(np.cov(values,rowvar=False,bias=True)-expected)/np.sqrt(np.outer(np.diag(expected),np.diag(expected))))<.075


def test_receiver_invalid_transforms_and_times_fail_before_random_generation():
    import numpy as np
    from lll.measurement_noise import receiver_errors
    from lll.ilvis0_error_model import Spec
    spec=Spec(white=np.eye(3))
    for kwargs in (dict(times=[1.,1.]),dict(times=[0.,1.],transforms=np.zeros((2,3,3))),
            dict(times=[0.,1.],maximum_epochs=1),dict(times=[0.,float('inf')])):
        with pytest.raises(ValueError):receiver_errors(spec=spec,seed=12,**{'maximum_epochs':2,**kwargs})


def test_sensor_perturbations_preserve_inputs_and_keep_components_independent():
    import numpy as np
    from lll.measurement_noise import perturb_imu
    theta=np.ones((8,3));dv=2*theta;dt=np.full(8,.005)
    settings=dict(seed=17,gyro_white_psd=1e-8*np.eye(3),accel_white_psd=1e-6*np.eye(3),
        gyro_bias_covariance=1e-10*np.eye(3),accel_bias_covariance=1e-8*np.eye(3),
        gyro_bias_tau_s=60.,accel_bias_tau_s=30.,maximum_steps=8)
    result=perturb_imu(theta,dv,dt,**settings)
    changed=perturb_imu(theta,dv,dt,**dict(settings,gyro_white_psd=4e-8*np.eye(3)))
    assert np.array_equal(changed['dv'],result['dv']) and not np.array_equal(changed['theta'],result['theta'])
    assert np.array_equal(theta,np.ones((8,3))) and np.array_equal(dv,np.full((8,3),2.))
    assert np.array_equal(result['dt'],dt) and not np.shares_memory(result['dt'],dt)
    prefix=perturb_imu(theta[:4],dv[:4],dt[:4],**dict(settings,maximum_steps=4))
    assert np.array_equal(result['theta'][:4],prefix['theta']) and np.array_equal(result['dv'][:4],prefix['dv'])


def test_invalid_sensor_arrays_are_rejected_before_noise_is_drawn():
    import numpy as np
    from lll.measurement_noise import perturb_imu
    settings=dict(seed=17,gyro_white_psd=np.eye(3),accel_white_psd=np.eye(3),
        gyro_bias_covariance=np.eye(3),accel_bias_covariance=np.eye(3),
        gyro_bias_tau_s=60.,accel_bias_tau_s=30.,maximum_steps=8)
    with pytest.raises(ValueError):perturb_imu(np.zeros((8,2)),np.zeros((8,3)),[.005]*8,**settings)
