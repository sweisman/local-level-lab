# SPDX-License-Identifier: AGPL-3.0-or-later
import math
import importlib.util
import json
from pathlib import Path

import pytest

from lll import ilvis0_saved_audit as audit


def sample_fit():
    return dict(model='sphere_rotating', converged=True, solver_reported_success=True,
                exact_projected_gradient_relative=1e-8, stationarity_tolerance=1e-4,
                active_parameters=['gyro_bias_z', 'gyro_gain_z'],
                normalized_parameters=[-1., .5],
                parameters=dict(gyro_bias_z=-math.pi/648000, gyro_gain_z=.01),
                active_bounds=['gyro_bias_z'], residual_sum_squares=12.,
                conservative_fixed_parameter_cost=3., residual_rms_neu_m=[3., 4., 2.],
                header_fixed_parameter_rms_neu_m=[6., 8., 4.],
                diagnostic_sections=[dict(epochs=4, residual_mean_neu_m=[0., 0., 0.],
                                          residual_rms_neu_m=[3., 4., 2.])],
                sections_are_refits=False, sections_are_independent_trials=False)


def test_signed_limits_and_units_preserve_calibration_meaning():
    rows = audit.parameter_rows(sample_fit(),
                                dict(gyro_bias_z=math.pi/648000, gyro_gain_z=.02))
    bias, gain = rows
    assert bias['boundary'] == 'lower'
    assert bias['value'] == pytest.approx(-1.)
    assert bias['unit'] == 'deg/hour'
    assert gain['value'] == pytest.approx(1.)
    assert gain['upper_limit'] == pytest.approx(2.)
    assert gain['boundary'] == 'interior'
    assert gain['normalized_distance_to_limit'] == .5


def test_profiled_removal_uses_zero_to_one_not_signed_scaling():
    fit = sample_fit()
    fit.update(active_parameters=['earth_removal'], normalized_parameters=[-1.],
               parameters=dict(earth_removal=0.), active_bounds=['earth_removal'])
    row, = audit.parameter_rows(fit, {}, profile=True)
    assert (row['value'], row['lower_limit'], row['upper_limit'], row['boundary']) == (0., 0., 1., 'lower')


@pytest.mark.parametrize('change', [
    dict(normalized_parameters=[-1.]),
    dict(normalized_parameters=[-1., math.nan]),
    dict(normalized_parameters=[-1., 1.2]),
    dict(parameters=dict(gyro_bias_z=0., gyro_gain_z=.01)),
    dict(active_bounds=[]),
])
def test_malformed_or_inconsistent_saved_parameters_are_rejected(change):
    fit = sample_fit(); fit.update(change)
    with pytest.raises(ValueError):
        audit.parameter_rows(fit, dict(gyro_bias_z=math.pi/648000, gyro_gain_z=.02))


def test_whitened_rms_uses_all_components_without_claiming_adequacy():
    row = audit.residual_summary(sample_fit(), 4)
    assert row['residual_components'] == 12
    assert row['whitened_rms'] == 1.
    assert row['conservative_whitened_rms'] == .5
    assert row['horizontal_rms_m'] == 5.
    assert row['vertical_rms_m'] == 2.
    assert row['header_to_nominal_rms_ratio'] == 2.
    assert row['absolute_fit_status'] == 'not_calibrated'
    assert row['held_out_validation'] is False


def test_epoch_mismatch_is_not_silently_used_as_a_residual_denominator():
    with pytest.raises(ValueError):
        audit.residual_summary(sample_fit(), 5)


def test_small_cost_never_promotes_an_unfinished_fit():
    fit = sample_fit(); fit.update(converged=False, residual_sum_squares=0.)
    assert audit.fit_status(fit) == 'unresolved'
    assert audit.residual_summary(fit, 4)['absolute_fit_status'] == 'not_calibrated'
    fit.update(converged=True, exact_projected_gradient_relative=.01)
    assert audit.fit_status(fit) == 'unresolved'


def test_correlations_handle_ties_and_saturated_numerical_jitter():
    assert audit.rank_correlation([1., 1., 2., 2.], [2., 2., 1., 1.]) == -1.
    assert audit.rank_correlation([-1., -1., -1.], [1., 2., 3.]) is None
    assert [audit.boundary_coordinate(x) for x in [-1., -1.+1e-15, -.9999]] == [-1., -1., -1.]


def test_one_weak_direction_keeps_parameter_order_and_no_covariance_claim():
    fit = sample_fit()
    fit.update(singular_values=[4., 1e-9], right_singular_vectors=[[1., 0.], [0., -1.]])
    rows = audit.weak_directions(fit)
    assert rows[0]['singular_value'] == 1e-9
    assert rows[0]['dominant_parameters'] == 'gyro_gain_z:-1;gyro_bias_z:0'


def test_artifact_hash_failure_is_reported_before_analysis(tmp_path):
    (tmp_path/'sample.csv').write_text('changed')
    with pytest.raises(ValueError, match='hash'):
        audit.verify_artifacts(tmp_path, dict(artifacts={'sample.csv': '0'*64}))


def test_analysis_keeps_baseline_and_trial_separate_and_refuses_duplicates():
    fit = sample_fit()
    result = dict(segment_id='s', filename='sample.013', provenance=dict(receiver_epochs=4),
                  profile=dict(conditional_shape_preference='unresolved'),
                  cases=[dict(case_id='c', fits=[fit])])
    selection = dict(selected=[dict(segment=dict(segment_id='s', imu_type=21, duration_s=240.,
                         median_receiver_ground_speed_kmh=800.,
                         receiver_fixes=[dict(latitude_rad=0., height_m=1000.) for _ in range(4)]))])
    cases = [dict(case_id='c', profile=False,
                  limits=dict(gyro_bias_z=math.pi/648000, gyro_gain_z=.02))]
    out = audit.analyze(dict(baseline=dict(results=[result]), trial=dict(results=[result])), selection, cases)
    assert len(out['fits']) == 2
    assert {r['study'] for r in out['fits']} == {'baseline', 'trial'}
    assert out['optimizer_starts'] == out['model_evaluations_performed'] == 0
    assert out['scientific_decision'] == 'abstain'
    with pytest.raises(ValueError, match='duplicate'):
        audit.analyze(dict(baseline=dict(results=[result, result])), selection, cases)


def test_builder_refuses_tampered_inputs_before_publishing(tmp_path):
    path = Path(__file__).resolve().parents[2]/'docs/ilvis0-calibration-audit-20261010/build_report.py'
    spec = importlib.util.spec_from_file_location('saved_calibration_report', path)
    builder = importlib.util.module_from_spec(spec); spec.loader.exec_module(builder)
    baseline = tmp_path/'baseline'; baseline.mkdir()
    (baseline/'summary.json.gz').write_bytes(b'tampered')
    (baseline/'evidence-receipt.json').write_text(json.dumps(dict(
        artifacts={'summary.json.gz': '0'*64})))
    output = tmp_path/'output'
    with pytest.raises(ValueError, match='hash'):
        builder.build(baseline=baseline, trial=tmp_path/'unused', output=output)
    assert not output.exists()
