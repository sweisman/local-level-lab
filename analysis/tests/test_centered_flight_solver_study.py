# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np

from lll.centered_flight_solver_study import CASES, QUERIES, SOLVERS, _paired_rows, recipes, tasks


def test_finite_flight_pairs_use_the_same_measurement_recipe_and_budget():
    declared = recipes()
    assert len(tasks()) == 6
    assert len({recipe['models'][0] for recipe in declared.values()}) == 3
    assert {recipe['clock'] for recipe in declared.values()} == {'nominal_200Hz', 'header_elapsed'}
    for key in CASES:
        left, right = [task for task in tasks() if task['input_key'] == key]
        assert left['limits'] == right['limits'] and left['limits']['native_calls'] > 0
        assert left['payload'] | {'solver': SOLVERS[1]} == right['payload']


def test_saved_forecast_qualification_counts_missing_and_nonpassing_pairs():
    path = np.zeros((QUERIES, 3))
    cases = {f'{key}-{method}-0': dict(forecast=path, training_cost=10., converged=True,
        physical_accuracy_passed=True) for key in CASES for method in SOLVERS}
    cases[f'{CASES[1]}-{SOLVERS[1]}-0']['converged'] = False
    cases[f'{CASES[2]}-{SOLVERS[1]}-0'] = {'technical_error': 'interrupted'}
    results = _paired_rows(cases)
    assert [row['passed'] for row in results] == [True, False, False]
    assert results[0]['maximum_later_spread_m'] == 0.
    assert results[1]['absolute_training_cost_gap'] == 0.
    assert results[2]['maximum_later_spread_m'] is None
