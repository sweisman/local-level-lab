# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path


def worker():
    path=Path(__file__).with_name('ilvis0_scaled_pair_worker.py')
    assert path.exists(), 'scaled-branch trial worker is missing'
    spec=importlib.util.spec_from_file_location('scaled_pair_worker',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_separate_finite_scope_preserves_observations_and_charged_failures():
    from test_ilvis0_final_pair_worker import inputs
    module=worker();plan=module.make_plan(*inputs())
    assert module.OUTPUT!=module.parent.OUTPUT
    assert len(plan['tasks'])==4 and plan['maximum_native_evaluations']==58
    assert plan['maximum_optimizer_starts']==0 and plan['numerical_threads']==4 and plan['retries']==0
    assert all(t['identity'].endswith('::scaled_branch_v1_check') for t in plan['tasks'])
    assert plan['local_linear_solver_changed'] and not plan['scientific_stopping_limits_changed']


def test_private_executor_uses_scaled_solver_with_original_full_native_gates():
    module=worker();path=Path(module.parent.parent.__file__);before=path.read_bytes()
    executor=module.build_executor()
    assert path.read_bytes()==before and executor.OUTPUT==module.OUTPUT
    assert executor.__file__==str(Path(module.__file__).resolve())
    assert any(p.endswith('ilvis0-correction-audit-20261018/summary.json') for p in module.sources())
    source=module.executor_source(module.parent.parent.parent.TEMPLATE.read_text())
    assert 'from lll.ilvis0_scaled_branch import check_endpoint' in source
    assert 'previous.check_full(scope,identity,full' in source and 'len(calls)>58' in source
    assert 'source[\'gps\']!=gps.tolist()' in source


def test_target_source_context_keeps_exact_original_arrays():
    import gzip
    import json
    module=worker();executor=module.build_executor();plan=executor.source_plan()
    for task in plan['tasks']:
        if task['kind']!='target':continue
        value=json.loads(gzip.decompress(module.parent.source_context(task)))
        assert value['normalized_parameters']==task['exact_point']
        assert value['active_parameters']==task['fit']['active_parameters']
        assert all(isinstance(row,list) and len(row)==3 for row in value['gps'])
