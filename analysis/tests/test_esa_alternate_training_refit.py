# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite ESA receiver-source refit controls."""

from types import SimpleNamespace

import pytest

from lll import esa_alternate_training_refit as study


def test_six_refits_have_exact_finite_allowances():
    tasks=study.tasks()
    assert len(tasks)==6
    assert len({row['identity'] for row in tasks})==6
    assert {row['payload']['source'] for row in tasks}==set(study.SOURCES)
    assert {row['payload']['model'] for row in tasks}==set(study.MODELS)
    assert all(row['payload']['profile'] is True
               and row['payload']['law']=='increment'
               and row['payload']['start']==0
               and row['limits']['native_calls']==700000
               and row['limits']['packet_visits']==45000000000
               for row in tasks)
    assert 'training' not in study.INPUTS


def test_refit_rejects_changed_task_before_running_fit(monkeypatch):
    monkeypatch.setattr(study,'run_fit',lambda *args:pytest.fail('fit ran'))
    task=study.tasks()[0]
    context=SimpleNamespace(manifest=dict(scope=study.SCOPE,
                                          inputs={key:'x' for key in study.INPUTS}))
    changed=dict(task,payload=dict(task['payload'],start=1))
    with pytest.raises(ValueError,match='unchanged finite'):
        study.evaluate(changed,context)
    context.manifest['inputs']['future_receiver_positions']='x'
    with pytest.raises(ValueError,match='unchanged finite'):
        study.evaluate(task,context)
