"""Known-answer controls for shared height-error transfer."""

import numpy as np
import pytest

from lll import ilvis0_shared_gps_error as shared
from lll.ilvis0_receiver_derivatives import LocalPolynomial
from lll.ilvis0_receiver_force import evaluate


def test_scalar_jet_weights_agree_with_the_equal_weight_reference():
    times = np.array([-5., -4.9, -3.6, -2.3, -1., -.25, 0., .5, 1.3, 2.6, 3.8, 4.9, 5.])
    reference = LocalPolynomial(times, 0., np.eye(3*len(times)), degree=2, maximum_gap_s=1.5)
    np.testing.assert_allclose(shared.quadratic_weights(times),
                               reference.weights[2::3, 2::3], atol=2e-15, rtol=0.)


def test_two_common_sinusoid_components_reproduce_force_at_an_unsampled_phase():
    times = np.linspace(-5., 5., 51)
    coordinates = np.column_stack((-.7+2e-6*times, -.8+4e-5*times, 2500.+.1*times))
    period, phase = 20., .719
    record, = shared.force_response(times, coordinates, (period,))
    weights = shared.quadratic_weights(times)
    coordinates[:, 2] += shared.AMPLITUDE_M*np.cos(2*np.pi*times/period-phase)
    jet = weights @ coordinates
    for model, row in record['models'].items():
        actual = evaluate(*jet, model=model, background_rate_rads=shared.rate(model),
                          gravity_mps2=shared.GRAVITY, disc_radius_m=shared.RADIUS)
        coefficients = np.array([np.cos(phase), np.sin(phase)])
        shift = actual['specific_force_ned_mps2']-row['nominal_force']
        np.testing.assert_allclose(shift, row['phase_response']@coefficients, rtol=0., atol=2e-12)
        assert np.linalg.norm(shift) <= row['maximum_vector_shift_mps2'] + 2e-12


def test_paired_height_difference_is_invariant_under_common_error():
    times = np.linspace(0., 50., 501)
    left = 2450.+.3*times
    right = left+.05*np.sin(times)
    assert shared.cancellation_residual(left, right, times, 20.) < 1e-11
    with pytest.raises(ValueError, match='ordered support'):
        shared.quadratic_weights(times[::-1])
