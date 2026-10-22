# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import pytest
from lll.studies.runtime import Definition, inspect_study, command


def test_definition_requires_finite_limits_and_existing_adapter(tmp_path):
    config=dict(id='test',adapter='analysis/lll/adapter.py',sources=['analysis/lll/adapter.py'],
        inputs={'fixture':'fixture.json'},tasks=[dict(identity='a',input_key='fixture',
            limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0))],
        workers=1,threads=1,maximum_wall_s=5)
    (tmp_path/'analysis/lll').mkdir(parents=True);(tmp_path/'analysis/lll/adapter.py').write_text('')
    (tmp_path/'fixture.json').write_text('{}')
    assert Definition.from_dict(config,tmp_path).id=='test'
    for key,value in [('id','../escape'),('threads',5),('maximum_wall_s',float('inf'))]:
        with pytest.raises(ValueError):Definition.from_dict(dict(config,**{key:value}),tmp_path)


def test_inspection_does_not_launch_or_infer_success(tmp_path):
    p=tmp_path/'docs/test';p.mkdir(parents=True);(p/'completion.json').write_text(json.dumps({'state':'complete','passed':False}))
    report=inspect_study(tmp_path,'docs/test')
    assert report['completion']['passed'] is False and report['numerical_work']==0


def test_restore_cli_only_restores_requested_prefix(tmp_path):
    from lll.studies import ArchiveStore
    store=ArchiveStore(tmp_path)
    for name in ('docs/a/result.json','docs/b/result.json'):
        p=tmp_path/name;p.parent.mkdir(parents=True);p.write_text('{}')
    store.pack(['docs/a/result.json','docs/b/result.json']);store.compact()
    assert command(['--root',str(tmp_path),'restore','docs/a'])==0
    assert (tmp_path/'docs/a/result.json').exists() and not (tmp_path/'docs/b/result.json').exists()


def test_indexed_runner_retains_failed_case_and_exact_resource_counts(tmp_path):
    from test_ilvis0_control_shards import fixture
    from lll import ilvis0_control_shards as shards
    output,_,tasks=fixture(tmp_path,workers=2,accounting_format='sqlite-v1')
    for i,task in enumerate(tasks):
        context=shards.TaskContext(output,i%2,task['identity'])
        context.charge(native_calls=1,packet_visits=3)
        context.charge(bound_calls=1,bound_steps=3)
        context.finish(dict(passed=i!=2,scientific_decision='abstain'))
    report=shards.merge(output)
    assert report['completed']==4 and not report['passed']
    assert report['charged']==dict(native_calls=4,packet_visits=12,bound_calls=4,bound_steps=12)
    assert len(list(output.glob('shards/*/charges/journal.sqlite')))==2
    assert not list(output.glob('shards/*/charges/*.json'))
    with pytest.raises(ValueError):shards.TaskContext(output,0,tasks[0]['identity'])
