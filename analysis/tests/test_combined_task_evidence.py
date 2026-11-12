# SPDX-License-Identifier: AGPL-3.0-or-later
"""A recovery ledger must retain all completed outcomes and all attempts."""
import json
import time

import pytest

from lll import ilvis0_control_shards as runner
from lll.studies.combined_task_evidence import inspect
from lll.airquantumgrav_observed_hybrid_combined_audit import CombinedStudy
from lll.studies.artifacts import digest
from lll.studies.task_resume import resume_campaign
from test_task_resume import _toy


def test_combines_original_and_recovery_without_repeating_a_failed_result(
        tmp_path,monkeypatch):
    project,parent,output=_toy(tmp_path)
    with pytest.raises(ValueError,match='closed continuation'):
        inspect(project,output)
    monkeypatch.setattr('lll.studies.task_resume._other_threads',
                        lambda project,workers:0)
    def launch(stage,*,reserved_threads):
        assert reserved_threads==0
        manifest=runner.verify(stage);runner._begin(stage,manifest)
        (stage/'worker.lock').touch()
        for task in manifest['tasks']:
            assert task['identity'] not in ('saved','failed')
            runner.TaskContext(stage,task['shard'],task['identity']).finish(
                dict(passed=True,converged=True,scientific_decision='abstain'))
        return runner._finish_study(stage,manifest)
    monkeypatch.setattr(runner,'launch',launch)
    assert resume_campaign(project,output)['state']=='all_tasks_finished'
    report=inspect(project,output)
    assert report['verified'] is True
    assert report['total']==report['completed']==4
    assert report['passing']==3
    assert report['completed_failures']==1
    assert report['technical_interruptions']==1
    assert set(report['selected'])=={'saved','failed','lost','unstarted'}
    assert report['selected']['failed']['origin']=='data/parent'
    assert len(report['attempts'])==5
    view=CombinedStudy(project,report)
    try:
        assert len({id(study.store) for study in view.studies.values()})==1
        assert len({id(study.catalog) for study in view.studies.values()})==1
        assert set(view.tasks)==set(view.rows)
        assert view.origin_manifest('saved')['scope']=='toy recovery check'
        assert view.origin_manifest('lost')['scope']=='toy recovery check'
        assert view.envelope('failed')['result']['passed'] is False
        assert view.summary['charged']['native_calls']==0
        stage_manifest=(output/'stage-000/manifest.json').read_bytes()
        assert view.read_artifact('lost','manifest.json',
                                  digest(stage_manifest),raw=True)==stage_manifest
    finally:
        view.close()
    receipt=output/'completion.json'
    changed=json.loads(receipt.read_bytes());changed['completed_failures']=0
    receipt.write_text(json.dumps(changed))
    with pytest.raises(ValueError,match='completion receipt'):
        inspect(project,output)


def test_expired_continuation_reports_unfinished_identities_without_rerunning(
        tmp_path,monkeypatch):
    project,_,output=_toy(tmp_path)
    frozen_now=time.time()
    monkeypatch.setattr(time,'time',lambda:frozen_now+7200)
    report=inspect(project,output)
    assert report['state']=='terminal_incomplete'
    assert report['terminal_reason']=='deadline_exhausted'
    assert report['completed']==2
    assert report['passing']==1
    assert report['pending_identities']==['lost','unstarted']
    assert report['campaign_completion_sha256'] is None
    assert len(report['attempts'])==3
    view=CombinedStudy(project,report)
    try:
        assert set(view.tasks)=={'saved','failed','lost','unstarted'}
        assert set(view.rows)=={'saved','failed'}
    finally:
        view.close()


def test_attempt_cap_reports_terminal_failure_with_every_charge(tmp_path,monkeypatch):
    project,_,output=_toy(tmp_path)
    monkeypatch.setattr('lll.studies.task_resume._other_threads',
                        lambda project,workers:0)
    def interrupt(stage,*,reserved_threads):
        assert reserved_threads==0
        manifest=runner.verify(stage);runner._begin(stage,manifest)
        for task in manifest['tasks']:
            runner.TaskContext(stage,task['shard'],task['identity']).charge(
                native_calls=1,packet_visits=1)
        return runner._finish_study(stage,manifest)
    monkeypatch.setattr(runner,'launch',interrupt)
    with pytest.raises(ValueError,match='per-task technical recovery allowance'):
        resume_campaign(project,output)
    report=inspect(project,output)
    assert report['state']=='terminal_incomplete'
    assert report['terminal_reason']=='per-task technical recovery allowance exhausted'
    assert report['completed']==2
    assert report['pending_identities']==['lost','unstarted']
    assert report['technical_interruptions']==3
    assert len(report['attempts'])==5
    assert report['campaign_completion_sha256'] is None
