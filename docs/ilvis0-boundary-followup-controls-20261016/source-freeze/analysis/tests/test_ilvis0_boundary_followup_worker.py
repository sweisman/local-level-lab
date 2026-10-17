# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
from pathlib import Path
import pytest


def worker():
    path = Path(__file__).with_name('ilvis0_boundary_followup_worker.py')
    spec = importlib.util.spec_from_file_location('adjacent_boundary_worker', path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def inputs():
    tasks = [dict(identity=f'control-{i}', source_identity=f'control-{i}', kind='control',
                  fit=dict(normalized_parameters=[0.], residual_sum_squares=1.)) for i in range(2)]
    results = []
    for role in ('primary', 'repeat'):
        sid = 'bb8061a43b4f14b6262ceda1'
        identity = f'{sid}::bias1_unsubtracted::sphere_still::{role}::boundary_diagnostic'
        tasks.append(dict(identity=identity, source_identity=identity.rsplit('::', 1)[0],
            kind='time_only', task=dict(segment_id=sid, case_id='bias1_unsubtracted', model='sphere_still'),
            fit=dict(normalized_parameters=[0.], residual_sum_squares=4.)))
        results.append(dict(identity=identity, normalized_parameters=[.1], residual_sum_squares=3.,
                            status='complete', passed=False, reason='boundary_check_unresolved'))
    return dict(plan=dict(tasks=tasks)), dict(results=results)


def test_only_declared_pair_and_two_controls_are_scheduled():
    parent, previous = inputs()
    plan = worker().make_plan(parent, previous)
    assert plan['maximum_starts'] == 4
    assert plan['maximum_native_evaluations'] == 66
    assert plan['maximum_local_joint_nuisance_starts'] == 2
    assert [t['kind'] for t in plan['tasks']] == ['control', 'control', 'neighbor', 'neighbor']
    for task in plan['tasks'][2:]:
        assert task['fit']['normalized_parameters'] == [.1]
        assert task['fit']['residual_sum_squares'] == 3.
        assert task['identity'].endswith('::neighbor_followup')


def test_missing_repeat_blocks_preparation():
    parent, previous = inputs()
    previous['results'].pop()
    with pytest.raises(ValueError):
        worker().make_plan(parent, previous)


def test_duplicate_target_cannot_increase_scope():
    parent, previous = inputs()
    parent['plan']['tasks'].append(copy.deepcopy(parent['plan']['tasks'][-1]))
    with pytest.raises(ValueError):
        worker().make_plan(parent, previous)


def test_control_failure_does_not_authorize_target_retries():
    module = worker()
    assert module._engine is None
    assert module.QUALIFICATION_TESTS == 63
