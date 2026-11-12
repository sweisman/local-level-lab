# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only identity ledger across a terminal study and its recovery stages.

This verifies technical completion and provenance. It makes no scientific
adequacy, model-selection or uncertainty claim.
"""
from pathlib import Path
import time

from lll import ilvis0_control_shards as runner
from .artifacts import digest, encoded
from .task_resume import (_frozen, _stage_matches, _stage_paths, _smoke_selection,
                          _stop_reason, _sha, _read, VERSION)
from .validation_continuation import next_stage_tasks
from .validation_resume import _campaign_lease


def inspect(project, output):
    project=Path(project).resolve();output=Path(output).resolve()
    if not output.is_relative_to(project):
        raise ValueError('project-relative campaign required')
    with _campaign_lease(output/'campaign.lock'):
        return _inspect_unowned(project,output)


def _inspect_unowned(project,output):
    plan,policy,parent=_frozen(project,output)
    receipt_path=output/'completion.json'
    has_receipt=receipt_path.is_file()
    parent_path=project/policy['parent']
    parent_summary=runner.verify_completion(parent_path)
    selected={}
    attempts=[]
    for row in parent_summary['results']:
        attempts.append(dict(origin=policy['parent'],**row))
        if row['status']=='complete':
            selected[row['identity']]=dict(origin=policy['parent'],row=row,
                manifest_sha256=plan['parent_manifest_sha256'])
    stages=[];paths=_stage_paths(output);stops=[]
    smoke=[task['identity'] for task in plan['tasks'][:policy['smoke_task_count']]]
    for index,stage in enumerate(paths):
        manifest=runner.verify(stage);_stage_matches(manifest,parent,policy)
        pending=next_stage_tasks(plan,stages,
            max_attempts_per_task=policy['max_attempts_per_task'],
            max_technical_interruptions=policy['max_technical_interruptions'])['tasks']
        expected,gate=_smoke_selection(pending,stages,smoke)
        if gate:
            raise ValueError('failed smoke gate cannot have a later stage')
        actual=[{key:value for key,value in task.items()
                 if key not in ('index','shard')} for task in manifest['tasks']]
        if actual!=expected:
            raise ValueError('stage changed pending scientific identities')
        summary=runner.verify_completion(stage)
        reason=_stop_reason(stage)
        if reason:
            if index!=len(paths)-1:
                raise ValueError('scientific stop followed by another stage')
            stops.append(reason)
        origin=stage.relative_to(project).as_posix()
        for row in summary['results']:
            attempts.append(dict(origin=origin,**row))
            if row['status']=='complete':
                if row['identity'] in selected:
                    raise ValueError('completed scientific task repeated')
                selected[row['identity']]=dict(origin=origin,row=row,
                    manifest_sha256=_sha(stage/'manifest.json'))
        stages.append(dict(manifest=manifest,merged=summary))
    exhausted=None
    try:
        state=next_stage_tasks(plan,stages,
            max_attempts_per_task=policy['max_attempts_per_task'],
            max_technical_interruptions=policy['max_technical_interruptions'])
    except ValueError as error:
        if str(error) not in ('finite technical recovery allowance exhausted',
                              'per-task technical recovery allowance exhausted'):
            raise
        exhausted=str(error);state=None
    all_ids={task['identity'] for task in parent['tasks']}
    pending_ids=sorted(all_ids-set(selected))
    if (not set(selected)<=all_ids
            or (state is not None and
                (set(pending_ids)!={task['identity'] for task in state['tasks']}
                 or plan['completed']+state['completed']!=len(selected)))):
        raise ValueError('combined scientific task inventory differs')
    failures=sum(item['row']['passed'] is False for item in selected.values())
    technical=sum(row['status']=='interrupted' for row in attempts)
    if has_receipt:
        if exhausted or pending_ids or state is None or stops:
            raise ValueError('combined scientific task inventory incomplete')
        result=dict(state='all_tasks_finished',original_completed=plan['completed'],
            continuation_completed=state['completed'],
            completed_failures=plan['completed_failures']+state['completed_failures'],
            technical_interruptions=state['technical_interruptions'],
            stages=len(paths),scientific_decision='abstain')
        expected_receipt=dict(version=VERSION,**result,
            parent_manifest_sha256=plan['parent_manifest_sha256'],
            parent_merged_sha256=plan['parent_merged_sha256'],
            policy_sha256=_sha(output/'policy.json'),
            stage_completion_sha256=[_sha(stage/'completion.json') for stage in paths])
        if _read(receipt_path)!=expected_receipt:
            raise ValueError('continuation completion receipt differs from verified stages')
        lineage=digest(encoded(expected_receipt))
    else:
        if not pending_ids and not stops:
            raise ValueError('completed continuation lacks its completion receipt')
        reason=('scientific_gate_stopped' if stops else exhausted or
                ('deadline_exhausted' if time.time()>=policy['deadline_unix'] else None))
        if reason is None:
            raise ValueError('closed continuation required')
        result=dict(state='terminal_incomplete' if pending_ids else 'terminal_failed',
            terminal_reason=reason,stop_reasons=stops,
            pending_identities=pending_ids,
            original_completed=plan['completed'],
            continuation_completed=len(selected)-plan['completed'],
            completed_failures=failures,technical_interruptions=technical,
            stages=len(paths),scientific_decision='abstain')
        lineage=digest(encoded(dict(version=VERSION,**result,
            parent_manifest_sha256=plan['parent_manifest_sha256'],
            parent_merged_sha256=plan['parent_merged_sha256'],
            policy_sha256=_sha(output/'policy.json'),
            stage_completion_sha256=[_sha(stage/'completion.json') for stage in paths])))
    if result['completed_failures']!=failures or result['technical_interruptions']!=technical:
        raise ValueError('combined completion counts differ from attempts')
    return dict(version='lll-combined-task-evidence-v1',verified=True,
        state=result['state'],terminal_reason=result.get('terminal_reason'),
        pending_identities=pending_ids,
        parent=policy['parent'],campaign=output.relative_to(project).as_posix(),
        total=len(parent['tasks']),completed=len(selected),
        passing=sum(item['row']['passed'] is True for item in selected.values()),
        completed_failures=result['completed_failures'],
        technical_interruptions=result['technical_interruptions'],
        selected=selected,attempts=attempts,
        parent_manifest_sha256=plan['parent_manifest_sha256'],
        parent_completion_sha256=_sha(parent_path/'completion.json'),
        campaign_completion_sha256=_sha(receipt_path) if has_receipt else None,
        lineage_sha256=lineage,
        scientific_decision='abstain')
