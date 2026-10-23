# SPDX-License-Identifier: AGPL-3.0-or-later
import fcntl
import hashlib
import json
from pathlib import Path

import pytest


def module():
    import importlib.util
    path=Path(__file__).resolve().parents[1]/'status.py'
    assert path.exists(), 'reusable status command is missing'
    spec=importlib.util.spec_from_file_location('study_status',path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value))


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def setup(tmp_path):
    study=tmp_path/'data/study';study.mkdir(parents=True)
    put(study/'manifest.json',dict(plan=dict(tasks=[dict(identity='a')],maximum_native_evaluations=3,numerical_threads=4)))
    put(study/'status.json',dict(state='working',completed=0,total=1,allocated_numerical_threads=4,pid=123))
    return study


def test_lock_overrides_untrusted_running_snapshot_without_writing(tmp_path):
    study=setup(tmp_path);before={p:p.read_bytes() for p in study.iterdir()}
    report=module().inspect_study(study)
    assert report['state']=='incomplete' and report['threads']==0
    assert report['lock']=='missing'
    assert {p:p.read_bytes() for p in study.iterdir()}==before


def test_hashed_summary_can_supply_completion_state(tmp_path):
    study=setup(tmp_path)
    put(study/'summary.json',dict(state='complete',native_evaluations=0,results=[dict(identity='a',passed=True)]))
    put(study/'completion.json',dict(manifest_sha256=digest(study/'manifest.json'),summary_sha256=digest(study/'summary.json')))
    report=module().inspect_study(study)
    assert report['state']=='complete' and report['passed']==1 and report['native_calls']==0


def test_sealed_cooperative_terminal_is_not_misreported_as_corruption(tmp_path):
    study=setup(tmp_path)
    put(study/'summary.json',dict(state='terminal',terminal_reason='cooperative wall allowance exhausted',
        results=[dict(identity='a',passed=False)],native_evaluations=0))
    put(study/'completion.json',dict(state='terminal',manifest_sha256=digest(study/'manifest.json'),
        summary_sha256=digest(study/'summary.json')))
    report=module().inspect_study(study)
    assert report['state']=='terminal' and report['completed']==1 and report['passed']==0
    assert report['threads']==0 and report['native_calls']==0
    assert any('cooperative' in w for w in report['warnings'])


def test_terminal_state_requires_matching_sealed_summary(tmp_path):
    study=setup(tmp_path)
    put(study/'summary.json',dict(state='running',results=[]))
    put(study/'completion.json',dict(state='terminal',manifest_sha256=digest(study/'manifest.json'),
        summary_sha256=digest(study/'summary.json')))
    assert module().inspect_study(study)['state']=='invalid'


def test_historical_mapping_results_are_read_without_rewriting_evidence(tmp_path):
    study=setup(tmp_path)
    put(study/'summary.json',dict(state='complete',native_sweeps=12,results={
        'a':dict(converged=True), 'b':dict(converged=False)}))
    put(study/'completion.json',dict(state='complete',manifest_sha256=digest(study/'manifest.json'),
        summary_sha256=digest(study/'summary.json')))
    before=(study/'summary.json').read_bytes()
    report=module().inspect_study(study)
    assert report['state']=='complete' and report['completed']==2 and report['passed']==1
    assert report['native_calls']==12
    assert (study/'summary.json').read_bytes()==before


def test_malformed_result_mapping_is_invalid_instead_of_crashing(tmp_path):
    study=setup(tmp_path)
    put(study/'summary.json',dict(state='complete',results={'a':'broken'}))
    put(study/'completion.json',dict(state='complete',manifest_sha256=digest(study/'manifest.json'),
        summary_sha256=digest(study/'summary.json')))
    assert module().inspect_study(study)['state']=='invalid'


def test_completion_without_any_explicit_complete_state_is_rejected(tmp_path):
    study=setup(tmp_path)
    put(study/'summary.json',dict(state='running',results=[]))
    put(study/'completion.json',dict(manifest_sha256=digest(study/'manifest.json'),summary_sha256=digest(study/'summary.json')))
    assert module().inspect_study(study)['state']=='invalid'


