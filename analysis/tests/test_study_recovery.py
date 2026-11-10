# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only recovery controls; no measurements, optimizer or native calls."""
import fcntl
import hashlib
import importlib.util
import json
from pathlib import Path
import time
from contextlib import contextmanager

import pytest

from lll import ilvis0_control_shards as runner


def fixture(tmp_path,*,uninterrupted=None,role='calibration'):
    project=tmp_path/'project';project.mkdir()
    (project/'adapter.py').write_text('# metadata control\n')
    script=project/runner.RUNNER;script.parent.mkdir(parents=True)
    script.write_text('# metadata runner control\n')
    recipe=dict(role=role,seeds=[7],order_statistic_rank=1)
    if uninterrupted is not None:recipe['require_uninterrupted_cohort']=uninterrupted
    (project/'recipe.json').write_text(json.dumps(recipe))
    tasks=[]
    for model in ('flat_still','sphere_still'):
        for start in (0,1):
            tasks.append(dict(identity=f'{model}-{start}',input_key='recipe',
                payload=dict(role=role,draw_seed=7,population_sha256='a'*64,
                    case=dict(model=model,law='increment',profile=False,start=start)),
                limits=dict(native_calls=2,packet_visits=6,bound_calls=0,bound_steps=0)))
    output=project/'data/control'
    runner.prepare(output,project_root=project,tasks=tasks,sources=['adapter.py',runner.RUNNER],
        inputs={'recipe':'recipe.json'},adapter='adapter.py',workers=2,threads=1,
        maximum_wall_s=60,environment=runner.runtime_environment(),accounting_format='sqlite-v1')
    return project,output


def inspect(project):
    from lll.studies.recovery import inspect
    return inspect(project,'data/control')


def start(output,identity):
    task=next(t for t in runner.verify(output)['tasks'] if t['identity']==identity)
    return runner.TaskContext(output,task['shard'],identity)


def fingerprint(root):
    return {str(p.relative_to(root)):(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns)
            for p in root.rglob('*') if p.is_file()}


def test_missing_process_handle_does_not_lose_charges_or_authorize_retry(tmp_path):
    project,output=fixture(tmp_path)
    start(output,'flat_still-0').charge(native_calls=1,packet_visits=3)
    before=fingerprint(project)
    report=inspect(project)
    assert report['state']=='uncharged_work_available'
    assert report['charged_identities']==1 and report['uncharged_identities']==3
    assert report['unavailable_identities']==['flat_still-0']
    assert 'flat_still-0' not in report['uncharged_tasks']
    assert report['resume_authorized'] is False and report['new_starts']==0
    assert report['new_native_calls']==0 and fingerprint(project)==before


def test_split_shard_lost_start_pair_prevents_futile_calibration_resume(tmp_path):
    project,output=fixture(tmp_path)
    start(output,'flat_still-0');start(output,'flat_still-1')
    before=fingerprint(project);report=inspect(project)
    assert report['state']=='cohort_unavailable'
    assert report['unavailable_calibration_settings']==[
        dict(seed=7,population_sha256='a'*64,
             case=dict(model='flat_still',law='increment',profile=False),
             identities=['flat_still-0','flat_still-1'])]
    assert report['uncharged_identities']==2 and fingerprint(project)==before


def test_one_usable_start_preserves_the_required_setting(tmp_path):
    project,output=fixture(tmp_path)
    start(output,'flat_still-0')
    start(output,'flat_still-1').finish(dict(passed=True,converged=True,scientific_decision='abstain'))
    report=inspect(project)
    assert report['state']=='uncharged_work_available'
    assert report['unavailable_calibration_settings']==[]


def test_interrupted_and_failed_sealed_results_are_unavailable(tmp_path):
    project,output=fixture(tmp_path)
    start(output,'flat_still-0');runner.mark_interrupted(output,0,'flat_still-0')
    start(output,'flat_still-1').finish(dict(passed=False,converged=False,scientific_decision='abstain'))
    assert inspect(project)['state']=='cohort_unavailable'


@pytest.mark.parametrize('lease',['coordinator.lock','shards/001/worker.lock'])
def test_held_lease_blocks_inspection_without_claiming_process_identity(tmp_path,lease):
    project,output=fixture(tmp_path);path=output/lease
    if not path.exists():path.write_bytes(b'')
    with path.open('rb') as held:
        fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
        before=fingerprint(project);report=inspect(project)
        assert report['state']=='owned' and report['owned_lease']==lease
        assert report['resume_authorized'] is False and fingerprint(project)==before


