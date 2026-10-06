# SPDX-License-Identifier: AGPL-3.0-or-later
"""Deterministic, durable campaign execution. Imports no numerical libraries at startup."""
from contextlib import contextmanager, ExitStack
from datetime import datetime, timezone
import base64
import fcntl
import hashlib
import heapq
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

VERSION = 'sharded-flight-campaign-1'
THREAD_KEYS = ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def one_thread():
    if any(os.environ.get(k)!='1' for k in THREAD_KEYS):
        raise ValueError('sharded campaigns require all three numerical thread settings to be 1 before numerical imports')


def build_plan(manifest, jobs, shards=2, decision_policy=None, pairwise_policy=None):
    from .research_design import validate_manifest, seed_range, freeze_manifest
    one_thread()
    config=manifest['config']
    validate_manifest(manifest,config)
    if isinstance(shards,bool) or not isinstance(shards,int) or not 1<=shards<=128:
        raise ValueError('shard count must be between 1 and 128; local concurrency is separately capped at two')
    if config.get('scenario')=='pool' or config.get('replay'):
        raise ValueError('sharded runner supports fresh flight tasks, not summary pools or replays')
    if config['partition'] not in ('development','calibration','validation'):
        raise ValueError('invalid campaign partition')
    if not jobs or any(digest(j) in {digest(k) for k in jobs[:i]} for i,j in enumerate(jobs)):
        raise ValueError('empty or duplicate candidate jobs')
    if config.get('candidate_jobs',jobs)!=jobs or config.get('campaign_execution_version',VERSION)!=VERSION:
        raise ValueError('candidate jobs differ from the frozen execution configuration')
    # Explicit jobs are part of the scientific freeze, not just execution metadata.
    config={**config,'candidate_jobs':jobs,'campaign_execution_version':VERSION}
    manifest=freeze_manifest(config)
    seed_range(config['partition'],config['seed'],config['seeds'])
    truths=['sphere_rotating','sphere_still','flat_still'] if config['truth']=='all' else [config['truth']]
    if not set(truths)<={'sphere_rotating','sphere_still','flat_still'}: raise ValueError('unknown model truth')
    scenarios=list(config['preregistered_scenarios'])
    geometries=list(config['preregistered_geometry_cells'])
    if not scenarios or not geometries or len(set(scenarios))!=len(scenarios) or len(set(geometries))!=len(geometries):
        raise ValueError('task axes must be nonempty and unique')
    if config['partition']!='development' and (config.get('flight_domain') is None or config['truth']!='all'):
        raise ValueError('holdout campaigns require all truths and a frozen observable flight domain')
    if config['geometry']=='observed' and (config['partition']!='development' or decision_policy or pairwise_policy):
        raise ValueError('observed replay remains development only without empirical policies')
    from .flight_domain import resolve_domain
    domain=resolve_domain(config.get('flight_domain'),decision_policy,pairwise_policy)
    if domain!=config.get('flight_domain'): raise ValueError('campaign must freeze the decision flight domain explicitly')
    for job in jobs:
        if job.get('flight_domain')!=domain or job.get('n_boot')!=config['bootstrap']:
            raise ValueError('candidate job domain or bootstrap differs from frozen campaign')
        if job.get('magnetic_ambiguity')=='model_and_compare' and (config['partition']!='development' or decision_policy or pairwise_policy):
            raise ValueError('magnetic two-path candidate remains development only without empirical policies')
    for policy,key in ((decision_policy,'decision_policy_hash'),(pairwise_policy,'pairwise_decision_policy_hash')):
        if config.get(key)!=(policy or {}).get('policy_hash'): raise ValueError('decision files differ from campaign manifest')
    if decision_policy is not None:
        from .research_calibration import check_policy
        check_policy(decision_policy)
    if pairwise_policy is not None:
        from .pairwise import check_pairwise_policy
        check_pairwise_policy(pairwise_policy,'flight')
    if config['partition']=='validation' and not (decision_policy or pairwise_policy):
        raise ValueError('independent validation requires the frozen calibrated decision files')
    content=dict(version=VERSION,manifest=manifest,jobs=jobs,shards=shards,truths=truths,
                 scenarios=scenarios,geometry_cells=geometries,task_count=config['seeds']*len(truths)*len(scenarios)*len(jobs)*len(geometries),
                 decision_policy=decision_policy,pairwise_policy=pairwise_policy,
                 execution_policy=dict(max_local_workers=2,numerical_threads_per_worker=1,
                    interrupted_attempt='preserve as failure, never rerun',task_order='seed,truth,scenario,candidate,geometry',
                    evidence_use='partition unchanged; preparation grants no execution budget'))
    return {**content,'plan_hash':digest(content)}


