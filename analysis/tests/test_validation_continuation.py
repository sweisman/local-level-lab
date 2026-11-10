# SPDX-License-Identifier: AGPL-3.0-or-later
"""A reboot may requeue unfinished work, never a completed scientific outcome."""
import pytest
import json
import fcntl
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

from lll.studies.validation_continuation import plan_pending_tasks, next_stage_tasks
from lll.studies.validation_resume import prepare_campaign, resume_campaign, _close_interrupted, _stop_reason
from lll.studies import validation_resume
from lll import ilvis0_control_shards as runner
from lll.ilvis0_receipt_journal import durable_write, encoded
from lll.studies.recovery import inspect


def _task(name, index):
    return dict(identity=name, index=index, shard=index % 2, input_key='recipe',
                payload=dict(draw_seed=100 + index), native_kind='tangent',
                limits=dict(native_calls=7, packet_visits=30, bound_calls=0, bound_steps=0))


def _planned(name, index):
    return {key:value for key,value in _task(name,index).items()
            if key not in ('index','shard')}


def test_reuses_completed_success_and_failure_but_requeues_only_technical_losses():
    tasks=[_task(name,i) for i,name in enumerate(('passed','failed','lost','unstarted'))]
    manifest=dict(tasks=tasks, allocation=dict(workers=2, threads=1),
                  environment=dict(python='frozen'))
    merged=dict(total=4, completed=2, charged_identities=3,
                results=[dict(identity='passed',status='complete',passed=True),
                         dict(identity='failed',status='complete',passed=False)])
    advice=dict(state='cohort_unavailable',manifest_sha256='a'*64,
                charged_identities=3, interrupted_identities=['lost'],
                uncharged_tasks=['unstarted'],uninterrupted_cohort_required=True)
    plan=plan_pending_tasks(manifest,merged,advice)
    assert plan['completed'] == 2
    assert plan['completed_failures'] == 1
    assert plan['prior_interrupted_charges'] == 1
    assert plan['prior_interrupted_identities'] == ['lost']
    assert [t['identity'] for t in plan['tasks']] == ['lost','unstarted']
    assert plan['tasks'][0] == {k:v for k,v in tasks[2].items() if k not in ('index','shard')}


def test_refuses_to_hide_an_unaccounted_or_duplicate_identity():
    tasks=[_task('done',0),_task('lost',1)]
    manifest=dict(tasks=tasks,allocation=dict(workers=2,threads=1),environment={})
    merged=dict(total=2,completed=1,charged_identities=2,
                results=[dict(identity='done',status='complete',passed=True)])
    advice=dict(state='cohort_unavailable',manifest_sha256='b'*64,
                charged_identities=2,interrupted_identities=[],uncharged_tasks=[],
                uninterrupted_cohort_required=True)
    with pytest.raises(ValueError,match='accounted'):
        plan_pending_tasks(manifest,merged,advice)


def test_rebooted_stage_requeues_only_interrupted_and_unstarted_tasks():
    plan=dict(tasks=[_planned(name,i) for i,name in enumerate(('lost','next','later'))],
              prior_interrupted_identities=['lost'])
    first=dict(manifest=dict(tasks=plan['tasks']),
               merged=dict(total=3,completed=2,charged_identities=2,
                           results=[dict(identity='lost',status='complete',passed=False),
                                    dict(identity='next',status='interrupted',passed=False)]))
    state=next_stage_tasks(plan,[first],max_attempts_per_task=4,
                           max_technical_interruptions=8)
    assert [task['identity'] for task in state['tasks']]==['next','later']
    assert state['completed_failures']==1
    assert state['technical_interruptions']==2
    second=dict(manifest=dict(tasks=state['tasks']),
                merged=dict(total=2,completed=2,charged_identities=2,
                            results=[dict(identity='next',status='complete',passed=True),
                                     dict(identity='later',status='complete',passed=True)]))
    assert next_stage_tasks(plan,[first,second],max_attempts_per_task=4,
                            max_technical_interruptions=8)['tasks']==[]
    with pytest.raises(ValueError,match='duplicates'):
        next_stage_tasks(plan,[first,first],max_attempts_per_task=4,
                         max_technical_interruptions=8)
    changed=dict(first,manifest=dict(tasks=[dict(plan['tasks'][0],payload=dict(draw_seed=999)),
                                            *plan['tasks'][1:]]))
    with pytest.raises(ValueError,match='scientific task'):
        next_stage_tasks(plan,[changed],max_attempts_per_task=4,
                         max_technical_interruptions=8)


