# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only checks for a future, separately frozen observed revision."""
import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest


def test_observed_wide_standalone_loader_keeps_original_matrix_and_limits():
    path=Path('analysis/lll/airquantumgrav_observed_wide.py')
    spec=importlib.util.spec_from_file_location('_observed_wide_worker',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    from lll.airquantumgrav_observed_height import recipe,tasks
    old=recipe();new=module.recipe(maximum_wall_s=900.)
    assert {k:v for k,v in new.items() if k not in ('version','maximum_wall_s')}=={
        k:v for k,v in old.items() if k not in ('version','maximum_wall_s')}
    assert new['maximum_wall_s']==900.
    layout=dict(native_packets=360028,training_prefix_packets=239867,training_epochs=800,receiver_epochs=1200)
    assert module.tasks(layout)==tasks(layout)
    assert sum(v['limits']['native_calls'] for v in module.tasks(layout))==4824
    assert sum(v['limits']['packet_visits'] for v in module.tasks(layout))==931458086400


def test_observed_wide_requires_qualification_before_inputs(tmp_path):
    from lll.airquantumgrav_observed_wide import prepare
    with pytest.raises(ValueError,match='qualification'):
        prepare(tmp_path,qualification=None,maximum_wall_s=900.)
    assert not (tmp_path/'data').exists()


def test_observed_wide_requires_explicit_finite_wall_allowance():
    from lll.airquantumgrav_observed_wide import recipe
    with pytest.raises(TypeError):recipe()
    for value in (0.,-1.,float('inf'),float('nan'),28801.,True):
        with pytest.raises(ValueError,match='allowance'):recipe(maximum_wall_s=value)


def test_observed_wide_rejects_unguarded_environment_before_inputs(tmp_path):
    from lll import airquantumgrav_observed_wide as module
    with patch.object(module,'environment',return_value=dict(numerical_environment={})):
        with pytest.raises(ValueError,match='thread environment'):
            module.prepare(tmp_path,qualification='missing',maximum_wall_s=900.)
    assert not (tmp_path/'data').exists()


def test_observed_wide_cannot_use_partial_or_unverified_training_qualification():
    from lll.airquantumgrav_observed_wide import require_qualification
    good=dict(verified=True,qualified=True,total=24,passed=24)
    require_qualification(good)
    for change in (dict(verified=False),dict(qualified=False),dict(total=23),dict(passed=23)):
        with pytest.raises(ValueError):require_qualification(dict(good,**change))


def test_observed_wide_freezes_every_dynamically_bound_protocol():
    from lll.airquantumgrav_observed_wide import qualification_sources
    from lll.ilvis0_wide_observed import SOURCES
    names=qualification_sources(Path.cwd())
    assert {'analysis/lll/'+name for name in SOURCES}<=set(names)
    assert 'analysis/lll/airquantumgrav_observed_wide_report.py' in names


def test_observed_wide_baseline_checks_observed_protocols_not_unused_generated_wrapper():
    from lll.airquantumgrav_observed_wide import BASELINE_PROTOCOL_SOURCES
    assert set(BASELINE_PROTOCOL_SOURCES)=={
        'airquantumgrav_prediction.py','airquantumgrav_observed.py','airquantumgrav_observed_height.py'}