def test_active_preflight_calls_are_included_before_any_fit_ledger(tmp_path):
    from lll.ilvis0_receipt_journal import Ledger
    study=setup(tmp_path);book=Ledger(study/'preflight',digest(study/'manifest.json'),['check'],fit_limit=1,diagnostic_limit=1)
    book.start('check');book.call('check','diagnostic','tangent',lambda:None)
    report=module().inspect_study(study)
    assert report['native_calls']==1 and report['preflight_identities']==1


def test_active_native_total_sums_separate_fit_and_preflight_ledgers(tmp_path):
    from lll.ilvis0_receipt_journal import Ledger
    study=setup(tmp_path);h=digest(study/'manifest.json')
    for path,identity in ((study,'fit'),(study/'preflight','check')):
        book=Ledger(path,h,[identity],fit_limit=1,diagnostic_limit=1)
        book.start(identity);book.call(identity,'diagnostic','tangent',lambda:None)
    report=module().inspect_study(study)
    assert report['native_calls']==2 and report['charged_identities']==1


def test_bound_report_prefix_is_progress_without_becoming_a_passing_case(tmp_path):
    from lll.studies.series import ReportStream
    study=setup(tmp_path);directory=study/'artifacts/a';directory.mkdir(parents=True)
    tasks=[dict(identity='a',payload=dict(recipe=dict(times_s=[2.,3.,4.]))),
           dict(identity='b',payload=dict(recipe=dict(times_s=[2.,3.,4.])))]
    put(directory/'series-binding.json',dict(binding='fixed',records=3,maximum_record_bytes=4096))
    with ReportStream(directory/'training-bounds.jsonl',binding='fixed',maximum_records=3,maximum_record_bytes=4096) as stream:
        stream.append(0,{'time_s':2.});stream.append(1,{'time_s':3.})
    before={p:p.read_bytes() for p in directory.iterdir()}
    result=module().series_snapshot(study,tasks)
    assert result['saved_reports']==2 and result['expected_reports']==6
    assert result['qualified_cases']==0 and result['provisional'] is True
    assert {p:p.read_bytes() for p in directory.iterdir()}==before


def test_bound_report_snapshot_rejects_corruption_or_truncation(tmp_path):
    from lll.studies.series import ReportStream
    study=setup(tmp_path);directory=study/'artifacts/a';directory.mkdir(parents=True)
    tasks=[dict(identity='a',payload=dict(recipe=dict(times_s=[2.,3.])))]
    put(directory/'series-binding.json',dict(binding='fixed',records=2,maximum_record_bytes=4096))
    path=directory/'training-bounds.jsonl'
    with ReportStream(path,binding='fixed',maximum_records=2,maximum_record_bytes=4096) as stream:
        stream.append(0,{'time_s':2.})
    path.write_bytes(path.read_bytes()[:-1]);raw=path.read_bytes()
    with pytest.raises(ValueError,match='truncated'):module().series_snapshot(study,tasks)
    assert path.read_bytes()==raw


def test_bound_report_snapshot_rejects_changed_query_order(tmp_path):
    from lll.studies.series import ReportStream
    study=setup(tmp_path);directory=study/'artifacts/a';directory.mkdir(parents=True)
    tasks=[dict(identity='a',payload=dict(recipe=dict(times_s=[2.,3.])))]
    put(directory/'series-binding.json',dict(binding='fixed',records=2,maximum_record_bytes=4096))
    with ReportStream(directory/'training-bounds.jsonl',binding='fixed',maximum_records=2,maximum_record_bytes=4096) as stream:
        stream.append(0,{'time_s':3.})
    with pytest.raises(ValueError,match='query'):module().series_snapshot(study,tasks)


