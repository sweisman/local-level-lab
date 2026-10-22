# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import pytest


def worker():
    path=Path(__file__).with_name('ilvis0_truth_probe_worker.py')
    spec=importlib.util.spec_from_file_location('_truth_publication_test',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def tasks():
    return [dict(identity=f'{int(p)}-{s}',payload=dict(profile=p,sign=s)) for p in (False,True) for s in (-1,1)]


def test_unfinished_actual_fixture_is_not_presented_as_feasible_evidence():
    text=worker().render(dict(tasks=tasks()),dict(total=4,completed=0),{})
    assert '0/4 numerical tasks' in text and '0/12' in text
    assert 'stored perturbed observations' in text


def test_publication_rejects_passing_tasks_with_missing_physical_columns():
    rows={tasks()[0]['identity']:dict(passed=True,physical_parameter_count=26)}
    with pytest.raises(ValueError):worker().render(dict(tasks=tasks()),dict(total=4,completed=1),rows)
