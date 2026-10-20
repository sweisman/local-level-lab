# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish joint-rotation product component controls."""
import argparse
import gzip
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication

DATA=ROOT/'data/ilvis0-rotation-product-controls-20261020'
PUBLIC=ROOT/'docs/ilvis0-rotation-product-controls'
OLD=ROOT/'docs/ilvis0-column-orientation-controls'
ADAPTER='analysis/lll/ilvis0_rotation_product_controls.py'
PLAN='docs/ilvis0-rotation-product-controls/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/lll/ilvis0_rotation_products.py',
    'analysis/tests/test_ilvis0_rotation_products.py','analysis/tests/test_ilvis0_rotation_product_controls.py',
    'analysis/tests/test_ilvis0_native_box_bounds.py','analysis/tests/ilvis0_rotation_product_worker.py',
    'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']


def prepare():
    if DATA.exists():raise ValueError('joint rotation component already frozen')
    for name,digest in runner._load(OLD/'evidence-receipt.json')['artifacts'].items():
        if runner._sha(OLD/name)!=digest:raise ValueError('sealed physical-control prerequisite changed')
    summary=runner._load(OLD/'summary.json');manifest=runner._load(OLD/'manifest.json')
    if not summary['passed'] or manifest['environment']!=runner.runtime_environment():
        raise ValueError('passing controls and qualified environment required')
    sources=set(SOURCES)
    for name,digest in manifest['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
            sources.add(name)
    tasks=[];inputs={};cases={}
    for task in manifest['tasks']:
        source_id=task['identity'];record=next(r for r in summary['results'] if r['identity']==source_id)
        old=runner._load(OLD/record['artifact'])['result'];key=task['input_key']
        if key not in cases:
            path=OLD/manifest['inputs'][key]['path']
            if runner._sha(path)!=manifest['inputs'][key]['sha256']:raise ValueError('generated source input changed')
            case=json.loads(gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes())
            cases[key]=dict(configuration=case['configuration'])
        source=dict(identity=old['identity'],passed=old['passed'],cuts=dict(transform_binding=old['cuts']['transform_binding']),
            probes=[dict(point=p['point'],common_error=p['common_error']) for p in old['probes']])
        bundle=dict(result=source,case=cases[key],source_result_sha256=runner._sha(OLD/record['artifact']))
        identity='products-'+source_id;path=PUBLIC/'saved-inputs'/(identity+'.json')
        runner._write(path,bundle);inputs[identity]=str(path.relative_to(ROOT))
        tasks.append(dict(identity=identity,input_key=identity,
            payload=dict(family=task['payload']['family'],maximum_probes=64,maximum_planes=129),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    if len(tasks)!=24:raise ValueError('all 24 prior control identities required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,
        adapter=ADAPTER,workers=4,threads=1,maximum_wall_s=180,environment=runner.runtime_environment())


def publish():
    summary=runner.verify_completion(DATA)
    rows=[runner._load(DATA/r['artifact'])['result'] for r in summary['results']]
    text=['# Joint rotation-product controls','',
        f"{sum(r.get('passed',False) for r in rows)}/24 controls passed.",'',
        f"Reused {sum(r.get('physical_probes_reused',0) for r in rows)}/1,536 sealed physical probes; "
        f"checked {sum(r.get('exact_inequalities',0) for r in rows)}/198,144 exact inequalities and "
        f"{sum(r.get('coordinate_bounds_checked',0) for r in rows)}/119,808 coordinate bounds.",'',
        'All original 51 coordinates and 27 physical parameters remain. Twenty-seven '
        'additional coordinates relax arithmetic products so matrix columns retain '
        'necessary joint rotation relationships. They add no physical sensor freedom.','',
        f"Completed in {summary['elapsed_s']:.1f} seconds. No completed physical generator was rerun; "
        'there are zero new physical-oracle calls, LP proposals, native integrations, '
        'original-aircraft reads or observed fits.','',
        'The construction preserves the stored mounting matrix and explicitly separates '
        'a dimensionless numerical allowance from sensor accuracy. Gram constraints and '
        'relaxed products do not prove a physically realizable proper rotation. Complete '
        'prediction usefulness and observational coverage remain separate gates.','',
        '[Frozen scope](PLAN.md) · [Preceding widths](../ilvis0-conditioned-prediction/INTERPRETATION.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)


def main():
    parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 24 joint-product controls on 1536 sealed probes; zero native calls.')
    elif args.package_only:publish();print('Published joint-rotation product controls.')
    else:publication.check(DATA,PUBLIC);print('Verified joint-product control evidence.')

if __name__=='__main__':main()
