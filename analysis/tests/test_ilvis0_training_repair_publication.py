# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import pytest


def load():
    spec=importlib.util.spec_from_file_location('_repair_worker',Path(__file__).with_name('ilvis0_training_repair_worker.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def tasks():return [dict(identity=f'{p}-{s}',payload=dict(profile=p,sign=s)) for p in (False,True) for s in (-1,1)]


def test_incomplete_matrix_is_not_published_as_complete_support():
    text=load().render(dict(tasks=tasks()),dict(total=4,completed=0),{})
    assert '0/4' in text and 'counterexample search' in text
    with pytest.raises(ValueError):load().render(dict(tasks=tasks()),dict(total=4,completed=1),{'False--1':dict(passed=True)})


def test_duplicate_identities_fail():
    bad=tasks();bad[1]['identity']=bad[0]['identity']
    with pytest.raises(ValueError):load().render(dict(tasks=bad),dict(total=4,completed=0),{})
