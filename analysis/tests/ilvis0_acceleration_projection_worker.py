# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish six training-only acceleration projections."""
import argparse
import gzip
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication

DATA=ROOT/'data/ilvis0-acceleration-projection-20261020'
PUBLIC=ROOT/'docs/ilvis0-acceleration-projection'
OLD=ROOT/'docs/ilvis0-column-orientation-prediction'
ADAPTER='analysis/lll/ilvis0_acceleration_projection.py'
PLAN='docs/ilvis0-acceleration-projection/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/tests/ilvis0_acceleration_projection_worker.py',
    'analysis/tests/test_ilvis0_acceleration_projection.py',
    'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']


def prepare():
    if DATA.exists():raise ValueError('acceleration projection already frozen')
    sources=set(SOURCES)
    for name,digest in runner._load(OLD/'evidence-receipt.json')['artifacts'].items():
        if runner._sha(OLD/name)!=digest:raise ValueError('sealed prerequisite changed')
    summary=runner._load(OLD/'summary.json')
    if not summary['passed']:raise ValueError('prerequisite correctness failed')
    previous=runner._load(OLD/'manifest.json')
    for name,digest in previous['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
            sources.add(name)
    inputs={};tasks=[];groups=set()
    for task in previous['tasks']:
        identity=task['identity'];record=next(r for r in summary['results'] if r['identity']==identity)
        row=runner._load(OLD/record['artifact'])['result']
        if not row['truth_in_sector']:continue
        group=(row['task']['model'],row['task']['profile'])
        if group in groups:raise ValueError('known-truth sector is not unique')
        groups.add(group)
        case_path=OLD/previous['inputs'][task['payload']['case_key']]['path']
        case=json.loads(gzip.decompress(case_path.read_bytes()) if case_path.suffix=='.gz' else case_path.read_bytes())
        future=runner._load(OLD/'artifacts'/identity/'future.json')
        bundle=dict(training=runner._load(OLD/'artifacts'/identity/'training.json'),
            reference=future['reference'],lower=future['lower'],upper=future['upper'])
        anchor_key=identity+'-anchor'
        for key,value in ((identity,bundle),(anchor_key,dict(point=case['truth']+row['known_shared_error']))):
            path=PUBLIC/'saved-inputs'/(key+'.json');runner._write(path,value)
            inputs[key]=str(path.relative_to(ROOT))
        tasks.append(dict(identity=identity,input_key=identity,
            payload=dict(anchor_key=anchor_key,model=group[0],profile=group[1],
                maximum_proposals=6,maximum_exact_supports=18),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    if len(tasks)!=6 or len(groups)!=6:raise ValueError('all six original groups required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=180,environment=runner.runtime_environment())


def publish():
    summary=runner.verify_completion(DATA)
    rows=[runner._load(DATA/r['artifact'])['result'] for r in summary['results']]
    labels=['Globe with specified field','Globe with zero field','Flat disc']
    useful=all(r.get('passed') and r.get('twofold_radius_reduction') for r in rows) and len(rows)==6
    text=['# Can training data constrain acceleration more tightly?','',
        f"{sum(r.get('passed',False) for r in rows)}/6 cases passed exact support and containment checks. "
        f"The all-group twofold reduction target {'passed' if useful else 'was not met'}.",'',
        'This bounds one combined quantity using saved generated controls. It does not '
        'produce new position predictions or measure aircraft uncertainty.','',
        '| Candidate / removal | Original acceleration radius (m/s²) | Projected radius (m/s²) | Fraction retained | Twofold reduction |',
        '|---|---:|---:|---:|---|']
    for r in rows:
        if 'norm_change' not in r:
            text.append(f"| {r['identity']} | — | Failed task | — | No |")
            continue
        label=labels[r['model']]+(' / profiled' if r['profile'] else ' / zero')
        text.append(f"| {label} | {r['source_norm_change']:.6g} | {r['norm_change']:.6g} | "
            f"{r['radius_ratio']:.3%} | {'Yes' if r['twofold_radius_reduction'] else 'No'} |")
    text+=['',f"Completed in {summary['elapsed_s']:.1f} seconds. Reserved "
        f"{sum(r.get('lp_proposals_reserved',0) for r in rows)}/36 LP proposals and "
        f"{sum(r.get('exact_supports_reserved',0) for r in rows)}/108 exact support evaluations. "
        'Zero native integration, bounds, original-file reads or observed fits.','',
        'All 51 coordinates remain. Bounds were saved before the separate known-anchor file '
        'was opened for checking. These are necessary-region bounds; observational coverage '
        'and the complete prediction method remain unqualified.','',
        '[Frozen scope](PLAN.md) · [Previous diagnosis](../ilvis0-error-block-ablation/INTERPRETATION.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)


def main():
    parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen six acceleration projections: 36 LP / 108 exact support evaluations.')
    elif args.package_only:publish();print('Published training-derived acceleration bounds.')
    else:publication.check(DATA,PUBLIC);print('Verified acceleration projection evidence.')

if __name__=='__main__':main()
