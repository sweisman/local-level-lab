# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import gzip
import importlib.util
import json
from pathlib import Path

import pytest


def worker():
    path=Path(__file__).with_name('ilvis0_last_zero_boundary_worker.py')
    assert path.exists(), 'final zero-field boundary worker is missing'
    spec=importlib.util.spec_from_file_location('last_zero_boundary',path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


def inputs():
    module=worker()
    return (module.load(module.PARENT/'manifest.json'),module.load(module.PARENT/'summary.json'),
            module.load(module.FREE/'manifest.json'),module.load(module.FREE/'summary.json'))


def test_exact_failed_free_time_population_and_full_saved_context():
    values=inputs();before=copy.deepcopy(values);module=worker();plan=module.make_plan(*values)
    assert before==values
    assert (plan['maximum_starts'],plan['maximum_optimizer_starts'],plan['maximum_native_evaluations'])==(6,0,110)
    assert plan['numerical_threads']==4 and plan['retries']==0
    assert [t['maximum_diagnostic_calls'] for t in plan['tasks']]==[3,3,26,26,26,26]
    assert {(t['task']['case_id'],t['start_role']) for t in plan['tasks'][2:]}=={
        (case,role) for case in module.CASES for role in ('primary','repeat')}
    for t in plan['tasks'][2:]:
        assert t['task']['segment_id']==module.SID and t['task']['model']=='sphere_still'
        with gzip.open(t['source_artifact'],'rt') as stream:saved=json.load(stream)
        assert saved['normalized_parameters']==t['exact_point']
        assert len(saved['times_s'])==len(saved['gps'])==len(saved['residual'])//3
        assert saved['gps']==[[r['latitude_rad'],r['longitude_rad'],r['height_m']]
            for r in t['task']['selected']['segment']['receiver_fixes']]


@pytest.mark.parametrize('bad',['missing','duplicate','model','case','bounds','controls','incomplete'])
def test_unmatched_or_failed_evidence_cannot_start(bad):
    cm,cs,fm,fs=inputs()
    if bad=='missing':fs['results'].pop()
    if bad=='duplicate':fs['results'].append(copy.deepcopy(fs['results'][-1]))
    if bad=='model':fm['plan']['tasks'][-1]['task']['model']='disc_stationary'
    if bad=='case':fm['plan']['tasks'][-1]['task']['case_id']='other'
    if bad=='bounds':fs['results'][-1]['normalized_parameters'][0]=1.1
    if bad=='controls':cs['results'][0]['passed']=False
    if bad=='incomplete':fs['state']='running'
    with pytest.raises(ValueError):worker().make_plan(cm,cs,fm,fs)


def test_private_executor_uses_qualified_two_sided_gates_and_new_scope():
    module=worker();path=Path(module.parent.__file__);before=path.read_bytes();executor=module.build_executor()
    assert path.read_bytes()==before
    assert executor.TESTS==40 and executor.OUTPUT==module.OUTPUT
    assert executor.source_plan is module.source_plan and executor.prepare.func is module.prepare
    source=module.executor_source(module.parent.parent.parent.parent.parent.TEMPLATE.read_text())
    assert 'from lll.ilvis0_scaled_branch import check_endpoint' in source
    assert "len(book.read('starts'))>6 or len(calls)>110" in source
    assert 'previous.check_full(scope,identity,full' in source
    assert executor.allowance.__globals__['source_plan'] is module.source_plan


def test_each_case_failure_blocks_overall_qualification(tmp_path,monkeypatch):
    # The previously checked paired-metric control is reused with the new planner.
    from test_ilvis0_last_field_worker import test_case_specific_repeat_failure_blocks_full_qualification as check
    import test_ilvis0_last_field_worker as previous
    actual=worker()
    class Fixture:
        CASES=actual.CASES
        compare_cases=staticmethod(actual.parent.compare_cases)
        @staticmethod
        def make_plan(*args):return actual.source_plan()
    monkeypatch.setattr(previous,'worker',lambda:Fixture)
    check(tmp_path)
