# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only complete review and gated continuation; no native work in coordinator."""
import argparse
import copy
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from ilvis0_projection_sequence import ROOT,sha,load,write,complete

OUTPUT=ROOT/'data/ilvis0-projected-advance-20261018'
REVIEW='ilvis0-projected-complete-review-20261018'
PRECEDING='ilvis0-projected-local-qualification-20261018'
CONTINUATION='ilvis0-projected-budget-continuation-20261018'
FULL='ilvis0-projected-fullcal-qualification-20261018'


def key(row):return row['model'],row['clock'],tuple(row['axes']),row['start']


def combine(parent,continued):
    bad=[p for p in parent['pairs'] if not p['passed']]
    if len(parent['results'])!=24 or len(parent['pairs'])!=12 or len(bad)!=1 or len(continued['results'])!=2 or len(continued['pairs'])!=1:
        raise ValueError('exact declared source inventories required')
    target=bad[0];fields=('model','clock','axes')
    originals=[r for r in parent['results'] if all(r[k]==target[k] for k in fields)]
    if len(originals)!=2 or {key(r) for r in originals}!={key(r) for r in continued['results']}:
        raise ValueError('only the two declared saved endpoints can change')
    if any(continued['pairs'][0][k]!=target[k] for k in fields):raise ValueError('continuation pair mismatch')
    replacement={key(r):copy.deepcopy(r) for r in continued['results']}
    rows=[replacement.get(key(r),copy.deepcopy(r)) for r in parent['results']]
    pairs=[copy.deepcopy(continued['pairs'][0] if not p['passed'] else p) for p in parent['pairs']]
    passed=bool(continued['passed'] and all(r['passed'] for r in rows) and all(p['passed'] for p in pairs))
    return dict(state='complete',passed=passed,results=rows,pairs=pairs,native_evaluations=0,
        original_recording_reads=0,observed_starts=0,reused_companions=22,continued_endpoints=2,
        preceding_qualification_passed=parent['passed'],scientific_decision='abstain')


def review(continued):
    data=ROOT/'data'/REVIEW;public=ROOT/'docs'/REVIEW
    data.mkdir(parents=True,exist_ok=True);public.mkdir(parents=True,exist_ok=True)
    with (data/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (data/'completion.json').exists():return load(data/'summary.json')
        if (data/'start.json').exists():raise ValueError('charged saved-only review cannot restart')
        parent=complete(PRECEDING)
        if parent is None:raise ValueError('verified completed preceding matrix required')
        sources={};inputs={};versions=[]
        for name in (PRECEDING,CONTINUATION):
            p=ROOT/'docs'/name;m=load(p/'manifest.json');versions.append(m['environment'])
            for filename,digest in m['sources'].items():
                if filename in sources and sources[filename]!=digest:raise ValueError('incompatible source versions')
                if sha(ROOT/filename)!=digest:raise ValueError('source changed before review')
                sources[filename]=digest
            for filename in ('manifest.json','summary.json','completion.json'):
                inputs[str((p/filename).relative_to(ROOT))]=sha(p/filename)
        if versions[0]!=versions[1]:raise ValueError('incompatible numerical environments')
        for filename in ('analysis/tests/ilvis0_projected_advance.py','analysis/tests/ilvis0_projected_fullcal_review_worker.py'):
            sources[filename]=sha(ROOT/filename)
        summary=combine(parent,continued)
        write(data/'manifest.json',dict(version='ilvis0-projected-complete-review-v1',sources=sources,
            inputs=inputs,environment=versions[0],optimizer_starts=0,native_evaluations=0,
            plan=dict(numerical_threads=0,maximum_native_evaluations=0,tasks=[dict(identity=r['identity']) for r in summary['results']])))
        write(data/'start.json',dict(manifest_sha256=sha(data/'manifest.json')))
        write(data/'summary.json',summary)
        write(data/'completion.json',dict(state='complete',manifest_sha256=sha(data/'manifest.json'),summary_sha256=sha(data/'summary.json')))
        write(data/'status.json',dict(state='complete',allocated_numerical_threads=0))
        for filename in ('manifest.json','summary.json','completion.json','start.json'):shutil.copy2(data/filename,public/filename)
        for filename in sources:
            target=public/'source-freeze'/filename;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/filename,target)
        text='# Complete projected-fitting software review\n\n'
        text+=f"**{'Passed' if summary['passed'] else 'Not qualified'}:** {sum(r['passed'] for r in summary['results'])}/24 fits and {sum(p['passed'] for p in summary['pairs'])}/12 paired-start comparisons. "
        text+='The review reuses 22 unchanged companions and two separately budgeted continuations. It makes no native predictions, optimizer starts or original-recording reads.\n\n'
        text+='The preceding failed matrices remain unchanged. Passing this review permits only the prepared full-calibration software controls, not observed refits or scientific promotion.\n\n'
        text+=f'[Earlier local matrix](../{PRECEDING}/README.md) · [Endpoint continuations](../{CONTINUATION}/README.md) · [Full-calibration scope](../{FULL}/PLAN.md).\n'
        (public/'README.md').write_text(text)
        write(public/'evidence-receipt.json',dict(artifacts={n:sha(public/n) for n in ('manifest.json','summary.json','completion.json','start.json','README.md')}))
        return summary


