# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll.ilvis0_matched_reuse_generated import assess


def test_passing_references_require_both_stopping_and_forecast_agreement():
    old = dict(initial_cost=5., residual_sum_squares=4., converged=True, evaluations=9)
    new = dict(old, evaluations=8, reused_full_rejections=[dict(after_evaluation=4, rejected_evaluation=3)])
    path = dict(training_epochs=2, coordinates=[[0., 0., 0.]]*4, later_positions_used=False)
    assert assess(old, new, path, path)['passed']
    assert not assess(old, dict(new, converged=False), path, path)['passed']
    changed = dict(path, coordinates=np.array(path['coordinates'])+np.array([0., 0., .02]))
    assert not assess(old, new, path, changed)['passed']


def test_comparison_preserves_old_failures_and_rejects_material_cost_regression():
    old = dict(initial_cost=5., residual_sum_squares=4., converged=False, evaluations=80)
    new = dict(old, residual_sum_squares=3.9, converged=True, reused_full_rejections=[])
    path = dict(training_epochs=2, coordinates=[[0., 0., 0.]]*4, later_positions_used=False)
    result = assess(old, new, path, path)
    assert result['passed'] and result['candidate_converged'] and not result['reference_converged']
    assert not assess(old, dict(new, residual_sum_squares=4.01), path, path)['passed']
