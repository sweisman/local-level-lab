# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def test_local_anchor_table_adds_curved_timing_without_replacing_original_cases():
    from lll import timing_stopping_local_study as local, timing_stopping_study as original
    rows=local.case_table();tasks=local.tasks()
    assert len(rows)==len(tasks)==44 and len({r['identity'] for r in rows})==44
    old={r['identity']:r for r in original.case_table()}
    assert all(r==old[r['identity']] for r in rows if r['identity'] in old)
    assert len(old)==40 and sum(r['kind']=='fit' for r in rows)==36
    assert sum(original.work_limits(r)['evaluations'] for r in rows)==7488
    assert sum(original.work_limits(r)['linear_solves'] for r in rows)==22439
    assert all(not any(t['limits'].values()) for t in tasks)
    assert (local.configuration()['workers'],local.configuration()['threads'])==(1,1)
    assert local.configuration()['maximum_linear_solves']==22500


def test_curved_timing_answer_has_independently_known_global_minimum():
    from lll.ilvis0_timing_controls import fit_reference,problem_for
    ref=fit_reference('timed_nonlinear');p=problem_for('timed_nonlinear')
    assert ref['cost']==1. and ref['optimum']==[0.] and not ref['unique']
    for x in (-1.,-.8,0.,.6,.9,1.):
        r,j,_=p.residual_tangent(np.array([x]),'control')
        assert r==pytest.approx([1.,.001*(x+x**3)],abs=1e-15)
        assert j[:,0]==pytest.approx([0.,.001*(1+3*x*x)],abs=1e-15)
        assert float(r@r)>=ref['cost']


def test_local_anchor_adapter_delegates_to_shared_evaluator(monkeypatch):
    from lll import timing_stopping_local_study as local,timing_stopping_study as shared
    captured={};context=object();work={}
    def run(w,c,**kwargs):
        assert w is work and c is context
        captured.update(kwargs);return {'delegated':True}
    monkeypatch.setattr(shared,'run_task',run)
    assert local.evaluate(work,context)=={'delegated':True}
    assert captured==dict(scope=local.SCOPE,configuration=local.configuration(),cases=local.case_table(),tasks=local.tasks())


def test_local_anchor_report_uses_actual_fit_count():
    from lll.timing_stopping_report import render
    report=dict(fit_passed=36,controls_correct=8,pairs=[dict(case=str(i),starts=4,agreement=True) for i in range(9)])
    assert '36/36 fits' in render(report)


def test_curved_local_timing_fit_preserves_known_answer_and_auditable_trace():
    from lll.timing_stopping_local_study import case_table
    from lll.timing_stopping_study import run_case
    from lll.timing_stopping_report import summarize
    row=next(r for r in case_table() if r['identity']=='fit-timed_nonlinear-start-2')
    values=[];evaluations=[];linear=[]
    result=run_case(row,reserve_evaluation=lambda:evaluations.append(1),reserve_linear=lambda:linear.append(1),
        save_evaluation=values.append,check_continue=lambda:None)
    assert result['passed'] and summarize(row,result,values)['qualification_passed']
    assert len(values)==len(evaluations)==result['evaluations']<=200
    assert len(linear)==result['linear_solves']<=620 and result['native_calls']==0


def test_frozen_local_adapter_has_same_table_without_package_context():
    import importlib.util
    from lll import timing_stopping_local_study as live
    spec=importlib.util.spec_from_file_location('_frozen_local_adapter',live.__file__)
    frozen=importlib.util.module_from_spec(spec);spec.loader.exec_module(frozen)
    assert frozen.case_table()==live.case_table() and frozen.tasks()==live.tasks()
