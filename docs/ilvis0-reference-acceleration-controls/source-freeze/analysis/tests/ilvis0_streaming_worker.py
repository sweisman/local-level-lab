# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated-only native streaming qualification; no observed starts."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll.compute_budget import environment as guarded_environment

if __name__=='__main__' and any(os.environ.get(k)!=v for k,v in guarded_environment(threads=4).items()):
    raise SystemExit('use run_numerical.py with one worker, four threads and zero reserved threads')

from ilvis0_channel_envelope_worker import sha,load,write,environment
from lll import ilvis0_stream_controls as controls

NAME='ilvis0-streaming-controls-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-streaming-controls'
TASKS=controls.tasks()
LIMITS=dict(maximum_identities=48,maximum_native_evaluations=2500,maximum_packet_visits=3000000,
    maximum_scaling_block_packets=1024,maximum_wall_s=600,numerical_threads=4,optimizer_starts=0,
    observed_starts=0,original_reads=0,retries=0,deadline_policy='cooperative-no-signals')
SOURCE_NAMES=['analysis/lll/'+n for n in ('ilvis0_streaming.py','ilvis0_stream_controls.py',
    'ilvis0_stream_body.h','ilvis0_stream_value.c','ilvis0_stream_tangent.cpp',
    'ilvis0_native.c','ilvis0_tangent.cpp','ilvis0_shape.py','ilvis0_exploratory.py',
    'ilvis0_estimator.py','ilvis0_forward.py','compute_budget.py','ilvis0_receipt_journal.py')]
SOURCE_NAMES+=['analysis/tests/'+n for n in ('ilvis0_streaming_worker.py','ilvis0_channel_envelope_worker.py',
    'test_ilvis0_streaming.py','test_ilvis0_stream_controls.py','test_ilvis0_streaming_worker.py')]
SOURCE_NAMES+=['docs/ilvis0-streaming-controls/PLAN.md']


class AllowanceExhausted(Exception):pass


def prepare():
    if DATA.exists():raise ValueError('study directory exists; never overwrite a freeze')
    manifest=dict(version=NAME,limits=LIMITS,tasks=TASKS,environment=environment(),
        numerical_environment=guarded_environment(threads=4),sources={name:sha(ROOT/name) for name in SOURCE_NAMES},
        compilers={compiler:subprocess.check_output([compiler,'--version'],text=True).splitlines()[0] for compiler in ('cc','c++')})
    write(DATA/'manifest.json',manifest)
    for name in SOURCE_NAMES:
        target=DATA/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    write(DATA/'authorization.json',dict(scope='standing approved L01 software roadmap; generated measurements only',limits=LIMITS,
        manifest_sha256=sha(DATA/'manifest.json'),scientific_decision='abstain'))


def verify(*,current=False):
    manifest=load(DATA/'manifest.json')
    if load(DATA/'authorization.json')['manifest_sha256']!=sha(DATA/'manifest.json'):raise ValueError('authorization/freeze mismatch')
    for name,digest in manifest['sources'].items():
        if sha(DATA/'source-freeze'/name)!=digest or (current and sha(ROOT/name)!=digest):raise ValueError('frozen source changed: '+name)
    if current and (manifest['environment']!=environment() or manifest['numerical_environment']!=guarded_environment(threads=4)):
        raise ValueError('study numerical environment mismatch')
    if current and manifest['compilers']!={c:subprocess.check_output([c,'--version'],text=True).splitlines()[0] for c in ('cc','c++')}:
        raise ValueError('study compiler environment mismatch')
    if (DATA/'completion.json').exists():
        completion=load(DATA/'completion.json')
        if completion['manifest_sha256']!=sha(DATA/'manifest.json') or completion['summary_sha256']!=sha(DATA/'summary.json'):
            raise ValueError('completed evidence changed')
        for row in load(DATA/'summary.json')['results']:
            if sha(DATA/row['artifact'])!=row['artifact_sha256']:raise ValueError('saved result changed')
    return manifest


