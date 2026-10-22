# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import pytest


def test_boundary_schedule_preserves_both_neighbors_and_the_native_tie():
    from lll.ilvis0_clock_path_controls import schedule,recipe,validate_recipe
    queries,owners=schedule([.005]*16)
    assert queries[0]<queries[1]<queries[2] and owners==[5,5,6]
    settings=recipe();validate_recipe(settings)
    assert settings['interval_calls_per_case']==81 and settings['interval_steps_per_case']==513
    settings['packets']=32
    with pytest.raises(ValueError):validate_recipe(settings)


def test_publication_does_not_promote_missing_boundaries_or_columns():
    spec=importlib.util.spec_from_file_location('_clock_control_worker',Path(__file__).with_name('ilvis0_clock_path_worker.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    tasks=[dict(identity=f'{m}-{p}',payload=dict(model=m,profile=bool(p))) for m in range(3) for p in range(2)]
    assert 'Not complete' in module.render(dict(tasks=tasks),dict(total=6,completed=0),{})
    with pytest.raises(ValueError):module.render(dict(tasks=tasks),dict(total=6,completed=1),{'0-0':dict(passed=True)})
