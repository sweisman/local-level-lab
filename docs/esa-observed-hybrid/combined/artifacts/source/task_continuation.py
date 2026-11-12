# SPDX-License-Identifier: AGPL-3.0-or-later
"""Plan task-level continuation without changing an open parent's frozen code.

The existing validation planner checks identity accounting and preservation of
completed failures. This adapter accepts a separately verified incomplete
study whose policy does not require an uninterrupted cohort. It launches no
worker and grants no retry permission by itself.
"""
from .validation_continuation import plan_pending_tasks


VERSION = 'lll-task-continuation-plan-v1'


def plan_incomplete_parent(manifest, merged, advice):
    if (advice.get('state') not in ('uncharged_work_available',
                                    'no_uncharged_work',
                                    'deadline_exhausted')
            or advice.get('uninterrupted_cohort_required') is not False
            or advice.get('resume_authorized') is True
            or advice.get('evidence_scope') != 'recovery_metadata_only'):
        raise ValueError('verified incomplete nonexclusive parent required')
    # Only the policy flags differ from the original validation cohort. The
    # common planner still checks every identity, sealed outcome and charge.
    checked = dict(advice, state='cohort_unavailable',
                   uninterrupted_cohort_required=True)
    plan = plan_pending_tasks(manifest, merged, checked)
    plan['version'] = VERSION
    return plan


def plan_closed_parent(manifest, merged, completion):
    """Use a verified terminal parent's sealed interruptions and unstarted work."""
    if (completion.get('state')!='terminal'
            or merged.get('completed')!=len(merged.get('results',[]))
            or merged.get('charged_identities')!=merged['completed']):
        raise ValueError('verified terminal parent with sealed charges required')
    rows=merged['results'];row_ids=[row['identity'] for row in rows]
    tasks=manifest['tasks'];all_ids={task['identity'] for task in tasks}
    if len(row_ids)!=len(set(row_ids)) or len(all_ids)!=len(tasks):
        raise ValueError('unique parent task and result identities required')
    interrupted=[row['identity'] for row in rows if row['status']=='interrupted']
    advice=dict(state='cohort_unavailable',resume_authorized=False,
        uninterrupted_cohort_required=True,
        manifest_sha256=completion['manifest_sha256'],
        charged_identities=merged['charged_identities'],
        interrupted_identities=interrupted,
        uncharged_tasks=sorted(all_ids-set(row_ids)))
    plan=plan_pending_tasks(manifest,merged,advice)
    plan['version']=VERSION
    return plan
