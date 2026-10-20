# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path

import pytest


def worker():
    spec=importlib.util.spec_from_file_location('certificate_worker',Path(__file__).with_name('ilvis0_scalar_certificate_worker.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_finite_allowance_and_unchanged_history_selection():
    module=worker();tasks=module.tasks()
    assert len(tasks)==len({t['identity'] for t in tasks})==228
    assert sum(t['kind']=='qualification' for t in tasks)==12
    assert module.LIMITS['maximum_calls']==228*404
    assert module.LIMITS['calls_per_start']==404
    assert module.LIMITS['maximum_magnitude_history_constructions']==228*2
    assert module.LIMITS['observed_starts']==module.LIMITS['original_reads']==0


def test_completed_or_charged_candidate_cannot_restart(tmp_path,monkeypatch):
    module=worker();monkeypatch.setattr(module,'DATA',tmp_path)
    (tmp_path/'completion.json').write_text('{}')
    with pytest.raises(ValueError,match='cannot restart'):module.require_unstarted()


def test_repeat_history_and_endpoint_rules_are_unchanged():
    module=worker()
    a=dict(passed=True,rms_mps2=.1,residual_mps2=[.1,.1])
    b=dict(passed=True,rms_mps2=.1,residual_mps2=[-.1,-.1])
    assert module.agreement([a]*3,1e-8)['passed']
    assert not module.agreement([a,b,a],1e-8)['passed']
    assert not module.agreement([a,dict(a,passed=False),a],1e-8)['passed']
