# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
from pathlib import Path
import numpy as np
import pytest


def module():
    assert Path(__file__).parents[1].joinpath('lll/ilvis0_horizontal_repeat_audit.py').exists(),'repeat audit helper missing'
    return importlib.import_module('lll.ilvis0_horizontal_repeat_audit')


def row():
    return dict(identity='control',passed=True,fit=dict(converged=True,normalized_parameters=[0.,0.],
        active_parameters=['position_x','null'],residual_sum_squares=4.,numerical_rank=1,columns=2,
        parameters=dict(time_offset=.001),message='known bound',evaluations=5,maximum_evaluations=200))


def saved():
    return dict(normalized_parameters=[0.,0.],active_parameters=['position_x','null'],
        residual=[-2.,0.],jacobian=[[1.,0.],[0.,0.]],times_s=[1.,2.],gps=[[0.,0.,0.],[0.,0.,0.]])


def test_known_bound_and_null_column_preserved_without_native_calls():
    result=module().endpoint(row(),saved())
    assert result['columns']==2 and result['original_fit_passed']
    for method in result['corrections']:
        assert method['affine_cost']==pytest.approx(1.) and method['step']==pytest.approx([1.,0.])
        assert method['feasible'] and method['affine_not_worse_than_zero']
    assert result['native_evaluations']==0


def test_changed_parameter_order_rejected_before_solving():
    s=saved();s['active_parameters'].reverse()
    with pytest.raises(ValueError):module().endpoint(row(),s)


def test_changed_residual_cost_rejected_before_solving():
    s=saved();s['residual'][0]=-3.
    with pytest.raises(ValueError):module().endpoint(row(),s)
