# SPDX-License-Identifier: AGPL-3.0-or-later
"""Deterministic coordinate-force adapter checks; no recordings or fitted data."""
import math

import numpy as np
import pytest

from lll import ilvis0_receiver_force as receiver


def context(model, *, position=None, rate=None, acceleration=None, background=0.):
    return receiver.evaluate(
        [0., .2, 1000.] if position is None else position,
        [0., 0., 0.] if rate is None else rate,
        [0., 0., 0.] if acceleration is None else acceleration,
        model=model, background_rate_rads=background,
        gravity_mps2=9.81, disc_radius_m=6371000.)


@pytest.mark.parametrize('model', ('sphere_rotating', 'sphere_still', 'flat_still'))
def test_stationary_force_is_opposite_declared_gravity(model):
    result=context(model, background=7.292115e-5 if model=='sphere_rotating' else 0.)
    np.testing.assert_allclose(result['velocity_ned_mps'], 0.)
    np.testing.assert_allclose(result['specific_force_ned_mps2'], [0., 0., -9.81])


def test_equatorial_eastward_globe_force_has_the_expected_centripetal_term():
    radius=6378137.+1000.;speed=220.
    result=context('sphere_still', rate=[0., speed/radius, 0.])
    np.testing.assert_allclose(result['velocity_ned_mps'], [0., speed, 0.])
    np.testing.assert_allclose(result['specific_force_ned_mps2'], [0., 0., -9.81+speed**2/radius])


def test_disc_metric_derivative_includes_changing_radius_and_height():
    phi=.6;r=6371000.;p=.00002;l=.00003
    result=context('flat_still', position=[phi, .2, 3000.],
                   rate=[p, l, 2.], acceleration=[1e-8, -2e-8, .1])
    np.testing.assert_allclose(result['acceleration_ned_mps2'],
        [r*1e-8, r*((math.pi/2-phi)*(-2e-8)-p*l), -.1])


def test_background_rate_is_explicit_rather_than_inserted_into_the_adapter():
    a=context('sphere_rotating', rate=[0., 3e-5, 0.], background=0.)
    b=context('sphere_still', rate=[0., 3e-5, 0.])
    np.testing.assert_array_equal(a['specific_force_ned_mps2'], b['specific_force_ned_mps2'])


@pytest.mark.parametrize('overrides', (
    dict(model='unknown'), dict(model='flat_still', background_rate_rads=.01),
    dict(model='sphere_still', background_rate_rads=.01),
    dict(gravity_mps2=-1.), dict(disc_radius_m=0.),
    dict(background_rate_rads=float('nan')),
))
def test_unsupported_physics_fails_closed(overrides):
    kwargs=dict(model='sphere_rotating', background_rate_rads=0., gravity_mps2=9.81, disc_radius_m=6371000.)
    kwargs.update(overrides)
    with pytest.raises(ValueError): receiver.evaluate([0., 0., 1000.], [0., 0., 0.], [0., 0., 0.], **kwargs)


@pytest.mark.parametrize('position', ([math.pi/2, 0., 1.], [0., 0., -1e8], [0., float('nan'), 0.]))
def test_unsupported_geographic_domain_fails_closed(position):
    with pytest.raises(ValueError): context('sphere_still', position=position)


def test_independent_cartesian_reference_reproduces_a_known_equatorial_circle():
    from ilvis0_channel_reference import reference
    profile=dict(phi=0.,longitude=.2,height=1000.,p=0.,l=4e-5,h=0.,pp=0.,ll=0.,hh=0.)
    result=reference('sphere_still', profile, 3.)
    radius=6378137.+1000.;speed=radius*4e-5
    np.testing.assert_allclose(result['velocity'], [0., speed, 0.], atol=1e-12)
    np.testing.assert_allclose(result['acceleration'], 0., atol=1e-12)
    np.testing.assert_allclose(result['force'], [0., 0., -9.81+speed**2/radius], atol=1e-12)


@pytest.mark.parametrize('model,profile', (
    ('sphere_rotating','climbing'), ('sphere_still','changing_direction'), ('flat_still','northbound'),
))
def test_adapter_agrees_with_independent_cartesian_motion(model, profile):
    from ilvis0_channel_reference import reference, PROFILES
    truth=reference(model, PROFILES[profile], 7.)
    result=receiver.evaluate(truth['coordinates'],truth['rate'],truth['second'],model=model,
        background_rate_rads=7.292115e-5 if model=='sphere_rotating' else 0.,
        gravity_mps2=9.81,disc_radius_m=6371000.)
    for actual,expected in (('velocity_ned_mps','velocity'),('acceleration_ned_mps2','acceleration'),
                            ('specific_force_ned_mps2','force'),('transport_ned_rads','transport')):
        np.testing.assert_allclose(result[actual],truth[expected],atol=1e-10,rtol=1e-10)
