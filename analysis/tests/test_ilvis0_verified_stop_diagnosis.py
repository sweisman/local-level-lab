# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path

import pytest


def module():
    path=Path(__file__).resolve().parents[2]/'docs/ilvis0-verified-stop-diagnosis-20261011/build_report.py'
    spec=importlib.util.spec_from_file_location('verified_stop_diagnosis',path)
    result=importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


def probe():
    return dict(passed=False,reason='linear_correction_not_stable',
        predicted_cost_change=2.4e-12,predicted_residual_step=1.55e-6)


def test_saved_failed_probe_remains_failed_and_has_no_fresh_observation():
    row=module().probe_row(probe())
    assert row['probe_passed'] is False
    assert row['predicted_residual_step_ratio']==pytest.approx(1.55)
    assert row['predicted_cost_change_ratio']==pytest.approx(.00024)
    assert row['fresh_nonlinear_probe_recorded'] is False


def test_absent_probe_does_not_imply_success():
    row=module().probe_row(None)
    assert row['probe_passed'] is None
    assert row['probe_reason']=='not_attempted'


@pytest.mark.parametrize('change',[
    dict(passed=True),dict(predicted_residual_step=1e-7),
    dict(predicted_cost_change=float('nan')),dict(passed='false'),
])
def test_inconsistent_probe_evidence_is_rejected(change):
    with pytest.raises(ValueError): module().probe_row(dict(probe(),**change))


def test_verified_probe_requires_both_fresh_measurement_and_stationarity():
    p=dict(passed=True,reason='fresh_stability_verified',predicted_cost_change=1e-10,
        predicted_residual_step=1e-7,actual_cost_change=1e-10,
        actual_residual_step=1e-7,fresh_stationarity=1e-8)
    assert module().probe_row(p)['fresh_nonlinear_probe_recorded']
    with pytest.raises(ValueError): module().probe_row(dict(p,actual_residual_step=1e-4))
    p.pop('fresh_stationarity')
    with pytest.raises(ValueError): module().probe_row(p)