def test_recovery_caps_are_enforced_without_rerunning_completed_failures():
    plan=dict(tasks=[_planned('lost',0)],prior_interrupted_identities=['lost'])
    reboot=dict(manifest=dict(tasks=plan['tasks']),
                merged=dict(total=1,completed=1,charged_identities=1,
                            results=[dict(identity='lost',status='interrupted',passed=False)]))
    with pytest.raises(ValueError,match='per-task'):
        next_stage_tasks(plan,[reboot],max_attempts_per_task=2,
                         max_technical_interruptions=3)


def test_real_fit_smoke_gate_survives_reboot_and_blocks_a_failed_result():
    tasks=[_planned(name,i) for i,name in enumerate(('smoke','second','third'))]
    assert hasattr(validation_resume,'_smoke_selection')
    _smoke_selection=validation_resume._smoke_selection
    assert _smoke_selection(tasks,[],['smoke'])==(tasks[:1],None)
    interrupted=[dict(manifest=dict(tasks=tasks[:1]),
                      merged=dict(results=[dict(identity='smoke',status='interrupted',passed=False)]))]
    assert _smoke_selection(tasks,interrupted,['smoke'])==(tasks[:1],None)
    passed=[dict(manifest=dict(tasks=tasks[:1]),
                 merged=dict(results=[dict(identity='smoke',status='complete',passed=True)]))]
    assert _smoke_selection(tasks[1:],passed,['smoke'])==(tasks[1:],None)
    failed=[dict(manifest=dict(tasks=tasks[:1]),
                 merged=dict(results=[dict(identity='smoke',status='complete',passed=False)]))]
    assert _smoke_selection(tasks[1:],failed,['smoke'])==(None,'smoke_fit_failed')


