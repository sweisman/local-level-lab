# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish finite known-answer source derivative controls."""
import argparse
import importlib.metadata
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication

DATA=ROOT/'data/ilvis0-source-derivative-v2-controls-20261021'
PUBLIC=ROOT/'docs/ilvis0-source-derivative-v2-controls'
PLAN='docs/ilvis0-source-derivative-v2-controls/PLAN.md'
ADAPTER='analysis/lll/ilvis0_source_derivative_v2_controls.py'


def prepare():
    if DATA.exists():raise ValueError('source derivative study already frozen')
    predecessor=ROOT/'docs/ilvis0-batched-native-controls'
    receipt=runner._load(predecessor/'evidence-receipt.json')
    for name,digest in receipt['artifacts'].items():
        if runner._sha(runner.path_within(predecessor,name))!=digest:raise ValueError('sealed prerequisite changed')
    manifest=runner._load(predecessor/'manifest.json')
    if not runner._load(predecessor/'summary.json')['passed']:raise ValueError('passing native predecessor required')
    if manifest['environment']!=runner.runtime_environment():raise ValueError('numerical environment changed')
    sources=set()
    for name,digest in manifest['sources'].items():
        if name.startswith('analysis/lll/') or name=='analysis/tests/test_ilvis0_native_box_bounds.py':
            if runner._sha(ROOT/name)!=digest:raise ValueError('reference source changed')
            sources.add(name)
    sources.update((ADAPTER,PLAN,'analysis/lll/ilvis0_source_derivative_intervals.py',
        'analysis/lll/ilvis0_source_derivative_intervals.cpp','analysis/tests/test_ilvis0_source_derivative_intervals.py',
        'analysis/tests/ilvis0_source_derivative_v2_worker.py','analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py'))
    catalog=[]
    for index,angle in enumerate(([0,0,0],[1e-12,-2e-12,3e-12],[.01,-.02,.003],[1.,-.3,.2],[8.,0,0])):
        catalog.append(dict(identity=f'rotation-{index}',function='test_rotation_values_and_derivatives_enclose_rational_reference',
            angle=angle,bounds=1,steps=1,initializations=0,rational=3))
    for identity,function,bounds,steps,initializations,rational in (
        ('zero-force','test_zero_motion_force_calibration_and_clock_crossing',13,52,1,0),
        ('nonzero-prefix','test_nonzero_prefix_values_and_bias_gain_rows_match_independent_rational_rotation',4,16,1,24),
        ('clock-boundary','test_clock_domain_crossing_packet_end_contains_both_one_sided_slopes',2,8,1,2),
        ('mean-value','test_mean_value_bound_accounts_for_arbitrary_supplied_rows_and_center',1,0,0,0),
        ('invalid-inputs','test_invalid_source_domains_and_stream_mutation_are_rejected',1,4,2,0)):
        catalog.append(dict(identity=identity,function=function,bounds=bounds,steps=steps,initializations=initializations,rational=rational))
    path=PUBLIC/'control-catalog.json';runner._write(path,catalog)
    compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0];tasks=[]
    for item in catalog:
        payload=dict(function=item['function'],compiler=compiler,pytest=importlib.metadata.version('pytest'),
            rational_references=item['rational'],auxiliary_limits=dict(source_initializations=item['initializations'],rational_references=item['rational']))
        if 'angle' in item:payload['angle']=item['angle']
        tasks.append(dict(identity=item['identity'],input_key='catalog',payload=payload,
            limits=dict(native_calls=0,packet_visits=0,bound_calls=item['bounds'],bound_steps=item['steps'])))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=dict(catalog=str(path.relative_to(ROOT))),
        adapter=ADAPTER,workers=4,threads=1,maximum_wall_s=120,environment=runner.runtime_environment())


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA)
    rows=[runner._load(DATA/row['artifact'])['result'] for row in summary['results']]
    accounts=[]
    for record,row in zip(summary['results'],rows,strict=True):
        task=next(task for task in manifest['tasks'] if task['identity']==record['identity'])
        counts=dict.fromkeys(task['payload']['auxiliary_limits'],0)
        envelope=runner._load(DATA/record['artifact'])
        for name in sorted(name for name in envelope['artifacts'] if Path(name).name.startswith('reservation-')):
            event=runner._load(DATA/name);increase=event['increase']
            if any(key not in counts or type(value) is not int or value<1 for key,value in increase.items()):
                raise ValueError('invalid auxiliary reservation')
            counts={key:value+increase.get(key,0) for key,value in counts.items()}
            if counts!=event['counts'] or any(value>task['payload']['auxiliary_limits'][key] for key,value in counts.items()):
                raise ValueError('auxiliary reservation changed')
        if 'work' in row and counts!=row['work']:raise ValueError('reported work and reservation disagree')
        accounts.append(dict(identity=record['identity'],**counts))
    text=['# Source derivative known-answer controls','',
        f"{sum(row.get('passed',False) for row in rows)}/10 fixed controls passed.",'',
        f"Charged {summary['charged']['bound_calls']}/26 bounds and {summary['charged']['bound_steps']}/85 logical bound steps. "
        f"Elapsed {summary['elapsed_s']:.2f} seconds.",'',
        'These generated controls compare rotations and source derivatives with independent rational and closed-form answers. '
        'They cover reference rounding, calibration rows, clipped clock slopes and a mean-value remainder with displaced numerical centers. '
        'They do not qualify training transfer, native propagation, full-recording widths or observational confidence.','',
        '[Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,charged=summary['charged'],
        source_initializations_reserved=sum(row['source_initializations'] for row in accounts),
        rational_references_reserved=sum(row['rational_references'] for row in accounts),
        complete=len(accounts)==10,full_native_evaluations=0,optimizer_starts=0,original_reads=0))
    receipt=runner._load(PUBLIC/'evidence-receipt.json');receipt['artifacts']['accounting.json']=runner._sha(PUBLIC/'accounting.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen ten controls / 26 bounds / 85 steps; zero observed fits.')
    elif args.package_only:publish();print('Published source derivative controls.')
    else:publication.check(DATA,PUBLIC);print('Verified source derivative controls.')


if __name__=='__main__':main()
