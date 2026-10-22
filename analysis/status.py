#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only study status: metadata, receipt counts and nonblocking lock checks."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
from lll.studies.readers import available as archived_available,read as archived_read


def read_bytes(path):
    path=Path(path)
    if path.is_file():return path.read_bytes()
    if path.is_relative_to(ROOT):return archived_read(ROOT,str(path.relative_to(ROOT)))
    raise FileNotFoundError(path)
def exists(path):
    path=Path(path)
    return path.exists() or (path.is_relative_to(ROOT) and archived_available(ROOT,str(path.relative_to(ROOT))))
def load(path):return json.loads(read_bytes(path))
def file_digest(path):return hashlib.sha256(read_bytes(path)).hexdigest()
def object_digest(value):
    data=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n'
    return hashlib.sha256(data.encode()).hexdigest()


def result_digest(value):
    # Result envelopes predate receipt chains and omit their trailing newline.
    data=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
    return hashlib.sha256(data.encode()).hexdigest()


@contextmanager
def read_lock(path):
    """Never create a lock file and never wait for a worker or ledger."""
    try:stream=path.open('rb')
    except FileNotFoundError:
        yield 'missing';return
    with stream:
        try:fcntl.flock(stream,fcntl.LOCK_SH|fcntl.LOCK_NB)
        except BlockingIOError:
            yield 'held';return
        try:yield 'free'
        finally:fcntl.flock(stream,fcntl.LOCK_UN)


def receipt_counts(directory,manifest_hash):
    charges=directory/'charges'
    with read_lock(charges/'ledger.lock') as state:
        if state=='held':raise ValueError('charge ledger busy; snapshot unavailable')
        pending=charges.is_dir() and any(p.name.startswith('.pending-') for p in charges.iterdir())
        if exists(charges/'journal.sqlite'):
            from lll.studies.journal import inspect_snapshot
            return inspect_snapshot(read_bytes(charges/'journal.sqlite'),manifest_hash)
        if not exists(charges/'HEAD.json'):return None
        head=load(charges/'HEAD.json');previous=None;counts=dict(starts=0,sweeps=0)
        events=head['events'];native_sweeps=0
        if type(events) is not int or not 0<=events<=1000000:raise ValueError('invalid charge count')
        for number in range(1,events+1):
            item=load(charges/f'{number:08d}.json');payload=item['payload'];kind=payload['record_type']
            if (kind not in counts or payload['event_number']!=number
                    or payload['previous_sha256']!=previous or item['sha256']!=object_digest(payload)
                    or payload['record']['manifest_sha256']!=manifest_hash):
                raise ValueError('charge chain mismatch')
            counts[kind]+=1;previous=item['sha256']
            if kind=='sweeps' and payload['record'].get('phase')=='fit':native_sweeps+=1
        if head['sha256']!=previous:raise ValueError('charge head mismatch')
        return dict(counts,native_sweeps=native_sweeps,incomplete_transaction=pending)


def completed_rows(directory,manifest,manifest_hash):
    rows=[]
    if manifest.get('version')=='ilvis0-sharded-native-controls-v1':
        workers=manifest['allocation']['workers']
        for task in manifest['tasks']:
            identity=task['identity'];shard=task['shard'];name=identity+'.json'
            if Path(name).name!=name or type(shard) is not int or not 0<=shard<workers:
                raise ValueError('invalid sealed shard result identity or assignment')
            base=directory/'shards'/f'{shard:03d}'/'results'
            candidates=[base/(identity+suffix+'.json') for suffix in ('','.interrupted')]
            sealed=[p for p in candidates if exists(p.with_suffix('.seal.json'))]
            if len(sealed)>1:raise ValueError('multiple sealed outcomes for one identity')
            if not sealed:continue
            path=sealed[0];receipt=load(path.with_suffix('.seal.json'));envelope=load(path);row=envelope['result']
            if (receipt.get('sha256')!=file_digest(path) or receipt.get('manifest_sha256')!=manifest_hash
                    or envelope.get('manifest_sha256')!=manifest_hash or envelope.get('identity')!=identity
                    or envelope.get('shard')!=shard or envelope.get('task_sha256')!=object_digest(task)
                    or envelope.get('result_sha256')!=object_digest(row)
                    or envelope.get('status') not in ('complete','interrupted')
                    or type(row.get('passed')) is not bool or row.get('scientific_decision')!='abstain'
                    or ('identity' in row and row['identity']!=identity)):
                raise ValueError('sealed shard result hash, identity or task mismatch')
            rows.append(dict(row,identity=identity,status=envelope['status']))
        return rows
    for task in manifest.get('plan',{}).get('tasks',[]):
        identity=task['identity'];name=identity.replace('::','-')+'.json'
        if Path(name).name!=name:raise ValueError('invalid result filename')
        path=directory/name
        if not exists(path):continue
        envelope=load(path);row=envelope['result']
        if (envelope['manifest_sha256']!=manifest_hash or envelope['result_sha256']!=result_digest(row)
                or row['identity']!=identity):raise ValueError('saved result hash or identity mismatch')
        rows.append(row)
    return rows