def test_closed_study_stays_closed_after_frozen_sources_are_compacted(tmp_path):
    project,output=fixture(tmp_path)
    start(output,'flat_still-0')
    runner._finish_study(output,runner.verify(output))
    for name in ('adapter.py',runner.RUNNER):(output/'source-freeze'/name).unlink()
    before=fingerprint(project);report=inspect(project)
    assert report['state']=='closed' and report['terminal_state']=='terminal'
    assert report['resume_authorized'] is False and fingerprint(project)==before


def test_fully_archived_completion_is_checked_without_restoring_files(tmp_path):
    from lll.studies.artifacts import ArchiveStore
    project,output=fixture(tmp_path);start(output,'flat_still-0')
    runner._finish_study(output,runner.verify(output))
    store=ArchiveStore(project)
    try:
        names=[str(p.relative_to(project)) for p in output.rglob('*') if p.is_file()]
        store.pack(names);store.compact(names=names)
    finally:store.close()
    before=fingerprint(project);report=inspect(project)
    assert report['state']=='closed' and report['charged_identities']==1
    assert not (output/'completion.json').exists() and fingerprint(project)==before


def test_symlinked_journal_is_not_followed(tmp_path):
    project,output=fixture(tmp_path);start(output,'flat_still-0')
    journal=output/'shards/000/charges/journal.sqlite'
    target=project/'journal-copy.sqlite';target.write_bytes(journal.read_bytes())
    journal.unlink();journal.symlink_to(target)
    with pytest.raises(ValueError):inspect(project)


@pytest.mark.parametrize('changed',['completion','source','input','current_source','journal','result','deadline'])
def test_mismatched_evidence_never_recommends_continuation(tmp_path,changed):
    project,output=fixture(tmp_path)
    context=start(output,'flat_still-0')
    if changed=='completion':
        runner._finish_study(output,runner.verify(output))
        path=output/'summary.json';value=json.loads(path.read_bytes());value['completed']=0
        path.write_text(json.dumps(value))
    elif changed=='source':(output/'source-freeze/adapter.py').write_text('changed')
    elif changed=='input':(output/'inputs/0000.json').write_text('changed')
    elif changed=='current_source':(project/'adapter.py').write_text('changed')
    elif changed=='journal':(output/'shards/000/charges/journal.sqlite').write_bytes(b'not a database')
    elif changed=='result':
        context.finish(dict(passed=True,converged=True,scientific_decision='abstain'))
        path=output/'shards/000/results/flat_still-0.json';value=json.loads(path.read_bytes())
        value['status']='interrupted';path.write_text(json.dumps(value))
    else:
        path=output/'start.json';value=json.loads(path.read_bytes());value['deadline_unix']+=60
        path.write_text(json.dumps(value))
    before=fingerprint(project)
    with pytest.raises(ValueError):inspect(project)
    assert fingerprint(project)==before


def test_original_deadline_and_stop_request_block_new_work(tmp_path,monkeypatch):
    project,output=fixture(tmp_path);start(output,'flat_still-0')
    deadline=json.loads((output/'start.json').read_bytes())['deadline_unix']
    with monkeypatch.context() as clock:
        clock.setattr(time,'time',lambda:deadline+1)
        report=inspect(project)
    assert report['state']=='deadline_exhausted' and report['deadline_unix']==deadline
    runner._request_stop(output,'declared stop')
    assert inspect(project)['state']=='stop_requested'


def test_unstarted_study_does_not_create_clock_or_empty_journals(tmp_path):
    project,output=fixture(tmp_path);before=fingerprint(project);report=inspect(project)
    assert report['state']=='uncharged_work_available' and report['charged_identities']==0
    assert report['deadline_unix'] is None and fingerprint(project)==before


def test_recovery_is_available_through_the_canonical_status_command(tmp_path,monkeypatch,capsys):
    project,_=fixture(tmp_path)
    spec=importlib.util.spec_from_file_location('recovery_status',Path(__file__).parents[1]/'status.py')
    status=importlib.util.module_from_spec(spec);spec.loader.exec_module(status)
    monkeypatch.setattr(status,'ROOT',project)
    monkeypatch.setattr('sys.argv',['status.py','--study','data/control','--recovery','--json'])
    assert status.main()==0
    value=json.loads(capsys.readouterr().out)
    assert value['studies'][0]['recovery']['state']=='uncharged_work_available'


