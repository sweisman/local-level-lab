# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path

import pytest


def worker():
    spec=importlib.util.spec_from_file_location('nonlinear_worker',Path(__file__).with_name('ilvis0_scalar_nonlinear_worker.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_finite_matrix_and_calls_are_declared():
    module=worker();tasks=module.tasks()
    assert len(tasks)==len({t['identity'] for t in tasks})==228
    assert sum(t['kind']=='qualification' for t in tasks)==12
    assert module.LIMITS['maximum_calls']==228*402
    assert module.LIMITS['observed_starts']==module.LIMITS['original_reads']==0


def test_completed_or_charged_work_cannot_restart(tmp_path,monkeypatch):
    module=worker();monkeypatch.setattr(module,'DATA',tmp_path)
    (tmp_path/'completion.json').write_text('{}')
    with pytest.raises(ValueError,match='cannot restart'):module.require_unstarted()


def test_repeat_gate_checks_residual_history_not_only_equal_cost():
    module=worker()
    def row(residual):return dict(passed=True,rms_mps2=.1,residual_mps2=residual)
    assert not module.agreement([row([.1,.1]),row([-.1,-.1]),row([.1,.1])],1e-8)['passed']
    assert module.agreement([row([.1,.1])]*3,1e-8)['passed']
    assert not module.agreement([row([.1,.1])]*2,1e-8)['passed']


def test_small_residual_does_not_override_failed_endpoint_gate():
    module=worker();rows=[dict(passed=True,rms_mps2=0.,residual_mps2=[0.])]*2
    assert not module.agreement(rows+[dict(passed=False,rms_mps2=0.,residual_mps2=[0.])],1e-7)['passed']
