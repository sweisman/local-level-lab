# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll import ilvis0_paired_precision_plan as planning


def test_scope_includes_all_models_cases_controls_and_repeats():
    plan=planning.build()
    assert len(plan['tasks'])==16
    assert len({t['identity'] for t in plan['tasks']})==16
    assert sum(t['role']=='primary' for t in plan['tasks'])==12
    assert sum(t['role']=='control' for t in plan['tasks'])==2
    assert sum(t['role']=='repeat' for t in plan['tasks'])==2
    assert plan['maximum_native_sweeps']==992
    for sid in plan['target_segment_ids']:
        tasks=[t for t in plan['tasks'] if t['segment_id']==sid and t['role']=='primary']
        assert len({(t['case_id'],t['model']) for t in tasks})==6
    assert plan['physical_bounds_changed'] is False
    assert plan['retry_allowance']==0


def test_repeat_budget_is_finite_and_primary_seed_is_explicit():
    for task in planning.build()['tasks']:
        assert task['maximum_evaluations']==(200 if task['role']=='repeat' else 40)
        if task['role']=='repeat':
            assert task['seed_policy']=='frozen_primary_endpoint_plus_0.01'


def test_position_failure_is_not_selected_for_a_cost_only_repair():
    assert 'e6629f14d2e03e471a446e06' not in planning.build()['target_segment_ids']
