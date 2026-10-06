# SPDX-License-Identifier: AGPL-3.0-or-later
"""Durability/concurrency fixtures only: no synthesize, flight fitting or campaign evidence."""
import base64
import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from lll import campaign_shards as runner
from lll.research_design import freeze_manifest, implementation_hash
from lll.research_calibration import validate_records
from test_candidate_eligibility import candidate_fit


@pytest.fixture(autouse=True)
def single_thread_environment(monkeypatch):
    for key in runner.THREAD_KEYS: monkeypatch.setenv(key,'1')


def plan(shards=2,seeds=2):
    config=dict(partition='development',seed=600800,seeds=seeds,truth='all',scenario='wind',
                variant='spp',geometry='fixed',bootstrap=0,flight_domain=None,
                preregistered_scenarios=['wind','wind+bias_mixed'],preregistered_geometry_cells=[None],
                decision_policy_hash=None,pairwise_decision_policy_hash=None)
    jobs=[dict(n_boot=0,bootstrap_sampling='moving',block_length=15,research_candidate=True)]
    return runner.build_plan(freeze_manifest(config),jobs,shards)


def fake_record(p,task,diagnostics):
    row=runner.failure_record(p,task,'fixture')
    row.pop('failure'); row.pop('infrastructure_failure')
    row.update(candidate_fit(),rejected=False,exclusions=[],elapsed_s=.01,runtime_unknown=False)
    # Seed-based, order-independent outcome to compare serial and sharded execution.
    row['fixture_value']=runner.digest({'seed':task['seed'],'truth':task['truth'],'scenario':task['scenario']})
    return row


def test_plan_ids_and_grid_do_not_depend_on_worker_or_shard_count():
    a,b=plan(2),plan(4)
    assert a['task_count']==12
    tasks=[runner.task_at(a,i) for i in range(12)]
    assert len({t['task_id'] for t in tasks})==12
    assert tasks==[runner.task_at(b,i) for i in range(12)]
    assert {t['seed'] for t in tasks}=={600800,600801}
    assert all(t['seed']==600800 for t in tasks[:6])
    assert a['manifest']['config']['candidate_jobs']==a['jobs']
    assert a['manifest']['config']['campaign_execution_version']==runner.VERSION
    runner.check_plan(json.loads(json.dumps(a)))
    bad=copy.deepcopy(a); bad['jobs'][0]['n_boot']=1
    with pytest.raises(ValueError,match='hash'): runner.check_plan(bad)
    with pytest.raises(ValueError,match='outside'): runner.task_at(a,12)


def test_shard_resume_keeps_successes_and_failures_and_merge_order(tmp_path):
    p=plan(); runner.bind_output(tmp_path,p); seen=[]
    def execute(p,task,diagnostics):
        seen.append(task['index'])
        if task['index']==2: raise RuntimeError('fixture failure')
        return fake_record(p,task,diagnostics)
    for shard in [1,0]: runner.run_shard(tmp_path,p,shard,12,execute)
    assert set(seen)==set(range(12))
    for shard in [0,1]: runner.run_shard(tmp_path,p,shard,12,lambda *a:pytest.fail('repeated attempt'))
    result=runner.merge_campaign(tmp_path,p)
    assert result['complete'] and result['analysis_failures']==1
    rows=json.loads((tmp_path/'campaign.json').read_text())['records']
    assert [r['task_index'] for r in rows]==list(range(12))
    assert rows[2]['failure']=='executor failed: RuntimeError(\'fixture failure\')'
    expected=[fake_record(p,runner.task_at(p,i),None)['fixture_value'] for i in range(12) if i!=2]
    assert [r['fixture_value'] for r in rows if not r.get('failure')]==expected
    before=[(tmp_path/f'shard-{s:03d}.jsonl').read_bytes() for s in range(2)]
    runner.merge_campaign(tmp_path,p)
    assert before==[(tmp_path/f'shard-{s:03d}.jsonl').read_bytes() for s in range(2)]


