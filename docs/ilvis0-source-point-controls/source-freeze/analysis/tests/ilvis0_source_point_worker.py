#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish independent point-source derivative controls."""
import argparse
import importlib.metadata
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-source-point-controls-20261021';PUBLIC=ROOT/'docs/ilvis0-source-point-controls'
PLAN='docs/ilvis0-source-point-controls/PLAN.md';ADAPTER='analysis/lll/ilvis0_source_point_controls.py'


def prepare():
    if DATA.exists():raise ValueError('point derivative controls already frozen')
    modules=('ilvis0_source_point_derivatives.py','ilvis0_source_point_derivatives.cpp',
        'ilvis0_source_derivative_intervals.cpp','ilvis0_compiled_bounds.cpp','ilvis0_compiled_bounds.py',
        'ilvis0_source_reference.py','ilvis0_rotation_roundoff.py','ilvis0_rotation_derivative.py',
        'ilvis0_exact_scale.py','ilvis0_saved_prediction_audit.py','ilvis0_coupled_map_controls.py',
        '__init__.py','ilvis0_control_shards.py','ilvis0_control_publication.py','ilvis0_receipt_journal.py','compute_budget.py')
    sources=[ADAPTER,PLAN,*('analysis/lll/'+name for name in modules),
        'analysis/tests/test_ilvis0_source_point_derivatives.py','analysis/tests/ilvis0_source_point_worker.py',
        'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']
    catalog=[]
    for identity,function,bounds,initializations,references,rejections,arguments in (
        ('nonzero','test_nonzero_point_values_and_gyro_rows_enclose_rational_reference',4,1,32,0,[]),
        ('end-knot','test_point_clock_boundary_encloses_native_preceding_packet_slope',2,1,2,0,[]),
        ('ownership','test_point_stream_owns_inputs_and_rejects_excess_work',2,1,0,0,[]),
        ('all-columns-origin','test_all_columns_noncommuting_source_against_rational_chain_rule',4,1,27,0,[0.]),
        ('all-columns-interior','test_all_columns_noncommuting_source_against_rational_chain_rule',4,1,27,0,[3/512]),
        ('all-columns-end','test_all_columns_noncommuting_source_against_rational_chain_rule',4,1,27,0,[2/256]),
        ('invalid-inputs','test_point_inputs_reject_invalid_shapes_domains_and_limits',0,0,0,7,[])):
        catalog.append(dict(identity=identity,function=function,bounds=bounds,arguments=arguments,
            auxiliary_limits=dict(initializations=initializations,rational_references=references,rejections=rejections)))
    if len(catalog)!=7 or sum(c['bounds'] for c in catalog)!=20:raise ValueError('point recipe changed')
    path=PUBLIC/'control-catalog.json';runner._write(path,catalog);tasks=[]
    compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
    for item in catalog:
        tasks.append(dict(identity=item['identity'],input_key='catalog',
            payload=dict(item,compiler=compiler,pytest=importlib.metadata.version('pytest')),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=item['bounds'],bound_steps=item['bounds'])))
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
        if 'work' in row and counts!=row['work']:raise ValueError('point work differs from reservation')
        accounts.append(dict(identity=item['identity'],**counts))
    text=['# Point-source derivative controls','',
        f"{sum(r.get('passed',False) for r in rows)}/7 fixed controls passed.",'',
        f"Charged {summary['charged']['bound_calls']}/20 source calls and {summary['charged']['bound_steps']}/20 packet steps. "
        f"Elapsed {summary['elapsed_s']:.2f} seconds.",'',
        'The checks compare values and all 27 derivative columns with a separate exact-rational rotation chain. '
        'They include nonzero calibration, noncommuting rotations, both clock-knot sides, input ownership and rejections. '
        'This does not qualify the complete numerical-reference bridge, native propagation, prediction widths or observational confidence. '
        'No aircraft data or fits were used.','',
        '[Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,charged=summary['charged']))
    receipt=runner._load(PUBLIC/'evidence-receipt.json');receipt['artifacts']['accounting.json']=runner._sha(PUBLIC/'accounting.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check','run'):group.add_argument('--'+name,action='store_true')
    parser.add_argument('--reserved-threads',type=int);args=parser.parse_args()
    if args.prepare:prepare();print('Frozen seven point controls / 20 calls / 20 steps / one thread.')
    elif args.run:
        if args.reserved_threads is None:parser.error('--run requires --reserved-threads')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Point controls: '+result['state'])
    elif args.package_only:publish();print('Published saved point-source controls.')
    else:publication.check(DATA,PUBLIC);print('Verified point-source component evidence.')


if __name__=='__main__':main()
