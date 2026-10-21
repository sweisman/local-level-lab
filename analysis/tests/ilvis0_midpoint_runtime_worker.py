# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish the separately bounded matched runtime comparison."""
import argparse,subprocess
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
from lll.ilvis0_matched_runtime import assess
DATA=ROOT/'data/ilvis0-midpoint-runtime-20261021';PUBLIC=ROOT/'docs/ilvis0-midpoint-runtime'
PLAN='docs/ilvis0-midpoint-runtime/PLAN.md';ADAPTER='analysis/lll/ilvis0_midpoint_runtime.py'


def prepare():
    if DATA.exists():raise ValueError('matched timing already frozen')
    old=ROOT/'docs/ilvis0-direct-range-preflight';qualified=ROOT/'docs/ilvis0-midpoint-native-controls'
    environment=runner.runtime_environment();sources={PLAN,ADAPTER,'analysis/lll/ilvis0_matched_runtime.py',
        'analysis/tests/test_ilvis0_matched_runtime.py','analysis/tests/ilvis0_midpoint_runtime_worker.py',
        'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py'}
    for directory in (old,qualified):
        for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(runner.path_within(directory,name))!=digest:raise ValueError('qualified prerequisite changed')
        manifest=runner._load(directory/'manifest.json')
        if not runner._load(directory/'summary.json')['passed'] or manifest['environment']!=environment:
            raise ValueError('passing prerequisite in the unchanged environment required')
        for name,digest in manifest['sources'].items():
            if name.startswith('analysis/lll/'):
                if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
                sources.add(name)
    previous=runner._load(old/'manifest.json');tasks=[];inputs={}
    compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
    for original in previous['tasks']:
        payload=original['payload'];key=original['input_key']
        bundle=runner._load(old/previous['inputs'][key]['path']);tag=bundle['result']['task']
        if tag['sector']!=0:raise ValueError('original sector-zero screen required')
        model=tag['model'];profile=tag['profile'];order=['predecessor','candidate'] if (model+int(profile))%2==0 else ['candidate','predecessor']
        for name in (key,payload['case_key'],payload['condition_key']):
            inputs[name]=str((old/previous['inputs'][name]['path']).relative_to(ROOT))
        per_bound={k:v for k,v in payload['limits'].items() if k not in ('setups','proofs','parent_supports')}
        limits=dict(setups=1,proofs=1,parent_supports=6,**{k:2*v for k,v in per_bound.items()})
        tasks.append(dict(identity=f'midpoint-time-{model}-{int(profile)}',input_key=key,
            payload=dict(model=model,profile=profile,case_key=payload['case_key'],condition_key=payload['condition_key'],
                order=order,compiler=compiler,maximum_bound_seconds=120.,limits=limits),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=2,bound_steps=28800)))
    if (len(tasks)!=6 or {(t['payload']['model'],t['payload']['profile']) for t in tasks}!={(m,p) for m in range(3) for p in (False,True)}
            or sum(t['payload']['order'][0]=='candidate' for t in tasks)!=3):
        raise ValueError('complete balanced six-case recipe required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=600,environment=environment)


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);rows=[]
    for item in summary['results']:
        envelope=runner._load(DATA/item['artifact']);row=envelope['result']
        task=next(t for t in manifest['tasks'] if t['identity']==item['identity']);spec=task['payload']
        limits=spec['limits'];counts=dict.fromkeys(limits,0)
        for name in sorted(n for n in envelope['artifacts'] if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);inc=event['increase']
            if not inc or any(k not in counts or type(v)!=int or v<1 for k,v in inc.items()):raise ValueError('invalid reservation')
            counts={k:v+inc.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):raise ValueError('matched work changed')
        if 'work' in row and (row['work']!=counts or counts!=limits):raise ValueError('matched work lacks reservation')
        rows.append(dict(row,model=spec['model'],profile=spec['profile']))
    result=assess(rows)
    text=['# Complete-domain runtime comparison','',
        f"{sum(r.get('passed',False) for r in rows)}/6 pairs completed with exact report agreement. "
        f"The fixed runtime screen {'passed' if result['qualified'] else 'did not pass'}.",'',
        '| Candidate / processing | Original | Midpoint-only | Time ratio |',
        '|---|---:|---:|---:|']
    for row in rows:
        label=('Specified-field globe','Zero-field globe','Flat disc')[row['model']]+(' / profiled' if row['profile'] else ' / zero')
        values=(f"{row['predecessor_s']:.3f} s | {row['candidate_s']:.3f} s | {row['candidate_ratio']:.4f}"
            if row.get('passed') else 'incomplete | incomplete | unavailable')
        text.append('| '+label+' | '+values+' |')
    text+=['',f"Median candidate/original ratio: {result['median_ratio']}; maximum: {result['maximum_ratio']}. "
        'The frozen limits are a median at most 0.95, no ratio above 1.10, every pair complete and every report exact.','',
        f"Elapsed {summary['elapsed_s']:.2f} seconds. Charged {summary['charged']['bound_calls']}/12 bounds and "
        f"{summary['charged']['bound_steps']}/172,800 logical steps. Compiler and preparation time are outside "
        'each measured bound. The fixed order is balanced across cases; concurrent load can still affect timings.','',
        'This is an engineering screen on the original complete generated domains. It is not recording-scale '
        'qualification, an aircraft fit or calibrated observational coverage. Earlier failures stay unchanged.','',
        '[Frozen scope](PLAN.md) · [Exact-report qualification](../ilvis0-midpoint-native-controls/README.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'comparison.json',dict(result,cases_detail=rows))
    receipt=runner._load(PUBLIC/'evidence-receipt.json');receipt['artifacts']['comparison.json']=runner._sha(PUBLIC/'comparison.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check','run'):group.add_argument('--'+name,action='store_true')
    parser.add_argument('--reserved-threads',type=int);args=parser.parse_args()
    if args.prepare:prepare();print('Frozen six pairs / twelve bounds / 172,800 steps / four threads / 600 seconds.')
    elif args.run:
        if args.reserved_threads is None:parser.error('--run requires --reserved-threads')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Matched midpoint runtime: '+result['state'])
    elif args.package_only:publish();print('Published matched runtime.')
    else:publication.check(DATA,PUBLIC);print('Verified matched runtime.')


if __name__=='__main__':main()
