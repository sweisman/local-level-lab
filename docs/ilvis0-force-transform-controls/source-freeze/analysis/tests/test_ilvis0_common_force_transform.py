# SPDX-License-Identifier: AGPL-3.0-or-later
import math
import numpy as np
import pytest
from lll import ilvis0_common_force_transform as transform
from lll.ilvis0_shared_reference_terms import ReferenceErrors
from lll.ilvis0_reference_acceleration import AccelerationTerms
from test_ilvis0_shared_reference_terms import config


def terms(center=None,lower=None,upper=None):
    center=np.full(27,.1) if center is None else center
    ref=ReferenceErrors(config(),-np.ones(27) if lower is None else lower,np.ones(27) if upper is None else upper,center)
    return ref,transform.ForceTransform(ref)


def independent(ref,point):
    p=ref.limits*point;v=p[:3];a=float(np.linalg.norm(v));x,y,z=v
    cross=np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
    rotation=np.eye(3) if a==0 else np.eye(3)+math.sin(a)/a*cross+(1-math.cos(a))/(a*a)*(cross@cross)
    return ref.initial_r@rotation@np.diag(1/(1+p[18:21]))


def test_independent_matrix_and_complete_tangent_and_remainder():
    ref,obj=terms();rng=np.random.default_rng(283)
    np.testing.assert_allclose(obj.center,independent(ref,ref.center),atol=4e-16,rtol=0)
    for point in [ref.lower,ref.upper,*rng.uniform(-1,1,(48,27))]:
        actual=independent(ref,point);delta=point-ref.center
        remainder=actual-obj.center-np.einsum('ijk,k->ij',obj.jacobian,delta)
        assert np.all(abs(remainder.ravel())<=obj.caps+2e-14)
        coefficients=obj.coefficients([1.,2.,-1.],[.3,-.7,.9])
        np.testing.assert_allclose(remainder@np.array([.3,-.7,.9])*[1.,2.,-1.],
            coefficients.matrix@obj.normalized_values_at(point),atol=1e-14,rtol=0)
    # A yaw scale of pi makes the central-difference O(h²) term visible at
    # 2e-5; 2e-6 separates that truncation from floating-point cancellation.
    step=2e-6
    for axis in range(27):
        delta=np.eye(27)[axis]*step
        measured=(independent(ref,ref.center+delta)-independent(ref,ref.center-delta))/(2*step)
        np.testing.assert_allclose(measured,obj.jacobian[:,:,axis],atol=3e-10,rtol=0)


def test_joint_augmentation_keeps_51_columns_and_rejects_another_reference():
    ref,obj=terms();acc=AccelerationTerms(ref,[.001,-.002,-.04905],.005,9.81)
    physical=np.arange(81.).reshape(3,27);previous=ref.coefficients([1.,1.,1.],1.,[1.,1.,1.])
    added=acc.coefficients([1.,1.,1.],clock_center=1.,time_slope=1.);force=obj.coefficients([1.,1.,1.],[.1,.2,.3])
    design=obj.augment(physical,acc,previous,added,force)
    assert design.shape==(3,51);np.testing.assert_array_equal(design[:,:27],physical)
    other_ref,other=terms(center=np.full(27,.2))
    with pytest.raises(ValueError):obj.augment(physical,acc,previous,added,other.coefficients([1.,1.,1.],[.1,.2,.3]))


def test_fixed_domain_has_zero_caps_and_no_oracle_outside_domain():
    center=np.full(27,.1);ref,obj=terms(center,center,center)
    np.testing.assert_array_equal(obj.caps,np.zeros(9));np.testing.assert_array_equal(obj.normalized_values_at(center),np.zeros(9))
    with pytest.raises(ValueError):obj.values_at(center+.01)
    with pytest.raises(ValueError):obj.caps[0]=1.
