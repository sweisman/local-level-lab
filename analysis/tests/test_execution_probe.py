# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite lifecycle probe controls; no numerical work or process signals."""
import json
from pathlib import Path
import pytest
from lll import ilvis0_control_shards as runner

ROOT=Path(__file__).resolve().parents[2]


def fixture(tmp_path,payload):
    from lll.studies.execution_probe import evaluate
    adapter='analysis/lll/studies/execution_probe.py'
    task=dict(identity='pulse-control',payload=payload,input_key='plan',
              limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0))
    runner.prepare(tmp_path/'study',project_root=ROOT,tasks=[task],sources=[adapter,runner.RUNNER],
        inputs={'plan':'docs/CALIBRATION_RECOVERY_PLAN.md'},adapter=adapter,workers=1,threads=1,
        maximum_wall_s=30,environment=runner.runtime_environment(),accounting_format='sqlite-v1')
    context=runner.TaskContext(tmp_path/'study',0,'pulse-control')
    return context,evaluate


def test_probe_records_finite_pulses_with_no_native_reservations(tmp_path):
    context,evaluate=fixture(tmp_path,dict(intervals=2,interval_s=.001))
    result=evaluate(context.task,context);context.finish(result)
    pulses=[json.loads((context.root/name).read_bytes()) for name in context.artifacts]
    assert result['passed'] is True and result['intervals']==2
    assert [p['interval'] for p in pulses]==[1,2]
    assert pulses[1]['monotonic_s']>=pulses[0]['monotonic_s']
    assert runner.merge(context.root)['native_evaluations']==0
    assert runner.merge(context.root)['charged_identities']==1


@pytest.mark.parametrize('payload',[dict(intervals=0,interval_s=.001),
    dict(intervals=1001,interval_s=.001),dict(intervals=1,interval_s=-1),
    dict(intervals=2,interval_s=1000),dict(intervals=True,interval_s=.001)])
def test_probe_rejects_unbounded_or_invalid_waits_before_writing(tmp_path,payload):
    context,evaluate=fixture(tmp_path,payload)
    with pytest.raises(ValueError):evaluate(context.task,context)
    assert context.artifacts=={}


def test_probe_honors_existing_cooperative_stop_without_a_signal(tmp_path):
    context,evaluate=fixture(tmp_path,dict(intervals=2,interval_s=.001))
    runner._request_stop(context.root,'finite control')
    with pytest.raises(runner.BudgetStopped):evaluate(context.task,context)
    assert context.artifacts=={}