def test_process_loss_after_start_is_preserved_as_failure_not_repeated(tmp_path):
    p=plan(); runner.bind_output(tmp_path,p)
    def interrupted(*args): raise KeyboardInterrupt('lost process')
    with pytest.raises(KeyboardInterrupt): runner.run_shard(tmp_path,p,0,12,interrupted)
    with pytest.raises(ValueError,match='unfinished'): runner.merge_campaign(tmp_path,p,allow_partial=True)
    seen=[]
    def resumed(p,task,path): seen.append(task['index']); return fake_record(p,task,path)
    runner.run_shard(tmp_path,p,0,12,resumed)
    assert 0 not in seen and set(seen)=={2,4,6,8,10}
    runner.run_shard(tmp_path,p,1,12,fake_record)
    runner.merge_campaign(tmp_path,p)
    first=json.loads((tmp_path/'campaign.json').read_text())['records'][0]
    assert first['infrastructure_failure'] and 'outcome unavailable' in first['failure']
    assert first['elapsed_s'] is None and first['runtime_unknown']
    assert json.loads((tmp_path/'merge-status.json').read_text())['runtime_unknown_attempts']==1


def test_truncated_tail_is_preserved_before_repair_and_no_started_task_rerun(tmp_path):
    p=plan(); runner.bind_output(tmp_path,p)
    task=runner.task_at(p,0); journal=tmp_path/'shard-000.jsonl'
    runner.append_event(journal,p,0,task,'start',None)
    tail=b'{"kind":"complete","record":'
    with journal.open('ab') as out: out.write(tail)
    with pytest.raises(ValueError,match='truncated'): list(runner.journal_events(journal,p,0))
    seen=[]
    def resumed(p,t,path): seen.append(t['index']); return fake_record(p,t,path)
    runner.run_shard(tmp_path,p,0,12,resumed)
    assert 0 not in seen
    recovery=json.loads(journal.with_suffix('.recovery.jsonl').read_text())
    assert base64.b64decode(recovery['discarded_base64'])==tail
    events=list(runner.journal_events(journal,p,0))
    assert events[1]['record']['infrastructure_failure']


def test_complete_corruption_and_wrong_shard_are_rejected(tmp_path):
    p=plan(); runner.bind_output(tmp_path,p)
    journal=tmp_path/'shard-000.jsonl'
    runner.run_shard(tmp_path,p,0,12,fake_record)
    saved=journal.read_bytes()
    with journal.open('ab') as out: out.write(b'{broken}\n')
    with pytest.raises(ValueError,match='malformed complete'): runner.run_shard(tmp_path,p,0,12,fake_record)
    assert journal.read_bytes()==saved+b'{broken}\n'
    (tmp_path/'shard-001.jsonl').write_bytes(saved)
    with pytest.raises(ValueError,match='shard mismatch'): list(runner.journal_events(tmp_path/'shard-001.jsonl',p,1))


def test_hash_consistent_but_wrong_result_provenance_is_rejected(tmp_path):
    p=plan(); runner.bind_output(tmp_path,p); journal=tmp_path/'shard-000.jsonl'
    task=runner.task_at(p,0)
    previous=runner.append_event(journal,p,0,task,'start',None)
    row=fake_record(p,task,None); row['seed']+=1
    runner.append_event(journal,p,0,task,'complete',previous,row)
    with pytest.raises(ValueError,match='provenance'): list(runner.journal_events(journal,p,0))


def test_source_drift_stops_before_result_is_committed(tmp_path,monkeypatch):
    p=plan(); runner.bind_output(tmp_path,p)
    original=implementation_hash(); drift=[False]
    monkeypatch.setattr('lll.research_design.implementation_hash',lambda:'changed' if drift[0] else original)
    def execute(p,t,path): drift[0]=True; return fake_record(p,t,path)
    with pytest.raises(ValueError,match='frozen manifest'): runner.run_shard(tmp_path,p,0,12,execute)
    assert len((tmp_path/'shard-000.jsonl').read_text().splitlines())==1
    drift[0]=False
    runner.run_shard(tmp_path,p,0,12,fake_record)
    assert list(runner.journal_events(tmp_path/'shard-000.jsonl',p,0))[1]['record']['infrastructure_failure']