def check_plan(plan):
    if plan.get('version')!=VERSION or digest({k:v for k,v in plan.items() if k!='plan_hash'})!=plan.get('plan_hash'):
        raise ValueError('sharded campaign plan hash or version mismatch')
    expected=build_plan(plan['manifest'],plan['jobs'],plan['shards'],plan.get('decision_policy'),plan.get('pairwise_policy'))
    if expected!=plan: raise ValueError('sharded campaign plan differs from frozen source, environment or task axes')


def task_at(plan,index):
    """Implicit grid: stable IDs without storing hundreds of thousands of designs."""
    if isinstance(index,bool) or not isinstance(index,int) or not 0<=index<plan['task_count']:
        raise ValueError('task index outside frozen campaign')
    remainder=index
    coordinates=[]
    for axis in (plan['geometry_cells'],plan['jobs'],plan['scenarios'],plan['truths']):
        remainder,position=divmod(remainder,len(axis)); coordinates.append(axis[position])
    cell,job,scenario,truth=coordinates
    config=plan['manifest']['config']
    task=dict(index=index,truth=truth,scenario=scenario,seed=config['seed']+remainder,geometry_cell=cell,
              fit_options=job,variant=config['variant'],partition=config['partition'],geometry=config['geometry'])
    return {**task,'task_id':digest({'manifest_hash':plan['manifest']['manifest_hash'],**task})}


def atomic_json(path,value):
    path=Path(path); temporary=path.with_suffix(path.suffix+'.tmp')
    with temporary.open('w') as out:
        json.dump(value,out,indent=2,allow_nan=False); out.write('\n'); out.flush(); os.fsync(out.fileno())
    os.replace(temporary,path)
    sync_directory(path.parent)


