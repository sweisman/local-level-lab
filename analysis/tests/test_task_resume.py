# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite toy worker losses qualify task-level continuation before real fits."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
from xml.etree import ElementTree as ET

import pytest

from lll import ilvis0_control_shards as runner
from lll.studies.qualification import request
from lll.studies.task_resume import (REQUIRED_TESTS, qualification_sources,
    close_original, prepare_campaign, resume_campaign)
from lll.studies.validation_continuation import next_stage_tasks


ROOT=Path(__file__).resolve().parents[2]


def _task(name):
    return dict(identity=name,input_key='recipe',payload=dict(seed=name),
                native_kind='tangent',limits=dict(native_calls=3,packet_visits=9,
                                                  bound_calls=0,bound_steps=0))


def _toy(tmp_path):
    project=tmp_path
    sources=qualification_sources(project)
    for name in sources:
        target=project/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((ROOT/name).read_bytes())
    adapter=project/'adapter.py';adapter.write_text('def evaluate(task,context): return dict(passed=True)\n')
    entry=project/runner.RUNNER;entry.parent.mkdir(parents=True,exist_ok=True)
    entry.write_text('# frozen toy entry\n')
    (project/'recipe.json').write_text('{}')
    registry=project/'analysis/study-status.json';registry.parent.mkdir(exist_ok=True)
    registry.write_text('{"studies":[]}')
    (project/'analysis/study-status.lock').touch()
    parent=project/'data/parent'
    runner.prepare(parent,project_root=project,
        tasks=[_task(name) for name in ('saved','failed','lost','unstarted')],
        sources=['adapter.py',runner.RUNNER],inputs={'recipe':'recipe.json'},
        adapter='adapter.py',workers=2,threads=1,maximum_wall_s=3600,
        environment=runner.runtime_environment(),accounting_format='sqlite-v1',
        scope='toy recovery check')
    manifest=runner.verify(parent);runner._begin(parent,manifest)
    for identity,passed in (('saved',True),('failed',False)):
        task=next(t for t in manifest['tasks'] if t['identity']==identity)
        runner.TaskContext(parent,task['shard'],identity).finish(
            dict(passed=passed,scientific_decision='abstain',converged=passed))
    task=next(t for t in manifest['tasks'] if t['identity']=='lost')
    runner.TaskContext(parent,task['shard'],'lost').charge(native_calls=1,packet_visits=1)
    (parent/'worker.lock').touch()
    q=request(project,sources=sources,environment=runner.runtime_environment(),
              output='qualification-request.json',report='qualification-report.xml')
    suite=ET.Element('testsuite',tests=str(len(REQUIRED_TESTS)),failures='0',errors='0',skipped='0')
    for name in REQUIRED_TESTS:ET.SubElement(suite,'testcase',name=name,classname='task_resume')
    (project/q['report']).write_bytes(ET.tostring(suite))
    closure=close_original(project,'data/parent',qualification_request=q['request'])
    assert closure==dict(state='terminal',completed=2,interrupted=1,never_started=1)
    assert runner.verify_completion(parent)['completed']==3
    output=project/'data/continuation'
    prepare_campaign(project,'data/parent',output,
        qualification_request=q['request'],max_attempts_per_task=3,
        max_technical_interruptions=4,maximum_wall_s=3600,
        minimum_free_bytes=0,smoke_task_count=1)
    return project,parent,output


def test_original_closure_is_idempotent_and_blocks_old_launch(tmp_path):
    project,parent,_=_toy(tmp_path)
    assert close_original(project,'data/parent',
        qualification_request='qualification-request.json')['state']=='already_terminal'
    with pytest.raises(ValueError,match='completed study cannot restart'):
        runner.launch(parent,reserved_threads=0)


