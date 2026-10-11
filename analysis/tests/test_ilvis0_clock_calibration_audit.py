# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
import json
import math
from pathlib import Path

import pytest


def sample():
    cases = [dict(case_id='retained', profile=False,
                  limits={'gyro_gain_z': .02, 'gyro_bias_z': math.pi/648000,
                          'gravity_delta': .05})]
    def fit(model, cost, gravity):
        return dict(model=model, converged=True, solver_reported_success=True,
            exact_projected_gradient_relative=1e-6, stationarity_tolerance=1e-4,
            active_parameters=['gyro_gain_z', 'gyro_bias_z', 'gravity_delta'],
            normalized_parameters=[-1., 1., gravity/.05],
            parameters=dict(gyro_gain_z=-.02, gyro_bias_z=math.pi/648000,
                            gravity_delta=gravity),
            active_bounds=['gyro_gain_z', 'gyro_bias_z'] +
                          (['gravity_delta'] if abs(gravity)==.05 else []),
            residual_sum_squares=cost, residual_rms_neu_m=[.03, .04, .7],
            evaluations=10, elapsed_s=30.)
    nominal = [fit(m, c, -.05) for m, c in
               [('sphere_rotating', 2.), ('sphere_still', 20.), ('flat_still', 40.)]]
    header = [fit(m, c, -.01) for m, c in
              [('sphere_rotating', 1.9), ('sphere_still', 20.), ('flat_still', 40.)]]
    return dict(state='complete', starts=3,
        cases=[dict(case_id='retained', fits=header)],
        nominal_reference=dict(cases=[dict(case_id='retained', fits=nominal)])), cases


def audit():
    from lll import ilvis0_clock_calibration_audit
    return ilvis0_clock_calibration_audit


def test_clock_pair_reports_gravity_release_without_claiming_z_recovery():
    summary, cases = sample()
    out = audit().compare(summary, cases)
    row = next(r for r in out['parameters'] if r['model']=='sphere_rotating'
               and r['parameter']=='gravity_delta')
    assert row['nominal_boundary']=='lower'
    assert row['header_boundary']=='interior'
    assert row['change']==pytest.approx(.04)
    gain = next(r for r in out['parameters'] if r['model']=='sphere_rotating'
                and r['parameter']=='gyro_gain_z')
    assert gain['change']==0
    assert out['comparisons'][0]['shape_preference']=='globe'
    assert out['comparisons'][0]['rotation_preference']=='rotating'
    assert out['comparisons'][0]['rotation_revealed']
    assert out['native_predictions']==out['optimizer_starts']==0


def test_corrected_z_rate_affine_convention_includes_bias_and_gain():
    a, c = audit().correction_coefficients(-.02, 1.)
    assert a==pytest.approx(1/.98)
    assert c==pytest.approx(-1/.98)
    for rate in (-15., 0., 15.):
        assert a*rate+c==pytest.approx((rate-1)/.98)


@pytest.mark.parametrize('problem', ['duplicate', 'missing', 'physical_mismatch', 'active_mismatch'])
def test_incompatible_matched_fits_rejected(problem):
    summary, cases = sample()
    rows = summary['cases'][0]['fits']
    if problem=='duplicate': rows[1]=copy.deepcopy(rows[0])
    if problem=='missing': rows.pop()
    if problem=='physical_mismatch': rows[0]['parameters']['gyro_gain_z']=.01
    if problem=='active_mismatch': rows[0]['active_parameters'].pop()
    with pytest.raises(ValueError): audit().compare(summary, cases)


def test_unfinished_comparison_withholds_ranking_and_rotation():
    summary, cases = sample()
    summary['cases'][0]['fits'][2]['converged']=False
    row = audit().compare(summary, cases)['comparisons'][0]
    assert row['shape_preference']=='unresolved'
    assert row['rotation_preference'] is None
    assert not row['rotation_revealed']


def test_zero_baseline_cost_has_no_infinite_ratio():
    summary, cases = sample()
    summary['nominal_reference']['cases'][0]['fits'][0]['residual_sum_squares']=0.
    out = audit().compare(summary, cases)
    assert out['fits'][0]['cost_change_percent'] is None


def test_conflicting_processing_cases_withhold_all_rotation_results():
    summary, cases = sample()
    cases.append(dict(cases[0], case_id='alternate'))
    for key in ('cases',):
        new = copy.deepcopy(summary[key][0]); new['case_id']='alternate'
        new['fits'][2]['residual_sum_squares']=.01
        summary[key].append(new)
    new = copy.deepcopy(summary['nominal_reference']['cases'][0]); new['case_id']='alternate'
    summary['nominal_reference']['cases'].append(new)
    summary['starts']=6
    rows = audit().compare(summary, cases)['comparisons']
    assert [r['shape_preference'] for r in rows]==['globe', 'flat']
    assert all(not r['rotation_revealed'] and r['rotation_preference'] is None for r in rows)


def test_report_rejects_changed_public_evidence_before_writing(tmp_path):
    source = Path(__file__).resolve().parents[2]/'docs/ilvis0-clock-calibration-audit-20261011/build_report.py'
    spec = importlib.util.spec_from_file_location('clock_calibration_report', source)
    report = importlib.util.module_from_spec(spec); spec.loader.exec_module(report)
    clock=tmp_path/'clock'; clock.mkdir()
    (clock/'summary.json').write_text('{}')
    (clock/'evidence-receipt.json').write_text(json.dumps(
        dict(artifacts={'summary.json': '0'*64})))
    with pytest.raises(ValueError, match='hash'):
        report.build(clock, tmp_path/'baseline', tmp_path/'output')
    assert not (tmp_path/'output').exists()