def test_partial_budget_cannot_become_holdout_evidence_or_discard_spent_attempts(tmp_path):
    p=plan(); runner.bind_output(tmp_path,p)
    for shard in [0,1]: runner.run_shard(tmp_path,p,shard,4,fake_record)
    with pytest.raises(ValueError,match='incomplete'): runner.merge_campaign(tmp_path,p)
    result=runner.merge_campaign(tmp_path,p,allow_partial=True)
    assert result['completed']==4 and not result['complete'] and result['contiguous_prefix']
    data=json.loads((tmp_path/'campaign.json').read_text())
    with pytest.raises(ValueError,match='incomplete sharded'): validate_records(data,'calibration')
    with pytest.raises(ValueError,match='drop previously started'): runner.run_shard(tmp_path,p,1,1,fake_record)
    for shard in [0,1]: runner.run_shard(tmp_path,p,shard,12,fake_record)
    assert runner.merge_campaign(tmp_path,p)['complete']


def test_locks_reject_duplicate_workers_and_live_merge(tmp_path):
    p=plan(); runner.bind_output(tmp_path,p)
    with runner.lock(tmp_path/'shard-000.lock'):
        with pytest.raises(RuntimeError,match='active'): runner.run_shard(tmp_path,p,0,12,fake_record)
        with pytest.raises(RuntimeError,match='active'): runner.merge_campaign(tmp_path,p,True)
    with runner.lock(tmp_path/'coordinator.lock'):
        with pytest.raises(RuntimeError,match='active'): runner.run_local(tmp_path,p,12)
        with pytest.raises(RuntimeError,match='active'): runner.merge_campaign(tmp_path,p,True)


def test_local_coordinator_caps_concurrency_and_passes_one_thread_environment(tmp_path,monkeypatch):
    p=plan(4); active=[0]; peak=[0]; launches=[]
    monkeypatch.setattr(runner.time,'sleep',lambda _:None)
    class Process:
        def __init__(self,command,env,**kwargs):
            active[0]+=1; peak[0]=max(peak[0],active[0]); self.polls=0
            assert all(env[k]=='1' for k in runner.THREAD_KEYS)
            assert command[0]==sys.executable
            self.shard=int(command[command.index('--shard')+1]); launches.append(self.shard)
        def poll(self):
            self.polls+=1
            if self.polls<2: return None
            if self.polls==2:
                runner.run_shard(tmp_path,p,self.shard,12,fake_record); active[0]-=1
            return 0
    assert runner.run_local(tmp_path,p,12,workers=2,launcher=Process)['complete']
    assert peak[0]==2 and launches==[0,1,2,3]
    with pytest.raises(ValueError,match='one or two'): runner.run_local(tmp_path,p,12,workers=3)


def test_prepare_cli_freezes_only_and_numerical_threads_are_required(tmp_path,monkeypatch):
    import research
    target=tmp_path/'plan.json'
    monkeypatch.setattr(research,'flight_run',lambda *a,**k:pytest.fail('preparation ran a flight'))
    monkeypatch.setattr(sys,'argv',['research.py','--truth','all','--seeds','2','--seed','600800',
        '--geometry','fixed','--scenario','wind','--bootstrap','0','--write-sharded-plan',str(target),
        '--shards','4','-o',str(tmp_path/'unused.json')])
    research.main()
    p=json.loads(target.read_text()); runner.check_plan(p)
    assert p['task_count']==6 and p['shards']==4
    assert not (tmp_path/'unused.json').exists()
    monkeypatch.setenv('OPENBLAS_NUM_THREADS','2')
    with pytest.raises(ValueError,match='before numerical imports'): runner.check_plan(p)


