# SPDX-License-Identifier: AGPL-3.0-or-later
"""Nonlinear boxes checked against independent Cartesian trajectory truth."""
import numpy as np
import pytest

from ilvis0_channel_reference import BACKGROUND, PROFILES, RADIUS, reference
from lll.ilvis0_force_bounds import force_bounds


def evaluate(jet, error, model, **kwargs):
    return force_bounds(np.column_stack((jet-error, jet+error)), model=model,
        background_rate_bounds_rads=[BACKGROUND, BACKGROUND] if model == 'sphere_rotating' else [0., 0.],
        gravity_bounds_mps2=[9.81, 9.81], disc_radius_m=RADIUS, **kwargs)


@pytest.mark.parametrize('model', ['sphere_rotating', 'sphere_still', 'flat_still'])
@pytest.mark.parametrize('name', list(PROFILES))
def test_independent_cartesian_truth_inside_nonlinear_jet_box(model, name):
    profile = PROFILES[name]
    jet = np.array([profile[key] for key in ['phi', 'longitude', 'height', 'p', 'l', 'h', 'pp', 'll', 'hh']])
    error = np.array([1e-5, 1e-5, .5, 1e-7, 1e-7, .02, 1e-9, 1e-9, .001])
    result = evaluate(jet, error, model)
    rng = np.random.default_rng(1901)
    samples = np.vstack((jet, jet-error, jet+error, jet+rng.uniform(-1., 1., (16, 9))*error))
    for sample in samples:
        generated = reference(model, dict(zip(['phi', 'longitude', 'height', 'p', 'l', 'h', 'pp', 'll', 'hh'], sample)), 0.)
        force = generated['force']
        assert np.all(force >= result['force_ned_bounds_mps2'][:, 0])
        assert np.all(force <= result['force_ned_bounds_mps2'][:, 1])
        assert result['magnitude_bounds_mps2'][0] <= np.linalg.norm(force) <= result['magnitude_bounds_mps2'][1]


@pytest.mark.parametrize('model', ['sphere_rotating', 'sphere_still', 'flat_still'])
def test_stationary_force_norm_matches_declared_gravity_range(model):
    jet = np.array([.7, .2, 1200., 0., 0., 0., 0., 0., 0.])
    result = force_bounds(np.column_stack((jet, jet)), model=model,
        background_rate_bounds_rads=[0., BACKGROUND] if model == 'sphere_rotating' else [0., 0.],
        gravity_bounds_mps2=[9.7, 9.9], disc_radius_m=RADIUS)
    np.testing.assert_allclose(result['magnitude_bounds_mps2'], [9.7, 9.9], atol=1e-12)
    assert not result['statistical_coverage_calibrated']
    assert result['scientific_decision'] == 'abstain'


def test_zero_width_box_reproduces_independent_truth_without_large_dependency_inflation():
    profile = PROFILES['changing_direction']; model = 'sphere_rotating'
    jet = np.array([profile[key] for key in ['phi', 'longitude', 'height', 'p', 'l', 'h', 'pp', 'll', 'hh']])
    result = evaluate(jet, np.zeros(9), model)
    expected = np.linalg.norm(reference(model, profile, 0.)['force'])
    np.testing.assert_allclose(result['magnitude_bounds_mps2'], expected, rtol=1e-12)


@pytest.mark.parametrize('latitude', [np.pi/2, -np.pi/2, np.pi/2-5e-7])
def test_polar_boxes_rejected(latitude):
    jet = np.array([latitude, 0., 0., 0., 0., 0., 0., 0., 0.])
    with pytest.raises(ValueError):
        evaluate(jet, np.zeros(9), 'sphere_still')


def test_nonpositive_metric_rejected():
    jet = np.array([0., 0., -7e6, 0., 0., 0., 0., 0., 0.])
    with pytest.raises(ValueError):
        evaluate(jet, np.zeros(9), 'sphere_still')


@pytest.mark.parametrize('bad', [[1., -1.], [0., np.inf], [np.nan, 0.]])
def test_invalid_physical_intervals_rejected(bad):
    jet = np.zeros((9, 2))
    with pytest.raises(ValueError):
        force_bounds(jet, model='sphere_still', background_rate_bounds_rads=[0., 0.],
            gravity_bounds_mps2=bad, disc_radius_m=RADIUS)


def test_zero_field_candidate_cannot_receive_nonzero_field_envelope():
    with pytest.raises(ValueError):
        force_bounds(np.zeros((9, 2)), model='flat_still',
            background_rate_bounds_rads=[0., BACKGROUND], gravity_bounds_mps2=[9., 10.], disc_radius_m=RADIUS)
