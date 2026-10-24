# SPDX-License-Identifier: AGPL-3.0-or-later
import math
import pytest


def settings():
    return dict(gyro_white=.003,accel_white=.02,gyro_bias_sd=.004,accel_bias_sd=.03,
        gyro_bias_tau_s=2.4,accel_bias_tau_s=4.1,gravity=9.7)


def ou_integral(t,u,*,power,tau):
    """Independent quadrature, split at the covariance kernel's cusp."""
    import numpy as np
    if not t or not u:return 0.
    nodes,weights=np.polynomial.legendre.leggauss(40)
    def integrate(function,start,end):
        if end<=start:return 0.
        scale=(end-start)/2
        return scale*sum(w*function(start+(x+1)*scale) for x,w in zip(nodes,weights))
    def outer(s):
        f=lambda r:((u-r)**power/(2 if power==2 else 1))*math.exp(-abs(s-r)/tau)
        inner=integrate(f,0.,min(s,u))+integrate(f,min(s,u),u)
        return ((t-s)**power/(2 if power==2 else 1))*inner
    return integrate(outer,0.,min(t,u))+integrate(outer,min(t,u),t)


def independent_covariance(times,values,receiver):
    import numpy as np
    from lll.inertial_error_budget import level_position_covariance
    c=np.zeros((3*len(times),3*len(times)))
    for i,t in enumerate(times):
        for j,u in enumerate(times):
            white=level_position_covariance(t,u,**{k:values[k] for k in ('gyro_white','accel_white','gravity')})
            force=values['accel_bias_sd']**2*ou_integral(t,u,power=1,tau=values['accel_bias_tau_s'])
            gyro=values['gravity']**2*values['gyro_bias_sd']**2*ou_integral(t,u,power=2,tau=values['gyro_bias_tau_s'])
            c[3*i:3*i+3,3*j:3*j+3]=np.diag([white['north_east_m2']+force+gyro]*2+[white['up_m2']+force])
            if i==j:c[3*i:3*i+3,3*j:3*j+3]+=receiver@receiver.T
    return c


@pytest.mark.parametrize('times',[(0.,1.2,2.7),(0.,.7,3.)])
def test_level_ou_covariance_matches_independent_stationary_bias_integrals(times):
    import numpy as np
    from lll.inertial_error_budget import ou_level_innovations
    d=np.array([[.1,0.,0.],[.01,.2,0.],[.02,-.03,.3]])
    op=ou_level_innovations(times,**settings(),receiver_loading=d,maximum_bytes=1024*1024)
    lower=op.unwhiten(np.eye(3*len(times)))
    np.testing.assert_allclose(lower@lower.T,independent_covariance(times,settings(),d),rtol=5e-10,atol=1e-11)
    assert op.state_dimension==13 and op.error_law_calibrated is False


@pytest.mark.parametrize('dt',[1/300,.3,2.])
def test_level_ou_step_matches_separate_endpoint_and_integral_moments(dt):
    import numpy as np
    from lll.inertial_error_budget import ou_level_dynamics
    from lll.measurement_noise import ou_moments
    values=settings();f,b=ou_level_dynamics(dt,**values);q=b@b.T
    for angle,bias,white,sd,tau in ((0,3,values['gyro_white'],values['gyro_bias_sd'],values['gyro_bias_tau_s']),
            (10,12,values['accel_white'],values['accel_bias_sd'],values['accel_bias_tau_s'])):
        m={k:v[0] for k,v in ou_moments(np.array([dt]),tau_s=tau).items()}
        assert f[bias,bias]==pytest.approx(m['rho'],rel=2e-12)
        assert f[angle,bias]==pytest.approx(-tau*math.expm1(-dt/tau),rel=2e-12)
        assert q[bias,bias]==pytest.approx(sd*sd*m['state_variance'],rel=2e-11)
        assert q[angle,bias]==pytest.approx(sd*sd*m['state_integral_covariance'],rel=2e-11)
        assert q[angle,angle]==pytest.approx(white*white*dt+sd*sd*m['integral_variance'],rel=2e-11)


def test_level_ou_future_prediction_matches_independent_dense_conditioning():
    import numpy as np
    from lll.inertial_error_budget import ou_level_innovations
    times=[0.,.4,1.1,2.];d=np.diag([.1,.2,.3]);op=ou_level_innovations(times,**settings(),receiver_loading=d,maximum_bytes=1024*1024)
    c=independent_covariance(times,settings(),d);earlier=np.sin(np.arange(6.))
    _,state=op.apply_block(earlier,first_epoch=0);answer=op.conditional_marginals(state=state)
    expected_mean=c[6:,:6]@np.linalg.solve(c[:6,:6],earlier)
    expected_cov=c[6:,6:]-c[6:,:6]@np.linalg.solve(c[:6,:6],c[:6,6:])
    np.testing.assert_allclose(answer['mean'].ravel(),expected_mean,rtol=5e-10,atol=1e-11)
    for i,block in enumerate(answer['covariance']):
        np.testing.assert_allclose(block,expected_cov[3*i:3*i+3,3*i:3*i+3],rtol=5e-10,atol=1e-11)
    assert answer['later_observations_used'] is False


@pytest.mark.parametrize('fault',['zero','negative','tau','nonfinite'])
def test_level_ou_step_rejects_unsupported_driver_values(fault):
    from lll.inertial_error_budget import ou_level_dynamics
    values=settings()
    if fault=='zero':values['gyro_white']=0.
    elif fault=='negative':values['accel_bias_sd']=-.01
    elif fault=='tau':values['gyro_bias_tau_s']=0.
    else:values['gravity']=float('nan')
    with pytest.raises(ValueError):ou_level_dynamics(.5,**values)


def test_level_ou_storage_cap_precedes_matrix_exponential(monkeypatch):
    import numpy as np
    import scipy.linalg
    from lll.inertial_error_budget import ou_level_innovations
    def forbidden(*args,**kwargs):raise AssertionError('storage cap must precede exponentiation')
    monkeypatch.setattr(scipy.linalg,'expm',forbidden)
    with pytest.raises(ValueError,match='storage'):
        ou_level_innovations(np.arange(1.,64081.),**settings(),receiver_loading=np.eye(3),maximum_bytes=1)


@pytest.mark.parametrize('dt',[1/300,1.,400.])
def test_level_ou_step_handles_declared_stress_scales_without_variance_repair(dt):
    import numpy as np
    from lll.inertial_error_budget import ou_level_dynamics
    from lll.measurement_noise import ou_moments
    # Explicit software stress values, not measured instrument specifications.
    q=math.radians(.02)/60;sd=math.radians(.05)/3600;tau=600.
    f,b=ou_level_dynamics(dt,gyro_white=q,accel_white=2e-4,gyro_bias_sd=sd,
        accel_bias_sd=5e-5,gyro_bias_tau_s=tau,accel_bias_tau_s=300.,gravity=9.80665)
    covariance=b@b.T;m={k:v[0] for k,v in ou_moments(np.array([dt]),tau_s=tau).items()}
    assert np.all(np.isfinite(f)) and np.all(np.diag(covariance)>0)
    assert covariance[0,0]==pytest.approx(q*q*dt+sd*sd*m['integral_variance'],rel=2e-11)
    assert covariance[0,3]==pytest.approx(sd*sd*m['state_integral_covariance'],rel=2e-11)
    assert covariance[3,3]==pytest.approx(sd*sd*m['state_variance'],rel=2e-11)
