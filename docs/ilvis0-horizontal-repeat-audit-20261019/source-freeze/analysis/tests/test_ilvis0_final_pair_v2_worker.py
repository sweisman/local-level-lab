# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path


def worker():
    path=Path(__file__).with_name('ilvis0_final_pair_v2_worker.py')
    assert path.exists(), 'corrected-context worker is missing'
    spec=importlib.util.spec_from_file_location('final_pair_v2_worker',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_separate_output_and_new_identities_preserve_completed_trial():
    from test_ilvis0_final_pair_worker import inputs
    module=worker();plan=module.make_plan(*inputs())
    assert module.OUTPUT!=module.parent.OUTPUT
    assert all(t['identity'].endswith('::final_pair_context_v2_check') for t in plan['tasks'])
    assert plan['maximum_starts']==4 and plan['maximum_native_evaluations']==58
    assert plan['maximum_optimizer_starts']==0 and plan['retries']==0


def test_private_executor_preserves_sources_and_complete_checks():
    module=worker();before=Path(module.parent.__file__).read_bytes();executor=module.build_executor()
    assert Path(module.parent.__file__).read_bytes()==before
    assert executor.OUTPUT==module.OUTPUT and executor.GUIDE==module.GUIDE
    assert executor.__file__==str(Path(module.__file__).resolve())
    assert executor.source_context is module.source_context
    source=module.executor_source(module.parent.parent.TEMPLATE.read_text())
    assert 'from lll.ilvis0_representable_boundary import check_endpoint' in source
    assert 'previous.check_full(scope,identity,full' in source and 'len(calls)>58' in source
    assert 'source[\'gps\']!=gps.tolist()' in source


def test_exact_source_plan_is_validated_before_original_extraction():
    import gzip
    import hashlib
    import json
    module=worker();executor=module.build_executor();plan=executor.source_plan()
    assert len(plan['tasks'])==4
    for t in plan['tasks']:
        if t['kind']!='target':continue
        payload=module.source_context(t)
        assert hashlib.sha256(payload).hexdigest()==t['source_artifact_sha256']
        value=json.loads(gzip.decompress(payload))
        assert all(isinstance(row,list) and len(row)==3 for row in value['gps'])
        assert value['normalized_parameters']==t['exact_point']