def test_reboot_resume_skips_sealed_and_preserves_charges(tmp_path,monkeypatch):
    project,parent,output=_toy(tmp_path)
    assert resume_campaign(project,output,launch=False)['next_stage_tasks']==1
    calls=[]
    monkeypatch.setattr('lll.studies.task_resume._other_threads',lambda project,workers:0)
    def launch(stage,*,reserved_threads):
        assert reserved_threads==0
        manifest=runner.verify(stage);runner._begin(stage,manifest)
        (stage/'worker.lock').touch()
        identities=[task['identity'] for task in manifest['tasks']]
        calls.append(identities)
        assert not {'saved','failed'}&set(identities)
        for task in manifest['tasks']:
            context=runner.TaskContext(stage,task['shard'],task['identity'])
            if len(calls)==2:
                context.charge(native_calls=1,packet_visits=1)
                raise RuntimeError('simulated notebook reboot')
            context.finish(dict(passed=True,converged=True,scientific_decision='abstain'))
        return runner._finish_study(stage,manifest)
    monkeypatch.setattr(runner,'launch',launch)
    with pytest.raises(RuntimeError,match='simulated notebook reboot'):
        resume_campaign(project,output)
    assert calls==[['lost'],['unstarted']]
    env=dict(os.environ,PYTHONPATH=str(ROOT/'analysis'))
    fresh=subprocess.run([sys.executable,'-m','lll.studies.task_resume',
        '--project',str(project),'resume','--output','data/continuation','--dry-run'],
        env=env,capture_output=True,text=True,check=True)
    assert json.loads(fresh.stdout)['state']=='needs_stage_closure'
    result=resume_campaign(project,output)
    assert result['state']=='all_tasks_finished'
    assert result['original_completed']==2
    assert result['continuation_completed']==2
    assert result['completed_failures']==1
    assert result['technical_interruptions']==2
    assert calls==[['lost'],['unstarted'],['unstarted']]
    assert resume_campaign(project,output)==result
    assert calls==[['lost'],['unstarted'],['unstarted']]
    assert runner.verify_completion(parent)['state']=='terminal'


def test_rejects_duplicate_owner(tmp_path):
    project,_,output=_toy(tmp_path)
    with (output/'campaign.lock').open('rb') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with pytest.raises(ValueError,match='already owned'):
            resume_campaign(project,output,launch=False)


def test_source_input_environment_mutation_blocks(tmp_path,monkeypatch):
    project,_,output=_toy(tmp_path)
    (project/'adapter.py').write_text('# changed source\n')
    with pytest.raises(ValueError,match='original source changed'):
        resume_campaign(project,output,launch=False)
    (project/'adapter.py').write_text('def evaluate(task,context): return dict(passed=True)\n')
    (project/'recipe.json').write_text('{"changed":true}')
    with pytest.raises(ValueError,match='original input changed'):
        resume_campaign(project,output,launch=False)
    (project/'recipe.json').write_text('{}')
    monkeypatch.setattr(runner,'runtime_environment',lambda:dict(changed=True))
    with pytest.raises(ValueError,match='numerical environment'):
        resume_campaign(project,output,launch=False)


def test_recovery_caps_and_completed_failure():
    task=_task('failed')
    plan=dict(tasks=[task],prior_interrupted_identities=['failed'])
    stage=dict(manifest=dict(tasks=[task]),merged=dict(total=1,completed=1,
        charged_identities=1,results=[dict(identity='failed',status='complete',passed=False)]))
    state=next_stage_tasks(plan,[stage],max_attempts_per_task=2,
                           max_technical_interruptions=2)
    assert state['tasks']==[]
    assert state['completed_failures']==1
    interrupted=dict(manifest=dict(tasks=[task]),merged=dict(total=1,completed=1,
        charged_identities=1,results=[dict(identity='failed',status='interrupted',passed=False)]))
    with pytest.raises(ValueError,match='per-task'):
        next_stage_tasks(plan,[interrupted],max_attempts_per_task=2,
                         max_technical_interruptions=2)
