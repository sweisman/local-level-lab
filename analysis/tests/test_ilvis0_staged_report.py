# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path

import pytest

from lll.ilvis0_staged_native_controls import LIMITS

PATH=Path(__file__).resolve().parents[2]/'docs/ilvis0-staged-training-controls/build_report.py'
spec=importlib.util.spec_from_file_location('staged_report',PATH)
report=importlib.util.module_from_spec(spec);spec.loader.exec_module(report)


def fixture():
    tasks=[dict(identity=f'{m}-{int(p)}',payload=dict(model=m,profile=p)) for m in range(3) for p in (False,True)]
    rows={t['identity']:dict(passed=True,work=LIMITS,native_evaluations=10,bound_evaluations=5,
        physical_parameter_count=27,parameter_count=51,stages=2,training_epochs=4,inequalities=24,
        known_truth_retained=True,original_reads=0,optimizer_starts=0,future_width_m=[.1,.2,.3]) for t in tasks}
    summary=dict(completed=6,total=6,elapsed_s=65.,charged=dict(native_calls=60,packet_visits=1920,bound_calls=30,bound_steps=8640))
    return dict(tasks=tasks),summary,rows


def test_complete_software_matrix_keeps_its_limits_explicit():
    text=report.render(*fixture())
    assert '6/6' in text and 'not recording-length' in text
    assert '53' not in text  # It adds no empirical outcomes.


def test_partial_and_failed_controls_are_not_hidden():
    manifest,summary,rows=fixture(); rows={k:v for k,v in list(rows.items())[:2]}
    rows['0-1']=dict(passed=False);summary['completed']=2;summary['charged']['native_calls']=11
    text=report.render(manifest,summary,rows)
    assert '1/6' in text and text.count('Not started')==4 and '| Failed |' in text


@pytest.mark.parametrize('field,value',[('inequalities',12),('physical_parameter_count',26),('known_truth_retained',False)])
def test_incomplete_success_cannot_pass_publication(field,value):
    manifest,summary,rows=fixture();rows['0-0'][field]=value
    with pytest.raises(ValueError):report.render(manifest,summary,rows)
