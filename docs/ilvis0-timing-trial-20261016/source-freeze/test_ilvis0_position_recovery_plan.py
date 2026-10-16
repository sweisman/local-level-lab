# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
from pathlib import Path

import pytest


def planner():
    path = Path(__file__).resolve().parents[2]/'docs/ilvis0-position-recovery-preparation-20261013/build_plan.py'
    spec = importlib.util.spec_from_file_location('position_recovery_plan', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def population():
    plan = planner()
    records, inventory, tasks = [], [], []
    for index in range(5):
        sid = 'segment-'+str(index)
        cases = []
        for case in plan.CASES:
            fits = []
            for model in plan.MODELS:
                converged = (index == 4 or index < 3 and (case, model) == (plan.CASES[0], plan.MODELS[0])
                             or index == 3 and (case, model) != (plan.CASES[0], plan.MODELS[0]))
                fits.append(dict(model=model, converged=converged, normalized_parameters=[.1],
                                 active_parameters=['x'], evaluations=10, elapsed_s=20.))
                if index < 3 and not converged or index == 4:
                    tasks.append(dict(segment_id=sid, case_id=case, model=model,
                                      role='control' if index == 4 else 'recovery',
                                      identity='::'.join((sid, case, model, 'primary'))))
            cases.append(dict(case_id=case, fits=fits))
        if index < 3:
            primary = next(task for task in tasks if task['segment_id'] == sid)
            tasks.append(dict(primary, role='repeatability',
                              identity=primary['identity'].removesuffix('primary')+'repeat'))
        records.append(dict(segment_id=sid, cases=cases,
                            profile=dict(conditional_shape_preference='globe' if index == 4 else 'unresolved')))
        if index < 4:
            inventory.append(dict(segment_id=sid, start_utc=str(index), filename=sid+'.013',
                                  unfinished_fits=5 if index < 3 else 1))
    return plan, records, inventory, dict(tasks=tasks)


def test_reuses_only_predeclared_qualified_subset_and_costs_remaining_work():
    plan, records, inventory, trial = population()
    result = plan.schedule(records, inventory, trial)
    assert result['original_unfinished_fits'] == 16
    assert result['reused_subset_fits'] == 18  # 15 primaries and three repeats
    assert result['primary_new_starts'] == 1 and result['repeat_new_starts'] == 1
    assert result['fresh_controls'] == 6 and result['maximum_starts'] == 8
    assert result['maximum_native_sweeps'] == 8*602
    assert not result['ready_to_launch']
    assert result['scientific_decision'] == 'abstain'


def test_model_cost_values_cannot_change_task_selection():
    plan, records, inventory, trial = population()
    before = plan.schedule(records, inventory, trial)
    for record in records:
        for case in record['cases']:
            for fit in case['fits']:
                fit['residual_sum_squares'] = -100000.
    assert plan.schedule(records, inventory, trial) == before


@pytest.mark.parametrize('change', ['invalid_start', 'wrong_unfinished_count', 'duplicate_record', 'missing_trial_task'])
def test_inconsistent_population_or_accounting_rejected(change):
    plan, records, inventory, trial = population()
    if change == 'invalid_start':
        records[0]['cases'][0]['fits'][1]['normalized_parameters'] = [1.01]
    elif change == 'wrong_unfinished_count':
        inventory[0]['unfinished_fits'] = 4
    elif change == 'duplicate_record':
        records.append(copy.deepcopy(records[0]))
    else:
        trial['tasks'].pop()
    with pytest.raises(ValueError):
        plan.schedule(records, inventory, trial)
