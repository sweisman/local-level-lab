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


def load(path):return json.loads(path.read_text())
def file_digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
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
        if not (charges/'HEAD.json').exists():return None
        head=load(charges/'HEAD.json');previous=None;counts=dict(starts=0,sweeps=0)
        events=head['events']
        if type(events) is not int or not 0<=events<=1000000:raise ValueError('invalid charge count')
        for number in range(1,events+1):
            item=load(charges/f'{number:08d}.json');payload=item['payload'];kind=payload['record_type']
            if (kind not in counts or payload['event_number']!=number
                    or payload['previous_sha256']!=previous or item['sha256']!=object_digest(payload)
                    or payload['record']['manifest_sha256']!=manifest_hash):
                raise ValueError('charge chain mismatch')
            counts[kind]+=1;previous=item['sha256']
        if head['sha256']!=previous:raise ValueError('charge head mismatch')
        return dict(counts,incomplete_transaction=pending)


def completed_rows(directory,manifest,manifest_hash):
    rows=[]
    for task in manifest.get('plan',{}).get('tasks',[]):
        identity=task['identity'];name=identity.replace('::','-')+'.json'
        if Path(name).name!=name:raise ValueError('invalid result filename')
        path=directory/name
        if not path.exists():continue
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
        plan=manifest.get('plan',{});tasks=plan.get('tasks',[])
        result.update(total=len(tasks) if tasks else status.get('total'),
            native_limit=plan.get('maximum_native_evaluations',plan.get('maximum_sweeps')),
            worker_phase=status.get('state'),identity=status.get('identity'),pid=status.get('pid'))
        with read_lock(directory/'worker.lock') as state:result['lock']=state
        held=result['lock']=='held'
        result['state']='running' if held else 'incomplete'
        result['threads']=status.get('allocated_numerical_threads',plan.get('numerical_threads',0)) if held else 0
        rows=[]
        if (directory/'completion.json').exists():
            completion=load(directory/'completion.json')
            if (completion.get('state')!='complete' or completion.get('manifest_sha256')!=manifest_hash
                    or completion.get('summary_sha256')!=file_digest(directory/'summary.json')):
                raise ValueError('completion/manifest/summary hash mismatch')
            summary=load(directory/'summary.json');rows=summary.get('results',[])
            result.update(state='complete',native_calls=summary.get('native_evaluations'))
        else:
            rows=completed_rows(directory,manifest,manifest_hash)
            if status.get('state')=='stopped' and not held:result['state']='stopped'
        result['completed']=len(rows)
        gates=('conditional_verified','passed','conditional_converged','converged')
        result['passed']=sum(next((r[k] is True for k in gates if k in r),False) for r in rows)
        result['errors']=sum(r.get('status') in ('error','interrupted','not_started') for r in rows)
        result['failures']=[dict(identity=r.get('identity'),reason=r.get('reason',r.get('status')))
            for r in rows if r.get('status') in ('error','interrupted','not_started')]
        try:
            counts=receipt_counts(directory,manifest_hash)
            if counts is not None:
                result.update(native_calls=counts['sweeps'],charged_identities=counts['starts'])
                if counts['incomplete_transaction']:
                    result['warnings'].append('incomplete charge transaction; preserve receipts; resumption blocked')
                    if not held:result['state']='blocked'
        except (OSError,ValueError,KeyError,TypeError) as error:
            result['warnings'].append('charge snapshot: '+str(error))
        if result['native_calls'] is None:result['native_calls']=status.get('native_evaluations')
        latest=max((p.stat().st_mtime for p in (directory/'status.json',directory/'completion.json',
            directory/'charges/HEAD.json') if p.exists()),default=None)
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
    if report.get('identity') and report['state']=='running':text+='\n  Current: '+report['identity']
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
