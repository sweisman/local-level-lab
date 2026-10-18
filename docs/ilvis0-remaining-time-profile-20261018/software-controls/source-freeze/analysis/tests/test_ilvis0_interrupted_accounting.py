# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path
import json
import pytest


def candidate():
    from lll import ilvis0_interrupted_accounting
    return ilvis0_interrupted_accounting


@pytest.fixture
def source(tmp_path):
    import hashlib
    p=tmp_path/'source';p.mkdir()
    sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
    write=lambda n,v:(p/n).write_text(json.dumps(v,sort_keys=True))
    tasks=[dict(identity=f't{i}',kind='control' if i<2 else 'time_only',source_identity=f'endpoint{i}') for i in range(21)]
    write('manifest.json',dict(plan=dict(tasks=tasks,maximum_starts=21,maximum_native_evaluations=546,maximum_evaluations_per_identity=26)))
    h=sha(p/'manifest.json');counts=[3,3,14,24,24,24,24,24,22];starts=[];calls=[];saved={}
    for i,count in enumerate(counts):
        starts.append(dict(number=i+1,manifest_sha256=h,identity=f't{i}'))
        for _ in range(count):calls.append(dict(number=len(calls)+1,manifest_sha256=h,identity=f't{i}',phase='diagnostic',kind='tangent'))
        if i==8:continue
        name=f't{i}.json';artifact=f't{i}-linearization.json.gz';(p/artifact).write_bytes(b'known saved bytes')
        r=dict(identity=f't{i}',kind=tasks[i]['kind'],passed=i not in (2,7),native_evaluations=count,
               linearization_file=artifact,linearization_sha256=sha(p/artifact))
        rh=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        write(name,dict(result=r,result_sha256=rh,manifest_sha256=h));saved[name]=dict(sha256=sha(p/name))
    (p/'starts.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in starts))
    (p/'sweeps.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in calls)+'{"identity":"t8')
    write('failure.json',dict(state='stopped_journal_integrity_failure',artifacts={n:sha(p/n) for n in ('manifest.json','starts.jsonl','sweeps.jsonl')},saved_results=saved))
    return p


def test_known_interruption_preserves_nine_charges_and_excludes_them_from_continuation(source):
    m=candidate();before={n:m.sha(source/n) for n in ('starts.jsonl','sweeps.jsonl')}
    result=m.inspect(source)
    assert result['charged_starts']==9 and result['verified_saved_results']==8
    assert result['valid_native_call_charges']==162 and result['incomplete_charge_line']==163
    assert len(result['unstarted_tasks'])==12 and result['maximum_remaining_native_evaluations']==312
    assert result['reserved_started_allowance']==234
    charged={t['identity'] for t in result['charged_tasks']}
    assert not any(t['identity'] in charged for t in result['unstarted_tasks'])
    assert result['controls_passed'] and len(result['interrupted_identities'])==1
    assert before=={n:m.sha(source/n) for n in before}


def test_changed_source_journal_is_rejected(source):
    (source/'sweeps.jsonl').write_bytes(b'changed')
    with pytest.raises(ValueError,match='hash'):candidate().inspect(source)


def test_changed_saved_native_artifact_is_rejected(source):
    failure=json.loads((source/'failure.json').read_text());name=next(iter(failure['saved_results']))
    r=json.loads((source/name).read_text())['result'];(source/r['linearization_file']).write_bytes(b'changed')
    with pytest.raises(ValueError,match='artifact'):candidate().inspect(source)
