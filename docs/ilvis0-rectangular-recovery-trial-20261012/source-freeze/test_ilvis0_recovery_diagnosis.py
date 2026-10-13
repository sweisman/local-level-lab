# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import hashlib
import json

import pytest

from lll import ilvis0_recovery_diagnosis as diagnosis


def fit():
    return dict(converged=False, evaluations=19, maximum_evaluations=600,
                model='sphere_rotating', role='primary',
                active_parameters=['bias', 'gain'], normalized_parameters=[.99998, 0.],
                gradient=[-1., 0.], projected_gradient=[-1., 0.],
                scaled_projected_gradient=[2e-8 * -1, 0.],
                exact_projected_gradient_relative=2e-8, stationarity_tolerance=1e-4,
                singular_values=[1e4, 1e-4], residual_sum_squares=13.,
                reference_cost=13., stability_verified=False,
                stability_probe=dict(passed=False, reason='linear_correction_not_stable',
                                     predicted_cost_change=1e-10, predicted_residual_step=2e-5),
                accepted_step_history=[], message='`xtol` termination condition is satisfied.')


def test_separates_gradient_and_stability_failures_without_relabeling():
    a = fit()
    before = copy.deepcopy(a)
    row = diagnosis.inspect_fit('segment::case::sphere_rotating::primary', a)
    assert row['failure_class'] == 'early_stability_failure'
    assert row['stationarity_passed'] and not row['converged']
    assert row['jacobian_condition_ratio'] == 1e8
    assert row['predicted_residual_step_ratio'] == pytest.approx(20.)
    assert a == before
    a['exact_projected_gradient_relative'] = 2e-4
    a['scaled_projected_gradient'][0] = -2e-4
    a['stability_probe'] = dict(passed=False, reason='not_stationary')
    row = diagnosis.inspect_fit('segment::case::sphere_rotating::primary', a)
    assert row['failure_class'] == 'early_stationarity_failure'
    assert row['dominant_parameter'] == 'bias'
    assert row['dominant_bound_distance'] == pytest.approx(2e-5)
    a['evaluations'] = 598
    a['message'] = 'The maximum number of function evaluations is exceeded.'
    assert diagnosis.inspect_fit('segment::case::sphere_rotating::primary', a)['failure_class'] == 'budget_exhausted'


def test_callback_acceptance_and_probe_disagreement_is_explicit():
    a = fit()
    a['converged'] = a['stability_verified'] = True
    row = diagnosis.inspect_fit('segment::case::sphere_rotating::primary', a)
    assert row['failure_class'] == 'passed'
    assert row['callback_probe_disagreement']


@pytest.mark.parametrize('field,value', [('singular_values', [1., float('nan')]),
                                       ('normalized_parameters', [2., 0.]),
                                       ('scaled_projected_gradient', [1.]),
                                       ('evaluations', 601)])
def test_corrupt_diagnostics_are_rejected(field, value):
    a = fit(); a[field] = value
    with pytest.raises(ValueError):
        diagnosis.inspect_fit('segment::case::sphere_rotating::primary', a)


def test_inconsistent_saved_gradient_is_rejected():
    a = fit(); a['exact_projected_gradient_relative'] = .01
    with pytest.raises(ValueError):
        diagnosis.inspect_fit('segment::case::sphere_rotating::primary', a)


def test_only_sealed_completed_results_can_be_loaded(tmp_path):
    identity = 'segment::case::sphere_rotating::primary'
    values = {'manifest.json': {}, 'summary.json': dict(state='complete', starts=1,
              native_sweeps=1, results={identity: fit()}),
              'starts.jsonl': dict(identity=identity, number=1),
              'sweeps.jsonl': dict(identity=identity, number=1)}
    hashes = {}
    for name, value in values.items():
        raw = json.dumps(value).encode() + b'\n'
        (tmp_path/name).write_bytes(raw)
        hashes[name] = hashlib.sha256(raw).hexdigest()
    completion = dict(state='complete', starts=1, native_sweeps=1,
                      manifest_sha256=hashes['manifest.json'], summary_sha256=hashes['summary.json'],
                      journal_hashes={n: hashes[n] for n in ('starts.jsonl', 'sweeps.jsonl')})
    (tmp_path/'completion.json').write_text(json.dumps(completion))
    assert diagnosis.load_completed(tmp_path)[0]['starts'] == 1
    (tmp_path/'summary.json').write_text('{}')
    with pytest.raises(ValueError, match='hash'):
        diagnosis.load_completed(tmp_path)


def test_missing_completion_is_rejected(tmp_path):
    with pytest.raises(ValueError, match='completed'):
        diagnosis.load_completed(tmp_path)