def run():
    manifest=verify(current=True)
    with (DATA/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (DATA/'start.json').exists() or (DATA/'completion.json').exists():raise ValueError('study already started or completed; no retries')
        started=time.time();write(DATA/'start.json',dict(pid=os.getpid(),started_unix=started,manifest_sha256=sha(DATA/'manifest.json')))
        write(DATA/'status.json',dict(state='running',pid=os.getpid(),total=len(manifest['tasks']),numerical_threads=4),replace=True)
        counts=dict(identities=0,native_calls=0,packet_visits=0);rows=[];terminal=None
        def charge(**increase):
            nonlocal counts
            if time.time()-started>=manifest['limits']['maximum_wall_s']:raise AllowanceExhausted('cooperative wall allowance exhausted')
            proposed=dict(counts)
            for key,value in increase.items():proposed[key]+=value
            for key,limit in (('native_calls','maximum_native_evaluations'),('packet_visits','maximum_packet_visits')):
                if proposed[key]>manifest['limits'][limit]:raise AllowanceExhausted('finite '+key+' allowance exhausted')
            # Persist before every native call; writes are never rolled back.
            write(DATA/'charges'/f"call-{proposed['native_calls']:05d}.json",dict(counts=proposed,increase=increase))
            counts=proposed
        try:
            for task in manifest['tasks']:
                if time.time()-started>=manifest['limits']['maximum_wall_s']:raise AllowanceExhausted('cooperative wall allowance exhausted')
                counts['identities']+=1
                write(DATA/'starts'/(task['identity']+'.json'),dict(task=task,started_unix=time.time()))
                try:result=controls.evaluate(task,DATA/'kernels',charge)
                except Exception as error:
                    result=dict(identity=task['identity'],kind=task['kind'],passed=False,error_type=type(error).__name__,error=str(error))
                    terminal='control failed; remaining identities not run'
                if time.time()-started>=manifest['limits']['maximum_wall_s']:
                    terminal=terminal or 'cooperative wall allowance exhausted'
                artifact='results/'+task['identity']+'.json';write(DATA/artifact,result)
                rows.append(dict(identity=task['identity'],passed=result['passed'],artifact=artifact,artifact_sha256=sha(DATA/artifact)))
                write(DATA/'progress.json',dict(completed=len(rows),passed=sum(r['passed'] for r in rows),charged=counts),replace=True)
                if terminal or not result['passed']:terminal=terminal or 'qualification acceptance failed; remaining identities not run';break
        except AllowanceExhausted as error:terminal=str(error)
        state='terminal' if terminal else 'complete'
        write(DATA/'summary.json',dict(state=state,passed=not terminal and len(rows)==len(manifest['tasks']) and all(r['passed'] for r in rows),
            results=rows,charged=counts,native_evaluations=counts['native_calls'],elapsed_s=time.time()-started,
            terminal_reason=terminal,original_reads=0,optimizer_starts=0,scientific_decision='abstain'))
        write(DATA/'completion.json',dict(state=state,manifest_sha256=sha(DATA/'manifest.json'),summary_sha256=sha(DATA/'summary.json')))
        write(DATA/'status.json',dict(state=state,total=len(manifest['tasks']),numerical_threads=0),replace=True)
    publish()


def publish():
    manifest=verify();summary=load(DATA/'summary.json');PUBLIC.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(DATA/'source-freeze/docs/ilvis0-streaming-controls/PLAN.md',PUBLIC/'PLAN.md')
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json']
    names += [r['artifact'] for r in summary['results']]
    names += ['source-freeze/'+name for name in manifest['sources']]
    # Explicit charged identities/calls only; never inspect an original corpus.
    names += ['starts/'+t['identity']+'.json' for t in manifest['tasks'][:summary['charged']['identities']]]
    names += [f'charges/call-{i:05d}.json' for i in range(1,summary['charged']['native_calls']+1)]
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    results=[load(DATA/r['artifact']) for r in summary['results']]
    lines=['# Streaming native integration','',f"{sum(r['passed'] for r in summary['results'])}/{len(manifest['tasks'])} generated controls passed; study state: {summary['state']}.",'',
        'This study compares chunked integration with the unchanged whole-array kernels, checks independent constant-pose inputs, '
        'and measures bounded-block memory/runtime. It performs no archive fits or protected ESA evaluation.','',
        '| Control family | Completed | Passed |','|---|---:|---:|']
    for kind in ('equivalence','pose','scaling'):
        selected=[r for r in results if r['kind']==kind]
        lines.append(f"| {kind} | {len(selected)} | {sum(r['passed'] for r in selected)} |")
    lines+=['','| Scaling mode | Packets | Duration | Runtime | Traced peak memory | State |','|---|---:|---:|---:|---:|---:|']
    for row in results:
        if row['kind']=='scaling' and 'runtime_s' in row:
            lines.append(f"| {'27-column tangent' if row['input']['tangent'] else 'Value only'} | {row['packet_count']:,} | {row['elapsed_s']:.1f} s | {row['runtime_s']:.2f} s | {row['peak_traced_bytes']/1024**2:.3f} MiB | {row['state_bytes']:,} bytes |")
    lines+=['','Traced memory includes generated block arrays and query results, but excludes the compiler and shared-library code. '
        'No complete long-record array is constructed in the scaling stage. The native loops are serial; four numerical threads '
        'are reserved as a ceiling, not four-way speedup.','',
        f"Charged {summary['charged']['native_calls']:,} native calls and {summary['charged']['packet_visits']:,} packet visits in {summary['elapsed_s']:.2f} seconds."]
    lines+=['','Passing these controls establishes software equivalence on the declared generated cases. '
        'It does not establish calibrated uncertainty, actual recording continuity, predictive adequacy or an eight-hour fit runtime. '
        'The recording-scale uncertainty bounds remain too wide; new observed prediction fits remain blocked.','',
        '[Frozen method and acceptance](PLAN.md) · [Technical roadmap](../ANALYSIS_ROADMAP.md) · [Next analyses](../NEXT_STEPS.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={name:sha(PUBLIC/name) for name in names+['README.md','PLAN.md']}),replace=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    operations=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','package-only','check'):operations.add_argument('--'+name,action='store_true')
    parser.add_argument('--detach',action='store_true');args=parser.parse_args()
    if args.detach:
        if not args.run:parser.error('--detach requires --run')
        with (DATA/'worker.log').open('ab') as log:
            process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--run'],cwd=ROOT,
                stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=os.environ.copy())
        print(json.dumps(dict(launched_pid=process.pid,study=str(DATA.relative_to(ROOT)))))
    elif args.prepare:prepare();print('Frozen 48 generated controls; zero observed starts.')
    elif args.run:run();print('Streaming qualification finished; inspect saved results.')
    elif args.package_only:publish();print('Published saved controls; no evaluations.')
    else:verify();print('Verified streaming source freeze and completed artifacts.')


if __name__=='__main__':main()
