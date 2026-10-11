# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from scipy.integrate import solve_ivp
from scipy.spatial.transform import Rotation

from lll import ilvis0_latitude_controls as latitude
from lll import ilvis0_compensation as correction
from lll import ilvis0_geographic_controls as original
from lll import ilvis0_exploratory as explore


@pytest.fixture(scope='module')
def kernel(tmp_path_factory):
    return correction.load_kernel(tmp_path_factory.mktemp('latitude-kernel'))[0]


@pytest.mark.parametrize('degrees',(-45.,45.))
def test_geographic_vector_signs_and_metrics(degrees):
    e,t,m=latitude.environment('sphere_rotating',degrees)
    phi=np.deg2rad(degrees)
    np.testing.assert_allclose(e,[7.292115e-5*np.cos(phi),0.,-7.292115e-5*np.sin(phi)],atol=1e-16)
    assert t[0]>0 and np.sign(t[2])==-np.sign(degrees)
    assert m[0]>6e6 and 4e6<m[1]<5e6
    e,t,m=latitude.environment('flat_still',degrees)
    np.testing.assert_array_equal(e,np.zeros(3))
    np.testing.assert_allclose(t,[0.,0.,-220/m[1]],atol=1e-16)


def test_euler_body_rate_matches_independent_attitude_derivative():
    f=latitude.fixture('sphere_rotating',45.,'near_roll')
    t=np.array([.12,1.8,8.9]);eps=1e-6
    r,w=latitude.motion(t,f['truth'],True)
    a,_=latitude.motion(t+eps,f['truth'],True); b,_=latitude.motion(t-eps,f['truth'],True)
    k=np.swapaxes(r,-1,-2)@((a-b)/(2*eps))
    np.testing.assert_allclose(w,np.stack((k[:,2,1],k[:,0,2],k[:,1,0]),axis=1),atol=1e-9)


@pytest.mark.parametrize('model',explore.MODELS)
@pytest.mark.parametrize('degrees',(-45.,45.))
@pytest.mark.parametrize('construction',('interior','near_roll'))
def test_known_calibration_prediction_at_latitude(model,degrees,construction,kernel):
    f=latitude.fixture(model,degrees,construction)
    q=correction.problem(f,kernel,'combined',convention='ordinary_rate_integrals')
    p=correction.problem(f,kernel,'baseline',convention='ordinary_rate_integrals')
    truth=original.truth_point(f,q)
    improved=original.position_error(f,q.predict(truth,model))
    baseline=original.position_error(f,p.predict(truth,model))
    assert improved<.02*baseline
    assert improved<.002
    assert np.all(f['gps'][:,0]==np.deg2rad(degrees))
    if construction=='near_roll':assert np.ptp(f['dt'])>0


def test_specific_force_is_transformed_in_the_correct_frame():
    f=latitude.fixture('sphere_rotating',-45.,'near_roll')
    e,t,_=latitude.environment(f['model'],f['latitude_deg'])
    force=np.cross(2*e+t,[0.,220.,0.])-np.array([0.,0.,9.81+f['truth']['gravity_delta']])
    r,_=latitude.motion(np.array([.2,1.,7.]),f['truth'],True)
    body=np.einsum('...ji,j->...i',r,force)
    np.testing.assert_allclose(np.einsum('...ij,...j->...i',r,body),np.broadcast_to(force,(3,3)),atol=1e-14)


def test_finite_increment_convention_matches_independent_continuous_ode():
    f=latitude.fixture('sphere_rotating',45.,'near_roll',convention='already_compensated')
    idx=377; h=f['dt'][idx]; start=np.sum(f['dt'][:idx])
    earth,transport,_=latitude.environment(f['model'],45.)
    force=np.cross(2*earth+transport,[0.,220.,0.])-np.array([0.,0.,9.81+f['truth']['gravity_delta']])
    def ode(u,state):
        c,relative=latitude.motion(np.array(start+u),f['truth'],True)
        w=c.T@(earth+transport)+relative; specific=c.T@force
        x,y,z=w; skew=np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
        r=state[:9].reshape(3,3)
        return np.r_[(r@skew).ravel(),r@specific]
    result=solve_ivp(ode,(0,h),np.r_[np.eye(3).ravel(),np.zeros(3)],method='DOP853',rtol=1e-12,atol=1e-14)
    assert result.success
    angle=f['theta'][idx].copy();angle[2]=(angle[2]-f['truth']['gyro_bias_z']*h)/(1+f['truth']['gyro_gain_z'])
    np.testing.assert_allclose(Rotation.from_rotvec(angle).as_matrix(),result.y[:9,-1].reshape(3,3),atol=2e-14)
    np.testing.assert_allclose(Rotation.from_rotvec(angle/2).apply(f['dv'][idx]),result.y[9:,-1],atol=2e-14)


@pytest.mark.parametrize('model',explore.MODELS)
def test_already_compensated_control_and_double_correction(model,kernel):
    f=latitude.fixture(model,-45.,'interior',convention='already_compensated')
    p=correction.problem(f,kernel,'baseline',convention=f['increment_convention'])
    truth=original.truth_point(f,p)
    good=original.position_error(f,p.predict(truth,model))
    with pytest.raises(ValueError):correction.problem(f,kernel,'combined',convention=f['increment_convention'])
    # Deliberately false label is a diagnostic, never an accepted conversion.
    q=correction.problem(f,kernel,'combined',convention='ordinary_rate_integrals')
    bad=original.position_error(f,q.predict(truth,model))
    assert good<1e-8 and bad>100*max(good,1e-12)


@pytest.mark.parametrize('arguments',(('sphere_rotating',90.,'interior'),('other',45.,'interior'),('sphere_still',45.,'unknown')))
def test_invalid_control_is_rejected(arguments):
    with pytest.raises(ValueError):latitude.fixture(*arguments)


@pytest.mark.parametrize('degrees',(-45.,45.))
def test_non_equatorial_calibration_and_latency_derivatives(degrees,kernel):
    f=latitude.fixture('sphere_rotating',degrees,'near_roll')
    p=correction.problem(f,kernel,'combined',convention=f['increment_convention'])
    point=original.truth_point(f,p)*.8
    _,jac,_=p.prediction_tangent(point,f['model'])
    for axis in range(len(point)):
        step=np.eye(len(point))[axis]*1e-3
        finite=(p.predict(point+step,f['model'])-p.predict(point-step,f['model'])).ravel()/2e-3
        assert np.max(abs((finite-jac[:,axis]).reshape(-1,3)*f['metric']))<2e-5
