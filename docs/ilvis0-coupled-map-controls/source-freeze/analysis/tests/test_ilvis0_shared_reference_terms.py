# SPDX-License-Identifier: AGPL-3.0-or-later
import math

import numpy as np
import pytest
from lll import ilvis0_shared_reference_terms as shared


def config():
    return dict(initial_r=np.eye(3),limits=np.r_[[.17,.17,math.pi],[20.]*3,[100.]*3,[1e-5]*3,
        [.25]*3,[.02]*3,[.15]*3,[10.]*3,.05,.15,1.],model=0,profile=True,source_id='unit-data-v1')


def test_original_domain_bounds_both_common_vectors_at_nonzero_actual_levers():
    lower=-np.ones(27);upper=np.ones(27);lower[2]=0.;upper[2]=.25
    center=np.zeros(27);center[2]=.125
    terms=shared.ReferenceErrors(config(),lower,upper,center)
    assert np.all(terms.caps[:3]>=3.) and terms.caps[3]<10.
    rng=np.random.default_rng(73)
    for _ in range(100):
        point=lower+(upper-lower)*rng.random(27)
        values=terms.values_at(point)
        assert np.all(abs(values)<=terms.caps*(1+1e-12))
        assert np.linalg.norm(values[3:])<=terms.caps[3]*(1+1e-12)


def test_nonzero_lever_and_rotation_center_use_the_full_derivative():
    c=config();c['limits'][:3]=[0.,0.,math.pi]
    center=np.zeros(27);center[2]=.1;center[21:24]=[.1,.05,0.]
    point=center.copy();point[2]=.2;point[21:24]=[.3,.2,0.]
    terms=shared.ReferenceErrors(c,-np.ones(27),np.ones(27),center)
    a0=math.pi*.1;a=math.pi*.2
    r=lambda x:np.array([[math.cos(x),-math.sin(x),0.],[math.sin(x),math.cos(x),0.],[0.,0.,1.]])
    derivative=np.array([[-math.sin(a0),-math.cos(a0),0.],[math.cos(a0),-math.sin(a0),0.],[0.,0.,0.]])
    l0=np.array([1.,.5,0.]);lever=np.array([3.,2.,0.])
    expected=r(a)@lever-r(a0)@l0-derivative@(l0*(a-a0))-r(a0)@(lever-l0)
    np.testing.assert_allclose(terms.values_at(point)[3:],expected,rtol=0,atol=2e-15)


def test_product_error_is_shared_across_different_epochs():
    terms=shared.ReferenceErrors(config(),-np.ones(27),np.ones(27),np.zeros(27))
    p=np.zeros(27);p[3:6]=[.2,-.3,.4];p[25]=.5
    gamma=terms.values_at(p)[:3]
    np.testing.assert_allclose(gamma,np.array([4.,-6.,8.])*.075,atol=1e-15)
    for t in (.2,1.5,1.8):
        actual=(np.array([150.,30.,.1])+np.array([4.,-6.,8.]))*(t+.075)
        linear=np.array([150.,30.,.1])*t+np.array([4.,-6.,8.])*t+np.array([150.,30.,.1])*.075
        np.testing.assert_allclose(actual-linear,gamma,atol=1e-13)


def test_augmentation_keeps_every_physical_and_auxiliary_column():
    terms=shared.ReferenceErrors(config(),-np.ones(27),np.ones(27),np.zeros(27))
    physical=np.arange(81.).reshape(3,27)
    coefficients=terms.coefficients([1e-7,2e-7,-1.],1.,[2e-7,3e-7,-1.])
    result=terms.augment(physical,coefficients)
    assert result.shape==(3,33)
    np.testing.assert_array_equal(result[:,:27],physical)
    assert terms.binding!=shared.ReferenceErrors(config(),-np.ones(27),np.ones(27),np.full(27,.01)).binding
    with pytest.raises(ValueError):terms.augment(physical,None)
    other=shared.ReferenceErrors(dict(config(),source_id='different-recording'),-np.ones(27),np.ones(27),np.zeros(27))
    with pytest.raises(ValueError,match='binding'):other.augment(physical,coefficients)


def test_zero_radius_and_mutation_are_explicit():
    terms=shared.ReferenceErrors(config(),np.zeros(27),np.zeros(27),np.zeros(27))
    np.testing.assert_array_equal(terms.normalized_values_at(np.zeros(27)),np.zeros(6))
    with pytest.raises(ValueError):terms.caps[0]=9.
    with pytest.raises(ValueError):terms.values_at(np.ones(27))
