# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish the finite training-conditioned native controls."""
import argparse
import gzip
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication

DATA=ROOT/'data/ilvis0-conditioned-native-controls-20261020'
PUBLIC=ROOT/'docs/ilvis0-conditioned-native-controls'
PROJECTION=ROOT/'docs/ilvis0-acceleration-projection'
OLD=ROOT/'docs/ilvis0-column-orientation-prediction'
ADAPTER='analysis/lll/ilvis0_conditioned_native_controls.py'
PLAN='docs/ilvis0-conditioned-native-controls/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/lll/ilvis0_conditioned_acceleration.py',
    'analysis/lll/ilvis0_conditioned_transform_native.py',
    'analysis/tests/test_ilvis0_conditioned_acceleration.py',
    'analysis/tests/test_ilvis0_conditioned_transform_native.py',
    'analysis/tests/test_ilvis0_acceleration_projection.py',
    'analysis/tests/test_ilvis0_native_box_bounds.py','analysis/tests/test_ilvis0_regrouped_history.py',
    'analysis/tests/ilvis0_conditioned_native_worker.py','analysis/tests/ilvis0_control_shards.py',
    'analysis/tests/run_numerical.py']


def prepare():
    if DATA.exists():raise ValueError('conditioned native controls already frozen')
    sources=set(SOURCES)
    for directory in (PROJECTION,OLD):
        for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(directory/name)!=digest:raise ValueError('sealed prerequisite changed')
        if not runner._load(directory/'summary.json')['passed']:raise ValueError('prerequisite correctness failed')
        for name,digest in runner._load(directory/'manifest.json')['sources'].items():
            if name.startswith('analysis/lll/'):
                if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
                sources.add(name)
    manifest=runner._load(PROJECTION/'manifest.json');summary=runner._load(PROJECTION/'summary.json')
    previous=runner._load(OLD/'manifest.json');inputs={};tasks=[]
    for task in manifest['tasks']:
        identity=task['identity'];record=next(r for r in summary['results'] if r['identity']==identity)
        projection=runner._load(PROJECTION/record['artifact'])['result']
        if not projection['twofold_radius_reduction']:raise ValueError('acceleration engineering target failed')
        old_task=next(t for t in previous['tasks'] if t['identity']==identity)
        input_path=PROJECTION/manifest['inputs'][identity]['path']
        bundle=dict(projection_input=runner._load(input_path),projection=projection,
            future=runner._load(OLD/'artifacts'/identity/'future.json'))
        path=PUBLIC/'saved-inputs'/(identity+'.json')
        if path.exists():
            if runner._load(path)!=bundle:raise ValueError('partial preparation input changed')
        else:runner._write(path,bundle)
        inputs[identity]=str(path.relative_to(ROOT))
        case_key=old_task['payload']['case_key'];anchor_key=task['payload']['anchor_key']
        inputs[case_key]=str((OLD/previous['inputs'][case_key]['path']).relative_to(ROOT))
        inputs[anchor_key]=str((PROJECTION/manifest['inputs'][anchor_key]['path']).relative_to(ROOT))
        case_path=ROOT/inputs[case_key]
        case=json.loads(gzip.decompress(case_path.read_bytes()) if case_path.suffix=='.gz' else case_path.read_bytes())
        n=len(case['dt'])
        payload=dict(case_key=case_key,anchor_key=anchor_key,packets=n,sector=int(identity.rsplit('-',1)[1]),
            model=task['payload']['model'],profile=task['payload']['profile'],maximum_exact_supports=6,
            maximum_bound_seconds=60.)
        tasks.append(dict(identity=identity,input_key=identity,payload=payload,
            limits=dict(native_calls=2,packet_visits=2*n,bound_calls=1,bound_steps=2*n)))
    if len(tasks)!=6:raise ValueError('all six groups required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=600,environment=runner.runtime_environment())


def publish():
    summary=runner.verify_completion(DATA)
    rows=[runner._load(DATA/r['artifact'])['result'] for r in summary['results']]
    text=['# Propagation with training-derived acceleration bounds','',
        f"{sum(r.get('passed',False) for r in rows)}/6 source-qualified native controls passed.",'',
        'These are generated controls, not aircraft results. They check whether a '
        'tighter training-derived acceleration bound can be used without changing '
        'the native prediction, its derivative or shared-error coefficients.','',
        '| Candidate / removal | Source remainder N / E / height (m) | Conditioned remainder N / E / height (m) | Passed |',
        '|---|---|---|---|']
    labels=['Globe with specified field','Globe with zero field','Flat disc']
    for row in rows:
        if 'model' not in row:
            text.append(f"| {row['identity']} | — | Failed task | No |")
            continue
        label=labels[row['model']]+(' / profiled' if row['profile'] else ' / zero')
        left=' / '.join(f'{v:.6g}' for v in row['source_remainder_m'])
        right=' / '.join(f'{v:.6g}' for v in row['conditioned_remainder_m'])
        text.append(f"| {label} | {left} | {right} | {'Yes' if row['passed'] else 'No'} |")
    text+=['',f"Completed in {summary['elapsed_s']:.1f} seconds. Native calls: "
        f"{sum(r.get('native_evaluations',0) for r in rows)}/12; enclosure calls: "
        f"{sum(r.get('bound_evaluations',0) for r in rows)}/6; exact verifier supports: "
        f"{sum(r.get('exact_supports_reserved',0) for r in rows)}/36. "
        'Zero LP proposals, original reads or observed fits.','',
        'A conditioned bound applies only to its verified training region. Original '
        'Taylor remainder allowances remain. This component check does not yet '
        'qualify complete prediction widths or observational coverage.','',
        '[Frozen scope](PLAN.md) · [Acceleration bounds](../ilvis0-acceleration-projection/INTERPRETATION.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)


def main():
    parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen six controls: 12 native / 6 bound calls / 36 exact verifications.')
    elif args.package_only:publish();print('Published conditioned native controls.')
    else:publication.check(DATA,PUBLIC);print('Verified conditioned native evidence.')

if __name__=='__main__':main()