def test_rebooted_campaign_reuses_sealed_results_and_finishes_only_missing_tasks(tmp_path,monkeypatch):
    project=tmp_path/'project';project.mkdir()
    registry=project/'analysis/study-status.json';registry.parent.mkdir()
    registry.write_text(json.dumps(dict(studies=[])))
    adapter_source=Path(__file__).resolve().parents[1]/'lll/studies/validation_task_adapter.py'
    adapter_target=project/'analysis/lll/studies/validation_task_adapter.py'
    adapter_target.parent.mkdir(parents=True)
    adapter_target.write_bytes(adapter_source.read_bytes())
    (project/'adapter.py').write_text('# toy frozen evaluator\n')
    entry=project/runner.RUNNER;entry.parent.mkdir(parents=True)
    entry.write_text('# toy frozen runner entry\n')
    recipe=dict(role='validation',seeds=[100],order_statistic_rank=1,minimum_free_bytes=0,
                require_uninterrupted_cohort=True)
    (project/'recipe.json').write_text(json.dumps(recipe))
    tasks=[dict(_task(name,i),payload=dict(role='validation',draw_seed=100,
            population_sha256='a'*64,case=dict(model='sphere_rotating',law='increment',
                                               profile=False,start=i%2)))
           for i,name in enumerate(('saved-a','saved-b','lost','unstarted'))]
    parent=project/'data/original'
    runner.prepare(parent,project_root=project,
                   tasks=[{k:v for k,v in task.items() if k not in ('index','shard')}
                          for task in tasks],
                   sources=['adapter.py',runner.RUNNER],inputs={'recipe':'recipe.json'},
                   adapter='adapter.py',workers=4,threads=1,maximum_wall_s=3600,
                   environment=runner.runtime_environment(),accounting_format='sqlite-v1')
    runner._begin(parent,runner.verify(parent))
    for name in ('saved-a','saved-b'):
        task=next(t for t in runner.verify(parent)['tasks'] if t['identity']==name)
        runner.TaskContext(parent,task['shard'],name).finish(
            dict(passed=True,converged=True,scientific_decision='abstain'))
    task=next(t for t in runner.verify(parent)['tasks'] if t['identity']=='lost')
    runner.TaskContext(parent,task['shard'],'lost').charge(native_calls=1,packet_visits=1)
    plan=plan_pending_tasks(runner.verify(parent),runner.merge(parent),
                            inspect(project,'data/original'))
    plan_path=project/'data/plan.json';durable_write(plan_path,encoded(plan))
    campaign=project/'data/continuation'
    prepare_campaign(project,'data/original','data/plan.json',campaign,
                     max_attempts_per_task=4,max_technical_interruptions=8,
                     maximum_wall_s=3600,smoke_task_count=1)
    assert resume_campaign(project,campaign,launch=False)==dict(
        state='ready',pending=2,next_stage=0,next_stage_tasks=1)
    assert not (campaign/'start.json').exists()
    with (campaign/'campaign.lock').open('rb') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with pytest.raises(ValueError,match='already owned'):
            resume_campaign(project,campaign,launch=False)
    (project/'adapter.py').write_text('# changed evaluator\n')
    with pytest.raises(ValueError,match='current source differs'):
        resume_campaign(project,campaign,launch=False)
    (project/'adapter.py').write_text('# toy frozen evaluator\n')
    monkeypatch.setattr('lll.studies.validation_resume.shutil.disk_usage',
                        lambda path:SimpleNamespace(free=-1))
    with pytest.raises(ValueError,match='disk reserve'):
        resume_campaign(project,campaign)
    monkeypatch.undo()

    calls=[]
    monkeypatch.setattr('lll.studies.validation_resume._other_threads',lambda project,workers:0)
    def frozen_evaluator(task,context):
        assert len(context.manifest['tasks'])==4
        assert context.manifest['scope']==runner.verify(parent)['scope']
        assert task['identity']==context.task['identity']
        assert context.root.name in ('stage-000','stage-001','stage-002')
        runner._clock_record(context.root,context.manifest)
        return dict(passed=True,converged=True,scientific_decision='abstain')
    def fake_launch(stage,*,reserved_threads):
        assert reserved_threads==0
        manifest=runner.verify(stage);runner._begin(stage,manifest)
        (stage/'worker.lock').touch()
        source=stage/'source-freeze/analysis/lll/studies/validation_task_adapter.py'
        spec=importlib.util.spec_from_file_location('_ilvis0_frozen_control_adapter',source)
        frozen=importlib.util.module_from_spec(spec);spec.loader.exec_module(frozen)
        frozen._original_evaluate=frozen_evaluator
        calls.append(stage.name)
        for task in manifest['tasks']:
            context=runner.TaskContext(stage,task['shard'],task['identity'])
            if len(calls)==2 and task['identity']=='unstarted':
                context.charge(native_calls=1,packet_visits=1)
                raise RuntimeError('simulated host reboot')
            context.finish(frozen.evaluate(task,context))
        return runner._finish_study(stage,manifest)
    monkeypatch.setattr(runner,'launch',fake_launch)
    with pytest.raises(RuntimeError,match='simulated host reboot'):
        resume_campaign(project,campaign)
    assert calls==['stage-000','stage-001']
    env=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[1]))
    fresh=subprocess.run([sys.executable,'-m','lll.studies.validation_resume',
        '--project',str(project),'resume','--output',str(campaign),'--dry-run'],
        env=env,capture_output=True,text=True,check=True)
    assert json.loads(fresh.stdout)==dict(state='needs_stage_closure',stage=1,interrupted=1)
    with (campaign/'stage-001/shards/000/worker.lock').open('rb') as worker_lock:
        fcntl.flock(worker_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert resume_campaign(project,campaign,launch=False)==dict(state='owned',stage=1)
    assert resume_campaign(project,campaign,launch=False)==dict(
        state='needs_stage_closure',stage=1,interrupted=1)
    result=dict(
        state='all_tasks_finished',original_completed=2,continuation_completed=2,
        completed_failures=0,technical_interruptions=2,stages=3)
    assert resume_campaign(project,campaign)==result
    assert calls==['stage-000','stage-001','stage-002']
    assert [task['identity'] for task in runner.verify(campaign/'stage-000')['tasks']]==['lost']
    assert [task['identity'] for task in runner.verify(campaign/'stage-002')['tasks']]==['unstarted']
    assert runner.verify_completion(campaign/'stage-000')['state']=='complete'
    assert runner.verify_completion(campaign/'stage-001')['state']=='terminal'
    receipt=json.loads((campaign/'completion.json').read_text())
    assert receipt['validation_coverage_qualified'] is False
    assert receipt['original_completed']+receipt['continuation_completed']==4
    registered=[row['path'] for row in json.loads(registry.read_text())['studies']]
    assert registered==['data/continuation/stage-002','data/continuation/stage-001',
                        'data/continuation/stage-000']
    assert resume_campaign(project,campaign,launch=False)==result
    from lll.studies.validation_combined_report import _verified_views
    views,selected,store,_,_,_=_verified_views(project,campaign)
    try:
        assert selected=={'saved-a':0,'saved-b':0,'lost':1,'unstarted':3}
        assert len(views)==4
    finally:
        for view in views:view.close()
        store.close()
    altered=dict(receipt,continuation_completed=99)
    runner._replace(campaign/'completion.json',altered)
    with pytest.raises(ValueError,match='combined completion'):
        _verified_views(project,campaign)
    runner._replace(campaign/'completion.json',receipt)


def test_abrupt_worker_process_exit_is_a_charged_recoverable_interruption(tmp_path):
    project=tmp_path/'project';project.mkdir()
    (project/'adapter.py').write_text('# frozen toy adapter\n')
    entry=project/runner.RUNNER;entry.parent.mkdir(parents=True)
    entry.write_text('# frozen toy runner\n')
    (project/'recipe.json').write_text(json.dumps(dict(role='validation',seeds=[7],
        order_statistic_rank=1,require_uninterrupted_cohort=True)))
    stage=project/'data/stage';runner.prepare(stage,project_root=project,
        tasks=[dict(_planned('lost',0),payload=dict(role='validation',draw_seed=7,
            population_sha256='a'*64,case=dict(model='sphere_rotating',
                law='increment',profile=False,start=0)))],
        sources=['adapter.py',runner.RUNNER],inputs={'recipe':'recipe.json'},
        adapter='adapter.py',workers=1,threads=1,maximum_wall_s=3600,
        environment=runner.runtime_environment(),accounting_format='sqlite-v1')
    script='''import os,sys
from pathlib import Path
from lll import ilvis0_control_shards as r
p=Path(sys.argv[1]);m=r.verify(p);r._begin(p,m)
(p/'worker.lock').touch()
t=m['tasks'][0]
r.TaskContext(p,t['shard'],t['identity']).charge(native_calls=1,packet_visits=1)
os._exit(23)
'''
    env=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[1]))
    child=subprocess.run([sys.executable,'-c',script,str(stage)],env=env,
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    assert child.returncode==23,child.stderr.decode()
    assert inspect(project,'data/stage')['interrupted_identities']==['lost']
    _close_interrupted(stage,runner.verify(stage))
    summary=runner.verify_completion(stage)
    assert summary['state']=='terminal' and summary['charged_identities']==1
    assert summary['results'][0]['status']=='interrupted'


def test_scientific_stop_request_is_bound_to_its_stage(tmp_path):
    stage=tmp_path/'stage';stage.mkdir()
    runner._write(stage/'manifest.json',dict(version='toy'))
    runner._write(stage/'stop-request.json',dict(manifest_sha256=runner._sha(stage/'manifest.json'),
                                                reason='validation_failure_budget_exceeded'))
    assert _stop_reason(stage)=='validation_failure_budget_exceeded'
    runner._replace(stage/'stop-request.json',dict(manifest_sha256='0'*64,reason='changed'))
    with pytest.raises(ValueError,match='stop request'):
        _stop_reason(stage)
