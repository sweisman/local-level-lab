# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import json
from pathlib import Path

import pytest


def worker():
    path=Path(__file__).with_name('ilvis0_hybrid_remaining_worker.py')
    spec=importlib.util.spec_from_file_location('six_target_worker',path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def test_engine_is_private_and_uses_complete_repeat_gate():
    module=worker();engine=module.engine()
    import ilvis0_precision_continuation_worker as original
    assert engine is not original and engine.OUTPUT==module.OUTPUT and engine.qualify is not original.qualify
    assert engine.solver.VERSION=='ilvis0-bounded-trust-candidate-v2'
    assert original.OUTPUT!=engine.OUTPUT


def test_changed_scope_is_rejected_before_scientific_inputs(tmp_path,monkeypatch):
    module=worker();monkeypatch.setattr(module,'OUTPUT',tmp_path)
    (tmp_path/'manifest.json').write_text(json.dumps(dict(version=module.VERSION,plan=dict(maximum_starts=25,maximum_native_sweeps=4528))))
    with pytest.raises(ValueError,match='finite matched scope'): module.verify()