def test_held_lock_reports_running_and_capped_allocation(tmp_path):
    study=setup(tmp_path)
    with (study/'worker.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        report=module().inspect_study(study)
    assert report['state']=='running' and report['threads']==4 and report['lock']=='held'


def test_qualification_schema_reports_active_threads_and_native_allowance(tmp_path):
    study=setup(tmp_path)
    put(study/'manifest.json',dict(limits=dict(numerical_threads=4,maximum_native_sweeps=2400),tests=['a','b']))
    put(study/'status.json',dict(state='running',numerical_threads=4))
    with (study/'worker.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        report=module().inspect_study(study)
    assert report['threads']==4 and report['total']==2 and report['native_limit']==2400


def test_worker_snapshot_does_not_replace_verified_result_counts(tmp_path):
    study=setup(tmp_path);status=module()
    put(study/'progress.json',dict(completed=1,passed=1,native_evaluations=2))
    with (study/'worker.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        report=status.inspect_study(study)
    assert report['completed']==0 and report['passed']==0
    assert report['worker_progress']==dict(completed=1,passed=1)
    assert 'Worker snapshot: 1/1 complete' in status.render(dict(report,name='test'))


def test_inconsistent_worker_snapshot_is_not_reported_as_progress(tmp_path):
    study=setup(tmp_path);put(study/'progress.json',dict(completed=2,passed=1))
    with (study/'worker.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        report=module().inspect_study(study)
    assert not report.get('worker_progress')
    assert any('progress' in message for message in report['warnings'])


def test_failed_qualification_counts_unrun_controls_separately(tmp_path):
    study=setup(tmp_path)
    put(study/'manifest.json',dict(limits=dict(numerical_threads=4,maximum_native_sweeps=2400),tests=['a','b','c']))
    put(study/'summary.json',dict(passed=False,tests=[dict(name='a',outcome='passed'),dict(name='b',outcome='failure')],
        unrun_tests=['c'],budget=dict(starts=1,native_sweeps=8)))
    put(study/'completion.json',dict(state='complete',manifest_sha256=digest(study/'manifest.json'),
        summary_sha256=digest(study/'summary.json')))
    report=module().inspect_study(study)
    assert report['state']=='complete' and report['completed']==2 and report['passed']==1 and report['errors']==1
    assert report['total']==3 and report['native_calls']==8 and report['charged_identities']==1
    assert any('not run' in warning for warning in report['warnings'])


def test_sealed_completion_overrides_stale_status_and_counts_failures(tmp_path):
    study=setup(tmp_path)
    put(study/'summary.json',dict(results=[dict(identity='a',status='error',conditional_converged=False,
        reason='invalid charge')],native_evaluations=2))
    put(study/'completion.json',dict(state='complete',manifest_sha256=digest(study/'manifest.json'),
        summary_sha256=digest(study/'summary.json')))
    report=module().inspect_study(study)
    assert report['state']=='complete' and report['completed']==1 and report['errors']==1
    assert report['native_calls']==2 and report['threads']==0


def test_verified_completed_total_includes_separately_charged_preflight(tmp_path,monkeypatch):
    study=setup(tmp_path);status=module()
    put(study/'summary.json',dict(results=[dict(identity='a',passed=True)],native_evaluations=3,
                                 preflight=[dict(identity='check',passed=True)]))
    put(study/'completion.json',dict(state='complete',manifest_sha256=digest(study/'manifest.json'),
                                    summary_sha256=digest(study/'summary.json')))
    monkeypatch.setattr(status,'receipt_counts',lambda *a:dict(starts=1,sweeps=2,incomplete_transaction=False))
    report=status.inspect_study(study)
    assert report['state']=='complete' and report['native_calls']==3
    assert report['charged_identities']==1


def test_altered_completion_is_never_reported_as_verified(tmp_path):
    study=setup(tmp_path)
    put(study/'completion.json',dict(state='complete',manifest_sha256='0'*64,summary_sha256='0'*64))
    report=module().inspect_study(study)
    assert report['state']=='invalid' and report['warnings']


def test_active_result_envelopes_and_receipts_supply_fresh_counts(tmp_path):
    study=setup(tmp_path);status=module();manifest_hash=digest(study/'manifest.json')
    result=dict(identity='a',status='complete',conditional_verified=True)
    result_hash=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    put(study/'a.json',dict(result=result,manifest_sha256=manifest_hash,result_sha256=result_hash))
    previous=None
    for number,kind in enumerate(('starts','sweeps','sweeps'),1):
        record=dict(identity='a',number=1 if kind=='starts' else number-1,manifest_sha256=manifest_hash)
        if kind=='sweeps':record.update(phase='diagnostic',kind='tangent')
        payload=dict(event_number=number,previous_sha256=previous,record_type=kind,record=record)
        previous=status.object_digest(payload)
        put(study/'charges'/f'{number:08d}.json',dict(payload=payload,sha256=previous))
    put(study/'charges/HEAD.json',dict(events=3,sha256=previous))
    report=status.inspect_study(study)
    assert report['completed']==1 and report['passed']==1 and report['native_calls']==2
    assert report['charged_identities']==1 and report['state']=='incomplete'


def test_corrupt_charge_snapshot_is_visible_and_never_repaired(tmp_path):
    study=setup(tmp_path);put(study/'charges/HEAD.json',dict(events=1,sha256='bad'))
    report=module().inspect_study(study)
    assert any('charge' in message for message in report['warnings'])
    assert not (study/'charges/00000001.json').exists()


def test_reading_busy_ledger_does_not_block_or_create_files(tmp_path):
    study=setup(tmp_path);charges=study/'charges';charges.mkdir()
    with (charges/'ledger.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        report=module().inspect_study(study)
    assert any('busy' in message for message in report['warnings'])
    assert not (charges/'HEAD.json').exists()


def test_registry_uses_only_named_paths_and_rejects_escape(tmp_path):
    status=module();setup(tmp_path)
    registry=tmp_path/'analysis/study-status.json'
    put(registry,dict(studies=[dict(name='Current check',path='data/study')]))
    assert status.read_registry(tmp_path,registry)==[('Current check',tmp_path/'data/study')]
    put(registry,dict(studies=[dict(name='Private',path='../outside')]))
    with pytest.raises(ValueError):status.read_registry(tmp_path,registry)


def test_missing_study_is_reported_without_creating_it(tmp_path):
    study=tmp_path/'data/absent'
    report=module().inspect_study(study)
    assert report['state']=='missing' and not study.exists()


def test_json_command_uses_registry_and_returns_a_readable_snapshot(tmp_path,monkeypatch,capsys):
    status=module();setup(tmp_path)
    put(tmp_path/'analysis/study-status.json',dict(studies=[dict(name='Test study',path='data/study')]))
    monkeypatch.setattr(status,'ROOT',tmp_path)
    monkeypatch.setattr(status.sys,'argv',['status.py','--json'])
    assert status.main()==0
    snapshot=json.loads(capsys.readouterr().out)
    assert snapshot['studies'][0]['name']=='Test study'
    assert snapshot['monitored_numerical_threads']==0


def test_incomplete_charge_transaction_blocks_status_even_with_valid_head(tmp_path):
    study=setup(tmp_path);put(study/'charges/HEAD.json',dict(events=0,sha256=None))
    pending=study/'charges/.pending-interrupted';pending.write_bytes(b'')
    report=module().inspect_study(study)
    assert any('incomplete charge transaction' in warning for warning in report['warnings'])
    assert pending.exists() and pending.read_bytes()==b''


def test_reserved_parent_lock_does_not_revive_an_interrupted_receipt_ledger(tmp_path):
    study=setup(tmp_path);put(study/'charges/HEAD.json',dict(events=0,sha256=None))
    (study/'charges/.pending-interrupted').write_bytes(b'')
    with (study/'worker.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        report=module().inspect_study(study)
    assert report['state']=='blocked' and report['threads']==0
