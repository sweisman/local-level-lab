# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def settings():
    import numpy as np
    gyro=np.array([[.02,.004,0.],[.004,.03,.002],[0.,.002,.01]])
    accel=gyro*3
    return dict(gyro_point_covariance=gyro,accel_point_covariance=accel,
        gyro_bias_covariance=gyro*.3,accel_bias_covariance=accel*.2,
        gyro_bias_tau_s=.3,accel_bias_tau_s=.7)


def generate(dt,**changes):
    import numpy as np
    from lll.measurement_noise import perturb_linear_rate_points
    charges=[];options=settings();options.update(changes)
    result=perturb_linear_rate_points(np.zeros((len(dt),3)),np.zeros((len(dt),3)),dt,
        seed=137,maximum_steps=len(dt),reserve=lambda **work:charges.append(work),**options)
    return result,charges


def test_rate_point_noise_matches_independent_sample_formula_and_shares_endpoints():
    import numpy as np
    dt=np.array([.005,.007,.004]);result,charges=generate(dt)
    assert charges==[dict(noise_normal_variates=12*(len(dt)+1))]
    for sensor,field in (('gyro','theta'),('accel','dv')):
        noise=result['noise'][sensor]
        white=noise['white_points'];bias=noise['bias_states']
        expected=((white[:-1]+white[1:])+(bias[:-1]+bias[1:]))*(dt[:,None]/2)
        np.testing.assert_allclose(result[field],expected,rtol=1e-15,atol=1e-17)
        np.testing.assert_array_equal(noise['white_increments'],(white[:-1]+white[1:])*(dt[:,None]/2))
    assert result['input_error_law']=='linear_rate_points'


def test_rate_point_extension_preserves_complete_earlier_noise_bitwise():
    import numpy as np
    short,_=generate([.005,.007]);long,_=generate([.005,.007,.004,.006])
    for field in ('theta','dv','dt'):np.testing.assert_array_equal(short[field],long[field][:2])
    for sensor in ('gyro','accel'):
        for field in ('white_points','bias_states'):
            np.testing.assert_array_equal(short['noise'][sensor][field],long['noise'][sensor][field][:3])


def test_rate_point_generator_uses_independent_named_streams():
    import numpy as np
    first,_=generate([.005,.007]);second,_=generate([.005,.007],gyro_point_covariance=np.eye(3))
    np.testing.assert_array_equal(first['dv'],second['dv'])
    np.testing.assert_array_equal(first['noise']['gyro']['bias_states'],second['noise']['gyro']['bias_states'])
    assert not np.array_equal(first['theta'],second['theta'])


def test_zero_rate_point_noise_preserves_input_increments():
    import numpy as np
    result,_=generate([.005,.007],**{key:np.zeros((3,3)) for key in settings() if key.endswith('covariance')})
    np.testing.assert_array_equal(result['theta'],np.zeros((2,3)))
    np.testing.assert_array_equal(result['dv'],np.zeros((2,3)))


@pytest.mark.parametrize('bad',['covariance','time','tau','shape','reserve'])
def test_invalid_rate_point_noise_fails_before_charge_or_draw(bad):
    import numpy as np
    from lll.measurement_noise import perturb_linear_rate_points
    theta=np.zeros((2,3));dv=theta.copy();dt=[.005,.007];options=settings();charges=[]
    if bad=='covariance':options['gyro_point_covariance']=-np.eye(3)
    elif bad=='time':dt=[.005,0.]
    elif bad=='tau':options['accel_bias_tau_s']=0.
    elif bad=='shape':theta=np.zeros((3,3))
    reserve=None if bad=='reserve' else lambda **counts:charges.append(counts)
    with pytest.raises(ValueError):perturb_linear_rate_points(theta,dv,dt,seed=137,maximum_steps=2,
        reserve=reserve,**options)
    assert not charges


def test_generated_rate_point_covariance_matches_independent_closed_form(monkeypatch):
    import numpy as np
    from lll import measurement_noise
    dt=np.array([.005,.007]);epochs=np.r_[0.,np.cumsum(dt)]
    labels=['imu.'+sensor+'.rate_points.'+component for sensor in ('gyro','accel')
        for component in ('white','bias')]
    matrix=np.empty((12,36))
    for direction in range(36):
        class Impulse:
            def __init__(self,label):self.label=label
            def standard_normal(self,shape):
                assert shape==(3,3)
                out=np.zeros(shape)
                if labels.index(self.label)==direction//9:out.ravel()[direction%9]=1.
                return out
        monkeypatch.setattr(measurement_noise,'stream',lambda seed,label:Impulse(label))
        result,charges=generate(dt)
        assert charges==[dict(noise_normal_variates=36)]
        matrix[:,direction]=np.column_stack((result['theta'],result['dv'])).ravel()
    expected=np.zeros((12,12));weights=np.array([[dt[0]/2,dt[0]/2,0.],[0.,dt[1]/2,dt[1]/2]])
    mapping=np.kron(weights,np.eye(3));values=settings()
    for offset,sensor in ((0,'gyro'),(3,'accel')):
        temporal=np.exp(-abs(epochs[:,None]-epochs[None,:])/values[sensor+'_bias_tau_s'])
        points=np.kron(np.eye(3),values[sensor+'_point_covariance'])
        points+=np.kron(temporal,values[sensor+'_bias_covariance'])
        indices=np.r_[np.arange(offset,offset+3),np.arange(offset+6,offset+9)]
        expected[np.ix_(indices,indices)]=mapping@points@mapping.T
    np.testing.assert_allclose(matrix@matrix.T,expected,rtol=3e-13,atol=1e-20)
    assert np.linalg.norm(expected[:3,6:9])>0
