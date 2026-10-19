# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path

import pytest


def worker():
    spec=importlib.util.spec_from_file_location('scalar_worker',Path(__file__).with_name('ilvis0_scalar_calibration_worker.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_matrix_has_finite_unique_identities_and_no_observed_work():
    module=worker();tasks=module.tasks()
    assert len(tasks)==len({t['identity'] for t in tasks})==72
    assert module.LIMITS['candidate_force_evaluations']==72*121
    assert module.LIMITS['reference_evaluations']==72*121
    assert module.LIMITS['svds']==72
    assert module.LIMITS['observed_starts']==module.LIMITS['native_evaluations']==0
    assert module.LIMITS['original_reads']==module.LIMITS['retries']==0


def test_completed_or_charged_work_cannot_restart(tmp_path,monkeypatch):
    module=worker();monkeypatch.setattr(module,'DATA',tmp_path)
    (tmp_path/'completion.json').write_text('{}')
    with pytest.raises(ValueError,match='cannot restart'):module.require_unstarted()
    (tmp_path/'completion.json').unlink()
    (tmp_path/'start.json').write_text('{}')
    with pytest.raises(ValueError,match='cannot restart'):module.require_unstarted()
