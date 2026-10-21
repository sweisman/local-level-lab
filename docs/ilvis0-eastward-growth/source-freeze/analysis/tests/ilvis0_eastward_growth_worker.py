#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish eight fixed generated-source propagation traces."""
import argparse
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication

DATA=ROOT/'data/ilvis0-eastward-growth-20261021';PUBLIC=ROOT/'docs/ilvis0-eastward-growth'
OLD=ROOT/'docs/ilvis0-taylor-complete-prediction';QUALIFIED=ROOT/'docs/ilvis0-traced-native-controls'
ADAPTER='analysis/lll/ilvis0_eastward_growth.py';PLAN='docs/ilvis0-eastward-growth/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/lll/ilvis0_dyadic_interface.py','analysis/lll/ilvis0_dyadic_timing.py',
    'analysis/tests/ilvis0_eastward_growth_worker.py','analysis/tests/test_ilvis0_dyadic_interface.py',
    'analysis/tests/test_ilvis0_traced_native.py','analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']


def prepare():
    if DATA.exists():raise ValueError('eastward trace already frozen')
    sources=set(SOURCES)
    for directory in (OLD,QUALIFIED):
        for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(runner.path_within(directory,name))!=digest:raise ValueError('prerequisite changed')
        manifest=runner._load(directory/'manifest.json')
        if manifest['environment']!=runner.runtime_environment():raise ValueError('numerical environment changed')
        for name,digest in manifest['sources'].items():
            if name.startswith('analysis/lll/'):
                if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
                sources.add(name)
    if not runner._load(QUALIFIED/'summary.json')['passed']:raise ValueError('complete tracing qualification required')
    previous=runner._load(OLD/'manifest.json');summary=runner._load(OLD/'summary.json')
    if summary['state']!='terminal':raise ValueError('completed predecessor required')
    records={r['identity']:r for r in summary['results']};inputs={};tasks=[]
    compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
    targets={f'transform-full-0-{int(p)}-{sector}' for p in (False,True) for sector in (1,7)}
    for old in previous['tasks']:
        parent_id=old['identity']
        if parent_id not in targets:continue
        record=runner._load(OLD/records[parent_id]['artifact'])
        if not record['result'].get('passed'):raise ValueError('fixed endpoint predecessor unavailable')
        keys={}
        for field in ('case_key','condition_key'):
            key=old['payload'][field];inputs[key]=str((OLD/previous['inputs'][key]['path']).relative_to(ROOT));keys[field]=key
        for index,time in ((6,6.),(7,7.2)):
            identity=parent_id+('-training' if index==6 else '-future')
            inputs[identity]=str((OLD/previous['inputs'][old['input_key']]['path']).relative_to(ROOT))
            name=next(n for n in record['artifacts'] if Path(n).name==f'bound-{index:02d}.json')
            baseline=runner._load(OLD/name)
            if baseline['time_s']!=time:raise ValueError('fixed query reference changed')
            baseline_key='baseline-'+identity;inputs[baseline_key]=str((OLD/name).relative_to(ROOT))
            limits=dict(setups=1,proofs=1,parent_supports=6,source_setups=1,source_steps=1600,
                source_body_bounds=1600,source_derivative_setups=1,source_derivative_steps=1600,trace_snapshots=32)
            tasks.append(dict(identity=identity,input_key=identity,
                payload=dict(keys,baseline_key=baseline_key,compiler=compiler,limits=limits,
                    maximum_bound_seconds=120.,time_s=time,nominal=baseline['center'],trace_stride=128),
                limits=dict(native_calls=0,packet_visits=0,bound_calls=1,bound_steps=12800)))
    if len(tasks)!=8:raise ValueError('all eight fixed source/time identities required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=600,environment=runner.runtime_environment())


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);rows=[];accounts=[];diagnostics=[]
    for item in summary['results']:
        record=runner._load(DATA/item['artifact']);row=record['result'];rows.append(row)
        task=next(t for t in manifest['tasks'] if t['identity']==item['identity'])
        limits=task['payload']['limits'];counts=dict.fromkeys(limits,0)
        for name in sorted(n for n in record['artifacts'] if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);inc=event['increase']
            if not inc or any(k not in counts or type(v)!=int or v<1 for k,v in inc.items()):raise ValueError('invalid reservation')
            counts={k:v+inc.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):raise ValueError('allowance changed')
        if 'work' in row and counts!=row['work']:raise ValueError('trace accounting changed')
        for field,resource in (('source_steps','source_steps'),('source_body_bounds','source_body_bounds'),
                ('derivative_steps','source_derivative_steps'),('trace_snapshots','trace_snapshots')):
            if row.get(field,0)>counts[resource]:raise ValueError('trace work lacks reservation')
        accounts.append(dict(identity=item['identity'],passed=row.get('passed',False),**counts))
        if row.get('passed'):
            name=next(n for n in record['artifacts'] if Path(n).name=='bound.json');bound=runner._load(DATA/name)
            trace=bound['propagation_trace'];last=trace['rows'][-1];scale=row['coordinate_scale'][1]
            if len(trace['rows'])!=row['trace_snapshots']:raise ValueError('trace snapshot count changed')
            diagnostics.append(dict(identity=item['identity'],profile=row['profile'],sector=row['sector'],time_s=row['time_s'],
                source_a_east=last['increment']['source_a']['component_remainder'][1],
                source_b_east=last['increment']['source_b']['component_remainder'][1],
                force_rest_east=last['increment']['force_rest']['component_remainder'][1],
                residual_velocity_east=last['residual_velocity_remainder'][1],
                departure_east_m=last['departure_remainder'][1]*scale,
                final_position_east_m=bound['position_unshared_remainder'][1]*scale,
                force_east_m=bound['force_unshared_remainder'][1]*scale,
                lever_east_m=bound['lever_unshared_remainder'][1]*scale,
                final_east_m=bound['unshared_remainder'][1]*scale,snapshots=len(trace['rows'])))
    text=['# Eastward propagation-allowance growth','',
        f"{sum(r.get('passed',False) for r in rows)}/8 fixed query traces passed exact predecessor checks.",'',
        '| Source | Query seconds | Departure allowance (m) | Final position allowance (m) | Force allowance (m) | Lever allowance (m) | Final allowance (m) |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for d in diagnostics:
        text.append(f"| {d['identity']} | {d['time_s']} | "+' | '.join(f'{d[k]:.6g}' for k in
            ('departure_east_m','final_position_east_m','force_east_m','lever_east_m','final_east_m'))+' |')
    text+=['',f"Elapsed {summary['elapsed_s']:.2f} seconds; charged {summary['charged']['bound_calls']}/8 bounds "
        f"and {summary['charged']['bound_steps']}/102,400 logical steps. Retained {sum(d['snapshots'] for d in diagnostics)}/256 allowed snapshots.",'',
        'These are overlapping bounds on generated trajectories, not measured aircraft errors. '
        'The departure term is part of the position term; force is also included there. '
        'Do not add the table columns as independent contributions. '
        'No bound is reduced, no missing model comparison is completed, and no observational '
        'uncertainty or scientific detection is established.','',
        '[Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,charged=summary['charged']))
    runner._replace(PUBLIC/'diagnostics.json',dict(cases=diagnostics,nested_allowances_are_not_additive=True))
    receipt=runner._load(PUBLIC/'evidence-receipt.json')
    for name in ('accounting.json','diagnostics.json'):receipt['artifacts'][name]=runner._sha(PUBLIC/name)
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check','run'):group.add_argument('--'+name,action='store_true')
    parser.add_argument('--reserved-threads',type=int);args=parser.parse_args()
    if args.prepare:prepare();print('Frozen eight traces / 102400 logical steps / 48 parent supports / 256 snapshots.')
    elif args.run:
        if args.reserved_threads is None:parser.error('--run requires --reserved-threads')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Completed growth traces: '+result['state'])
    elif args.package_only:publish();print('Published saved growth traces.')
    else:publication.check(DATA,PUBLIC);print('Verified propagation-growth evidence.')


if __name__=='__main__':main()
