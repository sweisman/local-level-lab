# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-system diagnosis must preserve dimensions, bounds and failed labels."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest


def module():
    path=Path(__file__).resolve().parents[2]/'docs/ilvis0-last-correction-audit-20261018/build_report.py'
    assert path.exists(), 'last-stretch correction audit is missing'
    spec=importlib.util.spec_from_file_location('last_correction_audit',path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


@pytest.mark.parametrize('method',['original','scaled','fixed_time'])
def test_known_affine_optimum_and_fixed_time_keep_other_parameters(method):
    report=module().solve(np.zeros(3),np.array([-2.,-.5,3.]),np.eye(3),time_index=1,method=method)
    assert report['success'] and report['feasible']
    assert report['step']==pytest.approx([1.,0. if method=='fixed_time' else .5,-1.])
    assert report['affine_cost']==pytest.approx(5.25 if method=='fixed_time' else 5.)
    assert report['relative_affine_cost_change']<0
    assert 'converged' not in report and 'scientific_decision' not in report


def test_rank_deficiency_remains_descriptive():
    report=module().spectrum(np.array([[1.,1.,0.],[0.,0.,1.],[0.,0.,0.]]))
    assert report['rank']==2 and report['columns']==3
    assert report['diagnostic_only'] is True


def test_history_retains_rejected_decreases_and_budget_information():
    row=dict(maximum_evaluations=80,evaluations=42,message='no positive predicted decrease',
        step_history=[dict(accepted=False,predicted_reduction=1.,actual_reduction=-.5,normalized_step=.2),
                      dict(accepted=False,predicted_reduction=1e-7,actual_reduction=-1e-8,normalized_step=1e-6)])
    report=module().history(row)
    assert report['accepted']==0 and report['rejected']==2 and not report['budget_exhausted']
    assert report['smallest_trial']['actual_reduction']==-1e-8


@pytest.mark.parametrize('bad',['nan','shape','bounds','method','index'])
def test_invalid_problem_fails_closed(bad):
    x=np.zeros(2);r=np.ones(2);j=np.eye(2);index=0;method='original'
    if bad=='nan':j[0,0]=np.nan
    if bad=='shape':j=np.ones((2,3))
    if bad=='bounds':x[1]=1.01
    if bad=='method':method='unknown'
    if bad=='index':index=2
    with pytest.raises(ValueError):module().solve(x,r,j,time_index=index,method=method)
