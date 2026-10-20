# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish the finite saved-region width diagnostic."""
import argparse
from fractions import Fraction as F
import gzip
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication

DATA=ROOT/'data/ilvis0-relaxed-width-audit-20261020';PUBLIC=ROOT/'docs/ilvis0-relaxed-width-audit'
OLD=ROOT/'docs/ilvis0-rotation-gain-prediction';QUALIFIED=ROOT/'docs/ilvis0-feasible-witness-controls'
BASELINE=ROOT/'docs/ilvis0-projected-future-bounds'
ADAPTER='analysis/lll/ilvis0_relaxed_width.py';PLAN='docs/ilvis0-relaxed-width-audit/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/tests/ilvis0_relaxed_width_worker.py',
    'analysis/tests/test_ilvis0_relaxed_width.py','analysis/tests/test_ilvis0_transform_audit.py',
    'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']


def prepare():
    if DATA.exists():raise ValueError('saved-region diagnostic already frozen')
    sources=set(SOURCES)
    for directory in (OLD,QUALIFIED,BASELINE):
        for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(directory/name)!=digest:raise ValueError('sealed prerequisite changed')
        if not runner._load(directory/'summary.json')['passed']:raise ValueError('prerequisite correctness failed')
    for directory in (OLD,QUALIFIED):
        for name,digest in runner._load(directory/'manifest.json')['sources'].items():
            if name.startswith('analysis/lll/'):
                if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
                sources.add(name)
    previous=runner._load(OLD/'manifest.json');summary=runner._load(OLD/'summary.json')
    baselines=runner._load(BASELINE/'case-unions.json')['cases'];inputs={};tasks=[];groups=set()
    for task in previous['tasks']:
        identity=task['identity'];record=next(r for r in summary['results'] if r['identity']==identity)
        row=runner._load(OLD/record['artifact'])['result']
        if not row['truth_in_sector']:continue
        group=(row['task']['model'],row['task']['profile'])
        if group in groups:raise ValueError('known-truth sector is not unique')
        groups.add(group);case_key=task['payload']['case_key']
        case_path=OLD/previous['inputs'][case_key]['path']
        case=json.loads(gzip.decompress(case_path.read_bytes()) if case_path.suffix=='.gz' else case_path.read_bytes())
        baseline=next(r for r in baselines if (r['model'],r['profile'])==group)
        bundle=dict(result=row,training=runner._load(OLD/'artifacts'/identity/'training.json'),
            future=runner._load(OLD/'artifacts'/identity/'future.json'),
            anchor=case['truth']+row['known_shared_error'],
            target_width_m=[v/2 for v in baseline['union_width_m']])
        path=PUBLIC/'saved-inputs'/(identity+'.json');runner._write(path,bundle)
        inputs[identity]=str(path.relative_to(ROOT))
        tasks.append(dict(identity=identity,input_key=identity,payload=dict(maximum_proposals=6),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    if len(tasks)!=6 or len(groups)!=6:raise ValueError('all six original groups required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=180,environment=runner.runtime_environment())


def publish():
    summary=runner.verify_completion(DATA)
    rows=[runner._load(DATA/r['artifact'])['result'] for r in summary['results']]
    supported=[r for r in rows if r.get('supported')]
    labels=['Globe with specified field','Globe with zero field','Flat disc']
    text=['# Why the prediction ranges remain wide','',
        f"{len(supported)}/6 cases supply exactly verified witnesses; {len(rows)}/6 tasks completed.",'',
        'This tests the current mathematical prediction region, using saved generated cases. '
        'It does not fit aircraft data or measure real sensor uncertainty.','',
        '| Candidate / removal | Affine width lower / upper (m), N; E; height | Lowest permitted total width (m) | Above target N / E / height |',
        '|---|---|---|---|']
    for row in rows:
        if not row.get('supported'):
            text.append(f"| {row['identity']} | Unsupported: {row.get('reason','failed task')} | — | — |")
            continue
        axes=row['axes']
        affine='; '.join(f"{float(F(a['affine_lower_width'])):.5f} / {float(F(a['affine_upper_width'])):.5f}" for a in axes)
        total=', '.join(f"{float(F(a['relaxed_lower_width'])):.5f}" for a in axes)
        flags=' / '.join('Yes' if a['lower_exceeds_target'] else 'No' for a in axes)
        text.append(f"| {labels[row['model']]} / {'profiled' if row['profile'] else 'zero'} | {affine} | {total} | {flags} |")
    text+=['','The lower value is established by two exactly feasible points; the upper value comes '
        'from the existing support certificate. Their difference measures what better optimization '
        'could still remove within this region. The total also includes the retained unshared and '
        'arithmetic allowances. Feasibility here does not establish a physically realizable calibration.','',
        f"LP proposals: {sum(r.get('lp_proposals',0) for r in rows)}/36; elapsed {summary['elapsed_s']:.1f} seconds. "
        'Zero new native integration, bounds or original-file reads. Unsupported cases remain without replacements.','',
        '[Frozen scope](PLAN.md) · [Known-answer controls](../ilvis0-feasible-witness-controls/README.md) · '
        '[Source predictions](../ilvis0-rotation-gain-prediction/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)


def main():
    parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen six saved-region diagnostics; maximum 36 LP proposals.')
    elif args.package_only:publish();print('Published saved-region width diagnosis.')
    else:publication.check(DATA,PUBLIC);print('Verified saved-region evidence.')

if __name__=='__main__':main()
