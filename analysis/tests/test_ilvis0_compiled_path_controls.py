# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
from copy import deepcopy
import pytest


def test_finite_recipe_covers_full_prefix_and_all_parameter_columns():
    from lll.ilvis0_compiled_path_controls import recipe,validate_recipe
    settings=recipe();validate_recipe(settings)
    assert settings['packets']==64 and settings['columns']==list(range(27))
    assert settings['interval_steps_per_case']==64*27
    assert settings['original_reads']==settings['optimizer_starts']==0
    for key in ('packets','comparison_tolerance_m','native_calls_per_case'):
        changed=deepcopy(settings);changed[key]*=2
        with pytest.raises(ValueError):validate_recipe(changed)


def test_publication_rejects_incomplete_counts_and_preserves_missing_cases():
    spec=importlib.util.spec_from_file_location('_compiled_path_worker',Path(__file__).with_name('ilvis0_compiled_path_worker.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    tasks=[dict(identity=f'{m}-{p}',payload=dict(model=m,profile=bool(p))) for m in range(3) for p in range(2)]
    assert 'Not complete' in module.render(dict(tasks=tasks),dict(total=6,completed=0),{})
    with pytest.raises(ValueError):module.render(dict(tasks=tasks),dict(total=6,completed=1),{'0-0':dict(passed=True)})
