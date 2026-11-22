# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify a completed one-stage continuation from archived evidence.

This historical read-only path checks frozen source snapshots, not mutable
checkout files. It supports audits after later library development.
"""

import json
from pathlib import Path

from .artifacts import digest, encoded
from .closed import ClosedStudy


def inspect(root, campaign, *, expected_parent, expected_total):
    root = Path(root).resolve()
    base = (root / campaign).resolve()
    if (not base.is_relative_to(root) or
            type(expected_total) is not int or expected_total < 1):
        raise ValueError('project campaign and finite total required')
    raw = {name: (base / name).read_bytes() for name in
           ('freeze.json', 'plan.json', 'policy.json', 'completion.json')}
    freeze, plan, policy, receipt = [json.loads(raw[name]) for name in raw]
    if (freeze.get('version') != 'lll-task-resume-v1'
            or plan.get('version') != 'lll-task-continuation-plan-v1'
            or policy.get('version') != 'lll-task-resume-v1'
            or receipt.get('version') != 'lll-task-resume-v1'
            or freeze.get('plan_sha256') != digest(raw['plan.json'])
            or freeze.get('policy_sha256') != digest(raw['policy.json'])
            or policy.get('plan_sha256') != digest(raw['plan.json'])
            or policy.get('parent') != expected_parent
            or policy.get('smoke_task_count') != 0
            or policy.get('parent_manifest_sha256') !=
                plan.get('parent_manifest_sha256')
            or receipt.get('parent_manifest_sha256') !=
                plan.get('parent_manifest_sha256')
            or receipt.get('parent_merged_sha256') !=
                plan.get('parent_merged_sha256')
            or receipt.get('policy_sha256') != digest(raw['policy.json'])
            or receipt.get('state') != 'all_tasks_finished'
            or receipt.get('scientific_decision') != 'abstain'
            or receipt.get('stages') != 1):
        raise ValueError('unchanged completed one-stage continuation required')
    stage_name = campaign.rstrip('/') + '/stage-000'
    parent = ClosedStudy(root, expected_parent)
    stage = ClosedStudy(root, stage_name)
    try:
        if (parent.completion['manifest_sha256'] !=
                plan['parent_manifest_sha256']
                or parent.completion['state'] != 'terminal'
                or stage.completion['state'] != 'complete'
                or len(parent.tasks) != expected_total
                or len(parent.rows) != plan['completed'] +
                    plan['prior_interrupted_charges']
                or len(stage.tasks) != expected_total - plan['completed']
                or len(stage.rows) != len(stage.tasks)
                or receipt['original_completed'] != plan['completed']
                or receipt['continuation_completed'] != len(stage.rows)
                or receipt['technical_interruptions'] !=
                    plan['prior_interrupted_charges']
                or receipt['stage_completion_sha256'] != [digest(
                    stage.read('completion.json', raw=True))]):
            raise ValueError('parent/stage completion differs from receipt')
        for study in (parent, stage):
            for name, sha in study.manifest['sources'].items():
                study.read('source-freeze/' + name, sha, raw=True)
        expected_sources = dict(parent.manifest['sources'])
        expected_sources.update({
            'analysis/lll/studies/task_resume.py': policy['runtime_sha256'],
            'analysis/lll/studies/task_continuation.py':
                policy['planner_sha256']})
        if (stage.manifest['sources'] != expected_sources
                or stage.manifest['adapter'] != parent.manifest['adapter']
                or stage.manifest['scope'] != parent.manifest['scope']
                or stage.manifest['environment'] != parent.manifest['environment']
                or stage.manifest['numerical_environment'] !=
                    parent.manifest['numerical_environment']
                or any(stage.manifest['inputs'][key]['sha256'] != item['sha256']
                       for key, item in parent.manifest['inputs'].items())
                or stage.manifest['inputs']['continuation-policy']['sha256']
                   != digest(raw['policy.json'])
                or stage.manifest['inputs']['continuation-plan']['sha256']
                   != digest(raw['plan.json'])):
            raise ValueError('continuation changed scientific source or inputs')
        complete = {identity for identity, row in parent.rows.items()
                    if row['status'] == 'complete'}
        interrupted = {identity for identity, row in parent.rows.items()
                       if row['status'] == 'interrupted'}
        if (len(complete) != plan['completed']
                or len(interrupted) != plan['prior_interrupted_charges']
                or {task['identity'] for task in plan['tasks']} !=
                    set(parent.tasks) - complete
                or {task['identity'] for task in plan['tasks']} != set(stage.tasks)
                or any({key: value for key, value in stage.tasks[task['identity']].items()
                        if key not in ('index', 'shard')} != task
                       for task in plan['tasks'])
                or any(row['status'] != 'complete' for row in stage.rows.values())):
            raise ValueError('stage repeated or changed a scientific task')
        selected = {identity: dict(origin=expected_parent, row=parent.rows[identity],
                    manifest_sha256=parent.completion['manifest_sha256'])
                    for identity in complete}
        selected.update({identity: dict(origin=stage_name, row=row,
                        manifest_sha256=stage.completion['manifest_sha256'])
                        for identity, row in stage.rows.items()})
        if len(selected) != expected_total:
            raise ValueError('complete unique scientific tasks required')
        return dict(verified=True, parent=expected_parent,
                    campaign=campaign, total=expected_total,
                    completed=expected_total, selected=selected,
                    lineage_sha256=digest(encoded(receipt)),
                    archived_source_snapshots_verified=True,
                    scientific_decision='abstain')
    finally:
        stage.close()
        parent.close()
