# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze/publish saved force-matrix diagnostics without new predictions."""
import argparse
import gzip
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication

DATA=ROOT/'data/ilvis0-matrix-gram-audit-20261020';PUBLIC=ROOT/'docs/ilvis0-matrix-gram-audit'
OLD=ROOT/'docs/ilvis0-relaxed-width-audit';PREDICTION=ROOT/'docs/ilvis0-rotation-gain-prediction'
ADAPTER='analysis/lll/ilvis0_matrix_gram_audit.py';PLAN='docs/ilvis0-matrix-gram-audit/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/lll/ilvis0_matrix_gram.py','analysis/tests/test_ilvis0_matrix_gram.py',
    'analysis/tests/ilvis0_matrix_gram_worker.py','analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']


def prepare():
    if DATA.exists():raise ValueError('matrix diagnostic already frozen')
    sources=set(SOURCES)
    for directory in (OLD,PREDICTION):
        for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(directory/name)!=digest:raise ValueError('saved prerequisite changed')
        if not runner._load(directory/'summary.json')['passed']:raise ValueError('source diagnosis failed')
    manifest=runner._load(OLD/'manifest.json');summary=runner._load(OLD/'summary.json')
    parent=runner._load(PREDICTION/'manifest.json');inputs={};tasks=[]
    for name,digest in manifest['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('qualified component changed')
            sources.add(name)
    for task in manifest['tasks']:
        identity=task['identity'];record=next(r for r in summary['results'] if r['identity']==identity)
        row=runner._load(OLD/record['artifact'])['result']
        if not row['supported']:raise ValueError('source case unsupported; no replacement permitted')
        original_task=next(t for t in parent['tasks'] if t['identity']==identity)
        case_path=PREDICTION/parent['inputs'][original_task['payload']['case_key']]['path']
        case=json.loads(gzip.decompress(case_path.read_bytes()) if case_path.suffix=='.gz' else case_path.read_bytes())
        bundle=dict(source_result=row,source_input=runner._load(OLD/manifest['inputs'][task['input_key']]['path']),
            witnesses=runner._load(OLD/'artifacts'/identity/'witnesses.json'),configuration=case['configuration'])
        path=PUBLIC/'saved-inputs'/(identity+'.json');runner._write(path,bundle);inputs[identity]=str(path.relative_to(ROOT))
        tasks.append(dict(identity=identity,input_key=identity,payload=dict(maximum_checks=7),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    if len(tasks)!=6:raise ValueError('all six saved cases required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=60,environment=runner.runtime_environment())


def publish():
    summary=runner.verify_completion(DATA);rows=[runner._load(DATA/r['artifact'])['result'] for r in summary['results']]
    text=['# Do the extreme matrices preserve a rotation?','',
        f"{sum(r.get('anchor_compatible',False) for r in rows)}/6 physical anchors pass; "
        f"{sum(r.get('witnesses_flagged',0) for r in rows)}/36 extreme examples are flagged.",'',
        'The test removes proposed gains and checks a rotation invariant using exact arithmetic. '
        'Its dimensionless 1e-8 numerical allowance is not a sensor specification.','',
        '| Model / removal | Anchor passes | Flagged / 6 | Largest Gram defect norm |','|---|---|---:|---:|']
    labels=['Globe with specified field','Globe with zero field','Flat disc']
    for row in rows:
        if 'model' not in row:text.append(f"| {row['identity']} | Failed task | — | — |");continue
        text.append(f"| {labels[row['model']]} / {'profiled' if row['profile'] else 'zero'} | "
            f"{'Yes' if row['anchor_compatible'] else 'No'} | {row['witnesses_flagged']} | {row['maximum_defect_norm']:.6g} |")
    text+=['','A flag diagnoses an extreme combination admitted by the relaxed prediction method. '
        'Passing does not establish full physical realizability, correct orientation or trajectory fit. '
        'This diagnostic changes no prediction interval or aircraft result.','',
        f"Completed {sum(r.get('matrix_checks',0) for r in rows)}/42 matrix checks in {summary['elapsed_s']:.1f} seconds. "
        'Zero new LP proposals, native integration, bounds or original aircraft reads.','',
        '[Frozen scope](PLAN.md) · [Width diagnosis](../ilvis0-relaxed-width-audit/INTERPRETATION.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)


def main():
    parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen six cases / 42 matrix checks; no integration or LP.')
    elif args.package_only:publish();print('Published saved matrix diagnosis.')
    else:publication.check(DATA,PUBLIC);print('Verified matrix diagnosis.')

if __name__=='__main__':main()
