# SPDX-License-Identifier: AGPL-3.0-or-later
"""The substitution gate compares saved predictions in physical metres."""
import pytest


def _case():
    result = dict(passed=True, converged=True, accuracy_all_sections=True,
                  model='sphere_rotating', profile=False,
                  policy_id='reported-short-v1', start=0,
                  training_cost=1.0, all_columns_retained=True,
                  original_reads=0, protected_reads=0,
                  scientific_decision='abstain')
    fit = dict(active_parameters=['gyro_bias_x', 'gyro_gain_z'],
               residual_sum_squares=1.0, converged=True)
    forecast = dict(coordinates=[[0.3, 0.2, 100.0]] * 3,
                    times_s=[0., 1., 2.],
                    prediction_receiver_positions_used=False)
    return result, fit, forecast


def test_hybrid_saved_pair_accepts_identical_positions_and_classification():
    from lll.airquantumgrav_observed_hybrid_report import compare_pair

    result, fit, forecast = _case()
    report = compare_pair(result, result, fit, fit, forecast, forecast,
                          tolerance_m=.01)
    assert report['passed']
    assert report['maximum_position_difference_m'] == 0
    assert report['training_cost_difference'] == 0


def test_hybrid_saved_pair_rejects_tiny_angle_but_large_ground_distance():
    from lll.airquantumgrav_observed_hybrid_report import compare_pair

    result, fit, forecast = _case()
    changed = dict(forecast, coordinates=[[.30000001, .2, 100.]] * 3)
    report = compare_pair(result, result, fit, fit, forecast, changed,
                          tolerance_m=.01)
    assert not report['passed']
    assert report['maximum_position_difference_m'] > .05


def test_hybrid_saved_pair_requires_every_nuisance_column_and_same_decisions():
    from lll.airquantumgrav_observed_hybrid_report import compare_pair

    result, fit, forecast = _case()
    missing = dict(fit, active_parameters=['gyro_bias_x'])
    assert not compare_pair(result, result, fit, missing,
                            forecast, forecast, tolerance_m=.01)['passed']
    different = dict(result, accuracy_all_sections=False)
    assert not compare_pair(result, different, fit, fit,
                            forecast, forecast, tolerance_m=.01)['passed']
    with pytest.raises(ValueError, match='qualified reference'):
        compare_pair(dict(result, passed=False), result, fit, fit,
                     forecast, forecast, tolerance_m=.01)


def test_hybrid_report_rejects_unclosed_study(tmp_path):
    from lll.airquantumgrav_observed_hybrid_report import inspect

    with pytest.raises((FileNotFoundError, ValueError)):
        inspect(tmp_path)


def test_hybrid_report_rejects_failed_or_incomplete_qualification():
    from lll.airquantumgrav_observed_hybrid_report import verify_qualification_report

    good = b'<testsuite tests="1" failures="0"><testcase classname="c" name="a"/></testsuite>'
    verify_qualification_report(good, ['a'], minimum_tests=1)
    with pytest.raises(ValueError, match='complete'):
        verify_qualification_report(good, ['a', 'b'], minimum_tests=1)
    failed = b'<testsuite tests="1" failures="1"><testcase name="a"><failure/></testcase></testsuite>'
    with pytest.raises(ValueError, match='complete'):
        verify_qualification_report(failed, ['a'], minimum_tests=1)
