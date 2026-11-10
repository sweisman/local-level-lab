# SPDX-License-Identifier: AGPL-3.0-or-later
"""Plan a separately frozen continuation from verified, immutable task evidence.

This module performs no launches and cannot change an interrupted study's verdict.
The caller must verify the parent manifest, journals, seals and artifacts first.
"""
from copy import deepcopy

from .artifacts import digest, encoded


def plan_pending_tasks(manifest, merged, advice):
    """Reuse every sealed completed task; select only unstarted or interrupted work."""
    if (advice.get('state') != 'cohort_unavailable'
            or advice.get('uninterrupted_cohort_required') is not True
            or advice.get('resume_authorized') is True):
        raise ValueError('verified interrupted parent cohort required')
    tasks=manifest.get('tasks', [])
    identities=[task['identity'] for task in tasks]
    if len(identities)!=len(set(identities)) or merged.get('total')!=len(tasks):
        raise ValueError('parent task identities or total changed')
    rows=merged.get('results', [])
    row_ids=[row['identity'] for row in rows]
    if len(row_ids)!=len(set(row_ids)) or merged.get('completed')!=len(rows):
        raise ValueError('duplicate or uncounted sealed result')
    sealed=set(row_ids)
    interrupted=set(advice.get('interrupted_identities', []))
    unstarted=set(advice.get('uncharged_tasks', []))
    all_ids=set(identities)
    if (not sealed<=all_ids or not interrupted<=all_ids or not unstarted<=all_ids
            or unstarted & sealed or unstarted & interrupted
            or sealed | interrupted | unstarted != all_ids):
        raise ValueError('every parent identity must be accounted for exactly once')
    for row in rows:
        if (row.get('status') not in ('complete', 'interrupted')
                or type(row.get('passed')) is not bool
                or (row['identity'] in interrupted) != (row['status']=='interrupted')):
            raise ValueError('completed outcome cannot become a recovery candidate')
    if (merged.get('charged_identities') != advice.get('charged_identities')
            or merged['charged_identities'] != len(sealed | interrupted)):
        raise ValueError('charged starts must remain accounted for')
    pending=interrupted | unstarted
    return dict(version='lll-validation-continuation-plan-v1',
                parent_manifest_sha256=advice['manifest_sha256'],
                parent_merged_sha256=digest(encoded(merged)),
                parent_environment=deepcopy(manifest['environment']),
                completed=sum(row['status']=='complete' for row in rows),
                completed_failures=sum(row['status']=='complete' and not row['passed'] for row in rows),
                prior_interrupted_charges=len(interrupted),
                prior_interrupted_identities=sorted(interrupted),
                never_started=len(unstarted),
                tasks=[{key:deepcopy(value) for key,value in task.items()
                        if key not in ('index','shard')}
                       for task in tasks if task['identity'] in pending])


def next_stage_tasks(plan, closed_stages, *, max_attempts_per_task, max_technical_interruptions):
    """Select pending tasks after sealed stages; never requeue a completed outcome.

    Each stage is a separately frozen, closed execution. Repeated host reboots
    consume finite technical attempts without repeating completed calculations.
    """
    tasks=plan['tasks']
    order=[task['identity'] for task in tasks]
    expected={task['identity']:task for task in tasks}
    if len(order)!=len(set(order)) or max_attempts_per_task<2 or max_technical_interruptions<0:
        raise ValueError('unique tasks and finite positive recovery limits required')
    pending=set(order)
    attempts={identity:1 if identity in plan['prior_interrupted_identities'] else 0
              for identity in order}
    technical=len(plan['prior_interrupted_identities'])
    completed={}
    for stage in closed_stages:
        manifest=stage['manifest']; merged=stage['merged']
        assigned=[task['identity'] for task in manifest['tasks']]
        if (len(assigned)!=len(set(assigned)) or not set(assigned)<=pending
                or merged.get('total')!=len(assigned)
                or merged.get('completed')!=len(merged.get('results',[]))
                or merged.get('charged_identities')!=len(merged['results'])):
            raise ValueError('closed stage changes or duplicates a pending task')
        if any({key:value for key,value in task.items() if key not in ('index','shard')}
               != expected[task['identity']] for task in manifest['tasks']):
            raise ValueError('closed stage changes frozen scientific task')
        seen=set()
        for row in merged['results']:
            identity=row['identity']
            if (identity not in assigned or identity in seen
                    or row.get('status') not in ('complete','interrupted')
                    or type(row.get('passed')) is not bool):
                raise ValueError('invalid or duplicate sealed stage outcome')
            seen.add(identity);attempts[identity]+=1
            if row['status']=='complete':
                pending.remove(identity);completed[identity]=row['passed']
            else:technical+=1
    if technical>max_technical_interruptions:
        raise ValueError('finite technical recovery allowance exhausted')
    if any(attempts[identity]>=max_attempts_per_task for identity in pending):
        raise ValueError('per-task technical recovery allowance exhausted')
    return dict(tasks=[deepcopy(task) for task in tasks if task['identity'] in pending],
                completed=len(completed),completed_failures=sum(not ok for ok in completed.values()),
                charged_attempts=sum(attempts.values()),technical_interruptions=technical)
