# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path

import pytest

PATH=Path(__file__).resolve().parents[2]/'docs/ilvis0-recording-duration-controls/build_report.py'
spec=importlib.util.spec_from_file_location('recording_duration_report',PATH)
report=importlib.util.module_from_spec(spec);spec.loader.exec_module(report)


def fixture():
    tasks=[dict(identity=f'{m}-{int(p)}',payload=dict(model=m,profile=p))
           for m in (0,1,2) for p in (False,True)]
    rows={t['identity']:dict(passed=True,model=t['payload']['model'],profile=t['payload']['profile'],
        packets=96000,query_times_s=[438.,478.],clock_offset_limit_s=1.,clock_column_norms=[.1,.2],
        warning_flags=[0,0],physical_parameter_count=27,bitwise_api_equivalent=True,
        native_evaluations=4,bound_evaluations=0,original_reads=0,optimizer_starts=0) for t in tasks}
    summary=dict(completed=6,total=6,elapsed_s=108.6,charged=dict(native_calls=24,packet_visits=2304000,bound_calls=0,bound_steps=0))
    return dict(tasks=tasks),summary,rows


def test_complete_report_uses_saved_results_and_keeps_qualification_limits():
    manifest,summary,rows=fixture(); text=report.render(manifest,summary,rows)
    assert '6/6 API cases pass' in text
    assert 'No new numerical work' in text
    assert 'not independent physical validation' in text


def test_partial_failure_and_unstarted_cases_remain_visible():
    manifest,summary,rows=fixture(); rows={k:v for k,v in list(rows.items())[:2]}
    rows['0-1']=dict(passed=False,reason='time limit')
    summary['completed']=2; summary['charged']['native_calls']=5
    text=report.render(manifest,summary,rows)
    assert '1/6 API cases pass' in text and text.count('Not started')==4
    assert '| Failed |' in text and '4 unstarted' in text


@pytest.mark.parametrize('change',['clock','column','aircraft','count'])
def test_inconsistent_success_cannot_be_published(change):
    manifest,summary,rows=fixture()
    if change=='clock':rows['0-0']['clock_offset_limit_s']=0.
    elif change=='column':rows['0-0']['clock_column_norms'][0]=0.
    elif change=='aircraft':rows['0-0']['original_reads']=1
    else:summary['completed']=5
    with pytest.raises(ValueError):report.render(manifest,summary,rows)
