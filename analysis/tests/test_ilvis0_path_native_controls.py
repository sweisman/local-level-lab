# SPDX-License-Identifier: AGPL-3.0-or-later
from copy import deepcopy
import pytest


def fixture():
    rows=[]
    for column in range(27):
        rows.append(dict(column=column,coordinates=[dict(exact_derivatives=[['0','0']]*4) for _ in range(3)]))
    return [0,0,0],[[0]*27 for _ in range(3)],rows,[6000000,3000000,1]


def test_comparison_checks_each_physical_column_including_clock_and_removal():
    from lll.ilvis0_path_native_controls import compare
    args=fixture();assert compare(*args)['passed']
    for column in (0,12,25,26):
        changed=deepcopy(args);changed[1][2][column]=.01
        result=compare(*changed)
        assert not result['passed'] and result['maximum_derivative_gap_m']==pytest.approx(.01)


def test_metric_scaling_and_fixed_numerical_tolerance_are_applied_separately():
    from lll.ilvis0_path_native_controls import compare
    position,jac,rows,scale=fixture();position[0]=1e-10
    result=compare(position,jac,rows,scale)
    assert not result['passed'] and result['maximum_position_gap_m']==pytest.approx(.0006)
    position[0]=1e-14
    assert compare(position,jac,rows,scale)['passed']


def test_missing_duplicate_columns_and_invalid_bound_intervals_are_rejected():
    from lll.ilvis0_path_native_controls import compare,recipe,validate_recipe
    args=fixture()
    with pytest.raises(ValueError):compare(args[0],args[1],args[2][:-1],args[3])
    bad=deepcopy(args);bad[2][26]['column']=25
    with pytest.raises(ValueError):compare(*bad)
    bad=deepcopy(args);bad[2][0]['coordinates'][0]['exact_derivatives'][1]=['1','-1']
    with pytest.raises(ValueError):compare(*bad)
    changed=recipe();changed['comparison_tolerance_m']=1
    with pytest.raises(ValueError):validate_recipe(changed)


def test_generated_recipe_has_finite_all_column_allowance_and_no_aircraft_fits():
    from lll.ilvis0_path_native_controls import recipe,validate_recipe
    spec=recipe();validate_recipe(spec)
    assert spec['native_calls_per_case']==1 and spec['interval_steps_per_case']==27
    assert spec['optimizer_starts']==0 and spec['original_reads']==0


def test_publication_keeps_incomplete_cases_and_rejects_incomplete_passing_counts():
    import importlib.util
    from pathlib import Path
    spec=importlib.util.spec_from_file_location('_path_native_worker',Path(__file__).with_name('ilvis0_path_native_worker.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    tasks=[dict(identity=f'{m}-{p}',payload=dict(model=m,profile=bool(p))) for m in range(3) for p in range(2)]
    text=module.render(dict(tasks=tasks),dict(total=6,completed=0),{})
    assert '0/6' in text and 'Not complete' in text
    bad={'0-0':dict(passed=True,physical_columns=26)}
    with pytest.raises(ValueError):module.render(dict(tasks=tasks),dict(total=6,completed=1),bad)
