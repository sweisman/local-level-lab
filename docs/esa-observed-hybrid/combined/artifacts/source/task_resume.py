# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite, reboot-safe continuation of an interrupted sealed-task study.

Only unfinished technical work is assigned to new stages. The original study
is never refitted or rewritten. This module imports no numerical library and
sends no process signals.
"""
import argparse
from contextlib import ExitStack
import fcntl
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time

from lll import ilvis0_control_shards as runner
from lll.ilvis0_receipt_journal import durable_write, encoded, digest
from .artifacts import digest as byte_digest
from .qualification import checked
from .recovery import inspect
from .task_continuation import (plan_incomplete_parent, plan_closed_parent,
                                VERSION as PLAN_VERSION)
from .validation_continuation import next_stage_tasks
from .validation_resume import (_campaign_lease, _stage_paths, _stop_reason,
                                _smoke_selection, _other_threads,
                                _close_interrupted)

VERSION = 'lll-task-resume-v1'
SELF = 'analysis/lll/studies/task_resume.py'
PLANNER = 'analysis/lll/studies/task_continuation.py'
REQUIRED_TESTS = ('test_reboot_resume_skips_sealed_and_preserves_charges',
                  'test_original_closure_is_idempotent_and_blocks_old_launch',
                  'test_rejects_duplicate_owner',
                  'test_source_input_environment_mutation_blocks',
                  'test_recovery_caps_and_completed_failure')


def _read(path):
    return json.loads(Path(path).read_bytes())


def _sha(path):
    return runner._sha(path)


def qualification_sources(root):
    return [SELF, PLANNER,
            'analysis/lll/studies/validation_continuation.py',
            'analysis/lll/studies/validation_resume.py',
            'analysis/lll/studies/recovery.py',
            'analysis/lll/ilvis0_control_shards.py',
            'analysis/tests/test_task_resume.py']


def _parent(project, parent, expected=None):
    parent=Path(parent)
    if parent.is_absolute() or not (project/parent).resolve().is_relative_to(project):
        raise ValueError('project-relative original study required')
    path=project/parent
    manifest=runner.verify(path)
    if not (path/'completion.json').exists():
        raise ValueError('verified terminal original study required')
    runner.verify_completion(path)
    completion=_read(path/'completion.json')
    merged=runner.merge(path)
    actual=plan_closed_parent(manifest,merged,completion)
    if expected is not None and encoded(actual)!=encoded(expected):
        raise ValueError('original task evidence changed')
    if manifest['environment']!=runner.runtime_environment():
        raise ValueError('numerical environment differs from original')
    for name,sha in manifest['sources'].items():
        if _sha(runner.path_within(project,name))!=sha:
            raise ValueError('original source changed: '+name)
    for record in manifest['inputs'].values():
        if _sha(runner.path_within(project,record['source']))!=record['sha256']:
            raise ValueError('original input changed')
    return manifest,actual


def close_original(project,parent,*,qualification_request):
    """Terminally seal charged losses only after recovery has qualified."""
    project=Path(project).resolve();parent=Path(parent)
    if parent.is_absolute() or not (project/parent).resolve().is_relative_to(project):
        raise ValueError('project-relative original study required')
    path=project/parent
    checked(project,qualification_request,sources=qualification_sources(project),
            environment=runner.runtime_environment(),
            required_tests=REQUIRED_TESTS,minimum_tests=len(REQUIRED_TESTS))
    if (path/'completion.json').exists():
        summary=runner.verify_completion(path)
        if summary['state']!='terminal':raise ValueError('original closure state changed')
        return dict(state='already_terminal',completed=summary['completed'])
    if not (path/'worker.lock').is_file():
        raise ValueError('original coordinator lease is missing')
    with runner._lease(path/'worker.lock',True):
        manifest=runner.verify(path)
        advice=inspect(project,parent.as_posix())
        before=plan_incomplete_parent(manifest,runner.merge(path),advice)
        with ExitStack() as leases:
            for shard in range(manifest['allocation']['workers']):
                leases.enter_context(runner._lease(
                    path/'shards'/f'{shard:03d}'/'worker.lock',True))
        summary=runner._finish_study(path,manifest)
        runner.verify_completion(path)
        after=plan_closed_parent(manifest,runner.merge(path),_read(path/'completion.json'))
        keys=('completed','completed_failures','prior_interrupted_identities',
              'never_started','tasks')
        if any(before[key]!=after[key] for key in keys):
            raise ValueError('closure changed the pending scientific inventory')
        return dict(state=summary['state'],completed=after['completed'],
                    interrupted=after['prior_interrupted_charges'],
                    never_started=after['never_started'])


def prepare_campaign(project,parent,output,*,qualification_request,
                     max_attempts_per_task,max_technical_interruptions,
                     maximum_wall_s,minimum_free_bytes,smoke_task_count=0):
    """Freeze limits and qualified recovery evidence; launch no worker."""
    project=Path(project).resolve();output=Path(output).resolve()
    if (output.exists() or not output.is_relative_to(project)
            or type(max_attempts_per_task) is not int or max_attempts_per_task<2
            or type(max_technical_interruptions) is not int or max_technical_interruptions<0
            or type(maximum_wall_s) is not int or maximum_wall_s<=0
            or type(minimum_free_bytes) is not int or minimum_free_bytes<0
            or type(smoke_task_count) is not int or smoke_task_count<0):
        raise ValueError('new output and finite recovery, wall and disk limits required')
    manifest,plan=_parent(project,parent)
    if (plan['version']!=PLAN_VERSION or not plan['tasks']
            or smoke_task_count>len(plan['tasks'])
            or max_technical_interruptions<plan['prior_interrupted_charges']
            or manifest['allocation']['threads']!=1
            or manifest['accounting_format']!='sqlite-v1'):
        raise ValueError('unsupported parent or insufficient recovery limit')
    env=runner.runtime_environment()
    request_raw,report_raw=checked(project,qualification_request,
        sources=qualification_sources(project),environment=env,
        required_tests=REQUIRED_TESTS,minimum_tests=len(REQUIRED_TESTS))
    prepared=time.time()
    policy=dict(version=VERSION,parent=Path(parent).as_posix(),
        parent_manifest_sha256=plan['parent_manifest_sha256'],
        parent_merged_sha256=plan['parent_merged_sha256'],
        plan_sha256=digest(plan),runtime_sha256=_sha(project/SELF),
        planner_sha256=_sha(project/PLANNER),
        qualification_request_sha256=byte_digest(request_raw),
        qualification_report_sha256=byte_digest(report_raw),
        qualification_request=str(qualification_request),
        max_attempts_per_task=max_attempts_per_task,
        max_technical_interruptions=max_technical_interruptions,
        maximum_wall_s=maximum_wall_s,minimum_free_bytes=minimum_free_bytes,
        smoke_task_count=smoke_task_count,prepared_unix=prepared,
        deadline_unix=prepared+maximum_wall_s,threads_per_worker=1)
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary=Path(tempfile.mkdtemp(prefix='.task-campaign-preparing-',dir=output.parent))
    durable_write(temporary/'plan.json',encoded(plan))
    durable_write(temporary/'policy.json',encoded(policy))
    durable_write(temporary/'freeze.json',encoded(dict(version=VERSION,
        plan_sha256=_sha(temporary/'plan.json'),
        policy_sha256=_sha(temporary/'policy.json'))))
    durable_write(temporary/'campaign.lock',b'')
    os.rename(temporary,output)
    fd=os.open(output.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
    return dict(state='prepared',pending=len(plan['tasks']),policy_sha256=_sha(output/'policy.json'))


def _frozen(project,output):
    freeze=_read(output/'freeze.json');plan=_read(output/'plan.json');policy=_read(output/'policy.json')
    if (freeze.get('version')!=VERSION or policy.get('version')!=VERSION
            or freeze.get('plan_sha256')!=_sha(output/'plan.json')
            or freeze.get('policy_sha256')!=_sha(output/'policy.json')
            or policy.get('runtime_sha256')!=_sha(project/SELF)
            or policy.get('planner_sha256')!=_sha(project/PLANNER)
            or policy.get('plan_sha256')!=_sha(output/'plan.json')
            or policy.get('parent_manifest_sha256')!=plan.get('parent_manifest_sha256')
            or policy.get('parent_merged_sha256')!=plan.get('parent_merged_sha256')):
        raise ValueError('continuation freeze or runtime changed')
    manifest,actual=_parent(project,policy['parent'],plan)
    request,report=checked(project,policy['qualification_request'],
        sources=qualification_sources(project),environment=manifest['environment'],
        required_tests=REQUIRED_TESTS,minimum_tests=len(REQUIRED_TESTS))
    if (byte_digest(request)!=policy['qualification_request_sha256']
            or byte_digest(report)!=policy['qualification_report_sha256']):
        raise ValueError('recovery qualification changed')
    return plan,policy,manifest


def _stage_matches(stage,parent,policy):
    sources={**parent['sources'],SELF:policy['runtime_sha256'],
             PLANNER:policy['planner_sha256']}
    inputs={key:record['sha256'] for key,record in parent['inputs'].items()}
    inputs.update({'continuation-parent-manifest':policy['parent_manifest_sha256'],
                   'continuation-policy':digest(policy),
                   'continuation-plan':policy['plan_sha256'],
                   'continuation-qualification-request':policy['qualification_request_sha256'],
                   'continuation-qualification-report':policy['qualification_report_sha256']})
    if (stage['sources']!=sources or stage['adapter']!=parent['adapter']
            or stage['environment']!=parent['environment']
            or stage['numerical_environment']!=parent['numerical_environment']
            or stage['scope']!=parent['scope']
            or stage['stop_after_failure']!=parent['stop_after_failure']
            or stage['accounting_format']!=parent['accounting_format']
            or stage['allocation']['threads']!=1
            or not 1<=stage['allocation']['workers']<=4
            or stage['allocation']['total']!=stage['allocation']['workers']
            or set(stage['inputs'])!=set(inputs)
            or any(stage['inputs'][key]['sha256']!=sha for key,sha in inputs.items())):
        raise ValueError('stage changed frozen source, inputs, method or allocation')


def _new_stage(project,output,index,tasks,parent,policy,remaining_s):
    sources=[*parent['sources'],SELF,PLANNER]
    inputs={key:record['source'] for key,record in parent['inputs'].items()}
    inputs.update({'continuation-parent-manifest':policy['parent']+'/manifest.json',
                   'continuation-policy':str((output/'policy.json').relative_to(project)),
                   'continuation-plan':str((output/'plan.json').relative_to(project)),
                   'continuation-qualification-request':policy['qualification_request'],
                   'continuation-qualification-report':_read(project/policy['qualification_request'])['report']})
    temporary=Path(tempfile.mkdtemp(prefix='.stage-preparing-',dir=output))
    candidate=temporary/'study'
    runner.prepare(candidate,project_root=project,tasks=tasks,sources=sources,inputs=inputs,
        adapter=parent['adapter'],workers=min(4,len(tasks)),threads=1,
        maximum_wall_s=remaining_s,environment=parent['environment'],
        stop_after_failure=parent['stop_after_failure'],
        accounting_format=parent['accounting_format'],scope=parent['scope'])
    manifest=runner.verify(candidate);_stage_matches(manifest,parent,policy)
    stage=output/f'stage-{index:03d}'
    os.rename(candidate,stage)
    fd=os.open(output,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
    return stage


def _register_stage(project,stage):
    registry=project/'analysis/study-status.json'
    lock=project/'analysis/study-status.lock'
    if not registry.is_file() or not lock.is_file():
        raise ValueError('canonical status registry required')
    with lock.open('a+b') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX)
        value=_read(registry)
        if not isinstance(value.get('studies'),list):
            raise ValueError('invalid status registry')
        name=stage.relative_to(project).as_posix()
        if not any(row.get('path')==name for row in value['studies']):
            value['studies'].insert(0,dict(name='Task recovery '+stage.name,path=name))
            runner._replace(registry,value)


def _disk_guard(project,policy):
    if shutil.disk_usage(project).free<policy['minimum_free_bytes']:
        raise ValueError('frozen continuation disk reserve unavailable')


def resume_campaign(project,output,*,launch=True):
    """Verify all saved stages and schedule only unfinished task identities."""
    project=Path(project).resolve();output=Path(output).resolve()
    if not output.is_relative_to(project):
        raise ValueError('project-relative campaign required')
    with _campaign_lease(output/'campaign.lock'):
        plan,policy,parent=_frozen(project,output)
        deadline=policy['deadline_unix']
        if deadline-policy['prepared_unix']!=policy['maximum_wall_s']:
            raise ValueError('campaign deadline changed')
        smoke=[task['identity'] for task in plan['tasks'][:policy['smoke_task_count']]]
        while True:
            stages=[];paths=_stage_paths(output)
            for index,stage in enumerate(paths):
                manifest=runner.verify(stage);_stage_matches(manifest,parent,policy)
                selected=next_stage_tasks(plan,stages,
                    max_attempts_per_task=policy['max_attempts_per_task'],
                    max_technical_interruptions=policy['max_technical_interruptions'])['tasks']
                expected,gate=_smoke_selection(selected,stages,smoke)
                if gate:return dict(state='qualification_failed',reason=gate,stage=index)
                actual=[{key:value for key,value in task.items()
                         if key not in ('index','shard')} for task in manifest['tasks']]
                if actual!=expected:
                    raise ValueError('stage assigned a changed or completed scientific task')
                if (stage/'completion.json').exists():
                    runner.verify_completion(stage)
                else:
                    advice=inspect(project,stage.relative_to(project).as_posix())
                    if advice['state']=='owned':return dict(state='owned',stage=index)
                    if (advice['state']=='uncharged_work_available'
                            and not advice['interrupted_identities']):
                        if time.time()>=deadline:return dict(state='deadline_exhausted',stage=index)
                        if not launch:return dict(state='ready',stage=index)
                        _disk_guard(project,policy);_register_stage(project,stage)
                        runner.launch(stage,reserved_threads=_other_threads(
                            project,manifest['allocation']['workers']))
                        break
                    if not launch:
                        return dict(state='needs_stage_closure',stage=index,
                                    interrupted=len(advice['interrupted_identities']))
                    _close_interrupted(stage,manifest)
                stages.append(dict(manifest=manifest,merged=runner.merge(stage)))
            else:
                reasons=[reason for stage in paths if (reason:=_stop_reason(stage))]
                if reasons:return dict(state='scientific_gate_stopped',reasons=reasons)
                selected=next_stage_tasks(plan,stages,
                    max_attempts_per_task=policy['max_attempts_per_task'],
                    max_technical_interruptions=policy['max_technical_interruptions'])
                assigned,gate=_smoke_selection(selected['tasks'],stages,smoke)
                if gate:return dict(state='qualification_failed',reason=gate)
                if not assigned:
                    if plan['completed']+selected['completed']!=len(parent['tasks']):
                        raise ValueError('combined task coverage incomplete')
                    result=dict(state='all_tasks_finished',original_completed=plan['completed'],
                                continuation_completed=selected['completed'],
                                completed_failures=plan['completed_failures']+selected['completed_failures'],
                                technical_interruptions=selected['technical_interruptions'],
                                stages=len(paths),scientific_decision='abstain')
                    receipt=dict(version=VERSION,**result,
                        parent_manifest_sha256=plan['parent_manifest_sha256'],
                        parent_merged_sha256=plan['parent_merged_sha256'],
                        policy_sha256=_sha(output/'policy.json'),
                        stage_completion_sha256=[_sha(stage/'completion.json') for stage in paths])
                    completion=output/'completion.json'
                    if completion.exists():
                        if _read(completion)!=receipt:raise ValueError('completion receipt changed')
                    else:runner._write(completion,receipt)
                    return result
                remaining=deadline-time.time()
                if remaining<=1:return dict(state='deadline_exhausted',pending=len(selected['tasks']))
                if not launch:return dict(state='ready',pending=len(selected['tasks']),
                                          next_stage=len(paths),next_stage_tasks=len(assigned))
                _disk_guard(project,policy)
                stage=_new_stage(project,output,len(paths),assigned,parent,policy,remaining-1)
                _register_stage(project,stage)
                runner.launch(stage,reserved_threads=_other_threads(
                    project,runner.verify(stage)['allocation']['workers']))
                continue


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',default='.')
    actions=parser.add_subparsers(dest='action',required=True)
    prep=actions.add_parser('prepare',help='freeze qualified finite limits; launch nothing')
    prep.add_argument('--parent',required=True)
    prep.add_argument('--output',required=True)
    prep.add_argument('--qualification-request',required=True)
    prep.add_argument('--max-attempts-per-task',required=True,type=int)
    prep.add_argument('--max-technical-interruptions',required=True,type=int)
    prep.add_argument('--maximum-wall-s',required=True,type=int)
    prep.add_argument('--minimum-free-bytes',required=True,type=int)
    prep.add_argument('--smoke-task-count',type=int,default=0)
    close=actions.add_parser('close-original',help='seal an interrupted original allowance')
    close.add_argument('--parent',required=True)
    close.add_argument('--qualification-request',required=True)
    resume=actions.add_parser('resume',help='verify all evidence and continue pending work')
    resume.add_argument('--output',required=True)
    resume.add_argument('--dry-run',action='store_true')
    args=parser.parse_args();project=Path(args.project).resolve()
    if args.action=='close-original':
        result=close_original(project,args.parent,
                              qualification_request=args.qualification_request)
    elif args.action=='prepare':
        result=prepare_campaign(project,args.parent,project/args.output,
            qualification_request=args.qualification_request,
            max_attempts_per_task=args.max_attempts_per_task,
            max_technical_interruptions=args.max_technical_interruptions,
            maximum_wall_s=args.maximum_wall_s,
            minimum_free_bytes=args.minimum_free_bytes,
            smoke_task_count=args.smoke_task_count)
    else:result=resume_campaign(project,project/args.output,launch=not args.dry_run)
    print(json.dumps(result,sort_keys=True));return 0


if __name__=='__main__':
    raise SystemExit(main())
