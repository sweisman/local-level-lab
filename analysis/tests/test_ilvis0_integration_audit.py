# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
import json
import math
from pathlib import Path

import pytest


def sample():
    case = dict(case_id='bias1_unsubtracted', profile=False,
                limits={'gyro_gain_z': .02, 'gyro_bias_z': math.pi/648000})
    def fit(model, cost):
        return dict(model=model, converged=True, solver_reported_success=True,
            exact_projected_gradient_relative=1e-6, stationarity_tolerance=1e-4,
            active_parameters=['gyro_gain_z', 'gyro_bias_z'],
            normalized_parameters=[-1., 1.], active_bounds=['gyro_gain_z', 'gyro_bias_z'],
            parameters=dict(gyro_gain_z=-.02, gyro_bias_z=math.pi/648000),
            residual_sum_squares=cost, residual_rms_neu_m=[.03, .04, .7],
            singular_values=[10., .001], clock_hypothesis='header_elapsed',
            evaluations=100, actual_tangent_sweeps=98, diagnostic_predictions=2,
            elapsed_s=400., message='finished')
    original = dict(state='complete', starts=3, provenance={'source_sha256': 'abc'},
        cases=[dict(case_id=case['case_id'], fits=[fit(m, c) for m, c in
            [('sphere_rotating', 2.), ('sphere_still', 20.), ('flat_still', 40.)]])])
    revised = copy.deepcopy(original)
    revised['header_reference'] = copy.deepcopy(original)
    for f in revised['cases'][0]['fits']:
        f.update(integration_mode='combined', increment_convention='ordinary_rate_integrals')
    return original, revised, [case]


def audit():
    from lll import ilvis0_integration_audit
    return ilvis0_integration_audit


def test_unfinished_fit_is_not_relabelled_and_rotation_is_withheld():
    old, new, cases = sample()
    f = new['cases'][0]['fits'][1]
    f.update(converged=False, solver_reported_success=False, evaluations=200,
             actual_tangent_sweeps=198,
             exact_projected_gradient_relative=.0053, message='evaluation cap')
    result = audit().compare(old, new, cases)
    row = result['fits'][1]
    assert row['revised_status'] == 'unresolved'
    assert row['stationarity_limit_ratio'] == pytest.approx(53.)
    assert not result['complete_matched_comparison']
    assert result['shape_preference'] == 'unresolved'
    assert result['background_field_preference'] is None
    f['exact_projected_gradient_relative'] = 1e-8
    assert audit().compare(old, new, cases)['fits'][1]['revised_status'] == 'unresolved'


def test_missing_vectors_do_not_become_parameter_coupling_claims():
    old, new, cases = sample()
    result = audit().compare(old, new, cases)
    row = result['fits'][0]
    assert row['jacobian_condition_ratio'] == pytest.approx(10000.)
    assert 'right_singular_vectors' in row['missing_diagnostics']
    assert not result['joint_calibration_identified']
    assert result['optimizer_starts'] == result['native_predictions'] == 0
    assert result['parameters'][0]['change'] == 0
    assert result['native_sweeps'] == 300
    assert result['tangent_sweeps'] == 294
    assert result['z_corrections'][0]['rate_addition_dph'] == pytest.approx(-1/.98)


def test_saved_native_accounting_must_include_predictions():
    old, new, cases = sample()
    new['cases'][0]['fits'][0]['diagnostic_predictions'] = 3
    with pytest.raises(ValueError, match='accounting'):
        audit().compare(old, new, cases)


@pytest.mark.parametrize('change', ['duplicate', 'missing', 'reference', 'provenance',
                                   'active', 'physical', 'clock', 'convention', 'case'])
def test_incompatible_saved_comparisons_fail(change):
    old, new, cases = sample()
    fits = new['cases'][0]['fits']
    if change == 'duplicate': fits[1] = copy.deepcopy(fits[0])
    if change == 'missing': fits.pop()
    if change == 'reference': new['header_reference']['starts'] = 0
    if change == 'provenance': new['provenance']['source_sha256'] = 'changed'
    if change == 'active': fits[0]['active_parameters'].reverse()
    if change == 'physical': fits[0]['parameters']['gyro_gain_z'] = .01
    if change == 'clock': fits[0]['clock_hypothesis'] = 'nominal'
    if change == 'convention': fits[0]['increment_convention'] = 'compensated'
    if change == 'case': new['cases'].append(copy.deepcopy(new['cases'][0]))
    with pytest.raises(ValueError): audit().compare(old, new, cases)


@pytest.mark.parametrize('values', [[1.], [.001, 10.], [10., -1.], [10., float('nan')]])
def test_invalid_spectrum_is_rejected(values):
    old, new, cases = sample()
    new['cases'][0]['fits'][0]['singular_values'] = values
    with pytest.raises(ValueError): audit().compare(old, new, cases)


def test_zero_singular_value_is_reported_without_infinite_json():
    old, new, cases = sample()
    new['cases'][0]['fits'][0]['singular_values'][-1] = 0.
    result = audit().compare(old, new, cases)
    assert result['fits'][0]['jacobian_condition_ratio'] is None
    assert result['fits'][0]['zero_singular_values'] == 1
    json.dumps(result, allow_nan=False)


def test_profile_plan_is_equal_and_finite_with_no_implicit_starts():
    scope = audit().profile_scope()
    assert len(scope['identities']) == len(set(scope['identities'])) == 27
    assert scope['maximum_native_sweeps'] == 5400
    assert scope['maximum_per_identity'] == 1
    assert scope['authorized_starts'] == 0
    assert {i.split('::')[2] for i in scope['identities']} == set(audit().MODELS)


def test_report_rejects_changed_evidence_before_output(tmp_path):
    source = Path(__file__).resolve().parents[2]/'docs/ilvis0-integration-audit-20261011/build_report.py'
    spec = importlib.util.spec_from_file_location('integration_report', source)
    report = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(report)
    original = tmp_path/'original'; original.mkdir()
    (original/'summary.json').write_text('{}')
    (original/'evidence-receipt.json').write_text(json.dumps(
        {'artifacts': {'summary.json': '0'*64}}))
    with pytest.raises(ValueError, match='hash'):
        report.build(original, tmp_path/'revised', tmp_path/'output')
    assert not (tmp_path/'output').exists()


def test_public_report_reproduces_without_measurements_or_native_imports(tmp_path, monkeypatch):
    import builtins
    from lll import ilvis0_saved_audit as saved
    source = Path(__file__).resolve().parents[2]/'docs/ilvis0-integration-audit-20261011/build_report.py'
    spec = importlib.util.spec_from_file_location('integration_report_reproduction', source)
    report = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(report)
    original_import = builtins.__import__
    def guarded_import(name, *args, **kwargs):
        if name in {'lll.ilvis0_shape', 'lll.ilvis0_estimator', 'lll.ilvis0_exploratory',
                    'numpy', 'scipy', 'ctypes'}:
            raise AssertionError('metadata report imported a numerical engine')
        return original_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', guarded_import)
    out = report.build(output=tmp_path)
    receipt = report.load(tmp_path/'report-receipt.json')
    saved.verify_artifacts(tmp_path, receipt)
    for path, digest in receipt['inputs'].items():
        assert report.sha(Path(path)) == digest
    assert out['native_sweeps'] == 974
    assert out['tangent_sweeps'] == 962
    assert sum(f['revised_status'] == 'converged' for f in out['fits']) == 4
    assert out['background_field_preference'] is None
    assert receipt['optimizer_starts'] == receipt['native_predictions'] == 0
