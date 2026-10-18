# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path

import numpy as np
import pytest


def module():
    p=Path(__file__).resolve().parents[2]/'docs/ilvis0-correction-audit-20261018/build_report.py'
    assert p.exists(), 'saved correction audit is missing'
    spec=importlib.util.spec_from_file_location('correction_audit',p)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


def test_affine_known_optimum_respects_branch_and_original_bounds():
    m=module();point=np.array([.2,0.]);r=np.array([0.,-3.]);j=np.eye(2)
    for side in ('left','right','fixed'):
        result=m.solve_local(point,r,j,time_index=0,edges=(.1,.3),side=side)
        assert result['success'] and result['correction']==pytest.approx([0.,1.])
        assert result['predicted_cost']==pytest.approx(4.)
        assert result['predicted_cost']<result['source_cost']


def test_fixed_time_removes_only_timing_and_keeps_other_directions():
    m=module();p=np.array([.2,0.]);r=np.array([-1.,-.5]);j=np.eye(2)
    result=m.solve_local(p,r,j,time_index=0,edges=(.1,.3),side='fixed')
    assert result['correction']==pytest.approx([0.,.5])
    assert result['predicted_cost']==pytest.approx(1.)
    right=m.solve_local(p,r,j,time_index=0,edges=(.1,.3),side='right')
    assert right['correction'][0]==pytest.approx(.1)
    assert right['predicted_cost']<result['predicted_cost']


def test_rank_deficient_system_reports_ambiguity_without_new_scientific_label():
    m=module();p=np.zeros(3);r=np.array([1.,-2.,0.]);j=np.array([[1.,1.,0.],[0.,0.,1.],[0.,0.,0.]])
    report=m.spectrum(j)
    assert report['numerical_rank']<3
    result=m.solve_local(p,r,j,time_index=0,edges=(-.1,.1),side='fixed')
    assert result['success'] and result['predicted_cost']==pytest.approx(1.)
    assert 'converged' not in result and 'scientific_decision' not in result


@pytest.mark.parametrize('bad',['nan','shape','bounds','edge','side'])
def test_invalid_local_problem_fails_closed(bad):
    p=np.zeros(2);r=np.ones(2);j=np.eye(2);edges=(-.1,.1);side='right'
    if bad=='nan':j[0,0]=float('nan')
    if bad=='shape':j=np.ones((2,3))
    if bad=='bounds':p[1]=1.1
    if bad=='edge':edges=(.1,.2)
    if bad=='side':side='other'
    with pytest.raises(ValueError):module().solve_local(p,r,j,time_index=0,edges=edges,side=side)