def inspect_study(directory):
    directory=Path(directory)
    result=dict(path=str(directory),state='missing',lock='missing',threads=0,completed=0,
        total=None,passed=0,errors=0,native_calls=None,native_limit=None,
        charged_identities=None,warnings=[])
    if not directory.is_dir():return result
    try:
        manifest=load(directory/'manifest.json');manifest_hash=file_digest(directory/'manifest.json')
        status=load(directory/'status.json') if (directory/'status.json').exists() else {}
        plan=manifest.get('plan',manifest.get('limits',{}));tasks=plan.get('tasks',manifest.get('tasks',[]))
        result.update(total=len(tasks) if tasks else len(manifest['tests']) if 'tests' in manifest else status.get('total'),
            native_limit=plan.get('maximum_native_evaluations',plan.get('maximum_sweeps',plan.get('maximum_native_sweeps'))),
            worker_phase=status.get('state'),identity=status.get('identity'),pid=status.get('pid'))
        with read_lock(directory/'worker.lock') as state:result['lock']=state
        held=result['lock']=='held'
        sharded=manifest.get('version')=='ilvis0-sharded-native-controls-v1'
        child_held=False
        if sharded:
            allocation=manifest['allocation'];workers=allocation['workers'];threads=allocation['threads']
            if type(workers) is not int or type(threads) is not int or not 1<=workers<=4 or not 1<=workers*threads<=4:
                raise ValueError('invalid sharded numerical allocation')
            states={}
            for shard in range(workers):
                with read_lock(directory/'shards'/f'{shard:03d}'/'worker.lock') as state:states[str(shard)]=state
            child_held=any(state=='held' for state in states.values());held=held or child_held
            result.update(shard_locks=states,native_limit=manifest['limits']['native_calls'],bound_limit=manifest['limits']['bound_calls'])
        result['state']='running' if held else 'incomplete'
        result['threads']=status.get('allocated_numerical_threads',status.get('numerical_threads',plan.get('numerical_threads',0))) if held else 0
        if sharded:result['threads']=workers*threads if held else 0
        rows=[]
        if (directory/'completion.json').exists():
            if child_held:raise ValueError('sealed completion still has an owned shard lease')
            completion=load(directory/'completion.json')
            terminal_state=completion.get('state','complete')
            if (terminal_state not in ('complete','terminal') or completion.get('manifest_sha256')!=manifest_hash
                    or completion.get('summary_sha256')!=file_digest(directory/'summary.json')):
                raise ValueError('completion/manifest/summary hash mismatch')
            summary=load(directory/'summary.json')
            if terminal_state=='terminal':
                if summary.get('state')!='terminal' or not summary.get('terminal_reason'):
                    raise ValueError('terminal receipt requires a matching sealed terminal summary')
                result['warnings'].append('study ended without qualification: '+str(summary['terminal_reason']))
            if 'state' not in completion and summary.get('state')!='complete':
                raise ValueError('verified completion requires explicit complete state')
            rows=summary.get('results',[])
            if isinstance(rows,dict):
                if any(not isinstance(r,dict) or ('identity' in r and r['identity']!=key) for key,r in rows.items()):
                    raise ValueError('invalid keyed result summary')
                rows=[dict(r,identity=key) for key,r in rows.items()]
            if not isinstance(rows,list) or any(not isinstance(r,dict) for r in rows):
                raise ValueError('invalid result summary rows')
            result.update(state=terminal_state,native_calls=summary.get('native_evaluations',summary.get('native_sweeps')))
            if sharded:result['threads']=0
            if 'tests' in summary and not rows:
                rows=[dict(row,passed=row['outcome']=='passed',status='error' if row['outcome'] in ('failure','error') else 'complete')
                      for row in summary['tests']]
                budget=summary.get('budget') or {}
                result.update(native_calls=budget.get('native_sweeps'),charged_identities=budget.get('starts'))
                if summary.get('passed') is False:
                    result['warnings'].append('qualification failed; '+str(len(summary.get('unrun_tests',[])))+' controls not run')
        else:
            rows=completed_rows(directory,manifest,manifest_hash)
            if status.get('state')=='stopped' and not held:result['state']='stopped'
            if held and (directory/'progress.json').exists():
                progress=load(directory/'progress.json')
                completed=progress.get('completed');passed=progress.get('passed');total=result['total']
                if (type(completed) is int and type(passed) is int and type(total) is int
                        and 0<=passed<=completed<=total):
                    result['worker_progress']=dict(completed=completed,passed=passed)
                else:result['warnings'].append('invalid worker progress snapshot; verified counts retained')
        result['completed']=len(rows)
        gates=('conditional_verified','passed','conditional_converged','converged')
        result['passed']=sum(next((r[k] is True for k in gates if k in r),False) for r in rows)
        result['errors']=sum(r.get('status') in ('error','interrupted','not_started') for r in rows)
        result['failures']=[dict(identity=r.get('identity'),reason=r.get('reason',r.get('status')))
            for r in rows if r.get('status') in ('error','interrupted','not_started')]
        try:
            counts=receipt_counts(directory,manifest_hash)
            preflight=receipt_counts(directory/'preflight',manifest_hash)
            if counts is not None:
                result.update(charged_identities=counts['starts'])
            if preflight is not None:result['preflight_identities']=preflight['starts']
            ledgers=[c for c in (counts,preflight) if c is not None]
            if ledgers:
                # Sum active subledgers, preserving an authoritative sealed total.
                if result['state']!='complete' or result['native_calls'] is None:
                    result['native_calls']=sum(c['sweeps'] for c in ledgers)
                if any(c['incomplete_transaction'] for c in ledgers):
                    result['warnings'].append('incomplete charge transaction; preserve receipts; resumption blocked')
                    # A dependent job may reserve the old worker lock. A sealed
                    # orphan transaction still prevents this ledger from working.
                    result.update(state='blocked',threads=0)
        except (OSError,ValueError,KeyError,TypeError) as error:
            result['warnings'].append('charge snapshot: '+str(error))
        if sharded:
            shard_native=0;shard_starts=0;shard_bounds=0;valid=True
            for shard in range(workers):
                try:
                    counts=receipt_counts(directory/'shards'/f'{shard:03d}',manifest_hash)
                    if counts:
                        shard_native+=counts['native_sweeps'];shard_starts+=counts['starts']
                        shard_bounds+=counts['sweeps']-counts['native_sweeps']
                        if counts['incomplete_transaction']:raise ValueError('incomplete transaction; continuation blocked')
                except (OSError,ValueError,KeyError,TypeError) as error:
                    valid=False;result['warnings'].append(f'shard {shard} charge snapshot: '+str(error))
            if valid:
                result['charged_identities']=shard_starts
                if result['state'] in ('complete','terminal') and result['native_calls']!=shard_native:
                    raise ValueError('sealed native total differs from shard receipts')
                result['native_calls']=shard_native
                if result['state'] in ('complete','terminal') and summary.get('bound_evaluations')!=shard_bounds:
                    raise ValueError('sealed bound total differs from shard receipts')
                result['bound_calls']=shard_bounds
        if result['native_calls'] is None:result['native_calls']=status.get('native_evaluations')
        latest=max((p.stat().st_mtime for p in (directory/'status.json',directory/'completion.json',
            directory/'charges/HEAD.json',directory/'preflight/charges/HEAD.json') if p.exists()),default=None)
        result['updated_seconds_ago']=round(max(0,time.time()-latest)) if latest is not None else None
    except (OSError,ValueError,KeyError,TypeError) as error:
        result.update(state='invalid');result['warnings'].append(str(error))
    return result


