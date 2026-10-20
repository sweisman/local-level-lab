# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from lll import ilvis0_reference_acceleration as acceleration
from lll.ilvis0_shared_reference_terms import ReferenceErrors
from test_ilvis0_shared_reference_terms import config


def setup(center=None,lower=None,upper=None):
    c=np.full(27,.1) if center is None else center
    lo=-np.ones(27) if lower is None else lower;hi=np.ones(27) if upper is None else upper
    reference=ReferenceErrors(config(),lo,hi,c)
    return reference,acceleration.AccelerationTerms(reference,[.001,-.002,-.04905],.005,9.81)


def test_common_acceleration_polynomial_identity_at_nonzero_centers():
    reference,terms=setup();rng=np.random.default_rng(519)
    for _ in range(50):
        p=rng.uniform(-1,1,27);a=terms.acceleration_at(p);delta=p-reference.center
        dt=reference.limits[25]*delta[25];gamma=terms.values_at(p)
        assert np.all(abs(gamma)<=terms.caps*(1+1e-11))
        for s,q in ((.2,0.),(.9,1.),(1.8,2.),(.3,-1.)):
            actual=.5*a*(s+q*dt)**2
            tangent=.5*terms.center*s*s+.5*s*s*(terms.jacobian@delta)+terms.center*s*q*dt
            coefficient=terms.coefficients([1.,1.,1.],clock_center=s,time_slope=q)
            np.testing.assert_allclose(actual-tangent,coefficient.matrix@terms.normalized_values_at(p),atol=3e-13,rtol=0)


def test_reference_acceleration_derivative_preserves_all_27_columns():
    reference,terms=setup();step=2e-5;differences=[]
    for axis in range(27):
        delta=np.zeros(27);delta[axis]=step
        derivative=(terms.acceleration_at(reference.center+delta)-terms.acceleration_at(reference.center-delta))/(2*step)
        differences.append(derivative-terms.jacobian[:,axis])
    assert terms.jacobian.shape==(3,27)
    assert np.max(abs(np.array(differences)))<2e-8
    np.testing.assert_array_equal(terms.jacobian[:,24],[0.,0.,reference.limits[24]])


def test_force_bias_gain_gravity_and_rotation_against_independent_formula():
    c=config();c['limits'][:3]=[0.,0.,np.pi]
    reference=ReferenceErrors(c,-np.ones(27),np.ones(27),np.zeros(27))
    terms=acceleration.AccelerationTerms(reference,[.001,-.002,-.04905],.005,9.81)
    p=np.zeros(27);p[2]=.25;p[12:15]=[.2,-.3,.4];p[18:21]=[.1,-.2,.3];p[24]=.6
    force=(np.array([.2,-.4,-9.81])-np.array([.05,-.075,.1]))/np.array([1.015,.97,1.045])
    angle=np.pi/4.;rotation=np.array([[np.cos(angle),-np.sin(angle),0.],[np.sin(angle),np.cos(angle),0.],[0.,0.,1.]])
    expected=rotation@force+[0.,0.,9.84]
    np.testing.assert_allclose(terms.acceleration_at(p),expected,rtol=0,atol=3e-15)


def test_augmentation_requires_both_common_blocks_and_keeps_zero_columns():
    reference,terms=setup();physical=np.arange(81.).reshape(3,27)
    previous=reference.coefficients([1.,1.,1.],1.,[1.,1.,1.])
    added=terms.coefficients([1.,2.,3.],clock_center=.8,time_slope=1.)
    design=terms.augment(physical,previous,added)
    assert design.shape==(3,42)
    np.testing.assert_array_equal(design[:,:27],physical)
    other_reference,other=setup(center=np.full(27,.2))
    with pytest.raises(ValueError):terms.augment(physical,previous,other.coefficients([1.,1.,1.],clock_center=.8,time_slope=1.))
    with pytest.raises(ValueError):terms.augment(physical,other_reference.coefficients([1.,1.,1.],1.,[1.,1.,1.]),added)


def test_fixed_domain_zero_caps_and_invalid_input_handling():
    c=np.full(27,.1);reference,terms=setup(center=c,lower=c,upper=c)
    np.testing.assert_array_equal(terms.caps,np.zeros(9))
    np.testing.assert_array_equal(terms.normalized_values_at(c),np.zeros(9))
    with pytest.raises(ValueError):terms.acceleration_at(c+.01)
    with pytest.raises(ValueError):acceleration.AccelerationTerms(reference,[0.,0.,0.],0.,9.81)
    with pytest.raises(ValueError):terms.caps[0]=2.