def prepare():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    if not (OUTPUT/'manifest.json').exists():
        names=('analysis/tests/ilvis0_projected_advance.py','analysis/tests/test_ilvis0_projected_advance.py',
            'analysis/tests/ilvis0_projected_fullcal_review_worker.py','analysis/tests/ilvis0_projected_fullcal_worker.py',
            'analysis/lll/ilvis0_projected_fullcal.py','analysis/tests/test_ilvis0_projected_fullcal.py',
            'data/'+CONTINUATION+'/manifest.json','docs/'+FULL+'/PLAN.md')
        write(OUTPUT/'manifest.json',dict(sources={n:sha(ROOT/n) for n in names},maximum_wall_s=7200,
            native_calls=0,optimizer_starts=0,full_stage_maximum_starts=24,full_stage_maximum_calls=3888))
    m=load(OUTPUT/'manifest.json')
    for name,digest in m['sources'].items():
        if sha(ROOT/name)!=digest:raise ValueError('advancement dependency changed: '+name)
    return m


def wait_for(name,started):
    while True:
        prepare()
        if time.monotonic()-started>7200:raise TimeoutError('advancement wall allowance exhausted')
        result=complete(name)
        if result is not None:return result
        write(OUTPUT/'status.json',dict(state='waiting',stage=name,numerical_threads=0));time.sleep(10)


def run():
    prepare()
    with (OUTPUT/'coordinator.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'start.json').exists():raise ValueError('advancement already charged')
        write(OUTPUT/'start.json',dict(manifest_sha256=sha(OUTPUT/'manifest.json')));started=time.monotonic()
        try:
            continued=wait_for(CONTINUATION,started);result=review(continued)
            if not result['passed']:
                write(OUTPUT/'completion.json',dict(state='complete',advanced=False,reason='continuation pair remains unqualified'));return
            command=[sys.executable,str(ROOT/'analysis/tests/run_numerical.py'),'--threads','4','--',
                sys.executable,str(ROOT/'analysis/tests/ilvis0_projected_fullcal_review_worker.py'),'--detach']
            launched=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=120)
            write(OUTPUT/'launch-result.json',dict(exit_code=launched.returncode,stdout=launched.stdout,stderr=launched.stderr))
            if launched.returncode:raise ValueError('full-calibration preparation/launch failed')
            full=wait_for(FULL,started)
            write(OUTPUT/'completion.json',dict(state='complete',advanced=True,fullcal_passed=full['passed']))
            write(OUTPUT/'status.json',dict(state='complete',numerical_threads=0))
        except BaseException as error:
            write(OUTPUT/'failure.json',dict(error=type(error).__name__+': '+str(error)));raise


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--detach',action='store_true');args=parser.parse_args()
    if not args.detach:run();return
    prepare()
    with (OUTPUT/'launch.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'start.json').exists() or (OUTPUT/'launch.json').exists():raise ValueError('advancement launch already charged')
        with (OUTPUT/'coordinator.log').open('ab') as log:
            child=subprocess.Popen([sys.executable,__file__],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
        write(OUTPUT/'launch.json',dict(pid=child.pid));print(json.dumps(dict(state='launched',pid=child.pid,numerical_threads=0)))


if __name__=='__main__':main()
