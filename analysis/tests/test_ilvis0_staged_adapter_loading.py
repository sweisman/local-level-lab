# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT=Path(__file__).resolve().parents[2]


def load(name):
    path=ROOT/'analysis/lll'/name
    spec=importlib.util.spec_from_file_location('_standalone_frozen_adapter',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_original_packaging_failure_reproduces_without_any_numerical_work(tmp_path):
    original=load('ilvis0_staged_native_controls.py')
    context=SimpleNamespace(root=tmp_path,manifest={},save=lambda *_:pytest.fail('no work before loader failure'))
    with pytest.raises(ImportError,match='relative import'):
        original.Runtime(context,{})


def test_corrected_adapter_supports_the_actual_standalone_loader(tmp_path,monkeypatch):
    from lll import ilvis0_control_shards as runner
    monkeypatch.setattr(runner,'_check_continue',lambda *_:None)
    candidate=load('ilvis0_staged_native_controls_v2.py');saved={}
    context=SimpleNamespace(root=tmp_path,manifest={},save=lambda name,value:saved.update({name:value}))
    runtime=candidate.Runtime(context,{})
    runtime.reserve(reference_setups=1);runtime.save('probe.json',dict(passed=True))
    assert saved['probe.json']==dict(passed=True)
    assert runtime.native_calls==runtime.bounds==0


def test_only_import_handling_changes_in_the_corrected_numeric_adapter():
    parent=(ROOT/'analysis/lll/ilvis0_staged_native_controls.py').read_text()
    candidate=(ROOT/'analysis/lll/ilvis0_staged_native_controls_v2.py').read_text()
    assert candidate==parent.replace('from .','from lll.')
