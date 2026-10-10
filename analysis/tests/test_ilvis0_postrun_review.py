# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import math


def module():
    path = Path(__file__).resolve().parents[2]/'docs/ilvis0-highspeed-segments-20261008/diagnose_results.py'
    spec = importlib.util.spec_from_file_location('ilvis0_postrun_review', path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def fit(**changes):
    return dict(converged=False, solver_reported_success=False,
                exact_projected_gradient_relative=1e-6, stationarity_tolerance=1e-4,
                message='The maximum number of function evaluations is exceeded.',
                **changes)


def test_budget_stop_with_small_gradient_remains_unresolved():
    d = module().classify(fit())
    assert d == dict(status='unresolved', reason='evaluation_limit', stationarity_pass=True)


def test_successful_stop_does_not_override_stationarity():
    f = fit()
    f.update(solver_reported_success=True, exact_projected_gradient_relative=.01,
             message='`xtol` termination condition is satisfied.')
    assert module().classify(f)['reason'] == 'stationarity_failure'


def test_nonfinite_stationarity_is_never_accepted():
    f = fit()
    f.update(converged=True, solver_reported_success=True,
             exact_projected_gradient_relative=math.nan)
    assert module().classify(f)['status'] == 'unresolved'
    assert not module().classify(f)['stationarity_pass']


def test_rank_correlation_handles_ties_and_constant_geometry():
    m = module()
    assert m.rank_correlation([1, 1, 2, 2], [2, 2, 1, 1]) == -1
    assert m.rank_correlation([1, 1, 1], [0, 3, 6]) is None


def test_ratio_does_not_hide_a_zero_minimum_singular_value():
    assert module().singular_ratio([5, 2, 0]) == 0


def test_review_does_not_promote_stationary_budget_stops():
    m = module()
    fits = [dict(fit(), model=model, active_bounds=[], singular_values=[1., 0.],
                 evaluations=200, initialization_evaluations=25, elapsed_s=1.,
                 residual_rms_neu_m=[1., 1., 1.], header_fixed_parameter_rms_neu_m=[2., 2., 2.])
            for model in m.public.MODELS]
    result = dict(segment_id='test', filename='sample.013',
                  cases=[dict(case_id=c, fits=fits) for c in m.public.CASES],
                  profile=dict(conditional_shape_preference='unresolved', rotation_diagnostics=None))
    selection = dict(selected=[dict(segment=dict(segment_id='test', duration_s=240.,
                         median_receiver_ground_speed_kmh=800., imu_type=21))])
    review = m.analyze(dict(results=[result]), selection)
    assert review['conditional_outcomes'] == {'unresolved': 1}
    assert review['stationarity_only_complete_stretches'] == 1
    assert review['fit_counts'] == {'unresolved': 6}
    assert review['scientific_decision'] == 'abstain'
    assert review['matched_shape_pairs_by_globe'] == {}
