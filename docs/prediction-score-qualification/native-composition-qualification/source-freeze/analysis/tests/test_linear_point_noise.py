# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


@pytest.fixture(scope='session')
def point_work():
    import time
    return dict(started=time.monotonic(),cases=0)


@pytest.fixture(autouse=True)
def finite_point_allowance(point_work):
    import time
    point_work['cases']+=1
    assert point_work['cases']<=16 and time.monotonic()-point_work['started']<120
    yield
    assert time.monotonic()-point_work['started']<120


def settings(mode='mixed'):
    import numpy as np
    root=np.array([[.02,0.,0.],[.003,.03,0.],[-.002,.004,.04]])
    white=root@root.T if mode in ('white','mixed') else np.zeros((3,3))
    bias=root@root.T*.1 if mode in ('bias','mixed') else np.zeros((3,3))
    return dict(gyro_point_covariance=white,accel_point_covariance=white*4,
        gyro_bias_covariance=bias,accel_bias_covariance=bias*5,
        gyro_bias_tau_s=.02,accel_bias_tau_s=.04)


def driver_covariance(noise,dt):
    import numpy as np
    n=len(dt);width=12+12*n;state=np.zeros((12,width))
    state[:,:12]=noise.initial_loading()[9:];outputs=[]
    for i,interval in enumerate(dt):
        root,rho,mean=noise.at(float(interval));draw=np.zeros((12,width))
        draw[:,12+12*i:24+12*i]=np.eye(12)
        outputs.append(mean@state+root[:6]@draw)
        state=rho[:,None]*state+root[6:]@draw
    loading=np.vstack(outputs)
    return loading@loading.T


def dense_point_covariance(dt,values):
    import numpy as np
    times=np.r_[0.,np.cumsum(dt)];n=len(dt);integrate=np.zeros((n,n+1))
    for i,interval in enumerate(dt):integrate[i,i:i+2]=interval/2
    result=np.zeros((6*n,6*n))
    for start,white,bias,tau in ((0,values['gyro_point_covariance'],values['gyro_bias_covariance'],values['gyro_bias_tau_s']),
            (3,values['accel_point_covariance'],values['accel_bias_covariance'],values['accel_bias_tau_s'])):
        point_cov=np.kron(np.eye(n+1),white)+np.kron(np.exp(-abs(times[:,None]-times[None,:])/tau),bias)
        weights=np.kron(integrate,np.eye(3));family=weights@point_cov@weights.T
        indices=np.array([6*i+start+j for i in range(n) for j in range(3)])
        result[np.ix_(indices,indices)]=family
    return result


@pytest.mark.parametrize('mode',['white','bias','mixed','zero'])
@pytest.mark.parametrize('unequal',[False,True])
def test_linear_point_noise_matches_independent_trapezoidal_covariance(mode,unequal):
    import numpy as np
    from lll.linear_point_noise import LinearPointNoise
    dt=np.resize(np.array([1/300,.005,.0045,.006]),12) if unequal else np.full(12,1/300)
    values=settings(mode);noise=LinearPointNoise(**values)
    actual=driver_covariance(noise,dt);expected=dense_point_covariance(dt,values)
    np.testing.assert_allclose(actual,expected,rtol=3e-13,atol=1e-21)
    assert noise.hidden_dimension==12 and noise.initial_loading().shape==(21,12)
    if mode=='white':
        for i in range(len(dt)-1):
            np.testing.assert_allclose(actual[6*i:6*i+3,6*i+6:6*i+9],
                dt[i]*dt[i+1]/4*values['gyro_point_covariance'],rtol=2e-14,atol=1e-22)
        assert not np.any(actual[:6,12:])
    if mode=='zero':assert not np.any(actual)


def test_linear_point_noise_preserves_exact_zero_axes():
    import numpy as np
    from lll.linear_point_noise import LinearPointNoise
    values=settings()
    for key in ('gyro_point_covariance','accel_point_covariance','gyro_bias_covariance','accel_bias_covariance'):
        values[key]=np.diag([values[key][0,0],0.,0.])
    noise=LinearPointNoise(**values);cov=driver_covariance(noise,np.array([.005,.007]))
    np.testing.assert_array_equal(cov[[1,2,4,5,7,8,10,11]],np.zeros((8,12)))


def test_linear_point_noise_rejects_negative_variance_without_repair():
    import numpy as np
    from lll.linear_point_noise import LinearPointNoise
    values=settings();values['gyro_point_covariance']=np.diag([1.,-1e-20,0.])
    with pytest.raises(ValueError,match='nonnegative'):LinearPointNoise(**values)


@pytest.mark.parametrize('bad',['interval','nan','tau','shape'])
def test_linear_point_noise_rejects_unsupported_inputs(bad):
    import numpy as np
    from lll.linear_point_noise import LinearPointNoise
    values=settings()
    if bad=='tau':values['gyro_bias_tau_s']=0.
    elif bad=='shape':values['gyro_point_covariance']=np.eye(2)
    with pytest.raises(ValueError):
        noise=LinearPointNoise(**values)
        noise.at(-.005 if bad=='interval' else float('nan') if bad=='nan' else .005)


def test_linear_point_bias_conversion_is_not_continuous_ou_integration():
    import numpy as np
    from lll.linear_point_noise import LinearPointNoise
    from lll.measurement_noise import ou_moments
    values=settings('bias');dt=.01;tau=values['gyro_bias_tau_s']
    noise=LinearPointNoise(**values);cov=driver_covariance(noise,np.array([dt]))
    expected=.5*dt*dt*(1+np.exp(-dt/tau))*values['gyro_bias_covariance'][0,0]
    assert cov[0,0]==pytest.approx(expected,rel=2e-14)
    moments={k:v[0] for k,v in ou_moments([dt],tau_s=tau).items()}
    mean=-tau*np.expm1(-dt/tau)
    continuous=(mean*mean+moments['integral_variance'])*values['gyro_bias_covariance'][0,0]
    assert abs(cov[0,0]-continuous)/continuous>.01
