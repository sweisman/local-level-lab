# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite software-control planning; no archive access or matrix execution."""
import importlib.util
from pathlib import Path


def worker():
    path=Path(__file__).with_name('ilvis0_channel_trajectory_worker.py')
    spec=importlib.util.spec_from_file_location('channel_trajectory_worker',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_declared_matrix_is_finite_and_preserves_ambiguous_controls():
    module=worker();tasks=module.tasks()
    assert len(tasks)==18 and len({t['identity'] for t in tasks})==18
    assert len({t['model'] for t in tasks})==3
    assert len([t for t in tasks if t['profile']=='stationary'])==3
    assert module.LIMITS['receiver_force_evaluations']==18*21*3
    assert module.LIMITS['magnitude_comparisons']==18*21*3*2
    assert module.LIMITS['optimizer_starts']==0 and module.LIMITS['native_evaluations']==0


def test_existing_start_blocks_reexecution(tmp_path,monkeypatch):
    import pytest
    module=worker();monkeypatch.setattr(module,'DATA',tmp_path)
    (tmp_path/'start.json').write_text('{}')
    with pytest.raises(ValueError,match='cannot restart'):module.require_unstarted()
