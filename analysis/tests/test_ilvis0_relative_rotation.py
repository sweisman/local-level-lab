# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from scipy.linalg import expm
from lll import ilvis0_relative_rotation as relative
from lll.ilvis0_local_step_bounds import Matrix,Value,exponential


def skew(v):
    x,y,z=v;return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])


def test_zero_relative_motion_retains_exact_zero_at_uncertain_initial_attitude():
    zero=relative.Delta(np.zeros((3,3)))
    initial=Matrix(np.eye(3),.5,.125,'rotation')
    result=relative.action(zero,zero,initial,Value([0.,0.,-9.81],2.,.3))
    np.testing.assert_array_equal(result.center,np.zeros(3))
    assert result.change==0 and result.remainder==0


def test_relative_factor_bounds_preserve_small_motion_and_its_tangent():
    base=np.array([1e-4,2e-4,-1e-4]);direction=np.array([1e-5,0.,1e-5])
    left=relative.Delta(np.zeros((3,3)));right=relative.Delta(np.zeros((3,3)))
    for _ in range(5):
        left=relative.advance_left(left,exponential(Value(base,np.linalg.norm(direction))))
        right=relative.advance_right(right,exponential(Value(-base/2,np.linalg.norm(direction)/2)))
    initial=Matrix(np.eye(3),.25,.5*.25**2,'rotation');force=Value([0.,0.,-9.81])
    bound=relative.action(left,right,initial,force)
    def actual(z):
        q=np.eye(3);p=np.eye(3)
        for _ in range(5):
            q=expm(skew(base+z*direction))@q;p=p@expm(skew(-base/2-z*direction/2))
        r=expm(skew([0.,z*.25,0.]))
        return (q@r@p-r)@force.center
    step=1e-5;j=(actual(step)-actual(-step))/(2*step)
    for z in np.linspace(-1,1,33):
        assert np.linalg.norm(actual(z)-bound.center-j*z)<=bound.remainder+1e-10
    assert bound.remainder<.001 and np.linalg.norm(bound.center)<.01
    full=relative.compose(left,right,initial)
    assert full.structure=='rotation'


def test_general_bounded_product_retains_cross_terms():
    a=relative.Delta(np.diag([2.,3.,4.]),.2,.01)
    b=relative.Delta(np.eye(3)*.1,.3,.02)
    product=relative.multiply(a,b)
    assert product.remainder>=a.norm*.02+b.norm*.01+.2*.3
    value=relative.apply(product,Value([1.,2.,3.],.4,.03))
    assert value.remainder>=product.norm*.03+np.sqrt(14)*product.remainder+product.change*.4
    with pytest.raises(ValueError):a.center[0,0]=7.
    with pytest.raises(ValueError):relative.Delta(np.full((3,3),np.nan))