def sync_directory(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


@contextmanager
def lock(path):
    with Path(path).open('a') as handle:
        try: fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: raise RuntimeError('campaign or shard already active') from None
        yield


def bind_output(output,plan):
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    path=output/'plan.json'
    if path.exists():
        if json.loads(path.read_text())!=plan: raise ValueError('output belongs to a different frozen campaign')
    else:
        if any((output/f'shard-{s:03d}.jsonl').exists() for s in range(plan['shards'])):
            raise ValueError('cannot create a new plan over existing journals')
        atomic_json(path,plan)


def failure_record(plan,task,reason):
    from .runtime import numerical_environment, numerical_environment_hash
    options=task['fit_options']
    row={k:task[k] for k in ('truth','scenario','seed','variant','partition','geometry','geometry_cell','fit_options')}
    row.update(candidate_id=digest(options),sampling=options['bootstrap_sampling'],block=options['block_length'],
               numerical_environment=numerical_environment(),numerical_environment_hash=numerical_environment_hash(),
               failure=reason,infrastructure_failure=True,elapsed_s=None,runtime_unknown=True)
    return row


def check_record(plan,task,row):
    config=plan['manifest']['config']
    for key in ('truth','scenario','seed','variant','partition','geometry','geometry_cell','fit_options'):
        if row.get(key)!=task[key]: raise ValueError('journal result task provenance mismatch: '+key)
    if (row.get('replay') or row.get('candidate_id')!=digest(task['fit_options']) or
            row.get('sampling')!=task['fit_options']['bootstrap_sampling'] or row.get('block')!=task['fit_options']['block_length'] or
            row.get('numerical_environment')!=plan['manifest']['numerical_environment'] or
            row.get('numerical_environment_hash')!=plan['manifest']['numerical_environment_hash']):
        raise ValueError('journal result candidate, seed partition or numerical provenance mismatch')
    if not row.get('failure'):
        from .policy import eligibility_provenance, is_candidate
        settings=row.get('inference_policy',{}).get('settings',row.get('fit_options',{}))
        if row.get('eligibility_policy')!=eligibility_provenance(is_candidate(row),settings):
            raise ValueError('journal result eligibility policy mismatch')
        if config.get('flight_domain') is not None:
            from .flight_domain import check_record_domain
            check_record_domain(row,config['flight_domain'])
        if plan.get('decision_policy') and row.get('decision_policy_hash')!=plan['decision_policy']['policy_hash']:
            raise ValueError('journal result primary decision policy mismatch')
        if plan.get('pairwise_policy') and any(e.get('decision_policy_hash')!=plan['pairwise_policy']['policy_hash']
                                               for e in (row.get('pairwise') or {}).values()):
            raise ValueError('journal result pairwise decision policy mismatch')
    elapsed=row.get('elapsed_s')
    if row.get('runtime_unknown') is True:
        if elapsed is not None or not row.get('failure') or not row.get('infrastructure_failure'):
            raise ValueError('unknown runtime requires an interrupted infrastructure failure')
    elif isinstance(elapsed,bool) or not isinstance(elapsed,(int,float)) or not math.isfinite(elapsed) or elapsed<0:
        raise ValueError('invalid journal runtime')


def append_event(path,plan,shard,task,kind,previous,row=None):
    content=dict(version=VERSION,plan_hash=plan['plan_hash'],shard=shard,index=task['index'],
                 task_id=task['task_id'],kind=kind,previous_hash=previous)
    if row is not None: content['record']=row
    event={**content,'event_hash':digest(content)}
    path=Path(path); newly_created=not path.exists()
    with path.open('a') as out:
        out.write(json.dumps(event,separators=(',',':'),allow_nan=False)+'\n'); out.flush(); os.fsync(out.fileno())
    if newly_created: sync_directory(path.parent)
    return event['event_hash']


def journal_events(path,plan,shard,repair=False):
    """Completed events are immutable; repair preserves only an incomplete final write."""
    path=Path(path)
    if not path.exists(): return
    previous,active,last_index=None,None,shard-plan['shards']
    offset=0; needs_newline=False; damaged=None
    with path.open('rb') as source:
        for line in source:
            try: event=json.loads(line)
            except (ValueError,UnicodeDecodeError):
                if line.endswith(b'\n'): raise ValueError('malformed complete journal entry') from None
                damaged=line; break
            if (not isinstance(event,dict) or event.get('version')!=VERSION or event.get('plan_hash')!=plan['plan_hash'] or
                    event.get('shard')!=shard or event.get('previous_hash')!=previous or
                    digest({k:v for k,v in event.items() if k!='event_hash'})!=event.get('event_hash')):
                raise ValueError('journal hash chain, plan or shard mismatch')
            task=task_at(plan,event['index'])
            if task['index']%plan['shards']!=shard or event.get('task_id')!=task['task_id']:
                raise ValueError('journal task ID or shard assignment mismatch')
            if event['kind']=='start':
                if active is not None or task['index']!=last_index+plan['shards']:
                    raise ValueError('duplicate, missing or out-of-order journal task')
                active=task['index']
            elif event['kind']=='complete':
                if active!=task['index']: raise ValueError('completion without matching task start')
                check_record(plan,task,event['record']); active=None; last_index=task['index']
            else: raise ValueError('unknown journal event')
            previous=event['event_hash']; offset+=len(line); needs_newline=not line.endswith(b'\n')
            yield event
    if damaged is not None:
        if not repair: raise ValueError('truncated journal tail; resume its shard to preserve and repair it')
        recovery=path.with_suffix('.recovery.jsonl')
        with recovery.open('a') as saved:
            saved.write(json.dumps(dict(offset=offset,discarded_base64=base64.b64encode(damaged).decode(),
                                        recovered_utc=datetime.now(timezone.utc).isoformat()))+'\n')
            saved.flush(); os.fsync(saved.fileno())
        sync_directory(path.parent)
        with path.open('r+b') as out: out.truncate(offset); out.flush(); os.fsync(out.fileno())
    elif needs_newline and repair:
        with path.open('ab') as out: out.write(b'\n'); out.flush(); os.fsync(out.fileno())


def execute_task(plan,task,diagnostics):
    """Lazy numerical imports: standalone workers start with BLAS threads fixed to one."""
    import research
    from .research_design import realize
    config=plan['manifest']['config']; job=task['fit_options']
    design=realize(task['seed'],task['scenario'],partition=task['partition'],geometry=task['geometry'],
        variant=task['variant'],same_side_up_turns=config.get('same_side_up_turns',False),
        hardware=research.scenario_options('hardware') if task['scenario']=='hardware' else None,
        turn_schedule=config.get('turn_schedule'),turn_min_spacing=config.get('turn_min_spacing',10.),
        turn_edge_margin=config.get('turn_edge_margin',5.),geometry_cell=task['geometry_cell'],
        protocol=config.get('protocol'),trajectory_input=config.get('trajectory_input'))
    return research.flight_run(task['truth'],task['scenario'],task['seed'],job['bootstrap_sampling'],job['block_length'],
        job['n_boot'],task['variant'],config.get('same_side_up_turns',False),partition=task['partition'],geometry=task['geometry'],
        fit_options={k:v for k,v in job.items() if k not in ('n_boot','bootstrap_sampling','block_length')},design=design,
        decision_policy=plan.get('decision_policy'),pairwise_decision_policy=plan.get('pairwise_policy'),
        diagnostics_directory=diagnostics)


def attempt_limit(plan,value):
    if isinstance(value,bool) or not isinstance(value,int) or not 1<=value<=plan['task_count']:
        raise ValueError('explicit total attempt limit must be within the frozen task count')
    return value


def run_shard(output,plan,shard,limit,executor=None):
    one_thread(); check_plan(plan); limit=attempt_limit(plan,limit)
    if isinstance(shard,bool) or not isinstance(shard,int) or not 0<=shard<plan['shards']: raise ValueError('unknown shard')
    output=Path(output)
    if not (output/'plan.json').exists() or json.loads((output/'plan.json').read_text())!=plan:
        raise ValueError('worker requires an output bound to its plan')
    journal=output/f'shard-{shard:03d}.jsonl'
    with lock(output/f'shard-{shard:03d}.lock'):
        done=set(); previous=None; active=None
        for event in journal_events(journal,plan,shard,repair=True):
            previous=event['event_hash']
            if event['kind']=='start': active=event['index']
            else: done.add(event['index']); active=None
        if any(i>=limit for i in done) or (active is not None and active>=limit):
            raise ValueError('attempt limit cannot drop previously started tasks')
        # A durable start proves the attempt was spent, even if its result was lost.
        if active is not None:
            task=task_at(plan,active)
            previous=append_event(journal,plan,shard,task,'complete',previous,
                                  failure_record(plan,task,'interrupted after durable start; original outcome unavailable'))
            done.add(active)
        execute=execute_task if executor is None else executor
        def status(state,error=None):
            atomic_json(output/f'shard-{shard:03d}.status.json',dict(state=state,pid=os.getpid(),shard=shard,
                plan_hash=plan['plan_hash'],completed=len(done),attempt_limit=limit,error=error,
                updated_utc=datetime.now(timezone.utc).isoformat()))
        status('running')
        try:
            for index in range(shard,limit,plan['shards']):
                if index in done: continue
                check_plan(plan)
                task=task_at(plan,index)
                previous=append_event(journal,plan,shard,task,'start',previous)
                start=time.monotonic()
                try: row=execute(plan,task,output/'diagnostics'/task['task_id'])
                except Exception as exc:
                    row=failure_record(plan,task,'executor failed: '+repr(exc))
                    row.update(elapsed_s=time.monotonic()-start,runtime_unknown=False)
                check_plan(plan)
                from .research_design import plain
                row=plain(row)
                check_record(plan,task,row)
                previous=append_event(journal,plan,shard,task,'complete',previous,row)
                done.add(index); status('running')
            status('complete')
        except BaseException as exc:
            status('interrupted' if isinstance(exc,(KeyboardInterrupt,SystemExit)) else 'failed',repr(exc)); raise


def completed_events(path,plan,shard):
    active=False
    for event in journal_events(path,plan,shard):
        active=event['kind']=='start'
        if not active: yield event
    if active: raise ValueError('unfinished started attempt; resume its shard before merging')


def merge_campaign(output,plan,allow_partial=False,*,_coordinator_held=False):
    one_thread(); check_plan(plan); output=Path(output)
    with ExitStack() as locks:
        if not _coordinator_held: locks.enter_context(lock(output/'coordinator.lock'))
        locks.enter_context(lock(output/'merge.lock'))
        if json.loads((output/'plan.json').read_text())!=plan: raise ValueError('merge plan mismatch')
        for shard in range(plan['shards']): locks.enter_context(lock(output/f'shard-{shard:03d}.lock'))
        metadata={k:plan['manifest'][k] for k in ('analysis_version','implementation_hash','eligibility_policies',
                  'numerical_environment','numerical_environment_hash','manifest_hash')}
        metadata.update(partition=plan['manifest']['config']['partition'],manifest=plan['manifest'],
                        config=plan['manifest']['config'],sharded_plan_hash=plan['plan_hash'],
                        simulation_assumption='approved provenance and usable bench tier; remaining gates applied')
        temporary=output/'campaign.json.tmp'; total=0; failures=0; elapsed=0.; unknown_runtime=0; expected=0; contiguous=True
        streams=[completed_events(output/f'shard-{s:03d}.jsonl',plan,s) for s in range(plan['shards'])]
        with temporary.open('w') as out:
            out.write(json.dumps(metadata,allow_nan=False)[:-1]+',"records":[')
            for event in heapq.merge(*streams,key=lambda e:e['index']):
                index=event['index']
                if index<expected: raise ValueError('duplicate task across shards')
                if index!=expected: contiguous=False
                expected=index+1
                row=event['record']; total+=1; failures+=bool(row.get('failure'))
                elapsed+=row['elapsed_s'] or 0.; unknown_runtime+=row.get('runtime_unknown') is True
                if total>1: out.write(',')
                out.write(json.dumps({**row,'task_id':event['task_id'],'task_index':index},separators=(',',':'),allow_nan=False))
            complete=total==plan['task_count'] and contiguous
            if not complete and not allow_partial: raise ValueError('campaign incomplete; partial merge requires explicit --allow-partial')
            execution=dict(version=VERSION,task_count=plan['task_count'],completed=total,missing=plan['task_count']-total,
                           complete=complete,analysis_failures=failures,contiguous_prefix=contiguous,
                           runtime_unknown_attempts=unknown_runtime)
            out.write('],"execution":'+json.dumps(execution)+',"elapsed_s":'+json.dumps(elapsed)+
                      ',"elapsed_s_basis":"sum of known per-attempt times, not coordinator wall time; missing runtime excluded"}\n')
            out.flush(); os.fsync(out.fileno())
        os.replace(temporary,output/'campaign.json'); sync_directory(output)
        atomic_json(output/'merge-status.json',{**execution,'plan_hash':plan['plan_hash']})
        return execution


def run_local(output,plan,limit,workers=2,launcher=None):
    """Coordinator uses no BLAS work; at most two single-thread worker processes."""
    one_thread(); check_plan(plan); attempt_limit(plan,limit)
    if isinstance(workers,bool) or not isinstance(workers,int) or not 1<=workers<=2: raise ValueError('local workers must be one or two')
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    entry=Path(__file__).resolve().parents[1]/'tests'/'sharded_campaign.py'
    launch=subprocess.Popen if launcher is None else launcher
    with lock(output/'coordinator.lock'):
        bind_output(output,plan)
        # Orphaned children may outlive a killed coordinator. Detect them before
        # starting any new process, rather than importing more numerical workers.
        with ExitStack() as probe:
            for shard in range(plan['shards']): probe.enter_context(lock(output/f'shard-{shard:03d}.lock'))
        queued=list(range(min(plan['shards'],limit))); running=[]
        env={**os.environ,**dict.fromkeys(THREAD_KEYS,'1')}
        status=dict(plan_hash=plan['plan_hash'],attempt_limit=limit,workers=workers,pid=os.getpid(),state='running')
        atomic_json(output/'status.json',status)
        try:
            while queued or running:
                while queued and len(running)<workers:
                    shard=queued.pop(0)
                    log=(output/f'shard-{shard:03d}.log').open('a')
                    try:
                        process=launch([sys.executable,str(entry),'worker',str(output/'plan.json'),'--output',str(output),
                                        '--shard',str(shard),'--attempt-limit',str(limit)],env=env,stdout=log,stderr=subprocess.STDOUT)
                    finally: log.close()
                    running.append((shard,process))
                for shard,process in list(running):
                    code=process.poll()
                    if code is not None:
                        running.remove((shard,process))
                        if code: raise RuntimeError(f'shard {shard} exited {code}; inspect its log and resume the same plan')
                if running: time.sleep(.1)
            result=merge_campaign(output,plan,allow_partial=limit<plan['task_count'],_coordinator_held=True)
            atomic_json(output/'status.json',{**status,'state':'complete' if result['complete'] else 'budget_complete',**result})
            return result
        except BaseException as exc:
            for _,process in running:
                if process.poll() is None:
                    try: process.terminate()
                    except ProcessLookupError: pass
            for _,process in running:
                try: process.wait(timeout=5)
                except subprocess.TimeoutExpired: process.kill(); process.wait()
            atomic_json(output/'status.json',{**status,'state':'interrupted' if isinstance(exc,(KeyboardInterrupt,SystemExit)) else 'failed','error':repr(exc)})
            raise


def detach_local(output,plan,limit,workers=2):
    """Explicit background launch; preparation alone never calls this function."""
    one_thread(); check_plan(plan); attempt_limit(plan,limit)
    if isinstance(workers,bool) or not isinstance(workers,int) or not 1<=workers<=2:
        raise ValueError('local workers must be one or two')
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    with lock(output/'launch.lock'):
        with lock(output/'coordinator.lock'):
            bind_output(output,plan)
        entry=Path(__file__).resolve().parents[1]/'tests'/'sharded_campaign.py'
        command=[sys.executable,str(entry),'run',str(output/'plan.json'),'--output',str(output),
                 '--attempt-limit',str(limit),'--workers',str(workers)]
        with (output/'coordinator.log').open('a') as log:
            process=subprocess.Popen(command,start_new_session=True,stdout=log,stderr=subprocess.STDOUT,
                                     env={**os.environ,**dict.fromkeys(THREAD_KEYS,'1')})
        launch=dict(pid=process.pid,command=command,plan_hash=plan['plan_hash'],attempt_limit=limit,
                    workers=workers,started_utc=datetime.now(timezone.utc).isoformat())
        atomic_json(output/'launch.json',launch)
        # Do not report a successful detached launch before the child owns the
        # campaign and has written status. This also closes the launch/resume race.
        deadline=time.monotonic()+10.
        while True:
            status_path=output/'status.json'
            state=json.loads(status_path.read_text()) if status_path.exists() else {}
            if state.get('pid')==process.pid and state.get('plan_hash')==plan['plan_hash']:
                if state.get('state') in ('failed','interrupted'): raise RuntimeError('background coordinator failed; inspect coordinator.log')
                break
            if process.poll() is not None: raise RuntimeError('background coordinator exited before becoming ready; inspect coordinator.log')
            if time.monotonic()>=deadline:
                process.terminate()
                try: process.wait(timeout=5)
                except subprocess.TimeoutExpired: process.kill(); process.wait()
                raise RuntimeError('background coordinator startup deadline exceeded; inspect coordinator.log')
            time.sleep(.1)
    return launch
