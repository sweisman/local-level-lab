#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish direct source-remainder known-answer controls."""
import argparse
import importlib.metadata
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-source-remainder-controls-20261021';PUBLIC=ROOT/'docs/ilvis0-source-remainder-controls'
PLAN='docs/ilvis0-source-remainder-controls/PLAN.md';ADAPTER='analysis/lll/ilvis0_source_remainder_controls.py'


def prepare():
    if DATA.exists():raise ValueError('direct source controls already frozen')
    sources=[ADAPTER,PLAN,'analysis/lll/ilvis0_source_remainder.py',
        'analysis/lll/ilvis0_rotation_roundoff.py','analysis/lll/ilvis0_rotation_derivative.py',
        'analysis/lll/ilvis0_exact_scale.py','analysis/lll/ilvis0_saved_prediction_audit.py',
        'analysis/lll/ilvis0_coupled_map_controls.py','analysis/lll/__init__.py',
        'analysis/lll/ilvis0_control_shards.py','analysis/lll/ilvis0_control_publication.py',
        'analysis/lll/ilvis0_receipt_journal.py','analysis/lll/compute_budget.py',
        'analysis/tests/test_ilvis0_source_remainder.py','analysis/tests/ilvis0_source_remainder_worker.py',
        'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']
    catalog=[]
    def add(identity,function,bounds,steps,probes,references=0,rejections=0,arguments=(),rational=False):
        catalog.append(dict(identity=identity,function=function,bounds=bounds,steps=steps,
            arguments=list(arguments),rational_arguments=rational,
            auxiliary_limits=dict(grid_axis_probes=probes,rational_references=references,rejection_checks=rejections)))
    for rate in (False,True):add('calibration-'+str(int(rate)),
        'test_calibration_remainder_contains_exact_bias_gain_law',1,0,49,arguments=[rate])
    for index,args in enumerate((('0','0','4'),('1/4','0','4'),('1/4','1/4','0'),('1/8','0','4'))):
        add('clock-'+str(index),'test_clipped_clock_remainder_preserves_both_boundary_sides',1,0,41,arguments=args,rational=True)
    add('shared-product','test_scalar_product_keeps_correlated_calibration_and_clock_errors',3,0,41)
    for index,angle in enumerate((.001,.1,.6)):
        add('noncommuting-'+str(index),'test_noncommuting_prefix_bound_contains_independent_rotation_values',1,2,4,2,arguments=[angle])
    add('force-product','test_force_product_remainder_contains_shared_parameter_polynomials',1,0,41)
    add('nonzero-prefix','test_nonzero_reference_prefix_with_nonlinear_arguments',1,2,20,16)
    add('rejections','test_invalid_denominators_and_finite_work_limits_are_rejected',4,0,0,rejections=4)
    if len(catalog)!=13 or sum(c['bounds'] for c in catalog)!=18 or sum(c['steps'] for c in catalog)!=8:
        raise ValueError('fixed component recipe changed')
    path=PUBLIC/'control-catalog.json';runner._write(path,catalog);tasks=[]
    for item in catalog:
        payload=dict(item,pytest=importlib.metadata.version('pytest'))
        tasks.append(dict(identity=item['identity'],input_key='catalog',payload=payload,
            limits=dict(native_calls=0,packet_visits=0,bound_calls=item['bounds'],bound_steps=item['steps'])))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sources,inputs=dict(catalog=str(path.relative_to(ROOT))),
        adapter=ADAPTER,workers=1,threads=1,maximum_wall_s=60,environment=runner.runtime_environment())


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
        if 'work' in row and counts!=row['work']:raise ValueError('component work differs from reservation')
        accounts.append(dict(identity=item['identity'],**counts))
    text=['# Direct source-remainder component controls','',
        f"{sum(r.get('passed',False) for r in rows)}/13 fixed controls passed.",'',
        f"Charged {summary['charged']['bound_calls']}/18 bound calls and {summary['charged']['bound_steps']}/8 rotation-argument steps. "
        f"Elapsed {summary['elapsed_s']:.2f} seconds.",'',
        'These controls exercise exact calibration, clipped-clock remainders, shared-parameter products '
        'and noncommuting rotation prefixes, including nonlinear arguments about nonzero references. '
        'Independent rational rotation references provide the comparison. '
        'This does not qualify the numerical-reference bridge, native source installation, complete '
        'prediction widths or observational confidence. No aircraft data, LP or fit was used.','',
        '[Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,charged=summary['charged']))
    receipt=runner._load(PUBLIC/'evidence-receipt.json');receipt['artifacts']['accounting.json']=runner._sha(PUBLIC/'accounting.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check','run'):group.add_argument('--'+name,action='store_true')
    parser.add_argument('--reserved-threads',type=int);args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 13 mathematical controls / 18 bounds / 8 rotation steps / one thread.')
    elif args.run:
        if args.reserved_threads is None:parser.error('--run requires --reserved-threads')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Completed source remainder controls: '+result['state'])
    elif args.package_only:publish();print('Published saved source-remainder controls.')
    else:publication.check(DATA,PUBLIC);print('Verified direct-remainder component evidence.')


if __name__=='__main__':main()
