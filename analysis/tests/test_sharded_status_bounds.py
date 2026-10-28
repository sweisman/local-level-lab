# SPDX-License-Identifier: AGPL-3.0-or-later
"""Long bound operations must be visible without treating them as native calls."""
import importlib.util
import fcntl
import json
from pathlib import Path
import pytest
from lll import ilvis0_control_shards as runner
from test_ilvis0_control_shards import fixture


def test_status_separates_native_and_bound_reservations(tmp_path):
    output,_,_=fixture(tmp_path);context=runner.TaskContext(output,0,'task-0')
    context.charge(native_calls=1,packet_visits=3);context.charge(bound_calls=1,bound_steps=3)
    path=Path(__file__).resolve().parents[1]/'status.py'
    spec=importlib.util.spec_from_file_location('bound_status_test',path);status=importlib.util.module_from_spec(spec);spec.loader.exec_module(status)
    result=status.inspect_study(output)
    assert result['native_calls']==1
    assert result['bound_calls']==1 and result['bound_limit']==4
    assert '1/4 charged bounds' in status.render(dict(result,name='fixture'))


def status_module():
    path=Path(__file__).resolve().parents[1]/'status.py'
    spec=importlib.util.spec_from_file_location('_sealed_shard_status',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_status_counts_sealed_results_while_shard_continues(tmp_path):
    output,_,_=fixture(tmp_path,workers=1)
    first=runner.TaskContext(output,0,'task-0')
    first.finish(dict(passed=False,scientific_decision='abstain',reason='too wide'))
    second=runner.TaskContext(output,0,'task-1')
    second.finish(dict(passed=True,scientific_decision='abstain'))
    third=runner.TaskContext(output,0,'task-2')
    third.charge(bound_calls=1,bound_steps=3)
    with (output/'shards/000/worker.lock').open('rb') as held:
        fcntl.flock(held,fcntl.LOCK_EX)
        result=status_module().inspect_study(output)
        assert result['state']=='running' and result['threads']==1
        assert result['completed']==2 and result['passed']==1
        assert '2/4 results' in status_module().render(dict(result,name='fixture'))
    assert not (output/'summary.json').exists() and not (output/'completion.json').exists()


def test_status_does_not_count_an_unsealed_result(tmp_path):
    output,_,_=fixture(tmp_path,workers=1)
    context=runner.TaskContext(output,0,'task-0');context.finish(dict(passed=True,scientific_decision='abstain'))
    (output/'shards/000/results/task-0.seal.json').unlink()
    assert status_module().inspect_study(output)['completed']==0


@pytest.mark.parametrize('target', ['seal','result','task'])
def test_changed_sealed_provenance_is_rejected(tmp_path,target):
    output,_,_=fixture(tmp_path,workers=1)
    context=runner.TaskContext(output,0,'task-0');context.finish(dict(passed=True,scientific_decision='abstain'))
    path=output/'shards/000/results/task-0.json';seal=path.with_suffix('.seal.json')
    if target=='seal':
        value=json.loads(seal.read_text());value['sha256']='0'*64;seal.write_text(json.dumps(value))
    else:
        value=json.loads(path.read_text())
        if target=='result':value['result']['passed']=False
        else:value['task_sha256']='0'*64
        path.write_text(json.dumps(value))
        receipt=json.loads(seal.read_text());receipt['sha256']=runner._sha(path);seal.write_text(json.dumps(receipt))
    with pytest.raises(ValueError):status_module().completed_rows(output,runner.verify(output),runner._sha(output/'manifest.json'))


def test_status_avoids_per_future_result_archive_probes(tmp_path,monkeypatch):
    status=status_module();status.ROOT=tmp_path;study=tmp_path/'data/study';study.mkdir(parents=True)
    manifest=dict(version='ilvis0-sharded-native-controls-v1',allocation={'workers':4},
        tasks=[dict(identity=f'future-{i}',shard=i%4) for i in range(1000)])
    calls=[]
    monkeypatch.setattr(status,'archived_available',lambda *a:calls.append(a) or False)
    monkeypatch.setattr(status,'archive_evidence',lambda root:(None,{'paths':{}}),raising=False)
    assert status.completed_rows(study,manifest,'a'*64)==[]
    assert not calls, 'unexecuted identities should use one catalog view, not individual archive probes'


def test_status_fast_seal_inventory_still_reads_archived_receipts(tmp_path,monkeypatch):
    import hashlib
    status=status_module();status.ROOT=tmp_path;study=tmp_path/'data/study';study.mkdir(parents=True)
    task={'identity':'archived','shard':0};freeze='a'*64
    row=dict(passed=True,scientific_decision='abstain')
    envelope=dict(manifest_sha256=freeze,identity=task['identity'],shard=0,task_sha256=status.object_digest(task),
        result_sha256=status.object_digest(row),result=row,status='complete')
    raw=json.dumps(envelope).encode();base='data/study/shards/000/results/'
    files={base+'archived.json':raw,base+'archived.seal.json':json.dumps(dict(
        sha256=hashlib.sha256(raw).hexdigest(),manifest_sha256=freeze)).encode()}
    monkeypatch.setattr(status,'archived_available',lambda root,name:name in files)
    monkeypatch.setattr(status,'archive_evidence',lambda root:(None,{'paths':files}),raising=False)
    monkeypatch.setattr(status,'read_bytes',lambda path:files[Path(path).relative_to(tmp_path).as_posix()])
    result=status.completed_rows(study,dict(version='ilvis0-sharded-native-controls-v1',
        allocation={'workers':1},tasks=[task]),freeze)
    assert len(result)==1 and result[0]['identity']=='archived' and result[0]['passed']