def test_completion_during_lock_acquisition_takes_precedence(tmp_path,monkeypatch):
    project,output=fixture(tmp_path);start(output,'flat_still-0')
    (output/'coordinator.lock').write_bytes(b'');lease=runner._lease
    @contextmanager
    def finishing(path,exclusive):
        if path==output/'coordinator.lock':runner._finish_study(output,runner.verify(output))
        with lease(path,exclusive) as held:yield held
    monkeypatch.setattr(runner,'_lease',finishing)
    assert inspect(project)['state']=='closed'


def test_shard_done_record_does_not_make_its_uncharged_tasks_runnable(tmp_path):
    project,output=fixture(tmp_path)
    runner._write(output/'shards/000/done.json',dict(manifest_sha256=runner._sha(output/'manifest.json'),shard=0))
    report=inspect(project)
    assert report['uncharged_identities']==4
    assert report['uncharged_tasks']==['flat_still-1','sphere_still-1']


def test_corrupt_journal_index_is_rejected_without_repair(tmp_path):
    import sqlite3
    project,output=fixture(tmp_path);start(output,'flat_still-0')
    with sqlite3.connect(output/'shards/000/charges/journal.sqlite') as db:
        db.execute('DELETE FROM starts')
    before=fingerprint(project)
    with pytest.raises(ValueError,match='index'):inspect(project)
    assert fingerprint(project)==before


def test_incomplete_transaction_blocks_without_charging_or_removing_it(tmp_path):
    project,output=fixture(tmp_path);start(output,'flat_still-0')
    (output/'shards/000/charges/.pending-control').write_bytes(b'preserve')
    before=fingerprint(project)
    with pytest.raises(ValueError,match='transaction'):inspect(project)
    assert fingerprint(project)==before


def test_wrong_shard_result_is_never_treated_as_an_available_start(tmp_path):
    project,output=fixture(tmp_path)
    start(output,'flat_still-0').finish(dict(passed=True,converged=True,scientific_decision='abstain'))
    source=output/'shards/000/results/flat_still-0.json'
    (output/'shards/001/results/flat_still-0.json').write_bytes(source.read_bytes())
    with pytest.raises(ValueError,match='wrong shard'):inspect(project)


def test_changed_environment_blocks_resume(tmp_path,monkeypatch):
    project,_=fixture(tmp_path)
    monkeypatch.setattr(runner,'runtime_environment',lambda:dict(python='different'))
    with pytest.raises(ValueError,match='environment'):inspect(project)


def test_calibration_futility_requires_the_frozen_maximum_order_policy(tmp_path):
    project,output=fixture(tmp_path)
    manifest=runner.verify(output)
    policy_path=output/manifest['inputs']['recipe']['path']
    policy=json.loads(policy_path.read_bytes());policy['order_statistic_rank']=0
    policy_path.write_text(json.dumps(policy))
    manifest['inputs']['recipe']['sha256']=runner._sha(policy_path)
    (output/'manifest.json').write_text(json.dumps(manifest))
    authorization=dict(manifest_sha256=runner._sha(output/'manifest.json'),limits=manifest['limits'])
    (output/'authorization.json').write_text(json.dumps(authorization))
    start(output,'flat_still-0');start(output,'flat_still-1')
    report=inspect(project)
    assert report['state']=='uncharged_work_available' and report['unavailable_calibration_settings']==[]
    assert report['cohort_check']=='not_maximum_order_calibration'


@pytest.mark.parametrize('role',['calibration','validation'])
def test_explicit_uninterrupted_policy_blocks_a_single_lost_start(tmp_path,role):
    project,output=fixture(tmp_path,uninterrupted=True,role=role)
    start(output,'flat_still-0')
    start(output,'flat_still-1').finish(dict(passed=True,converged=True,scientific_decision='abstain'))
    before=fingerprint(project);report=inspect(project)
    assert report['state']=='cohort_unavailable'
    assert report['interrupted_identities']==['flat_still-0']
    assert report['uninterrupted_cohort_required'] is True
    assert fingerprint(project)==before


def test_uninterrupted_policy_allows_completed_failed_start_with_usable_repeat(tmp_path):
    project,output=fixture(tmp_path,uninterrupted=True)
    start(output,'flat_still-0').finish(dict(passed=False,converged=False,scientific_decision='abstain'))
    start(output,'flat_still-1').finish(dict(passed=True,converged=True,scientific_decision='abstain'))
    report=inspect(project)
    assert report['state']=='uncharged_work_available' and report['interrupted_identities']==[]