def study_path(root,name):
    root=root.resolve();path=(root/name).resolve()
    if not path.is_relative_to(root/'data'):raise ValueError('study path must stay inside repository data/')
    return path


def read_registry(root,path):
    rows=load(path)['studies']
    return [(r['name'],study_path(root,r['path'])) for r in rows]


def render(report):
    total=report['total'] if report['total'] is not None else '?'
    calls=report['native_calls'] if report['native_calls'] is not None else '?'
    limit=report['native_limit'] if report['native_limit'] is not None else '?'
    text=f"{report['name']}: {report['state']} | {report['completed']}/{total} results, {report['passed']} passed, {report['errors']} errors"
    text+=f" | {calls}/{limit} charged native calls | {report['threads']} threads | lock {report['lock']}"
    if report.get('shard_locks'):
        text+=f" | {sum(v=='held' for v in report['shard_locks'].values())} owned shard leases"
    if 'bound_calls' in report:
        text+=f" | {report['bound_calls']}/{report['bound_limit']} charged bounds"
    if report.get('identity') and report['state']=='running':text+='\n  Current: '+report['identity']
    if report.get('worker_progress'):
        progress=report['worker_progress']
        text+=f"\n  Worker snapshot: {progress['completed']}/{total} complete, {progress['passed']} passing; completion verification pending"
    for warning in report['warnings']:text+='\n  Warning: '+warning
    return text


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study',action='append',help='explicit repository data/ directory; repeat for several studies')
    parser.add_argument('--json',action='store_true',help='machine-readable output')
    args=parser.parse_args()
    try:
        entries=[(Path(name).name,study_path(ROOT,name)) for name in args.study] if args.study else read_registry(ROOT,ROOT/'analysis/study-status.json')
        reports=[dict(inspect_study(path),name=name) for name,path in entries]
    except (OSError,ValueError,KeyError,TypeError) as error:parser.error(str(error))
    active=sum(r['threads'] for r in reports);warnings=[]
    if active>4:warnings.append('monitored numerical allocation exceeds four total threads')
    payload=dict(studies=reports,monitored_numerical_threads=active,warnings=warnings)
    if args.json:print(json.dumps(payload,indent=2))
    else:
        for report in reports:print(render(report))
        print(f'Monitored numerical allocation: {active}/4 threads.')
        for warning in warnings:print('Warning: '+warning)
    return int(any(r['state']=='invalid' or r['warnings'] for r in reports) or bool(warnings))


if __name__=='__main__':sys.exit(main())
