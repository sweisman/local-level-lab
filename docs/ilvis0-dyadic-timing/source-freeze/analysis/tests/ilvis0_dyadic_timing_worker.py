#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish a finite serial implementation benchmark."""
import argparse
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication
from lll.ilvis0_sharded_native import read

DATA=ROOT/'data/ilvis0-dyadic-timing-20261021';PUBLIC=ROOT/'docs/ilvis0-dyadic-timing'
OLD=ROOT/'docs/ilvis0-taylor-runtime-profile';QUALIFIED=ROOT/'docs/ilvis0-dyadic-native-controls'
ADAPTER='analysis/lll/ilvis0_dyadic_timing.py';PLAN='docs/ilvis0-dyadic-timing/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/tests/ilvis0_dyadic_timing_worker.py',
    'analysis/tests/test_ilvis0_dyadic_timing.py','analysis/tests/ilvis0_control_shards.py',
    'analysis/tests/run_numerical.py']


def prepare():
    if DATA.exists():raise ValueError('matched timing already frozen')
    sources=set(SOURCES)
    for directory in (OLD,QUALIFIED):
        for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(runner.path_within(directory,name))!=digest:
                raise ValueError('published prerequisite changed')
        previous=runner._load(directory/'manifest.json')
        if not runner._load(directory/'summary.json')['passed'] or previous['environment']!=runner.runtime_environment():
            raise ValueError('qualified unchanged prerequisites required')
        for name,digest in previous['sources'].items():
            if name.startswith('analysis/lll/'):
                if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
                sources.add(name)
    previous=runner._load(OLD/'manifest.json');inputs={};tasks=[]
    compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
    for profile in (False,True):
        old=next(t for t in previous['tasks'] if t['payload']['profile'] is profile)
        path=OLD/previous['inputs'][old['input_key']]['path']
        for implementation in (('taylor','dyadic') if not profile else ('dyadic','taylor')):
            identity=('profiled-' if profile else 'fixed-')+implementation
            inputs[identity]=str(path.relative_to(ROOT))
            tasks.append(dict(identity=identity,input_key=identity,
                payload=dict(old['payload'],implementation=implementation,compiler=compiler),
                limits=dict(native_calls=0,packet_visits=0,bound_calls=1,bound_steps=1024)))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,
        adapter=ADAPTER,workers=1,threads=1,maximum_wall_s=240,environment=runner.runtime_environment())


def publish():
    from lll.ilvis0_dyadic_timing import matched_bounds
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);rows={};accounts=[]
    for item in summary['results']:
        record=runner._load(DATA/item['artifact']);row=record['result']
        task=next(t for t in manifest['tasks'] if t['identity']==item['identity'])
        limits=task['payload']['limits'];counts=dict.fromkeys(limits,0)
        for name in sorted(n for n in record['artifacts'] if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);inc=event['increase']
            if not inc or any(k not in counts or type(v)!=int or v<1 for k,v in inc.items()):raise ValueError('invalid reservation')
            counts={k:v+inc.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):raise ValueError('changed allowance')
        if 'work' in row and counts!=row['work']:raise ValueError('timing accounting mismatch')
        bound=next((name for name in record['artifacts'] if Path(name).name=='bound.json'),None)
        rows[item['identity']]=(row,runner._load(DATA/bound) if bound else None)
        accounts.append(dict(identity=item['identity'],**counts))
    pairs=[]
    for profile in (False,True):
        label='profiled-' if profile else 'fixed-';old,a=rows[label+'taylor'];new,b=rows[label+'dyadic']
        complete=bool(old.get('passed') and new.get('passed') and a is not None and b is not None)
        pair=dict(profile=profile,complete=complete,matched=False)
        if complete:
            comparison=matched_bounds(a,b);before=old['timing']['elapsed_s'];after=new['timing']['elapsed_s']
            pair.update(matched=comparison['passed'],comparison=comparison,old_seconds=before,new_seconds=after,
                ratio=after/before,new_faster=after<before)
        pairs.append(pair)
    qualified=all(p['complete'] and p['matched'] and p['new_faster'] for p in pairs)
    old_total=sum(p.get('old_seconds',0.) for p in pairs);new_total=sum(p.get('new_seconds',0.) for p in pairs)
    qualified=qualified and new_total<=.95*old_total
    comparison=dict(pairs=pairs,qualified=qualified,old_seconds=old_total,new_seconds=new_total,
        observational_coverage_qualified=False,scientific_decision='abstain')
    text=['# Matched propagation timing','',
        'The preregistered engineering screen passed: '+('**yes**.' if qualified else '**no**.'),'',
        '| Processing | Exact match | Original seconds | Integer seconds | New / old |','|---|---|---:|---:|---:|']
    for p in pairs:
        label='Profiled removal' if p['profile'] else 'Fixed-zero removal'
        numbers=' | '.join(f"{p[k]:.4f}" for k in ('old_seconds','new_seconds','ratio')) if p['complete'] else 'unavailable | unavailable | unavailable'
        text.append(f"| {label} | {'Yes' if p['matched'] else 'No'} | {numbers} |")
    text+=['',f"Elapsed {summary['elapsed_s']:.2f} seconds; charged {summary['charged']['bound_calls']}/4 bounds "
        f"and {summary['charged']['bound_steps']}/4,096 logical steps.",'',
        'Each implementation ran once per source, with alternating order in one single-thread worker. '
        'Compilation and profiler instrumentation are excluded from propagation time. '
        'This is a short engineering screen, not a general speed guarantee or an aircraft result. '
        'No failed study was retried, and no new scientific uncertainty was established.','',
        '[Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'comparison.json',comparison);runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,charged=summary['charged']))
    receipt=runner._load(PUBLIC/'evidence-receipt.json')
    for name in ('comparison.json','accounting.json'):receipt['artifacts'][name]=runner._sha(PUBLIC/name)
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check','run'):group.add_argument('--'+name,action='store_true')
    parser.add_argument('--reserved-threads',type=int);args=parser.parse_args()
    if args.prepare:prepare();print('Frozen four serial bounds / 4096 steps / one numerical thread.')
    elif args.run:
        if args.reserved_threads is None:parser.error('--run requires --reserved-threads')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Completed timing: '+result['state'])
    elif args.package_only:publish();print('Published saved timing results.')
    else:publication.check(DATA,PUBLIC);print('Verified matched-timing evidence.')


if __name__=='__main__':main()
