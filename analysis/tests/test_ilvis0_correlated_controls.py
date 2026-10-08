# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
import json

from lll import ilvis0_correlated_controls as correlated
from lll import ilvis0_gps_sensitivity as sensitivity
from ilvis0_correlated_controls_worker import charge, cached, result_hash


def test_full_covariance_reaches_estimator_without_diagonalization():
    assumption = sensitivity.assumptions()[3]
    p = correlated.problem_for('bias', assumption)
    covariance = p.cholesky@p.cholesky.T
    assert covariance[0, 3] > 0 and covariance[0, 1] != 0
    residual = np.arange(p.gps.size, dtype=float).reshape(p.gps.shape)*1e-10
    white = p.whiten(residual)
    assert white@white == pytest.approx(residual.ravel()@np.linalg.solve(covariance, residual.ravel()))


def test_independently_known_bias_jacobian_and_local_precision():
    p = correlated.problem_for('bias', sensitivity.assumptions()[0])
    result = correlated.local_precision(p, [.4])
    assert result['nuisance_rank'] == 1 and result['prediction_evaluations'] == 3
    # Correcting a bias changes north position by -t²/2 times the bias.
    derivative = np.zeros_like(p.gps); derivative[:, 0] = -.5*p.gps_times**2/p.radius
    white = p.whiten(derivative)
    expected = 1/np.linalg.norm(white)
    assert result['marginal_precision']['accel_bias_x']['local_sigma'] == pytest.approx(expected, rel=1e-5)


def test_hypothetical_error_scales_change_precision_not_physical_observations():
    grid = sensitivity.assumptions()
    a = correlated.problem_for('bias', grid[0]); b = correlated.problem_for('bias', grid[3])
    np.testing.assert_array_equal(a.gps, b.gps)
    np.testing.assert_array_equal(a.theta, b.theta)
    np.testing.assert_array_equal(a.dv, b.dv)
    sa = correlated.local_precision(a, [.4])['marginal_precision']['accel_bias_x']['local_sigma']
    sb = correlated.local_precision(b, [.4])['marginal_precision']['accel_bias_x']['local_sigma']
    assert sb > 100*sa


def test_orientation_bias_null_direction_has_no_finite_marginal_sigma():
    p = correlated.problem_for('orientation_acceleration_ambiguity', sensitivity.assumptions()[3])
    point = [0.2, 0., 0.]
    r = correlated.local_precision(p, point)
    assert r['nuisance_rank'] < r['parameters']
    assert all(s['local_sigma'] is None for s in r['marginal_precision'].values())


def test_offset_drift_controls_preserve_exact_ambiguities():
    result = correlated.structural_error_controls()
    assert result['prediction_evaluations'] == 3
    assert all(r['passed'] and r['same_observation_response'] for r in result['controls'])
    assert result['empirical_earth_fit_attempts'] == 0


def test_bounded_fit_keeps_scientific_abstention():
    result = correlated.run_case('bias', sensitivity.assumptions()[3])
    assert result['noiseless_fit']['evaluations'] <= correlated.MAXIMUM_EVALUATIONS
    assert result['noiseless_recovery_passed']
    assert result['noiseless_fit']['scientific_decision'] == 'abstain'
    assert result['local_precision']['covariance_calibrated'] is False
    assert result['empirical_earth_fit_attempts'] == result['scientific_eligibility_changes'] == 0


def test_control_journal_counts_interruptions_and_rejects_changes(tmp_path):
    path = tmp_path/'starts.jsonl'
    with pytest.raises(ValueError, match='unknown'):
        charge(path, 'unknown', 'manifest', {'task'})
    assert not path.exists()
    charge(path, 'task', 'manifest', {'task'})
    with pytest.raises(ValueError, match='corrupt'):
        charge(path, 'task', 'changed', {'task'})
    charge(path, 'task', 'manifest', {'task'})
    with pytest.raises(ValueError, match='exhausted'):
        charge(path, 'task', 'manifest', {'task'})
    assert len(path.read_text().splitlines()) == 2


def test_cached_control_requires_matching_manifest_and_result_hash(tmp_path):
    path = tmp_path/'case.json'
    assert cached(path, 'case', 'manifest') is None
    result = {'recovery': True}
    record = dict(task='case', manifest_sha256='manifest', result=result, result_sha256=result_hash(result))
    path.write_text(json.dumps(record))
    assert cached(path, 'case', 'manifest') == result
    with pytest.raises(ValueError, match='corrupt'):
        cached(path, 'case', 'changed')
    record['result']['recovery'] = False; path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match='corrupt'):
        cached(path, 'case', 'manifest')
