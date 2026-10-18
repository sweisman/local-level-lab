# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
from pathlib import Path

import pytest


def worker():
    path=Path(__file__).with_name('ilvis0_projection_worker.py')
    assert path.exists(), 'bounded saved-projection worker is missing'
    spec=importlib.util.spec_from_file_location('projection_worker',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def fixture():
    from test_ilvis0_projection_audit import population
    rows=population();tasks=[dict(segment_id=r['segment_id'],case_id=r['case_id'],model=r['model'],
        fit=dict(converged=True,normalized_parameters=[0.],active_parameters=['time_offset'])) for r in rows]
    for r in rows:r.update(linearization_file='docs/fake.gz',linearization_sha256='a'*64,epoch_file='docs/epochs.gz',epoch_sha256='b'*64)
    return rows,tasks


def test_exact_budget_scales_with_fixed_complete_population_and_preserves_inputs():
    rows,tasks=fixture();before=copy.deepcopy((rows,tasks));plan=worker().make_plan(rows,tasks,expected_total=2,expected_complete=2)
    assert before==(rows,tasks)
    assert len(plan['tasks'])==2 and plan['maximum_projections']==36
    assert plan['maximum_svd']==36 and plan['maximum_dense_factorizations']==14
    assert plan['maximum_native_evaluations']==0 and plan['maximum_optimizer_starts']==0
    assert plan['numerical_threads']==4 and plan['retries']==0


def test_missing_companion_or_changed_ready_population_cannot_silently_shrink_run():
    rows,tasks=fixture();module=worker();rows[0]['status']='not_saved'
    with pytest.raises(ValueError):module.make_plan(rows,tasks,expected_total=2,expected_complete=2)
    rows[0]['status']='ready';tasks.pop()
    with pytest.raises(ValueError):module.make_plan(rows,tasks,expected_total=2,expected_complete=2)


def test_detached_launcher_and_finite_scope_are_unique_to_saved_diagnostics():
    module=worker();assert module.OUTPUT.name=='ilvis0-receiver-projection-20261018'
    assert module.MAXIMUM_WALL_S==1200 and module.SOFTWARE_TESTS==31
    assert module.environment()['python']


def test_frozen_allowance_tampering_blocks_verification(tmp_path):
    import json
    module=worker();module.OUTPUT=tmp_path
    plan=module.make_plan(*fixture(),expected_total=2,expected_complete=2)
    manifest=dict(version=module.audit.VERSION,plan=plan,environment=module.environment(),sources={},inputs={})
    (tmp_path/'manifest.json').write_text(json.dumps(manifest))
    authorization=module.allowance(plan);(tmp_path/'authorization.json').write_text(json.dumps(authorization))
    assert module.verify()==manifest
    authorization['maximum_projections']+=1
    (tmp_path/'authorization.json').write_text(json.dumps(authorization))
    with pytest.raises(ValueError,match='allowance'):module.verify()
