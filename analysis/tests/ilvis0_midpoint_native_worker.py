# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish exact-report midpoint-only native qualification."""
import argparse,subprocess
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-midpoint-native-controls-20261021'
PUBLIC=ROOT/'docs/ilvis0-midpoint-native-controls'
OLD=ROOT/'docs/ilvis0-direct-native-controls'
PLAN='docs/ilvis0-midpoint-native-controls/PLAN.md'
ADAPTER='analysis/lll/ilvis0_midpoint_native_controls.py'


def prepare():
    if DATA.exists():raise ValueError('midpoint qualification already frozen')
    environment=runner.runtime_environment()
    for directory in (OLD,ROOT/'docs/ilvis0-direct-source-cost-profile'):
        for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(runner.path_within(directory,name))!=digest:raise ValueError('sealed qualification/profile changed')
        if not runner._load(directory/'summary.json')['passed']:raise ValueError('passing source prerequisites required')
        if runner._load(directory/'manifest.json')['environment']!=environment:raise ValueError('qualified environment changed')
    previous=runner._load(OLD/'manifest.json');summary=runner._load(OLD/'summary.json')
    sources={PLAN,ADAPTER,'analysis/lll/ilvis0_midpoint_source.py','analysis/lll/ilvis0_midpoint_native.py',
        'analysis/tests/ilvis0_midpoint_native_worker.py','analysis/tests/test_ilvis0_midpoint_source.py',
        'analysis/tests/test_ilvis0_midpoint_native.py','analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py'}
    for name,digest in previous['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
            sources.add(name)
    tasks=[];inputs={};compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
    for old in previous['tasks']:
        identity='midpoint-'+old['identity'];record=previous['inputs'][old['input_key']]
        inputs[identity]=str((OLD/record['path']).relative_to(ROOT))
        result=next(r for r in summary['results'] if r['identity']==old['identity'])
        envelope=runner._load(OLD/result['artifact']);bounds={};ceilings={};fields=None
        for name,digest in envelope['artifacts'].items():
            if not Path(name).name.startswith('bound-'):continue
            if runner._sha(OLD/name)!=digest:raise ValueError('qualified bound changed')
            row=runner._load(OLD/name);index=str(int(Path(name).stem.split('-')[-1]))
            if fields is None:fields=sorted(row)
            if sorted(row)!=fields:raise ValueError('predecessor report schemas differ within case')
            bounds[index]=row
            ceilings[index]={key:row[key] for key in ('unshared_remainder','position_unshared_remainder',
                'force_unshared_remainder','lever_unshared_remainder')}
        if len(bounds)!=old['limits']['bound_calls']:raise ValueError('every qualified predecessor bound required')
        baseline=PUBLIC/'saved-inputs'/(identity+'.json')
        runner._write(baseline,dict(fields=fields,bounds=bounds,ceilings=ceilings))
        baseline_key=identity+'-baseline';inputs[baseline_key]=str(baseline.relative_to(ROOT))
        tasks.append(dict(identity=identity,input_key=identity,limits=old['limits'],
            payload=dict(old['payload'],identity=identity,compiler=compiler,baseline_key=baseline_key)))
    totals={key:sum(t['limits'][key] for t in tasks) for key in ('native_calls','packet_visits','bound_calls','bound_steps')}
    if len(tasks)!=24 or totals!=dict(native_calls=78,packet_visits=19632,bound_calls=348,bound_steps=67824):
        raise ValueError('fixed 24-case qualification matrix changed')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=600,environment=environment)


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);rows=[];accounts=[]
    for item in summary['results']:
        envelope=runner._load(DATA/item['artifact']);row=envelope['result'];rows.append(row)
        task=next(t for t in manifest['tasks'] if t['identity']==item['identity'])
        limits=task['payload']['source_limits'];counts=dict.fromkeys(limits,0)
        for name in sorted(n for n in envelope['artifacts'] if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);inc=event['increase']
            if not inc or any(k not in counts or type(v)!=int or v<1 for k,v in inc.items()):raise ValueError('invalid reservation')
            counts={k:v+inc.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):raise ValueError('reserved source work changed')
        if 'work' in row and row['work']!=counts:raise ValueError('source work mismatch')
        for field in ('arithmetic','source_compilation','source_derivative_compilation','source_point_compilation'):
            for name,digest in row.get(field,{}).get('sources',{}).items():
                if digest!=manifest['sources']['analysis/lll/'+name]:raise ValueError('compiler source changed')
        accounts.append(dict(identity=item['identity'],**counts))
    text=['# Native qualification of the midpoint-only source','',
        f"{sum(r.get('passed',False) for r in rows)}/24 known-answer cases passed. "
        f"Elapsed {summary['elapsed_s']:.2f} seconds.",'',
        f"Charged {summary['charged']['native_calls']}/78 native evaluations and "
        f"{summary['charged']['bound_calls']}/348 bounds. Every successful report must match every "
        'saved predecessor field exactly, including all remainder arrays, rather than merely avoid widening.','',
        'The original physical parameters, clock, coefficient maps, shared errors and acceptance checks '
        'remain. Earlier source and full-matrix failures keep their original labels. No new aircraft '
        'measurement, optimizer, LP or scientific decision is involved.','',
        'These controls do not establish a speedup or useful recording-scale prediction errors. '
        'A separate complete-domain timing comparison is required before new future-bound generation.','',
        '[Frozen scope](PLAN.md) · [Cost profile](../ilvis0-direct-source-cost-profile/README.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,charged=summary['charged']))
    receipt=runner._load(PUBLIC/'evidence-receipt.json');receipt['artifacts']['accounting.json']=runner._sha(PUBLIC/'accounting.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check','run'):group.add_argument('--'+name,action='store_true')
    parser.add_argument('--reserved-threads',type=int);args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 24 exact-report controls / 78 native calls / 348 bounds / 600 seconds.')
    elif args.run:
        if args.reserved_threads is None:parser.error('--run requires --reserved-threads')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Midpoint native qualification: '+result['state'])
    elif args.package_only:publish();print('Published midpoint qualification.')
    else:publication.check(DATA,PUBLIC);print('Verified midpoint qualification.')


if __name__=='__main__':main()
