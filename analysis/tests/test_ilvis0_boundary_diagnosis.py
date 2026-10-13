# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import gzip
import hashlib
import json

import numpy as np
import pytest

from lll import ilvis0_boundary_diagnosis as audit
from lll.ilvis0_solver_refinement import projected_stationarity


def example():
    point = np.array([0.])
    residual = np.array([-1e-5, 1.])
    jac = np.array([[1.], [0.]])
    stationarity, gradient, projected, scaled = projected_stationarity(point, residual, jac)
    value = dict(active_parameters=['x'], normalized_parameters=point.tolist(),
                 residual=residual.tolist(), jacobian=jac.tolist(),
                 convention='whitened residual derivative by normalized parameter')
    cost = float(residual @ residual)
    fit = dict(active_parameters=['x'], normalized_parameters=point.tolist(),
               gradient=gradient.tolist(), projected_gradient=projected.tolist(),
               scaled_projected_gradient=scaled.tolist(), singular_values=[1.],
               exact_projected_gradient_relative=stationarity, stationarity_tolerance=1e-4,
               evaluations=4, maximum_evaluations=600, converged=False,
               stability_verified=False, residual_sum_squares=cost, reference_cost=cost,
               initial_cost=cost, message='no decreasing feasible nonlinear step',
               stability_probe=dict(passed=False, reason='linear_correction_not_stable',
                                    predicted_cost_change=1e-10, predicted_residual_step=1e-5),
               step_history=[dict(evaluation=2, accepted=False, cost=cost+1e-9,
                                  fraction=1., normalized_step=1e-5),
                             dict(evaluation=3, accepted=False, cost=cost+1e-10,
                                  fraction=1e-7, normalized_step=1e-12)])
    return fit, value


def test_stationary_stall_is_not_budget_failure_or_recovered_fit():
    fit, value = example()
    row = audit.inspect_fit('segment::case::model::primary', fit, value)
    assert row['failure_class'] == 'stationary_stability_stall'
    assert row['stationarity_passed']
    assert row['predicted_cost_drop'] == pytest.approx(1e-10, rel=1e-5)
    assert row['predicted_residual_step'] == pytest.approx(1e-5)
    assert row['last_full_step_cost_change'] > 0
    assert row['rejected_tail_count'] == 2
    assert row['roundoff_bound_count'] == 0
    assert not row['qualifies_archival_fit']


def test_tangent_exhaustion_is_classified_even_with_reserved_fresh_call():
    fit, value = example()
    fit.update(message='tangent allowance exhausted', evaluations=599)
    row = audit.inspect_fit('segment::case::model::primary', fit, value)
    assert row['failure_class'] == 'budget_exhausted'


@pytest.mark.parametrize('field', ['normalized_parameters', 'active_parameters'])
def test_tangent_must_match_fit(field):
    fit, value = example()
    value[field] = [.1] if field == 'normalized_parameters' else ['other']
    with pytest.raises(ValueError, match='disagrees'):
        audit.inspect_fit('segment::case::model::primary', fit, value)


def test_corrupt_local_cost_rejected():
    fit, value = example()
    value['residual'][1] = 2.
    with pytest.raises(ValueError, match='cost'):
        audit.inspect_fit('segment::case::model::primary', fit, value)


def test_nonfinite_history_rejected():
    fit, value = example()
    fit['step_history'][0]['cost'] = float('nan')
    with pytest.raises(ValueError, match='history'):
        audit.inspect_fit('segment::case::model::primary', fit, value)


def test_false_accepted_cost_increase_rejected():
    fit, value = example()
    fit['step_history'][0]['accepted'] = True
    with pytest.raises(ValueError, match='accepted'):
        audit.inspect_fit('segment::case::model::primary', fit, value)


def write_epochs(directory, name, errors):
    content = gzip.compress(json.dumps(dict(times_s=[0., 1.], errors_neu_m=errors)).encode(), mtime=0)
    (directory/name).write_bytes(content)
    return dict(epoch_file=name, epoch_sha256=hashlib.sha256(content).hexdigest())


def test_saved_track_agreement_does_not_promote_failed_primary(tmp_path):
    first = write_epochs(tmp_path, 'a.json.gz', [[1., 2., 3.], [1., 2., 3.]])
    second = write_epochs(tmp_path, 'b.json.gz', [[1.003, 2., 3.], [1.003, 2., 3.]])
    first.update(converged=False, residual_sum_squares=2.)
    second.update(converged=True, residual_sum_squares=2.+1e-8)
    row = audit.compare_saved_predictions(tmp_path, first, second)
    assert row['track_difference_rms_neu_m'] == pytest.approx([.003, 0., 0.])
    assert row['numerical_agreement']
    assert not row['qualified_repeatability']
    assert not row['qualifies_archival_fit']


def test_epoch_hash_failure_and_path_escape_rejected(tmp_path):
    fit = write_epochs(tmp_path, 'a.json.gz', [[1., 2., 3.], [1., 2., 3.]])
    corrupt = copy.deepcopy(fit)
    corrupt['epoch_sha256'] = '0'*64
    with pytest.raises(ValueError, match='hash'):
        audit.load_epochs(tmp_path, corrupt)
    corrupt['epoch_file'] = '../a.json.gz'
    with pytest.raises(ValueError, match='filename'):
        audit.load_epochs(tmp_path, corrupt)
