#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish finite independent direct-source remainder controls."""
import argparse
import importlib.metadata
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-direct-source-controls-20261021';PUBLIC=ROOT/'docs/ilvis0-direct-source-controls'
PLAN='docs/ilvis0-direct-source-controls/PLAN.md';ADAPTER='analysis/lll/ilvis0_direct_source_controls.py'


def prepare():
    if DATA.exists():raise ValueError('direct-source controls already frozen')
    previous=ROOT/'data/ilvis0-source-point-controls-20261021'
    manifest=runner.verify(previous)
    if not runner.verify_completion(previous)['passed']:raise ValueError('passing point controls required')
    sources=[]
    for name,digest in manifest['sources'].items():
        if name.startswith('analysis/lll/') or name=='analysis/tests/test_ilvis0_source_point_derivatives.py':
            if runner._sha(ROOT/name)!=digest:raise ValueError('qualified point source changed')
            sources.append(name)
    sources.extend((ADAPTER,PLAN,'analysis/lll/ilvis0_direct_source.py','analysis/lll/ilvis0_source_remainder.py',
        'analysis/tests/test_ilvis0_direct_source.py','analysis/tests/ilvis0_direct_source_worker.py',
        'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py'))
    catalog=[]
    for wide in (False,True):
        for index,time in enumerate((3/512,2/256)):
            catalog.append(dict(identity=f'chain-{int(wide)}-{index}',
                function='test_direct_remainders_contain_independent_calibrated_rotation_chains',
                arguments=[time,wide],bounds=12,steps=4,
                auxiliary_limits=dict(initializations=1,rational_references=135 if wide else 108,rejections=0)))
    catalog.append(dict(identity='bridge-rejections',function='test_bridge_accounts_for_all_columns_and_rejects_domain_mismatch',
        arguments=[],bounds=4,steps=2,auxiliary_limits=dict(initializations=1,rational_references=0,rejections=5)))
    if sum(c['bounds'] for c in catalog)!=52 or sum(c['steps'] for c in catalog)!=18:
        raise ValueError('direct-source recipe changed')
    path=PUBLIC/'control-catalog.json';runner._write(path,catalog);tasks=[]
    compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
    for item in catalog:
        tasks.append(dict(identity=item['identity'],input_key='catalog',
            payload=dict(item,compiler=compiler,pytest=importlib.metadata.version('pytest')),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=item['bounds'],bound_steps=item['steps'])))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sources,inputs=dict(catalog=str(path.relative_to(ROOT))),
        adapter=ADAPTER,workers=1,threads=1,maximum_wall_s=120,environment=runner.runtime_environment())


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);rows=[];accounts=[]
    for item in summary['results']:
        record=runner._load(DATA/item['artifact']);row=record['result'];rows.append(row)
        task=next(t for t in manifest['tasks'] if t['identity']==item['identity'])
        limits=task['payload']['auxiliary_limits'];counts=dict.fromkeys(limits,0)
        for name in sorted(n for n in record['artifacts'] if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);inc=event['increase']
            if not inc or any(k not in counts or type(v)!=int or v<1 for k,v in inc.items()):raise ValueError('invalid reservation')
            counts={k:v+inc.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):raise ValueError('allowance changed')
        if 'work' in row and counts!=row['work']:raise ValueError('direct-source work differs from reservation')
        accounts.append(dict(identity=item['identity'],**counts))
    text=['# Direct source and reference-transfer controls','',
        f"{sum(r.get('passed',False) for r in rows)}/5 fixed controls passed.",'',
        f"Charged {summary['charged']['bound_calls']}/52 bound calls and {summary['charged']['bound_steps']}/18 packet steps. "
        f"Elapsed {summary['elapsed_s']:.2f} seconds.",'',
        'Separate exact-rational chains check both clock sides, narrow/broad gain domains, noncommuting rotations and displaced numerical values/rows. '
        'All 27 columns remain in the reference transfer. No trajectory fits or aircraft data were used. '
        'Complete native integration, full-history usefulness, useful prediction widths and observational confidence are not established here.','',
        '[Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,charged=summary['charged']))
    receipt=runner._load(PUBLIC/'evidence-receipt.json');receipt['artifacts']['accounting.json']=runner._sha(PUBLIC/'accounting.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check','run'):group.add_argument('--'+name,action='store_true')
    parser.add_argument('--reserved-threads',type=int);args=parser.parse_args()
    if args.prepare:prepare();print('Frozen five direct-source controls / 52 bounds / 18 steps / one thread.')
    elif args.run:
        if args.reserved_threads is None:parser.error('--run requires --reserved-threads')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Direct source controls: '+result['state'])
    elif args.package_only:publish();print('Published saved direct-source controls.')
    else:publication.check(DATA,PUBLIC);print('Verified direct-source component evidence.')


if __name__=='__main__':main()
