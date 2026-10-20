# SPDX-License-Identifier: AGPL-3.0-or-later
import math

import numpy as np
import pytest

from lll import ilvis0_geographic_bounds as bounds
from lll.ilvis0_local_step_bounds import Value,Matrix


def scalar(center,lower=None,upper=None):
    return bounds.Scalar.interval(center,center if lower is None else lower,center if upper is None else upper)


def state(phi=-65.):
    return bounds.State(bounds.Coordinates(scalar(math.radians(phi)),scalar(3.14159),scalar(12000.)),
        Value([200.,30.,-.2]),Matrix(np.eye(3),0.,0.,'rotation'))


def test_physical_intervals_allow_asymmetric_boundary_centers():
    x=bounds.Scalar(Value(0.,1.),0.,1.)
    assert x.lower==0. and x.upper==1. and x.value.change==1.
    period=scalar(.0015,.0015,.0035)
    assert float(period.value.center)-period.value.change<0.
    assert period.lower>0.


@pytest.mark.parametrize('center,lower,upper',[(2.,1.,3.),(-2.,-3.,-1.)])
def test_scalar_inverse_contains_exact_nonlinear_remainders(center,lower,upper):
    x=scalar(center,lower,upper);result=bounds.inverse(x)
    for actual in np.linspace(lower,upper,31):
        error=abs(1./actual-1./center+(actual-center)/center**2)
        assert error<=result.value.remainder+1e-14
        assert result.lower<=1./actual<=result.upper


def test_trigonometric_ranges_and_global_remainders_include_extrema():
    x=scalar(1.,-2.,3.)
    for function,reference,derivative in ((bounds.sine,np.sin,np.cos),(bounds.cosine,np.cos,lambda x:-np.sin(x))):
        result=function(x)
        for actual in np.linspace(-2.,3.,101):
            assert result.lower<=reference(actual)<=result.upper
            assert abs(reference(actual)-reference(1.)-derivative(1.)*(actual-1.))<=result.value.remainder+1e-14


def test_positive_power_covers_nonzero_input_remainder():
    x=bounds.Scalar(Value(2.,1.,.1),1.,3.);result=bounds.power(x,-1.5)
    assert result.value.remainder>=1.5*2.**-2.5*.1
    with pytest.raises(ValueError):bounds.power(scalar(.1,-.1,.3),-.5)


@pytest.mark.parametrize('model',['sphere_rotating','sphere_still','flat_still'])
@pytest.mark.parametrize('removal_center',[0.,1.])
def test_full_step_accepts_valid_profiled_domain_at_bound(model,removal_center):
    result=bounds.step(state(),Value([3e-5,-2e-5,1e-5]),Value([0.,0.,-.04905]),
        period=scalar(.005),removal=scalar(removal_center,0.,1.),gravity=scalar(9.81),model=model,disc_radius_m=6371000.)
    assert np.all(np.isfinite(result.position.center))
    assert result.report()['packet_boundary_crossing_covered'] is False


def test_zero_period_with_zero_increments_is_identity():
    initial=state()
    result=bounds.step(initial,Value(np.zeros(3)),Value(np.zeros(3)),period=scalar(0.),
        removal=scalar(.5,0.,1.),gravity=scalar(9.81),model='sphere_rotating',disc_radius_m=6371000.)
    np.testing.assert_allclose(result.position.center,initial.position.center,atol=1e-14)
    np.testing.assert_allclose(result.velocity.center,initial.velocity.center,atol=1e-12)


def test_longitude_is_not_wrapped_and_lever_is_not_discarded():
    initial=state();lever=Value([1.,2.,.5])
    a=bounds.observation(initial,Value(np.zeros(3)),model='sphere_still',disc_radius_m=6371000.)
    b=bounds.observation(initial,lever,model='sphere_still',disc_radius_m=6371000.)
    assert b.longitude.value.center>a.longitude.value.center
    initial=bounds.State(bounds.Coordinates(scalar(.1),scalar(math.pi+.1),scalar(1.)),initial.velocity,initial.attitude)
    assert bounds.observation(initial,Value(np.zeros(3)),model='sphere_still',disc_radius_m=6371000.).longitude.value.center>math.pi


def test_domain_crossings_are_not_clipped():
    with pytest.raises(ValueError):bounds.inverse(scalar(0.,-1.,1.))
    with pytest.raises(ValueError):bounds.coordinate_map(state(89.99999).position,Value([1.,1.,0.]),model='sphere_still',disc_radius_m=6371000.)


def test_partial_packet_constructs_shared_fraction_and_rejects_crossings():
    kwargs=dict(packet_dt=.005,removal=scalar(0.,0.,1.),gravity=scalar(9.81),model='flat_still',disc_radius_m=6371000.)
    result=bounds.partial_packet(state(),Value([0.,0.,0.]),Value([0.,0.,-.04905]),fraction=scalar(.3,.3,.7),**kwargs)
    assert np.all(np.isfinite(result.position.center))
    with pytest.raises(ValueError):bounds.partial_packet(state(),Value(np.zeros(3)),Value(np.zeros(3)),fraction=scalar(.5,-.1,1.),**kwargs)
