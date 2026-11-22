"""Receiver-only selected windows connect to joint force uncertainty."""

import math

import numpy as np
import pytest

from lll.ilvis0_receiver_support import SupportPolicy


def _inputs():
    radius = 6378137. + 1000.
    fixes = [dict(utc_week_s=float(i), latitude_deg=0.,
                  longitude_deg=math.degrees(200.*i/radius),
                  orthometric_height_m=970., geoid_separation_m=30.,
                  fix_quality=1)
             for i in range(21)]
    covariance = np.kron(np.eye(len(fixes)),
                         np.diag([1e-16, 1e-16, .09]))
    policy = SupportPolicy(
        half_windows_s=(5., 10.), maximum_gap_s=1.5,
        minimum_samples=5, minimum_speed_mps=100.,
        maximum_speed_mps=300., maximum_course_span_deg=5.,
        maximum_speed_span_mps=5.,
        maximum_vertical_rate_span_mps=.5)
    return fixes, covariance, policy


def test_joint_receiver_force_reuses_model_independent_windows_and_shared_error():
    from lll.ilvis0_joint_receiver_force import assess
    fixes, covariance, policy = _inputs()
    original = [dict(row) for row in fixes]
    results = {}
    for model in ('sphere_rotating', 'sphere_still', 'flat_still'):
        results[model] = assess(
            fixes, covariance, targets_s=[0., 10., 12.], policy=policy,
            degree=2, model=model,
            background_rate_rads=7.292115e-5 if model == 'sphere_rotating' else 0.,
            gravity_mps2=9.8, disc_radius_m=6371000.)
    windows = [row['selected_indices'] for row in results['sphere_still']['targets']]
    assert windows == [None, (0, 20), (7, 17)]
    assert all([row['selected_indices'] for row in result['targets']] == windows
               for result in results.values())
    for result in results.values():
        assert result['supported_target_indices'] == [1, 2]
        matrix = result['conditional_covariance_mps4']
        assert matrix.shape == (2, 2)
        assert result['required_force_magnitude_mps2'].shape == (2,)
        assert np.all(result['required_force_magnitude_mps2'] > 0)
        assert matrix[0, 0] > 0 and matrix[1, 1] > 0
        assert abs(matrix[0, 1]) > 0
        assert result['gyro_observations_used'] is False
        assert result['scientific_decision'] == 'abstain'
    assert fixes == original


def test_joint_receiver_force_all_windows_rejected_without_model_scoring():
    from lll.ilvis0_joint_receiver_force import assess
    fixes, covariance, policy = _inputs()
    result = assess(fixes, covariance, targets_s=[0.], policy=policy,
                    degree=2, model='sphere_still',
                    background_rate_rads=0., gravity_mps2=9.8,
                    disc_radius_m=6371000.)
    assert result['supported_target_indices'] == []
    assert result['conditional_covariance_mps4'] is None
    assert result['required_force_magnitude_mps2'] is None
    assert result['targets'][0]['selected_indices'] is None
    assert result['scientific_decision'] == 'abstain'
    with pytest.raises(ValueError, match='physical model'):
        assess(fixes, covariance, targets_s=[0.], policy=policy,
               degree=2, model='flat_still',
               background_rate_rads=7.292115e-5, gravity_mps2=9.8,
               disc_radius_m=6371000.)


def test_candidate_force_errors_share_the_same_receiver_perturbations():
    from lll.ilvis0_joint_receiver_force import assess_candidates
    fixes, covariance, policy = _inputs()
    result = assess_candidates(
        fixes, covariance, targets_s=[10., 12.], policy=policy,
        degree=2, background_rate_rads=7.292115e-5,
        gravity_mps2=9.8, disc_radius_m=6371000.)
    assert result['model_order'] == (
        'sphere_rotating', 'sphere_still', 'flat_still')
    assert result['supported_target_indices'] == [0, 1]
    joint = result['joint_covariance_mps4']
    assert joint.shape == (6, 6)
    np.testing.assert_allclose(joint, joint.T, atol=1e-14)
    assert np.linalg.eigvalsh(joint).min() > -1e-12
    # A common GPS error influences both candidates. Counting their two
    # diagonal variances as independent would misstate this contrast.
    assert abs(joint[0, 2]) > 0
    assert joint[0, 0] + joint[2, 2] - 2*joint[0, 2] < joint[0, 0] + joint[2, 2]
    assert result['scientific_decision'] == 'abstain'


def test_candidate_force_accepts_single_pass_receiver_fix_iterable():
    from lll.ilvis0_joint_receiver_force import assess_candidates
    fixes, covariance, policy = _inputs()
    result = assess_candidates(
        iter(fixes), covariance, targets_s=[10.], policy=policy,
        degree=2, background_rate_rads=7.292115e-5,
        gravity_mps2=9.8, disc_radius_m=6371000.)
    assert result['supported_target_indices'] == [0]


def test_candidate_force_abstains_when_receiver_support_is_empty():
    from lll.ilvis0_joint_receiver_force import assess_candidates
    fixes, covariance, policy = _inputs()
    result = assess_candidates(
        fixes, covariance, targets_s=[0.], policy=policy,
        degree=2, background_rate_rads=7.292115e-5,
        gravity_mps2=9.8, disc_radius_m=6371000.)
    assert result['selected_indices'] == [None]
    assert result['supported_target_indices'] == []
    assert result['joint_covariance_mps4'] is None
    assert all(value is None for value in result['required_force_magnitude_mps2'].values())
    assert result['scientific_decision'] == 'abstain'
