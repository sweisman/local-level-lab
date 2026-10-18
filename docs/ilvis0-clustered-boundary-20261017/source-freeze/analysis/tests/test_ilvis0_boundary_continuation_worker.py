# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import pytest
from test_ilvis0_interrupted_accounting import source


def worker():
    p=Path(__file__).with_name('ilvis0_boundary_continuation_worker.py')
    spec=importlib.util.spec_from_file_location('boundary_continuation',p)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def test_only_unstarted_identities_transfer_with_original_allowances(source):
    from lll.ilvis0_interrupted_accounting import inspect,load
    w=worker();a=inspect(source);plan=w.make_plan(load(source/'manifest.json'),a)
    assert len(plan['tasks'])==12 and plan['maximum_native_evaluations']==312
    assert plan['reserved_parent_allowance']==234 and plan['original_combined_ceiling']==546
    assert plan['maximum_starts']==12 and all(t['kind']=='time_only' for t in plan['tasks'])
    assert plan['tasks']==a['unstarted_tasks']


def test_charged_identity_cannot_be_renamed_or_retried(source):
    from lll.ilvis0_interrupted_accounting import inspect,load
    w=worker();a=inspect(source);a['unstarted_tasks'][0]=a['charged_tasks'][0]
    with pytest.raises(ValueError):w.make_plan(load(source/'manifest.json'),a)


def test_failing_controls_block_transfer(source):
    from lll.ilvis0_interrupted_accounting import inspect,load
    w=worker();a=inspect(source);a['controls_passed']=False
    with pytest.raises(ValueError):w.make_plan(load(source/'manifest.json'),a)


def test_modified_original_allowance_cannot_expand_transfer(source):
    from lll.ilvis0_interrupted_accounting import inspect,load
    w=worker();a=inspect(source);p=load(source/'manifest.json');p['plan']['maximum_native_evaluations']=600
    with pytest.raises(ValueError):w.make_plan(p,a)


def test_worker_import_does_not_load_numerical_engine():
    assert worker()._engine is None
