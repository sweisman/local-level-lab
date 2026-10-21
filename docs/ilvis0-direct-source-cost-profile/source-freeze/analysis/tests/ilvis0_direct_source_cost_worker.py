# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish an unchanged-source cost profile."""
import argparse,subprocess
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-direct-source-cost-profile-20261021'
PUBLIC=ROOT/'docs/ilvis0-direct-source-cost-profile'
PLAN='docs/ilvis0-direct-source-cost-profile/PLAN.md'
ADAPTER='analysis/lll/ilvis0_direct_source_cost_profile.py'


def prepare():
    if DATA.exists():raise ValueError('source cost profile already frozen')
    sources={PLAN,ADAPTER,'analysis/tests/ilvis0_direct_source_cost_worker.py',
        'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py'}
    provider=ROOT/'docs/ilvis0-direct-complete-prediction'
    qualified=ROOT/'docs/ilvis0-direct-native-controls';environment=runner.runtime_environment()
    for directory in (provider,qualified):
        for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(runner.path_within(directory,name))!=digest:raise ValueError('sealed input changed')
        manifest=runner._load(directory/'manifest.json')
        if manifest['environment']!=environment:raise ValueError('qualified environment changed')
        for name,digest in manifest['sources'].items():
            if name.startswith('analysis/lll/'):
                if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
                sources.add(name)
    if not runner._load(qualified/'summary.json')['passed']:raise ValueError('qualified native source required')
    previous=runner._load(provider/'manifest.json');tasks=[];inputs={}
    compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
    for model in range(3):
        for profile in (False,True):
            identity=f'transform-full-{model}-{int(profile)}-7'
            old=next(t for t in previous['tasks'] if t['identity']==identity);key=old['payload']['case_key']
            for name in (old['input_key'],key):inputs[name]=str((provider/previous['inputs'][name]['path']).relative_to(ROOT))
            limits=dict(setups=1,source_steps=1600,derivative_setups=1,derivative_steps=1600,point_setups=1,direct_steps=1600)
            tasks.append(dict(identity='source-cost-'+identity,input_key=old['input_key'],
                payload=dict(model=model,profile=profile,case_key=key,compiler=compiler,limits=limits,maximum_profile_seconds=90.),
                limits=dict(native_calls=0,packet_visits=0,bound_calls=1,bound_steps=4800)))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=240,environment=environment)


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);rows=[]
    for item in summary['results']:
        envelope=runner._load(DATA/item['artifact']);row=envelope['result'];rows.append(row)
        task=next(t for t in manifest['tasks'] if t['identity']==item['identity'])
        limits=task['payload']['limits'];counts=dict.fromkeys(limits,0)
        for name in sorted(n for n in envelope['artifacts'] if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);inc=event['increase']
            if not inc or any(k not in counts or type(v)!=int or v<1 for k,v in inc.items()):raise ValueError('invalid reservation')
            counts={k:v+inc.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):raise ValueError('source work changed')
        if 'work' in row and (row['work']!=counts or counts!=limits):raise ValueError('source profile work mismatch')
        if row.get('native_evaluations',0) or row.get('original_reads',0) or row.get('optimizer_starts',0):
            raise ValueError('source profile ran unauthorized work')
    text=['# Where the source calculation spends its time','',
        f"{sum(r.get('passed',False) for r in rows)}/6 original source profiles completed. "
        f"Elapsed {summary['elapsed_s']:.2f} seconds.",'',
        '| Candidate / processing | Prefixes | Physical values | Derivative intervals | Direct remainder |',
        '|---|---:|---:|---:|---:|']
    for row in rows:
        if 'components' not in row:continue
        label=('Specified-field globe','Zero-field globe','Flat disc')[row['model']]+(' / profiled' if row['profile'] else ' / zero')
        values={r['file']:r['cumulative_s'] for r in row['components']}
        text.append(f"| {label} | {row['actual_visits']['physical']}/{row['expected_prefixes']} | "+
            ' | '.join(f"{values.get(name,0):.3f} s" for name in ('ilvis0_batched_source_values.py',
                'ilvis0_source_derivative_intervals.py','ilvis0_direct_source.py'))+' |')
    text+=['','Profiler overhead is included. These timings cover only source streams, not full prediction bounds. '
        'Both original phase certificates and endpoint rotation state remain. No optimization is qualified by these timings.','',
        f"Charged {summary['charged']['bound_calls']}/6 source profiles and {summary['charged']['bound_steps']}/28,800 "
        'logical source steps; unused reserved work remains charged. No full native trajectory, LP, optimizer '
        'or original-aircraft read ran.','',
        '[Frozen scope](PLAN.md) · [Remaining width](../ilvis0-east-width-audit/INTERPRETATION.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check','run'):group.add_argument('--'+name,action='store_true')
    parser.add_argument('--reserved-threads',type=int);args=parser.parse_args()
    if args.prepare:prepare();print('Frozen six source profiles / 28,800 source steps / four threads / 240 seconds.')
    elif args.run:
        if args.reserved_threads is None:parser.error('--run requires --reserved-threads')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Source cost profile: '+result['state'])
    elif args.package_only:publish();print('Published source cost profile.')
    else:publication.check(DATA,PUBLIC);print('Verified source cost profile.')


if __name__=='__main__':main()
