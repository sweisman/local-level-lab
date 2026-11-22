# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np
import pytest

from lll.ilvis0_receiver_force import FIELD_MODELS, MATCHED_MODELS, evaluate, evaluate_batch
from lll.esa_doppler_force import GRAVITY_LAWS, WIDTHS, predicted_force, predicted_force_batch, rate_operator
from lll.models import OMEGA_E, WGS84_A


@pytest.mark.parametrize('model', MATCHED_MODELS)
def test_batched_receiver_force_matches_scalar_reference(model):
    coordinates = [[.38, -1.5, 3000.], [1.10, 2., 850.], [-.92, 1., 10000.]]
    rates = [[4e-6, 1e-5, -.12], [-5e-6, 3e-6, 8.], [9e-6, -6e-6, -2.]]
    acceleration = [[-4e-8, -6e-7, .15], [2e-7, 3e-6, -.28], [-2e-7, 5e-8, .47]]
    gravity = [9.80, 9.82, 9.79]
    options = dict(model=model, background_rate_rads=OMEGA_E if model in FIELD_MODELS else 0.,
                   disc_radius_m=WGS84_A)
    expected = [evaluate(q, v, a, gravity_mps2=g, **options)
                for q, v, a, g in zip(coordinates, rates, acceleration, gravity, strict=True)]
    actual = evaluate_batch(coordinates, rates, acceleration, gravity_mps2=gravity, **options)
    for name, values in actual.items():
        np.testing.assert_allclose(values, [row[name] for row in expected], atol=1e-13, rtol=1e-13)


def test_batched_receiver_force_rejects_polar_or_unmatched_coordinates():
    options = dict(model='sphere_still', background_rate_rads=0., disc_radius_m=WGS84_A)
    with pytest.raises(ValueError):
        evaluate_batch([[np.pi/2, 0., 0.]], [[0., 0., 0.]], [[0., 0., 0.]],
                       gravity_mps2=[9.8], **options)
    with pytest.raises(ValueError):
        evaluate_batch([[0., 0., 0.]], [[0., 0., 0.]], [[0., 0., 0.]],
                       gravity_mps2=[9.8, 9.8], **options)


@pytest.mark.parametrize('model', MATCHED_MODELS)
@pytest.mark.parametrize('width', WIDTHS)
@pytest.mark.parametrize('gravity', GRAVITY_LAWS)
def test_batched_force_average_matches_same_scalar_quadrature(model, width, gravity):
    knots = np.linspace(-5.5, 5.5, width)
    knots += .08*np.sin(knots)
    _, kernel = rate_operator(knots)
    coefficients = np.array([[6e-6, -8e-6, 5.], [2e-7, 9e-8, -.11], [9e-9, -3e-8, .12]])
    args = (knots, kernel, [1.1, -.5, 1940.], coefficients, model, gravity, 1500.)
    assert predicted_force_batch(*args) == pytest.approx(predicted_force(*args), abs=2e-13, rel=0.)
