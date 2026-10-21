# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish one bounded whole-calculation cost diagnostic."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-whole-bound-profile-20261021';PUBLIC=ROOT/'docs/ilvis0-whole-bound-profile'
PLAN='docs/ilvis0-whole-bound-profile/PLAN.md';ADAPTER='analysis/lll/ilvis0_whole_bound_profile.py'


def prepare():
    if DATA.exists():raise ValueError('whole-bound profile already frozen')
    old=ROOT/'docs/ilvis0-direct-range-preflight';manifest=runner._load(old/'manifest.json')
    for name,digest in runner._load(old/'evidence-receipt.json')['artifacts'].items():
        if runner._sha(runner.path_within(old,name))!=digest:raise ValueError('sealed domain changed')
    if not runner._load(old/'summary.json')['passed'] or manifest['environment']!=runner.runtime_environment():
        raise ValueError('unchanged qualified domain and environment required')
    sources={PLAN,ADAPTER,'analysis/tests/ilvis0_whole_bound_profile_worker.py',
        'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py'}
    for name,digest in manifest['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
            sources.add(name)
    sources.add('analysis/lll/ilvis0_direct_range_preflight.py')
    selected=[]
    for task in manifest['tasks']:
        bundle=runner._load(old/manifest['inputs'][task['input_key']]['path']);tag=bundle['result']['task']
        if (tag['model'],tag['profile'],tag['sector'])==(0,False,0):selected.append(task)
    if len(selected)!=1:raise ValueError('one fixed original specified-field domain required')
    old_task=selected[0];payload=old_task['payload'];inputs={}
    for key in (old_task['input_key'],payload['case_key'],payload['condition_key']):
        inputs[key]=str((old/manifest['inputs'][key]['path']).relative_to(ROOT))
    task=dict(identity='whole-bound-specified-zero',input_key=old_task['input_key'],
        payload=dict(payload,baseline_key=None,maximum_bound_seconds=90.),
        limits=dict(native_calls=0,packet_visits=0,bound_calls=1,bound_steps=14400))
    runner.prepare(DATA,project_root=ROOT,tasks=[task],sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=1,threads=1,maximum_wall_s=150,environment=runner.runtime_environment())


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA)
    envelope=runner._load(DATA/summary['results'][0]['artifact']);row=envelope['result']
    limits=manifest['tasks'][0]['payload']['limits'];counts=dict.fromkeys(limits,0)
    for name in sorted(n for n in envelope['artifacts'] if Path(n).name.startswith('reservation-')):
        event=runner._load(DATA/name);inc=event['increase']
        if not inc or any(k not in counts or type(v)!=int or v<1 for k,v in inc.items()):raise ValueError('invalid reservation')
        counts={k:v+inc.get(k,0) for k,v in counts.items()}
        if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):raise ValueError('profile reservation changed')
    if row.get('native_evaluations',0) or row.get('original_reads',0) or row.get('optimizer_starts',0):
        raise ValueError('unauthorized profile work')
    text=['# Whole-bound cost profile','',
        'Full bound completed: '+('**yes**.' if row.get('bound_completed') else '**no**; the partial profile is retained.'),'',
        f"Wall time: {row.get('wall_s')}; process CPU time: {row.get('process_cpu_s')}; "
        f"CPU/wall ratio: {row.get('cpu_to_wall_ratio')}.",'',
        '| Function | Calls | Cumulative seconds |','|---|---:|---:|']
    for r in row.get('functions',[])[:20]:
        text.append(f"| {r['file']}:{r['function']} | {r['calls']} | {r['cumulative_s']:.4f} |")
    text+=['',f"Charged {summary['charged']['bound_calls']}/1 bound and {summary['charged']['bound_steps']}/14,400 logical steps. "
        'Profiler overhead is included; setup and compilation also appear in the function list. '
        'This diagnostic supplies no replacement certificate, speed qualification or aircraft result. '
        'If unfinished, the original finite allowance remains spent.','',
        '[Frozen scope](PLAN.md) · [Failed timing comparison](../ilvis0-midpoint-runtime/INTERPRETATION.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check','run'):group.add_argument('--'+name,action='store_true')
    parser.add_argument('--reserved-threads',type=int);args=parser.parse_args()
    if args.prepare:prepare();print('Frozen one whole-bound profile / 14,400 steps / one thread / 150 seconds.')
    elif args.run:
        if args.reserved_threads is None:parser.error('--run requires --reserved-threads')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Whole-bound profile: '+result['state'])
    elif args.package_only:publish();print('Published whole-bound profile.')
    else:publication.check(DATA,PUBLIC);print('Verified whole-bound profile.')


if __name__=='__main__':main()
