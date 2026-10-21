# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import numpy as np
import pytest


def test_component_transport_exists():
    assert importlib.util.find_spec('lll.ilvis0_component_transport') is not None


def test_norm_and_component_caps_are_both_retained():
    from lll.ilvis0_component_transport import Value
    a=Value([1,2,3],1,.1,component_change=[1,1,.01],component_remainder=[.1,.1,.001])
    assert a.change==1 and a.remainder==.1
    np.testing.assert_array_equal(a.component_change,[1,1,.01])
    assert not a.component_change.flags.writeable
    b=Value([1,2,3],5,2,component_change=[0,0,1],component_remainder=[0,0,.1])
    assert b.change==1 and b.remainder==.1


def test_fixed_yaw_and_coriolis_preserve_vertical_component():
    from lll.ilvis0_component_transport import Value,add,scale,matrix_vector,cross
    from lll.ilvis0_local_step_bounds import Matrix
    from scipy.spatial.transform import Rotation
    a=Value([0,0,-9.81],1,.1,component_change=[1,1,.01],component_remainder=[.1,.1,.001])
    rotation=Matrix(Rotation.from_rotvec([0,0,.03]).as_matrix(),0,0,'rotation')
    result=matrix_vector(rotation,add(a,scale(a,.5)))
    assert result.component_change[2]<.016 and result.component_remainder[2]<.0016
    c=cross(Value([0,0,.01]),a)
    assert c.component_change[2]==0 and c.component_remainder[2]==0


def test_nonlinear_values_and_affine_errors_are_contained():
    from lll import ilvis0_component_transport as c
    from lll.ilvis0_local_step_bounds import Matrix
    width=.1
    x=np.array([.1,.2,-.3]);dx=np.array([1.,-.2,.3]);qx=np.array([.02,.01,-.01])
    y=np.array([-.3,.5,.2]);dy=np.array([.1,.3,-.2]);qy=np.array([-.01,0.,.02])
    def box(center,linear,quadratic):
        change=abs(linear)*width+abs(quadratic)*width**2;rem=abs(quadratic)*width**2
        return c.Value(center,np.linalg.norm(change),np.linalg.norm(rem),component_change=change,component_remainder=rem)
    a=box(x,dx,qx);b=box(y,dy,qy);s=c.Value(.7,.03,.001)
    fixed=np.array([[.99,-.01,0],[.01,.99,0],[0,0,.99]])
    matrix=Matrix(fixed,0,0,'contraction')
    outputs=[(c.add(a,b),x+y,dx+dy,lambda t:(x+dx*t+qx*t*t)+(y+dy*t+qy*t*t)),
        (c.cross(a,b),np.cross(x,y),np.cross(dx,y)+np.cross(x,dy),lambda t:np.cross(x+dx*t+qx*t*t,y+dy*t+qy*t*t)),
        (c.matrix_vector(matrix,a),fixed@x,fixed@dx,lambda t:fixed@(x+dx*t+qx*t*t)),
        (c.scalar_product(s,a),.7*x,.7*dx+.3*x,lambda t:(.7+.3*t+.1*t*t)*(x+dx*t+qx*t*t))]
    # Include the scalar's quadratic term in its declared change radius.
    outputs[-1]=(c.scalar_product(c.Value(.7,.031,.001),a),*outputs[-1][1:])
    for result,center,linear,function in outputs:
        for t in np.linspace(-width,width,31):
            actual=function(t)
            assert np.linalg.norm(actual-result.center)<=result.change+1e-13
            assert np.linalg.norm(actual-result.center-linear*t)<=result.remainder+1e-13
            assert np.all(abs(actual-result.center)<=result.component_change+1e-13)
            assert np.all(abs(actual-result.center-linear*t)<=result.component_remainder+1e-13)


def test_coordinate_extraction_uses_axis_bound_and_plain_inputs_remain_supported():
    from lll.ilvis0_component_transport import Value,component
    from lll.ilvis0_local_step_bounds import Value as Legacy
    a=Value([0,0,0],1,.1,component_change=[1,1,.01],component_remainder=[.1,.1,.001])
    assert component(a,2).value.change<.011
    assert component(a,2).value.remainder==.001
    assert component(Legacy([1,2,3],.5,.1),1).value.change==.5
    with pytest.raises(ValueError):component(a,3)
