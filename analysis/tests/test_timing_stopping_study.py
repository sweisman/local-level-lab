# SPDX-License-Identifier: AGPL-3.0-or-later
from types import SimpleNamespace
import numpy as np
import pytest


def test_timing_qualification_table_freezes_32_fits_eight_controls_and_zero_native_work():
    from lll.timing_stopping_study import case_table,tasks,work_limits,configuration
    rows=case_table();work=tasks();cfg=configuration()
    assert len(rows)==len(work)==40 and len({r['identity'] for r in rows})==40
    assert sum(r['kind']=='fit' for r in rows)==32
    assert sum(work_limits(r)['evaluations'] for r in rows)==6688
    assert sum(work_limits(r)['linear_solves'] for r in rows)<=20000
    assert all(not any(t['limits'].values()) for t in work)
    assert (cfg['workers'],cfg['threads'],cfg['maximum_wall_s'])==(1,1,600.)


@pytest.mark.parametrize('name',['interior','boundary','nonlinear','curved_redundant',
    'kink_zero','kink_shifted','timed_quadratic','timed_redundant27'])
def test_timing_control_references_are_independently_declared_known_answers(name):
    from lll.ilvis0_timing_controls import fit_reference,problem_for
    ref=fit_reference(name);p=problem_for(name)
    r,j,_=p.residual_tangent(np.asarray(ref['optimum']), 'control')
    assert r==pytest.approx(ref['residual'],abs=1e-12)
    assert float(r@r)==pytest.approx(ref['cost'],abs=1e-12)
    assert j.shape==(len(r),len(p.bounds.active))
    if name=='timed_redundant27':assert len(p.bounds.active)==27


def test_timing_runner_reserves_before_each_residual_and_preserves_all_evidence(monkeypatch):
    from lll.timing_stopping_study import run_case,case_table
    from lll import ilvis0_timing_controls as controls
    row=next(r for r in case_table() if r['identity']=='fit-kink_zero-start-2')
    problem=controls.problem_for(row['case']);original=problem.residual_tangent;charges=[];values=[];linear=[]
    def checked(u,model):
        assert len(charges)==problem.calls+1
        return original(u,model)
    problem.residual_tangent=checked
    monkeypatch.setattr(controls,'problem_for',lambda name:problem)
    result=run_case(row,reserve_evaluation=lambda:charges.append(1),reserve_linear=lambda:linear.append(1),
        save_evaluation=lambda v:values.append(v),check_continue=lambda:None)
    assert result['passed'] and len(charges)==len(values)==result['evaluations']
    assert len(linear)==result['linear_solves'] and result['native_calls']==0


def test_timing_direct_budget_control_really_rejects_before_linear_work():
    from lll.timing_stopping_study import run_case,case_table
    row=next(r for r in case_table() if r['identity']=='probe-budget_failure');values=[];attempts=[]
    def reject():attempts.append(1);raise ValueError('frozen resource allowance exceeded')
    result=run_case(row,reserve_evaluation=lambda:None,reserve_linear=reject,
        save_evaluation=lambda v:values.append(v),check_continue=lambda:None)
    assert result['passed'] and result['expected_acceptance'] is False
    assert result['budget_rejected'] and len(attempts)==1 and len(values)==3
    assert result['linear_solves']==0


def test_timing_study_requires_qualification_and_scope_before_inputs(tmp_path):
    from lll.timing_stopping_study import prepare,evaluate
    with pytest.raises(ValueError,match='qualification'):prepare(tmp_path,qualification=None)
    with pytest.raises(ValueError,match='scope'):evaluate({},SimpleNamespace(manifest={'scope':'unapproved'}))
    assert not (tmp_path/'data').exists()


def test_frozen_timing_adapter_enumerates_exact_controls_without_package_context():
    import importlib.util
    from pathlib import Path
    from lll import timing_stopping_study as live
    spec=importlib.util.spec_from_file_location('_frozen_timing_adapter',Path(live.__file__))
    frozen=importlib.util.module_from_spec(spec);spec.loader.exec_module(frozen)
    assert frozen.case_table()==live.case_table() and frozen.tasks()==live.tasks()
