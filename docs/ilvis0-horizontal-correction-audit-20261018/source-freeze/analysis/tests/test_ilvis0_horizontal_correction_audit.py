# SPDX-License-Identifier: AGPL-3.0-or-later
"""Constructed affine systems; no integrations or archive access."""
import importlib
import numpy as np
import pytest


def module():
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath('lll/ilvis0_horizontal_correction_audit.py').exists(), 'saved correction audit missing'
    return importlib.import_module('lll.ilvis0_horizontal_correction_audit')


def row(jac=None):
    return dict(identity='control',passed=False,fit=dict(
        normalized_parameters=[.9999,-.2,0.],active_parameters=['a','b','null'],
        converged=False,exact_projected_gradient_relative=1e-6,
        stability_probe=dict(passed=False,actual_cost_change=1e-7,fresh_stationarity=3e-4),
        local_linearization=dict(residual=[1e-6,2e-6],jacobian=jac or [[1.,0.,0.],[0.,2.,0.]])))


def test_all_columns_and_zero_direction_are_preserved():
    report=module().audit(row())
    assert report['columns']==3 and report['numerical_rank']==2
    assert report['original_fit_passed'] is False
    assert len(report['corrections'])==3
    for c in report['corrections']:
        assert len(c['step'])==3 and c['step'][2]==0.
        assert c['feasible'] and c['affine_not_worse_than_zero']
    assert report['native_evaluations']==0 and report['scientific_decision']=='abstain'


def test_scaled_formulation_keeps_same_physical_bounds():
    value=row([[1e6,0.,0.],[0.,2e-6,0.]])
    report=module().audit(value)
    for c in report['corrections']:
        point=np.asarray(value['fit']['normalized_parameters'])+c['step']
        assert np.max(abs(point))<=1.
        assert np.max(abs(np.asarray(c['step'])))<=.00100000000001
    assert report['saved_probe_actual_cost_change']==1e-7


@pytest.mark.parametrize('change',[lambda x:x['fit']['local_linearization'].update(jacobian=[[1.]]),
                                    lambda x:x['fit']['normalized_parameters'].__setitem__(0,2.),
                                    lambda x:x['fit']['local_linearization'].update(residual=[float('nan'),0.])])
def test_invalid_saved_system_is_rejected(change):
    value=row();change(value)
    with pytest.raises(ValueError):module().audit(value)
