# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import pytest


def worker():
    spec=importlib.util.spec_from_file_location('_ray_publication_test',Path(__file__).with_name('ilvis0_ray_probe_worker.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def tasks():
    return [dict(identity=f'{int(p)}-{a}-{s}',payload=dict(profile=p,axis=a,sign=s))
        for p in (False,True) for a in range(3) for s in (-1,1)]


def test_publication_preserves_unfinished_results_without_calling_them_feasible():
    report=worker().render(dict(tasks=tasks()),dict(total=12,completed=0),{})
    assert '0/12 numerical checks complete' in report and 'Not complete' in report
    assert 'not outer uncertainty bounds' in report


def test_publication_rejects_incomplete_passing_accounting():
    items=tasks();rows={items[0]['identity']:dict(passed=True,physical_parameter_count=26)}
    with pytest.raises(ValueError):worker().render(dict(tasks=items),dict(total=12,completed=1),rows)