def test_entry_point_initializes_environment_before_loading_scientific_modules(tmp_path):
    # A fresh interpreter imports the entry point (which does not start its CLI),
    # then the numerical runtime. No simulator or flight fit is invoked.
    from pathlib import Path
    entry=Path(__file__).with_name('sharded_campaign.py')
    script='import runpy,os,sys; runpy.run_path(sys.argv[1],run_name="fixture"); from lll.runtime import numerical_environment; import json; print(json.dumps(numerical_environment()["thread_settings"]))'
    result=subprocess.run([sys.executable,'-c',script,str(entry)],capture_output=True,text=True,timeout=20,
                          env={**runner.os.environ,**dict.fromkeys(runner.THREAD_KEYS,'2')})
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)==dict.fromkeys(runner.THREAD_KEYS,'1')


def test_two_actual_processes_write_and_merge_only_fixture_records(tmp_path):
    p=plan()
    original=runner.subprocess.Popen
    def launch(command,**kwargs):
        shard=command[command.index('--shard')+1]
        script=('import json,sys; from pathlib import Path; '
                'sys.path[:0]=[sys.argv[4],str(Path(sys.argv[4]).parent)]; '
                'from lll.campaign_shards import run_shard; '
                'from test_campaign_shards import fake_record; '
                'p=json.loads(Path(sys.argv[1]).read_text()); '
                'run_shard(Path(sys.argv[2]),p,int(sys.argv[3]),12,executor=fake_record)')
        return original([sys.executable,'-c',script,str(tmp_path/'plan.json'),str(tmp_path),shard,
                         str(Path(__file__).resolve().parent)],**kwargs)
    result=runner.run_local(tmp_path,p,12,workers=2,launcher=launch)
    assert result['complete'] and result['completed']==12
    records=json.loads((tmp_path/'campaign.json').read_text())['records']
    assert all('fixture_value' in r for r in records)


def test_real_task_adapter_forwards_the_existing_pipeline_without_running_it(tmp_path,monkeypatch):
    import research
    p=plan(); task=runner.task_at(p,3); seen=[]
    def spy(*args,**kwargs): seen.append((args,kwargs)); return {'adapter_fixture':True}
    monkeypatch.setattr(research,'flight_run',spy)
    assert runner.execute_task(p,task,tmp_path)['adapter_fixture']
    args,options=seen[0]
    assert args[:3]==(task['truth'],task['scenario'],task['seed'])
    assert args[3:6]==('moving',15,0)
    assert options['partition']=='development' and options['geometry']=='fixed'
    assert options['fit_options']=={'research_candidate':True}
    assert options['design']['seed']==task['seed'] and options['design']['scenario']==task['scenario']
    assert options['diagnostics_directory']==tmp_path


def test_detached_launch_waits_for_ready_coordinator_without_starting_one(tmp_path,monkeypatch):
    p=plan()
    class Process:
        pid=12345
        def __init__(self,command,**kwargs):
            assert kwargs['start_new_session'] and all(kwargs['env'][k]=='1' for k in runner.THREAD_KEYS)
            assert '--detach' not in command and '--attempt-limit' in command
            # A child must be able to acquire the coordinator lock during startup.
            with runner.lock(tmp_path/'coordinator.lock'):
                runner.atomic_json(tmp_path/'status.json',dict(pid=self.pid,plan_hash=p['plan_hash'],state='running'))
        def poll(self): return None
    monkeypatch.setattr(runner.subprocess,'Popen',Process)
    launch=runner.detach_local(tmp_path,p,4)
    assert launch['pid']==12345 and launch['attempt_limit']==4
    assert json.loads((tmp_path/'launch.json').read_text())==launch


def test_orphaned_workers_are_detected_before_new_process_launch(tmp_path):
    p=plan(); runner.bind_output(tmp_path,p)
    with runner.lock(tmp_path/'shard-001.lock'):
        with pytest.raises(RuntimeError,match='active'):
            runner.run_local(tmp_path,p,12,launcher=lambda *a,**k:pytest.fail('spawned alongside orphan'))
