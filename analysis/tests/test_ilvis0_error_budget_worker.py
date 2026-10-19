# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path

import pytest


def worker():
    spec=importlib.util.spec_from_file_location('error_budget_worker',Path(__file__).with_name('ilvis0_error_budget_worker.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_complete_matrix_and_formula_limits_are_finite():
    module=worker();tasks=module.tasks()
    assert len(tasks)==46 and len({t['identity'] for t in tasks})==46
    assert sum(t['kind']=='trajectory' for t in tasks)==36
    assert module.LIMITS['maximum_force_evaluations']==36*168
    assert module.LIMITS['maximum_constructed_increments']==6*200
    assert module.LIMITS['maximum_quadrature_evaluations']==4*854
    assert module.LIMITS['maximum_observed_starts']==module.LIMITS['maximum_native_evaluations']==0


def test_charged_or_completed_diagnostic_cannot_restart(tmp_path,monkeypatch):
    module=worker();monkeypatch.setattr(module,'DATA',tmp_path)
    (tmp_path/'completion.json').write_text('{}')
    with pytest.raises(ValueError,match='cannot restart'):module.require_unstarted()
