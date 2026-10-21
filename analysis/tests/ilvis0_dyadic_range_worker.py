#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze six finite full-history child-domain performance checks."""
import argparse
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication

DATA=ROOT/'data/ilvis0-dyadic-range-preflight-20261021';PUBLIC=ROOT/'docs/ilvis0-dyadic-range-preflight'
OLD=ROOT/'docs/ilvis0-taylor-complete-prediction';QUALIFIED=ROOT/'docs/ilvis0-dyadic-native-controls'
TIMING=ROOT/'docs/ilvis0-dyadic-timing'
ADAPTER='analysis/lll/ilvis0_dyadic_range_preflight.py';PLAN='docs/ilvis0-dyadic-range-preflight/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/lll/ilvis0_dyadic_interface.py','analysis/lll/ilvis0_dyadic_timing.py',
    'analysis/tests/ilvis0_dyadic_range_worker.py','analysis/tests/test_ilvis0_dyadic_interface.py',
    'analysis/tests/test_ilvis0_dyadic_timing.py','analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']


def prepare():
    if DATA.exists():raise ValueError('full-history performance already frozen')
    sources=set(SOURCES)
    for directory in (OLD,QUALIFIED,TIMING):
        for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(runner.path_within(directory,name))!=digest:raise ValueError('prerequisite changed')
        manifest=runner._load(directory/'manifest.json')
        if manifest['environment']!=runner.runtime_environment():raise ValueError('numerical environment changed')
        for name,digest in manifest['sources'].items():
            if name.startswith('analysis/lll/'):
                if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
                sources.add(name)
    if not runner._load(QUALIFIED/'summary.json')['passed'] or not runner._load(TIMING/'comparison.json')['qualified']:
        raise ValueError('native equality and useful matched timing required')
    previous=runner._load(OLD/'manifest.json');summary=runner._load(OLD/'summary.json')
    if summary['state']!='terminal':raise ValueError('completed predecessor required')
    records={r['identity']:r for r in summary['results']};inputs={};tasks=[];groups=set()
    compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
    for old in previous['tasks']:
        if not old['identity'].endswith('-0'):continue
        identity=old['identity'];inputs[identity]=str((OLD/previous['inputs'][old['input_key']]['path']).relative_to(ROOT))
        bundle=runner._load(ROOT/inputs[identity]);group=(bundle['result']['task']['model'],bundle['result']['task']['profile'])
        if group in groups or bundle['result']['task']['sector']!=0:raise ValueError('unique fixed source groups required')
        groups.add(group)
        keys={}
        for name in ('case_key','condition_key'):
            key=old['payload'][name];inputs[key]=str((OLD/previous['inputs'][key]['path']).relative_to(ROOT));keys[name]=key
        record=runner._load(OLD/records[identity]['artifact']);baseline=None
        if record['result'].get('passed',False):
            path=next(n for n in record['artifacts'] if Path(n).name=='bound-07.json')
            baseline='baseline-'+identity;inputs[baseline]=str((OLD/path).relative_to(ROOT))
        limits=dict(setups=1,proofs=1,parent_supports=6,source_setups=1,source_steps=1600,
            source_body_bounds=1600,source_derivative_setups=1,source_derivative_steps=1600)
        tasks.append(dict(identity=identity,input_key=identity,
            payload=dict(keys,baseline_key=baseline,compiler=compiler,limits=limits,maximum_bound_seconds=120.),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=1,bound_steps=12800)))
    if len(tasks)!=6 or groups!={(m,p) for m in range(3) for p in (False,True)}:raise ValueError('all six source groups required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=600,environment=runner.runtime_environment())


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);rows=[];accounts=[]
    for item in summary['results']:
        record=runner._load(DATA/item['artifact']);row=record['result'];rows.append(row)
        task=next(t for t in manifest['tasks'] if t['identity']==item['identity'])
        limits=task['payload']['limits'];counts=dict.fromkeys(limits,0)
        for name in sorted(n for n in record['artifacts'] if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);inc=event['increase']
            if not inc or any(k not in counts or type(v)!=int or v<1 for k,v in inc.items()):raise ValueError('invalid reservation')
            counts={k:v+inc.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):raise ValueError('allowance changed')
        if 'work' in row and counts!=row['work']:raise ValueError('source accounting changed')
        for name,resource in (('source_steps','source_steps'),('source_body_bounds','source_body_bounds'),('derivative_steps','source_derivative_steps')):
            if row.get(name,0)>counts[resource]:raise ValueError('source work lacks reservation')
        accounts.append(dict(identity=item['identity'],passed=row.get('passed',False),**counts))
    text=['# Full-history performance on training-restricted domains','',
        f"{sum(r.get('passed',False) for r in rows)}/6 source calculations passed.",'',
        '| Source | Passed | Propagation seconds | Saved predecessor match |','|---|---|---:|---|']
    for item,row in zip(summary['results'],rows,strict=True):
        elapsed=f"{row['bound_elapsed_s']:.3f}" if 'bound_elapsed_s' in row else 'unavailable'
        match='Yes' if row.get('matched',{}).get('passed',False) else 'unavailable'
        text.append(f"| {item['identity']} | {'Yes' if row.get('passed') else 'No'} | {elapsed} | {match} |")
    text+=['',f"Elapsed {summary['elapsed_s']:.2f} seconds; charged {summary['charged']['bound_calls']}/6 bounds "
        f"and {summary['charged']['bound_steps']}/76,800 logical steps.",'',
        'Each source retains its actual complete-comparison child domain and verified parent training proof. '
        'The original 120-second bound limit is unchanged. A missing predecessor remains unavailable. '
        'This is finite implementation qualification, not a complete sector union or an aircraft result. '
        'No original-aircraft measurements, native trajectory oracle, LP or optimizer was used.','',
        '[Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,charged=summary['charged']))
    receipt=runner._load(PUBLIC/'evidence-receipt.json');receipt['artifacts']['accounting.json']=runner._sha(PUBLIC/'accounting.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check','run'):group.add_argument('--'+name,action='store_true')
    parser.add_argument('--reserved-threads',type=int);args=parser.parse_args()
    if args.prepare:prepare();print('Frozen six full-history bounds / 76800 steps / 36 parent supports / four threads.')
    elif args.run:
        if args.reserved_threads is None:parser.error('--run requires --reserved-threads')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Completed full-history screen: '+result['state'])
    elif args.package_only:publish();print('Published saved full-history results.')
    else:publication.check(DATA,PUBLIC);print('Verified full-history performance evidence.')


if __name__=='__main__':main()
