# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reboot-safe execution of a separately frozen validation continuation.

The original interrupted study remains immutable. Each execution stage uses the
shared sealed-task runner; a new stage contains only unfinished task identities.
This module imports no numerical libraries and sends no process signals.
"""
from contextlib import contextmanager
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

from lll import ilvis0_control_shards as runner
from lll.ilvis0_receipt_journal import durable_write, encoded, digest
from .recovery import inspect
from .validation_continuation import plan_pending_tasks, next_stage_tasks
from .validation_task_adapter import ADAPTER

VERSION='lll-validation-resume-v1'
STAGE=re.compile(r'stage-[0-9]{3}$')


def _read(path):
    return json.loads(Path(path).read_bytes())


def _sha(path):
    return runner._sha(path)


@contextmanager
def _campaign_lease(path):
    fd=os.open(path,os.O_RDONLY)
    try:
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('continuation already owned') from None
        yield
    finally:os.close(fd)


def _parent(project,parent,plan):
    """Verify the old source, environment, charges, seals and all artifacts."""
    parent=Path(parent)
    if parent.is_absolute() or not (project/parent).resolve().is_relative_to(project):
        raise ValueError('parent must be a project-relative study')
    manifest=runner.verify(project/parent)
    advice=inspect(project,parent.as_posix())
    merged=runner.merge(project/parent)
    actual=plan_pending_tasks(manifest,merged,advice)
    if encoded(actual)!=encoded(plan):
        raise ValueError('parent evidence or continuation inventory changed')
    if manifest['environment']!=runner.runtime_environment():
        raise ValueError('current numerical environment differs from parent')
    for name,sha in manifest['sources'].items():
        if _sha(runner.path_within(project,name))!=sha:
            raise ValueError('current source differs from parent freeze: '+name)
    for record in manifest['inputs'].values():
        if _sha(runner.path_within(project,record['source']))!=record['sha256']:
            raise ValueError('current input differs from parent freeze')
    return manifest,merged


def prepare_campaign(project,parent,plan_path,output,*,max_attempts_per_task,
                     max_technical_interruptions,maximum_wall_s,smoke_task_count=0):
    """Freeze finite recovery limits; do not launch any fit."""
    project=Path(project).resolve();output=Path(output).resolve()
    if (output.exists() or not output.is_relative_to(project)
            or type(max_attempts_per_task) is not int or max_attempts_per_task<2
            or type(max_technical_interruptions) is not int or max_technical_interruptions<0
            or type(maximum_wall_s) is not int or maximum_wall_s<=0
            or type(smoke_task_count) is not int or smoke_task_count<0):
        raise ValueError('new project output and finite technical recovery limits required')
    plan_path=runner.path_within(project,plan_path)
    plan=_read(plan_path)
    manifest,_=_parent(project,parent,plan)
    if smoke_task_count>len(plan['tasks']):raise ValueError('smoke gate exceeds pending tasks')
    if max_technical_interruptions<len(plan['prior_interrupted_identities']):
        raise ValueError('technical recovery cap is below existing charged interruptions')
    if manifest['allocation']['workers']!=4 or manifest['allocation']['threads']!=1:
        raise ValueError('continuation preserves the original four-thread allocation')
    prepared=time.time()
    policy=dict(version=VERSION,parent=Path(parent).as_posix(),
                parent_manifest_sha256=plan['parent_manifest_sha256'],
                parent_merged_sha256=plan['parent_merged_sha256'],
                plan_sha256=digest(plan),adapter_sha256=_sha(project/ADAPTER),
                max_attempts_per_task=max_attempts_per_task,
                max_technical_interruptions=max_technical_interruptions,
                smoke_task_count=smoke_task_count,
                maximum_wall_s=maximum_wall_s,prepared_unix=prepared,
                deadline_unix=prepared+maximum_wall_s,workers=4,threads=1,
                runtime_sha256=_sha(__file__))
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary=Path(tempfile.mkdtemp(prefix='.campaign-preparing-',dir=output.parent))
    durable_write(temporary/'plan.json',encoded(plan))
    durable_write(temporary/'policy.json',encoded(policy))
    durable_write(temporary/'freeze.json',encoded(dict(version=VERSION,
        plan_sha256=_sha(temporary/'plan.json'),policy_sha256=_sha(temporary/'policy.json'))))
    durable_write(temporary/'campaign.lock',b'')
    os.rename(temporary,output)
    fd=os.open(output.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
    return policy


def _frozen(project,output):
    freeze=_read(output/'freeze.json');plan=_read(output/'plan.json');policy=_read(output/'policy.json')
    if (freeze.get('version')!=VERSION or policy.get('version')!=VERSION
            or freeze.get('plan_sha256')!=_sha(output/'plan.json')
            or freeze.get('policy_sha256')!=_sha(output/'policy.json')
            or policy.get('runtime_sha256')!=_sha(__file__)
            or policy.get('adapter_sha256')!=_sha(project/ADAPTER)
            or policy.get('plan_sha256')!=_sha(output/'plan.json')
            or policy.get('parent_manifest_sha256')!=plan.get('parent_manifest_sha256')
            or policy.get('parent_merged_sha256')!=plan.get('parent_merged_sha256')):
        raise ValueError('continuation freeze or runtime changed')
    manifest,_=_parent(project,policy['parent'],plan)
    return plan,policy,manifest


def _stage_manifest_matches(stage_manifest,parent_manifest,policy):
    expected_sources={**parent_manifest['sources'],ADAPTER:policy['adapter_sha256']}
    expected_inputs={key:record['sha256'] for key,record in parent_manifest['inputs'].items()}
    expected_inputs.update({'continuation-parent-manifest':policy['parent_manifest_sha256'],
                            'continuation-policy':digest(policy),
                            'continuation-plan':policy['plan_sha256']})
    if (stage_manifest['sources']!=expected_sources
            or stage_manifest['environment']!=parent_manifest['environment']
            or stage_manifest['numerical_environment']!=parent_manifest['numerical_environment']
            or stage_manifest['adapter']!=ADAPTER
            or stage_manifest['stop_after_failure']!=parent_manifest['stop_after_failure']
            or stage_manifest['accounting_format']!=parent_manifest['accounting_format']
            or stage_manifest['allocation']['workers'] not in (1,2,3,4)
            or stage_manifest['allocation']['threads']!=1
            or stage_manifest['allocation']['reserved']!=0
            or stage_manifest['allocation']['total']!=stage_manifest['allocation']['workers']
            or set(stage_manifest['inputs'])!=set(expected_inputs)
            or any(stage_manifest['inputs'][key]['sha256']!=sha
                   for key,sha in expected_inputs.items())):
        raise ValueError('execution stage changed frozen numerical inputs or method')


def _close_interrupted(stage,manifest):
    """Seal charged losses and close a stage only after its leases are free."""
    with runner._lease(stage/'worker.lock',True):
        if (stage/'completion.json').exists():return runner.verify_completion(stage)
        if (stage/'summary.json').exists():
            summary=_read(stage/'summary.json');merged=runner.merge(stage)
            if any(summary.get(key)!=value for key,value in merged.items()):
                raise ValueError('partial stage closure differs from saved evidence')
            runner._write(stage/'completion.json',dict(state=summary['state'],
                manifest_sha256=_sha(stage/'manifest.json'),summary_sha256=_sha(stage/'summary.json')))
            return runner.verify_completion(stage)
        return runner._finish_study(stage,manifest)


def _stage_paths(output):
    paths=[];index=0
    while (output/f'stage-{index:03d}').exists():
        paths.append(output/f'stage-{index:03d}');index+=1
    if any(p.is_dir() and STAGE.fullmatch(p.name) for p in output.iterdir()
           if p.name not in {s.name for s in paths}):
        raise ValueError('nonconsecutive execution stage')
    return paths


def _stop_reason(stage):
    request=stage/'stop-request.json'
    if not request.exists():return None
    value=_read(request)
    if (value.get('manifest_sha256')!=_sha(stage/'manifest.json')
            or not isinstance(value.get('reason'),str) or not value['reason']):
        raise ValueError('stage stop request differs from its frozen manifest')
    return value['reason']


def _smoke_selection(pending,closed_stages,smoke_identities):
    """Require real completed smoke fits before assigning the remaining tasks."""
    if not smoke_identities:return pending,None
    completed={}
    for stage in closed_stages:
        for row in stage['merged']['results']:
            if row['identity'] in smoke_identities and row['status']=='complete':
                completed[row['identity']]=row['passed']
    if any(value is False for value in completed.values()):return None,'smoke_fit_failed'
    remaining=set(smoke_identities)-completed.keys()
    if remaining:return [task for task in pending if task['identity'] in remaining],None
    return pending,None


def _other_threads(project,workers):
    status=project/'analysis/status.py'
    if not status.is_file():raise ValueError('canonical numerical status command required')
    result=subprocess.run([sys.executable,str(status),'--json'],cwd=project,
                          capture_output=True,text=True,timeout=120,check=False)
    if result.returncode not in (0,1):raise ValueError('canonical status check failed')
    report=json.loads(result.stdout)
    if (report.get('warnings') or any(row.get('state')=='invalid'
            or (row.get('warnings') and row.get('threads',0)>0)
            for row in report.get('studies',[]))):
        raise ValueError('canonical status reports an active or invalid warning')
    observed=report['monitored_numerical_threads']
    if type(observed) is not int or observed<0 or observed+workers>4:
        raise ValueError('other numerical jobs exhaust the four-thread allocation')
    return observed


def _disk_guard(project,parent_manifest):
    recipe=parent_manifest['inputs']['recipe']['source']
    minimum=_read(runner.path_within(project,recipe))['minimum_free_bytes']
    if type(minimum) is not int or minimum<0 or shutil.disk_usage(project).free<minimum:
        raise ValueError('frozen validation disk reserve unavailable')


def _register_stage(project,stage):
    """Expose each stage to the canonical four-thread status registry."""
    registry=project/'analysis/study-status.json'
    if not registry.is_file():raise ValueError('canonical status registry required')
    lock=project/'analysis/study-status.lock'
    with lock.open('a+b') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX)
        value=_read(registry)
        if not isinstance(value.get('studies'),list):
            raise ValueError('invalid status registry')
        name=stage.relative_to(project).as_posix()
        if not any(row.get('path')==name for row in value['studies']):
            value['studies'].insert(0,dict(name='Recoverable prediction validation '+stage.name,
                                           path=name))
            runner._replace(registry,value)


def _new_stage(project,output,stage_index,tasks,parent_manifest,policy,remaining_s):
    sources=[*parent_manifest['sources'],ADAPTER]
    inputs={key:record['source'] for key,record in parent_manifest['inputs'].items()}
    inputs.update({'continuation-parent-manifest':policy['parent']+'/manifest.json',
                   'continuation-policy':str((output/'policy.json').relative_to(project)),
                   'continuation-plan':str((output/'plan.json').relative_to(project))})
    stage=output/f'stage-{stage_index:03d}'
    # A reboot during source copying leaves only an inert preparation directory.
    temporary=Path(tempfile.mkdtemp(prefix='.stage-preparing-',dir=output))
    candidate=temporary/'study'
    runner.prepare(candidate,project_root=project,tasks=tasks,sources=sources,inputs=inputs,
        adapter=ADAPTER,workers=min(4,len(tasks)),threads=1,
        maximum_wall_s=remaining_s,environment=parent_manifest['environment'],
        stop_after_failure=parent_manifest['stop_after_failure'],
        accounting_format=parent_manifest['accounting_format'],
        scope='technical continuation of interrupted validation; original verdict unchanged')
    manifest=runner.verify(candidate)
    _stage_manifest_matches(manifest,parent_manifest,policy)
    os.rename(candidate,stage)
    fd=os.open(output,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
    return stage


def resume_campaign(project,output,*,launch=True):
    """Resume after reboot; verify every prior result and schedule only pending work."""
    project=Path(project).resolve();output=Path(output).resolve()
    if not output.is_relative_to(project):raise ValueError('project-relative campaign required')
    with _campaign_lease(output/'campaign.lock'):
        plan,policy,parent_manifest=_frozen(project,output)
        smoke_ids=[task['identity'] for task in plan['tasks'][:policy.get('smoke_task_count',0)]]
        deadline=policy['deadline_unix']
        if deadline-policy['prepared_unix']!=policy['maximum_wall_s']:
            raise ValueError('campaign deadline changed')
        while True:
            stages=[];paths=_stage_paths(output)
            for index,stage in enumerate(paths):
                manifest=runner.verify(stage)
                _stage_manifest_matches(manifest,parent_manifest,policy)
                selected=next_stage_tasks(plan,stages,
                    max_attempts_per_task=policy['max_attempts_per_task'],
                    max_technical_interruptions=policy['max_technical_interruptions'])['tasks']
                expected,gate=_smoke_selection(selected,stages,smoke_ids)
                if gate:return dict(state='qualification_failed',reason=gate,stage=index)
                actual=[{key:value for key,value in task.items() if key not in ('index','shard')}
                        for task in manifest['tasks']]
                if actual!=expected:
                    raise ValueError('prepared stage changes pending scientific task list')
                if (stage/'completion.json').exists():
                    runner.verify_completion(stage)
                else:
                    advice=inspect(project,stage.relative_to(project).as_posix())
                    if advice['state']=='owned':return dict(state='owned',stage=index)
                    if advice['state']=='uncharged_work_available' and not advice['interrupted_identities']:
                        if time.time()>=deadline:return dict(state='deadline_exhausted',stage=index)
                        if launch:
                            _disk_guard(project,parent_manifest)
                            _register_stage(project,stage)
                            runner.launch(stage,reserved_threads=_other_threads(
                                project,manifest['allocation']['workers']))
                            break
                        return dict(state='ready',stage=index)
                    if not launch:return dict(state='needs_stage_closure',stage=index,
                                               interrupted=len(advice['interrupted_identities']))
                    _close_interrupted(stage,manifest)
                stages.append(dict(manifest=manifest,merged=runner.merge(stage)))
            else:
                stops=[_stop_reason(stage) for stage in paths]
                if any(stops):
                    return dict(state='scientific_gate_stopped',
                                reasons=[reason for reason in stops if reason],stages=len(paths))
                selected=next_stage_tasks(plan,stages,
                    max_attempts_per_task=policy['max_attempts_per_task'],
                    max_technical_interruptions=policy['max_technical_interruptions'])
                assigned,gate=_smoke_selection(selected['tasks'],stages,smoke_ids)
                if gate:return dict(state='qualification_failed',reason=gate,stages=len(paths))
                if not assigned:
                    total=plan['completed']+selected['completed']
                    if total!=len(parent_manifest['tasks']):
                        raise ValueError('combined continuation does not cover every parent identity')
                    result=dict(state='all_tasks_finished',original_completed=plan['completed'],
                                continuation_completed=selected['completed'],
                                completed_failures=plan['completed_failures']+selected['completed_failures'],
                                technical_interruptions=selected['technical_interruptions'],
                                stages=len(paths))
                    receipt=dict(version=VERSION,scientific_decision='abstain',
                                 validation_coverage_qualified=False,**result,
                                 parent_manifest_sha256=plan['parent_manifest_sha256'],
                                 parent_merged_sha256=plan['parent_merged_sha256'],
                                 policy_sha256=_sha(output/'policy.json'),
                                 stage_completion_sha256=[_sha(stage/'completion.json') for stage in paths])
                    completion=output/'completion.json'
                    if completion.exists():
                        if _read(completion)!=receipt:raise ValueError('continuation completion changed')
                    else:runner._write(completion,receipt)
                    return result
                remaining=deadline-time.time()
                if remaining<=1:return dict(state='deadline_exhausted',pending=len(selected['tasks']))
                if not launch:return dict(state='ready',pending=len(selected['tasks']),
                                          next_stage=len(paths),next_stage_tasks=len(assigned))
                _disk_guard(project,parent_manifest)
                stage=_new_stage(project,output,len(paths),assigned,parent_manifest,policy,remaining-1)
                _register_stage(project,stage)
                runner.launch(stage,reserved_threads=_other_threads(
                    project,runner.verify(stage)['allocation']['workers']))
                continue


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',default='.')
    commands=parser.add_subparsers(dest='command',required=True)
    prepare=commands.add_parser('prepare',help='freeze a new finite continuation; run no fits')
    prepare.add_argument('--parent',required=True)
    prepare.add_argument('--plan',required=True)
    prepare.add_argument('--output',required=True)
    prepare.add_argument('--max-attempts-per-task',required=True,type=int)
    prepare.add_argument('--max-technical-interruptions',required=True,type=int)
    prepare.add_argument('--maximum-wall-s',required=True,type=int)
    prepare.add_argument('--smoke-task-count',type=int,default=0)
    resume=commands.add_parser('resume',help='verify saved work and continue unfinished tasks')
    resume.add_argument('--output',required=True)
    resume.add_argument('--dry-run',action='store_true')
    args=parser.parse_args(argv)
    if args.command=='prepare':
        result=prepare_campaign(args.project,args.parent,args.plan,args.output,
            max_attempts_per_task=args.max_attempts_per_task,
            max_technical_interruptions=args.max_technical_interruptions,
            maximum_wall_s=args.maximum_wall_s,smoke_task_count=args.smoke_task_count)
        result=dict(state='prepared',parent=result['parent'],
                    max_attempts_per_task=result['max_attempts_per_task'],
                    max_technical_interruptions=result['max_technical_interruptions'],
                    maximum_wall_s=result['maximum_wall_s'],
                    smoke_task_count=result['smoke_task_count'])
    else:result=resume_campaign(args.project,args.output,launch=not args.dry_run)
    print(json.dumps(result,sort_keys=True))
    return 0


if __name__=='__main__':raise SystemExit(main())
