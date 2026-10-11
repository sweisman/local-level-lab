# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from scipy.integrate import solve_ivp
from scipy.spatial.transform import Rotation

from lll import ilvis0_compensation as correction
from lll import ilvis0_geographic_controls as controls
from lll import ilvis0_exploratory as explore, ilvis0_shape as shape


def exact_linear_packet(w,f,a,b,h):
    # Independent continuous ODE, not the production midpoint or correction series.
    def ode(t,state):
        r=state[:9].reshape(3,3); omega=w+a*(t-h/2); force=f+b*(t-h/2)
        x,y,z=omega; k=np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
        return np.r_[(r@k).ravel(),r@force]
    result=solve_ivp(ode,(0,h),np.r_[np.eye(3).ravel(),np.zeros(3)],method='DOP853',rtol=1e-12,atol=1e-14)
    assert result.success
    return result.y[:9,-1].reshape(3,3),result.y[9:,-1]


@pytest.mark.parametrize('case',('constant','single_axis','changing_axes'))
def test_independent_ode_checks_coning_and_rotated_force(case):
    w=np.array([.3,-.2,.5]); f=np.array([.4,1.,-9.])
    a=np.array([2.,-3.,1.]); b=np.array([.7,-.9,.3]); h=.005
    if case=='constant':a*=0;b*=0
    if case=='single_axis':w=np.array([0.,0.,.5]);a=np.array([0.,0.,2.])
    reference_r,reference_v=exact_linear_packet(w,f,a,b,h)
    theta,dv=correction.packet(w*h,f*h,h,a,b,1.,'combined',convention='ordinary_rate_integrals')
    old_r=Rotation.from_rotvec(w*h).as_matrix()
    new_r=Rotation.from_rotvec(theta).as_matrix()
    old_v=Rotation.from_rotvec(w*h/2).apply(f*h)
    new_v=Rotation.from_rotvec(theta/2).apply(dv)
    if case=='changing_axes':assert np.linalg.norm(new_r-reference_r)<.01*np.linalg.norm(old_r-reference_r)
    assert np.linalg.norm(new_v-reference_v)<.01*np.linalg.norm(old_v-reference_v)
    if case=='single_axis':np.testing.assert_allclose(theta,w*h,atol=1e-15)


def test_partial_packet_matches_ordinary_integrals_without_full_packet_scaling():
    th=np.array([.001,.002,.003]); dv=np.array([.04,.03,.02]); h=.005
    a=np.array([2.,3.,4.]); b=np.array([1.,2.,3.]); fraction=.3
    theta,velocity=correction.packet(th,dv,h,a,b,fraction,'linear',convention='ordinary_rate_integrals')
    t=h*fraction
    np.testing.assert_allclose(theta,th*fraction+.5*a*(t*t-h*t),atol=1e-16)
    np.testing.assert_allclose(velocity,dv*fraction+.5*b*(t*t-h*t),atol=1e-16)


def test_compensated_input_is_not_corrected_twice():
    with pytest.raises(ValueError):
        correction.packet(np.zeros(3),np.zeros(3),.005,np.zeros(3),np.zeros(3),1.,'combined',convention='already_compensated')
    with pytest.raises(ValueError):
        correction.packet(np.zeros(3),np.zeros(3),0.,np.zeros(3),np.zeros(3),1.,'baseline',convention='ordinary_rate_integrals')


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    path=tmp_path_factory.mktemp('compensation-kernels')
    return explore.load_kernel(path)[0],shape.load_tangent(path)[0],correction.load_kernel(path)[0]


def test_disabled_correction_reproduces_frozen_value_and_derivative(kernels):
    f=controls.fixture('sphere_rotating','nominal'); old=controls.problem(f,*kernels[:2])
    new=correction.problem(f,kernels[2],'baseline',convention='ordinary_rate_integrals')
    point=controls.truth_point(f,old)*.8
    x,j,b=old.prediction_tangent(point,f['model']); y,k,c=new.prediction_tangent(point,f['model'])
    np.testing.assert_array_equal(x,y);np.testing.assert_array_equal(j,k);assert b==c


@pytest.mark.parametrize('model',explore.MODELS)
def test_combined_correction_improves_independent_geographic_prediction(model,kernels):
    f=controls.fixture(model,'nominal'); p=controls.problem(f,*kernels[:2]); point=controls.truth_point(f,p)
    old=controls.position_error(f,p.predict(point,model))
    q=correction.problem(f,kernels[2],'combined',convention='ordinary_rate_integrals')
    new=controls.position_error(f,q.predict(point,model))
    assert new<.1*old


def test_corrected_tangent_accounts_for_calibration_and_latency(kernels):
    f=controls.fixture('sphere_rotating','nominal')
    p=correction.problem(f,kernels[2],'combined',convention='ordinary_rate_integrals')
    point=controls.truth_point(f,p)*.8; _,j,_=p.prediction_tangent(point,f['model'])
    for i in range(len(point)):
        step=np.eye(len(point))[i]*1e-3
        fd=(p.predict(point+step,f['model'])-p.predict(point-step,f['model'])).ravel()/2e-3
        assert np.max(abs((fd-j[:,i]).reshape(-1,3)*f['metric']))<2e-5


def test_zero_motion_has_no_manufactured_correction():
    for mode in correction.MODES:
        theta,dv=correction.packet(np.zeros(3),np.zeros(3),.005,np.zeros(3),np.zeros(3),.37,mode,convention='ordinary_rate_integrals')
        np.testing.assert_array_equal(theta,np.zeros(3))
        np.testing.assert_array_equal(dv,np.zeros(3))


def test_variable_packet_spacing_preserves_prediction_improvement(kernels):
    f=controls.fixture('sphere_rotating','variable'); old=controls.problem(f,*kernels[:2])
    point=controls.truth_point(f,old)
    new=correction.problem(f,kernels[2],'combined',convention='ordinary_rate_integrals')
    assert controls.position_error(f,new.predict(point,f['model']))<.1*controls.position_error(f,old.predict(point,f['model']))


def test_geographic_problem_rejects_double_compensation(kernels):
    f=controls.fixture('sphere_rotating','nominal')
    with pytest.raises(ValueError):
        correction.problem(f,kernels[2],'combined',convention='already_compensated')
