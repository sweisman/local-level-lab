# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path

import pytest


def report():
    path=Path(__file__).parents[2]/'docs/ilvis0-long-staged-feasibility/build_report.py'
    spec=importlib.util.spec_from_file_location('_long_report_test',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def examples():
    from lll.ilvis0_long_staged import limits,recipe
    tasks=[dict(identity=f'long-{m}-{p}',payload=dict(model=m,profile=bool(p))) for m in range(3) for p in range(2)]
    summary=dict(total=6,completed=0,elapsed_s=0.,charged=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0))
    row=dict(passed=False,numerical_checks_passed=True,useful=False,work=limits(),
        native_evaluations=12,bound_evaluations=6,physical_parameter_count=27,parameter_count=51,
        stages=2,training_epochs=5,inequalities=30,known_truth_retained=True,future_truth_contained=True,
        future_observations_used=False,original_reads=0,optimizer_starts=0,future_width_m=[200.,2.,2.],
        width_target_m=recipe()['width_target_m'])
    return dict(tasks=tasks),summary,row


def test_unstarted_and_failed_cases_remain_visible():
    manifest,summary,_=examples();summary['completed']=1
    text=report().render(manifest,summary,{'long-0-0':dict(passed=False,reason='budget exhausted')})
    assert '0/6' in text and 'budget exhausted' in text and text.count('Not started')==5


def test_wide_numerically_valid_case_is_not_qualified():
    manifest,summary,row=examples();summary['completed']=1
    text=report().render(manifest,summary,{'long-0-0':row})
    assert 'Too wide' in text and '1/6 numerical' in text and '0/6 useful' in text
    row['passed']=True;row['useful']=True
    with pytest.raises(ValueError,match='width'):
        report().render(manifest,summary,{'long-0-0':row})


@pytest.mark.parametrize('key,value',[('parameter_count',27),('future_observations_used',True),('work',{}),('inequalities',18)])
def test_report_rejects_incomplete_numerical_claim(key,value):
    manifest,summary,row=examples();summary['completed']=1;row[key]=value
    with pytest.raises(ValueError):report().render(manifest,summary,{'long-0-0':row})
