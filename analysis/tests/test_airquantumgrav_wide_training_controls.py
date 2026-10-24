# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only checks; native checks follow the long-motion gate."""
import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest


def test_wide_training_standalone_loader_and_original_finite_matrix():
    path=Path('analysis/lll/airquantumgrav_wide_training_controls.py')
    spec=importlib.util.spec_from_file_location('_wide_training_worker',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    r=module.recipe();tasks=module.tasks()
    assert len(tasks)==len({v['identity'] for v in tasks})==24
    assert sum(v['limits']['native_calls'] for v in tasks)==4824
    assert sum(v['limits']['packet_visits'] for v in tasks)==931411200000
    assert (r['workers'],r['threads'],r['maximum_wall_s'])==(4,1,28800.)
    assert r['maximum_evaluations']==200 and r['duration_s']==1200.
    assert r['accuracy']==dict(horizontal_rms_m=.1,vertical_rms_m=.1,maximum_3d_m=.5)


def test_wide_training_preparation_requires_qualification_before_inputs(tmp_path):
    from lll.airquantumgrav_wide_training_controls import prepare
    with pytest.raises(ValueError,match='qualification'):prepare(tmp_path,qualification=None)
    assert not (tmp_path/'data').exists()


def test_wide_training_preparation_rejects_unguarded_environment_before_inputs(tmp_path):
    from lll import airquantumgrav_wide_training_controls as m
    with patch.object(m,'environment',return_value=dict(numerical_environment={})):
        with pytest.raises(ValueError,match='thread environment'):m.prepare(tmp_path,qualification='missing')
    assert not (tmp_path/'data').exists()


def test_wide_training_keeps_generated_truth_starts_physics_and_targets():
    from lll.airquantumgrav_wide_training_controls import recipe,tasks,construction_limits
    from lll.airquantumgrav_height_training import recipe as original,tasks as original_tasks
    r=recipe();old=original()
    for k in set(old)-{'version'}:assert r[k]==old[k],k
    assert tasks()==original_tasks()
    assert construction_limits(r)==dict(constructed_intervals=360000,generated_samples=362001)
