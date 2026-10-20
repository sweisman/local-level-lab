# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish an oracle-assisted saved-error-block diagnosis."""
import argparse
import gzip
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication
from lll.ilvis0_error_block_ablation import BLOCKS

DATA=ROOT/'data/ilvis0-error-block-ablation-20261020';PUBLIC=ROOT/'docs/ilvis0-error-block-ablation'
OLD=ROOT/'docs/ilvis0-column-orientation-prediction'
ADAPTER='analysis/lll/ilvis0_error_block_ablation.py';PLAN='docs/ilvis0-error-block-ablation/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/tests/ilvis0_error_block_worker.py','analysis/tests/test_ilvis0_error_block_ablation.py',
    'analysis/tests/test_ilvis0_transform_audit.py','analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']
LABELS=dict(reference_terms='Reference terms',acceleration_clock='Acceleration/clock',
    acceleration_remainder='Acceleration remainder',force_matrix='Force matrix')


def prepare():
    if DATA.exists():raise ValueError('oracle-assisted block study already frozen')
    for name,digest in runner._load(OLD/'evidence-receipt.json')['artifacts'].items():
        if runner._sha(OLD/name)!=digest:raise ValueError('sealed source evidence changed')
    previous=runner._load(OLD/'manifest.json');summary=runner._load(OLD/'summary.json')
    if not summary['passed']:raise ValueError('source correctness failed')
    sources=set(SOURCES)
    for name,digest in previous['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('qualified component changed')
            sources.add(name)
    inputs={};tasks=[];groups=set()
    for task in previous['tasks']:
        identity=task['identity'];record=next(r for r in summary['results'] if r['identity']==identity)
        row=runner._load(OLD/record['artifact'])['result']
        if not row['truth_in_sector']:continue
        group=(row['task']['model'],row['task']['profile'])
        if group in groups:raise ValueError('known-truth sector must be unique')
        groups.add(group);case_path=OLD/previous['inputs'][task['payload']['case_key']]['path']
        case=json.loads(gzip.decompress(case_path.read_bytes()) if case_path.suffix=='.gz' else case_path.read_bytes())
        bundle=dict(result=row,training=runner._load(OLD/'artifacts'/identity/'training.json'),
            future=runner._load(OLD/'artifacts'/identity/'future.json'),anchor=case['truth']+row['known_shared_error'])
        path=PUBLIC/'saved-inputs'/(identity+'.json');runner._write(path,bundle);inputs[identity]=str(path.relative_to(ROOT))
        for block in BLOCKS:
            tasks.append(dict(identity=identity+'-'+block,input_key=identity,
                payload=dict(source_identity=identity,block=block,maximum_proposals=6),
                limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    if len(tasks)!=24 or len(inputs)!=6 or len(groups)!=6:raise ValueError('all six cases crossed with four blocks required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=300,environment=runner.runtime_environment())


def publish():
    summary=runner.verify_completion(DATA);rows=[runner._load(DATA/r['artifact'])['result'] for r in summary['results']]
    names=['Globe with specified field','Globe with zero field','Flat disc']
    text=['# Which internal error terms keep predictions wide?','',
        '**Oracle-assisted diagnostic: these are not available prediction intervals.**','',
        f"{sum(r['passed'] for r in rows)}/24 cases pass containment and support checks; state: {summary['state']}.",'',
        'Each row supplies the exact simulated value of one internal error block. '
        'Those values would be unknown for a real calibration. This diagnoses the mathematical '
        'construction and cannot clear a prediction or scientific decision gate.','',
        '| Candidate / removal | Block fixed to its known value | Conditional width N / E / height (m) | Reduction from source sector N / E / height |',
        '|---|---|---:|---:|']
    for row in rows:
        if 'fixed_block' not in row:text.append(f"| {row['identity']} | Failed task | — | — |");continue
        widths=', '.join(f'{v:.5f}' for v in row['conditional_width_m'])
        reductions=', '.join(f'{100*(1-v):.2f}%' for v in row['width_ratio'])
        text.append(f"| {names[row['task']['model']]} / {'profiled' if row['task']['profile'] else 'zero'} | "
            f"{LABELS[row['fixed_block']]} | {widths} | {reductions} |")
    text+=['','All 51 coordinates and previous training constraints remain. Each conditional block '
        'is fixed only to its saved known physical value. These effects are not additive percentages '
        'of real uncertainty, and the selected source sector is not the complete union across sectors.','',
        f"Used {sum(r.get('lp_proposals_reserved',0) for r in rows)}/144 LP proposals and "
        f"{sum(r.get('exact_supports_checked',0) for r in rows)} independent support checks in {summary['elapsed_s']:.1f} seconds. "
        'Zero new native integration, bounds or original aircraft reads.','',
        '[Frozen scope](PLAN.md) · [Source predictions](../ilvis0-column-orientation-prediction/INTERPRETATION.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)


def main():
    parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 24 oracle-assisted block cases; maximum 144 LP proposals.')
    elif args.package_only:publish();print('Published oracle-assisted block diagnosis.')
    else:publication.check(DATA,PUBLIC);print('Verified saved block diagnosis.')

if __name__=='__main__':main()
