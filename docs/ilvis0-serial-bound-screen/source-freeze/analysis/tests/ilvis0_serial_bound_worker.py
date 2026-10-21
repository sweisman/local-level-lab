# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish a serial recipe without changing bound mathematics."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-serial-bound-screen-20261021';PUBLIC=ROOT/'docs/ilvis0-serial-bound-screen'
PLAN='docs/ilvis0-serial-bound-screen/PLAN.md';ADAPTER='analysis/lll/ilvis0_serial_bound_screen.py'


def prepare():
    if DATA.exists():raise ValueError('serial screen already frozen')
    old=ROOT/'docs/ilvis0-direct-range-preflight';environment=runner.runtime_environment()
    sources={PLAN,ADAPTER,'analysis/lll/ilvis0_direct_range_preflight.py',
        'analysis/tests/ilvis0_serial_bound_worker.py','analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py'}
    for directory in (old,ROOT/'docs/ilvis0-direct-native-controls',ROOT/'docs/ilvis0-whole-bound-profile'):
        for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(runner.path_within(directory,name))!=digest:raise ValueError('sealed prerequisite changed')
        manifest=runner._load(directory/'manifest.json')
        if not runner._load(directory/'summary.json')['passed'] or manifest['environment']!=environment:
            raise ValueError('passing prerequisite in the same environment required')
    previous=runner._load(old/'manifest.json');summary=runner._load(old/'summary.json')
    for name,digest in previous['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
            sources.add(name)
    tasks=[];inputs={}
    for task in previous['tasks']:
        record=next(r for r in summary['results'] if r['identity']==task['identity'])
        envelope=runner._load(old/record['artifact']);result=envelope['result']
        if not result['passed']:raise ValueError('complete original report required')
        names=[n for n in envelope['artifacts'] if Path(n).name=='bound.json']
        if len(names)!=1:raise ValueError('one exact original bound required')
        baseline_key=task['identity']+'-serial-exact';inputs[baseline_key]=str((old/names[0]).relative_to(ROOT))
        payload=task['payload']
        for key in (task['input_key'],payload['case_key'],payload['condition_key']):
            inputs[key]=str((old/previous['inputs'][key]['path']).relative_to(ROOT))
        tasks.append(dict(identity='serial-'+task['identity'],input_key=task['input_key'],limits=task['limits'],
            payload=dict(payload,baseline_key=baseline_key,exact_report_key=baseline_key,maximum_bound_seconds=120.)))
    if len(tasks)!=6 or sum(t['limits']['bound_steps'] for t in tasks)!=86400:
        raise ValueError('original six-case serial screen required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=1,threads=1,maximum_wall_s=900,environment=environment)


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);rows=[]
    for item in summary['results']:
        envelope=runner._load(DATA/item['artifact']);row=envelope['result'];rows.append(row)
        task=next(t for t in manifest['tasks'] if t['identity']==item['identity']);limits=task['payload']['limits']
        counts=dict.fromkeys(limits,0)
        for name in sorted(n for n in envelope['artifacts'] if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);inc=event['increase']
            if not inc or any(k not in counts or type(v)!=int or v<1 for k,v in inc.items()):raise ValueError('invalid reservation')
            counts={k:v+inc.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):raise ValueError('serial work changed')
        if 'work' in row and (row['work']!=counts or counts!=limits):raise ValueError('serial resource mismatch')
        if row.get('native_evaluations',0) or row.get('original_reads',0) or row.get('optimizer_starts',0):
            raise ValueError('unauthorized serial screen work')
    qualified=summary['passed'] and all(r.get('exact_report_match') is True for r in rows) and len(rows)==6
    text=['# Serial execution of the unchanged calculation','',
        f"{sum(r.get('passed',False) for r in rows)}/6 cases passed; serial execution recipe "
        f"{'qualified' if qualified else 'not qualified'}.",'',
        '| Case | Bound seconds | Exact saved report |','|---|---:|---|']
    for item,row in zip(summary['results'],rows,strict=True):
        elapsed=f"{row['bound_elapsed_s']:.3f}" if 'bound_elapsed_s' in row else 'unfinished'
        text.append(f"| {item['identity']} | {elapsed} | {'Yes' if row.get('exact_report_match') else 'No'} |")
    text+=['',f"Elapsed {summary['elapsed_s']:.2f} seconds. Charged {summary['charged']['bound_calls']}/6 bounds and "
        f"{summary['charged']['bound_steps']}/86,400 logical steps. The per-bound ceiling remains 120 seconds; "
        'only the separately frozen worker allocation is changed.','',
        'This is a finite execution check, not a causal concurrency benchmark, a new mathematical bound '
        'or an aircraft result. The failed four-worker study and unused-endpoint optimization remain '
        'unchanged. Future certificate generation needs a separate finite freeze.','',
        '[Frozen scope](PLAN.md) · [Whole-bound profile](../ilvis0-whole-bound-profile/README.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'verdict.json',dict(qualified=qualified,observational_coverage_qualified=False,
        scientific_decision='abstain'))
    receipt=runner._load(PUBLIC/'evidence-receipt.json');receipt['artifacts']['verdict.json']=runner._sha(PUBLIC/'verdict.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check','run'):group.add_argument('--'+name,action='store_true')
    parser.add_argument('--reserved-threads',type=int);args=parser.parse_args()
    if args.prepare:prepare();print('Frozen six serial cases / 86,400 steps / one thread / 900 seconds.')
    elif args.run:
        if args.reserved_threads is None:parser.error('--run requires --reserved-threads')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Serial execution screen: '+result['state'])
    elif args.package_only:publish();print('Published serial execution screen.')
    else:publication.check(DATA,PUBLIC);print('Verified serial execution screen.')


if __name__=='__main__':main()
