# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from scipy.integrate import solve_ivp
from scipy.spatial.transform import Rotation

from lll import airquantumgrav_body_bounds as bounds


def skew(x):
    a,b,c=x
    return np.array([[0.,-c,b],[c,0.,-a],[-b,a,0.]])


@pytest.mark.parametrize('h',[1/300.,.0049,.1])
@pytest.mark.parametrize('changing_axis',[False,True])
@pytest.mark.parametrize('changing_force',[False,True])
def test_local_body_errors_inside_bounds_against_independent_ode(h,changing_axis,changing_force):
    a=np.array([.12,-.03,.02]);b=np.array([-.02,.11,.04]) if changing_axis else a.copy()
    f=np.array([.1,-.2,-9.81]);g=np.array([-.2,.4,-9.7]) if changing_force else f.copy()
    def rhs(t,y):
        r=y[:9].reshape(3,3);omega=a+(b-a)*(t/h);force=f+(g-f)*(t/h)
        return np.r_[(r@skew(omega)).ravel(),r@force]
    initial=np.r_[np.eye(3).ravel(),np.zeros(3)]
    solution=solve_ivp(rhs,[0.,h],initial,rtol=1e-12,atol=1e-14,max_step=h/32.)
    assert solution.success
    final=solution.y[:,-1];middle=(a+b)/2
    approximation=Rotation.from_rotvec(middle*h).as_matrix()
    force=Rotation.from_rotvec(middle*h/2).apply((f+g)/2*h)
    actual_rotation=np.linalg.norm(final[:9].reshape(3,3)-approximation,ord=2)
    actual_force=np.linalg.norm(final[9:]-force)
    result=bounds.local_bounds(a,b,f,g,h)
    assert actual_rotation<=result['rotation_operator_error']+1e-12
    assert actual_force<=result['force_integral_error_mps']+1e-12
    assert result['actual_instrument_phase_established'] is False


def test_zero_rate_linear_force_is_exact():
    result=bounds.local_bounds([0.]*3,[0.]*3,[0.,0.,-9.8],[.1,0.,-9.9],.003)
    assert result['rotation_operator_error']==0.
    assert result['force_integral_error_mps']==0.


@pytest.mark.parametrize('h',[0.,-.001,float('nan')])
def test_unsupported_period_is_rejected(h):
    with pytest.raises(ValueError):bounds.local_bounds([0.]*3,[0.]*3,[0.]*3,[0.]*3,h)
