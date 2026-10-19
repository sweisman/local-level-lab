# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
import ilvis0_clustered_boundary_worker as worker
from test_ilvis0_profile_boundary_worker import inputs


def test_same_sources_have_new_identities_and_exact_58_call_scope():
    executor=worker.build_executor();plan=executor.make_plan(*inputs())
    assert len(plan['tasks'])==4 and plan['maximum_native_evaluations']==58
    assert sum(t['maximum_diagnostic_calls'] for t in plan['tasks'])==58
    assert [t['maximum_diagnostic_calls'] for t in plan['tasks']]==[3,3,26,26]
    assert all(t['identity'].endswith('::cluster_search_v1') for t in plan['tasks'])
    assert plan['maximum_optimizer_starts']==0 and plan['maximum_affine_solves']==6


def test_reuse_keeps_the_frozen_executor_file_unchanged():
    before=worker.TEMPLATE.read_bytes();executor=worker.build_executor()
    assert worker.TEMPLATE.read_bytes()==before
    assert executor.OUTPUT==worker.OUTPUT and executor.QUALIFICATION==worker.OUTPUT/'software-controls'
    assert executor.__file__==str(worker.Path(__file__).with_name('ilvis0_clustered_boundary_worker.py'))


@pytest.mark.parametrize('marker',[
    'from lll.ilvis0_exact_boundary import check_endpoint',
    "inputs=prior.scientific_inputs(parent['inputs'])",
    'len(calls)>66',
])
def test_changed_executor_layout_is_rejected_before_any_work(marker):
    source=worker.TEMPLATE.read_text().replace(marker,'unexpected_changed_layout')
    with pytest.raises(ValueError,match='layout'):worker.executor_source(source)


def test_executor_keeps_scope_and_full_control_checks_from_frozen_code():
    executor=worker.build_executor()
    assert executor.TESTS==12 and executor.VERSION==worker.VERSION
    assert executor.CallScope.__module__=='_ilvis0_cluster_executor'
    source=worker.executor_source(worker.TEMPLATE.read_text())
    assert 'previous.check_full(scope,identity,full' in source
    assert 'diagnostic_limit=26' in source and 'len(calls)>58' in source
