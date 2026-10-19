# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
from pathlib import Path
import pytest


def module():
    assert Path(__file__).parents[1].joinpath('lll/ilvis0_horizontal_multistart.py').exists()
    return importlib.import_module('lll.ilvis0_horizontal_multistart')


def selection():
    return [dict(segment=dict(segment_id='control',imu_type=8)),dict(segment=dict(segment_id='target',imu_type=21))]


def test_equal_grid_per_model_and_independent_seed_family():
    m=module();p=m.plan(selection());tasks=p['tasks']
    assert len(tasks)==38 and len({t['identity'] for t in tasks})==38
    assert sum(t['control'] for t in tasks)==2
    for case in ('bias1_unsubtracted','bias1_profiled_removal'):
        for model in ('sphere_rotating','sphere_still','flat_still'):
            for role in ('primary','repeat'):
                group=[t for t in tasks if not t['control'] and (t['case_id'],t['model'],t['role'])==(case,model,role)]
                assert [t['timing_start'] for t in group]==[-.8,0.,.8]
    assert p['maximum_native_evaluations']==38*(200+1)+8


def test_population_change_rejected():
    with pytest.raises(ValueError):module().plan(selection()[:1])


def test_missing_start_cannot_be_discarded_before_selection():
    m=module();tasks=m.plan(selection())['tasks'][:3]
    rows=[dict(identity=t['identity'],fit=dict(converged=True,residual_sum_squares=1.,normalized_parameters=[0.])) for t in tasks[:2]]
    with pytest.raises(ValueError):m.choose(rows,tasks)
