# SPDX-License-Identifier: AGPL-3.0-or-later
"""Candidate-law scores use matched earlier observations and keep abstention."""
import pytest


def candidate(nll, sigma, *, bound=False, converged=True):
    diagonal = [[sigma * sigma, 0., 0.],
                [0., sigma * sigma, 0.],
                [0., 0., sigma * sigma]]
    return dict(
        fit=dict(model='sphere_rotating', converged=converged,
                 stopping_rule_verified=converged,
                 prediction_receiver_positions_used_in_training=False,
                 active_parameters=['attitude_x'],
                 active_bounds=['attitude_x'] if bound else [],
                 gaussian_training_score=dict(
                     negative_log_likelihood=nll, row_count=18,
                     covariance_parameters_estimated=False,
                     scientific_decision='abstain')),
        binding=dict(training_receiver_sha256='a' * 64,
                     training_prefix_sha256={name: 'b' * 64
                                             for name in ('theta', 'dv', 'dt')},
                     training_epochs=6, prediction_epochs=3,
                     original_reads=0, protected_reads=0),
        diagnostic=dict(prediction_target='receiver_measurement',
                        training_epochs=6, prediction_epochs=3,
                        later_observations_used=False,
                        fixed_parameters=dict(mean=[[0., 0., 0.]] * 3,
                                              covariance=[diagonal] * 3,
                                              parameter_uncertainty_included=False),
                        linear_calibration=dict(
                            status='active_bounds_unsupported' if bound
                            else 'estimable')))


def test_ranks_matched_training_laws_without_selecting_or_claiming_coverage():
    from lll.prediction_training_law_comparison import compare
    result = compare({'white': candidate(12., 1.),
                      'persistent': candidate(10., 2.)})
    assert [row['law_id'] for row in result['training_ranking']] == [
        'persistent', 'white']
    assert result['training_ranking'][1]['delta_nll'] == 2.
    assert result['maximum_future_sigma_ratio'] == 2.
    assert result['numerical_unique_minimum']
    assert result['status'] == 'training_only_unqualified'
    assert result['selected_law'] is None
    assert result['scientific_decision'] == 'abstain'
    assert not result['coverage_calibrated']
    assert not result['later_observations_used']


def test_rejects_mismatched_measurements_or_later_outcomes():
    from lll.prediction_training_law_comparison import compare
    first = candidate(10., 1.)
    second = candidate(11., 1.)
    second['binding']['training_receiver_sha256'] = 'c' * 64
    with pytest.raises(ValueError, match='same measured training prefix'):
        compare({'a': first, 'b': second})
    second = candidate(11., 1.)
    second['later_scores'] = {'covered': True}
    with pytest.raises(ValueError, match='earlier-only candidate records'):
        compare({'a': first, 'b': second})


def test_failed_fit_abstains_without_rank_or_future_spread():
    from lll.prediction_training_law_comparison import compare
    result = compare({'a': candidate(10., 1.),
                      'b': candidate(11., 2., converged=False)})
    assert result['status'] == 'numerically_unqualified'
    assert result['training_ranking'] is None
    assert result['maximum_future_sigma_ratio'] is None
    assert result['selected_law'] is None


def test_active_bound_keeps_training_ranking_but_blocks_calibration_claim():
    from lll.prediction_training_law_comparison import compare
    result = compare({'a': candidate(10., 1., bound=True),
                      'b': candidate(11., 2.)})
    assert result['training_ranking'][0]['law_id'] == 'a'
    assert result['active_bounds_by_law'] == {'a': ['attitude_x'], 'b': []}
    assert result['status'] == 'active_bounds_unsupported'
    assert result['selected_law'] is None
    assert not result['coverage_calibrated']
