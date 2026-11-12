# SPDX-License-Identifier: AGPL-3.0-or-later
"""An open observed parent may continue only unfinished task identities."""
import pytest

from lll.studies.task_continuation import plan_incomplete_parent, plan_closed_parent


def _parent():
    tasks=[dict(identity=name,index=i,shard=i%2,input_key='recipe',
                payload=dict(seed=i),native_kind='tangent',
                limits=dict(native_calls=7,packet_visits=30,
                            bound_calls=0,bound_steps=0))
           for i,name in enumerate(('saved','failed','lost','unstarted'))]
    manifest=dict(tasks=tasks,allocation=dict(workers=2,threads=1),
                  environment=dict(python='frozen'))
    merged=dict(total=4,completed=2,charged_identities=3,
                results=[dict(identity='saved',status='complete',passed=True),
                         dict(identity='failed',status='complete',passed=False)])
    advice=dict(state='uncharged_work_available',evidence_scope='recovery_metadata_only',
                manifest_sha256='c'*64,charged_identities=3,
                interrupted_identities=['lost'],uncharged_tasks=['unstarted'],
                uninterrupted_cohort_required=False,resume_authorized=False)
    return manifest,merged,advice


def test_preserves_both_completed_outcomes_and_all_charges():
    plan=plan_incomplete_parent(*_parent())
    assert plan['version']=='lll-task-continuation-plan-v1'
    assert plan['completed']==2
    assert plan['completed_failures']==1
    assert plan['prior_interrupted_identities']==['lost']
    assert plan['never_started']==1
    assert [row['identity'] for row in plan['tasks']]==['lost','unstarted']


@pytest.mark.parametrize('state',('owned','closed','stop_requested'))
def test_rejects_parent_that_cannot_be_recovered(state):
    manifest,merged,advice=_parent();advice['state']=state
    with pytest.raises(ValueError,match='verified incomplete'):
        plan_incomplete_parent(manifest,merged,advice)


def test_rejects_missing_or_relabelled_completed_outcome():
    manifest,merged,advice=_parent()
    merged['results'].pop()
    with pytest.raises(ValueError):
        plan_incomplete_parent(manifest,merged,advice)


def test_terminal_parent_uses_only_sealed_interruptions_and_unstarted_tasks():
    manifest,merged,_=_parent()
    merged['results'].append(dict(identity='lost',status='interrupted',passed=False))
    merged['completed']=3
    completion=dict(state='terminal',manifest_sha256='c'*64)
    plan=plan_closed_parent(manifest,merged,completion)
    assert plan['completed']==2
    assert plan['completed_failures']==1
    assert plan['prior_interrupted_identities']==['lost']
    assert [row['identity'] for row in plan['tasks']]==['lost','unstarted']
    merged['charged_identities']=4
    with pytest.raises(ValueError,match='sealed charges'):
        plan_closed_parent(manifest,merged,completion)
