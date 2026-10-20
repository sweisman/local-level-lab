# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish source reference coefficients before full propagation."""
import argparse
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication

DATA=ROOT/'data/ilvis0-source-reference-20261020';PUBLIC=ROOT/'docs/ilvis0-source-reference'
OLD=ROOT/'docs/ilvis0-source-norm-preflight';ADAPTER='analysis/lll/ilvis0_source_reference.py'
PLAN='docs/ilvis0-source-reference/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/lll/ilvis0_source_reference.cpp','analysis/lll/ilvis0_tangent.cpp',
    'analysis/tests/ilvis0_source_reference_worker.py','analysis/tests/test_ilvis0_source_reference.py',
    'analysis/tests/test_ilvis0_source_norm_preflight.py','analysis/tests/test_ilvis0_native_box_bounds.py',
    'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']


def prepare():
    from lll.ilvis0_orientation_cover import sector
    if DATA.exists():raise ValueError('source reference already frozen')
    for name,digest in runner._load(OLD/'evidence-receipt.json')['artifacts'].items():
        if runner._sha(runner.path_within(OLD,name))!=digest:raise ValueError('sealed source prerequisite changed')
    previous=runner._load(OLD/'manifest.json');summary=runner._load(OLD/'summary.json');sources=set(SOURCES)
    if not summary['passed'] or previous['environment']!=runner.runtime_environment():raise ValueError('qualified source environment required')
    for name,digest in previous['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
            sources.add(name)
    compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
    tasks=[];inputs={};groups=set()
    for old_task in previous['tasks']:
        identity=old_task['identity'];item=next(r for r in summary['results'] if r['identity']==identity)
        result=runner._load(OLD/item['artifact'])['result'];group=(result['model'],result['profile'])
        if not result['passed'] or group in groups:raise ValueError('six unique qualified sources required')
        groups.add(group);case_key=old_task['payload']['case_key'];case_record=previous['inputs'][case_key]
        inputs[case_key]=str((OLD/case_record['path']).relative_to(ROOT))
        original=runner._load(OLD/previous['inputs'][identity]['path'])
        bundle=dict(result=result,future=original['future'],range=runner._load(OLD/'artifacts'/identity/'range.json'))
        path=PUBLIC/'saved-inputs'/(identity+'.json');runner._write(path,bundle);inputs[identity]=str(path.relative_to(ROOT))
        limits=dict(setups=1,source_calls=1,source_packets=1600,independent_calls=1,independent_packets=1600,affine_bounds=1)
        tasks.append(dict(identity=identity,input_key=identity,payload=dict(case_key=case_key,compiler=compiler,
            reference_center=sector(4)['center'].tolist(),limits=limits),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    if len(tasks)!=6 or groups!={(m,p) for m in range(3) for p in (False,True)}:raise ValueError('complete six-group source matrix required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=180,environment=runner.runtime_environment())


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA)
    rows=[runner._load(DATA/r['artifact'])['result'] for r in summary['results']];accounts=[]
    for record,row in zip(summary['results'],rows,strict=True):
        if 'work' not in row:continue
        artifacts=runner._load(DATA/record['artifact'])['artifacts'];task=next(t for t in manifest['tasks'] if t['identity']==row['identity'])
        limits=task['payload']['limits'];counts=dict.fromkeys(limits,0)
        for name in sorted(n for n in artifacts if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);inc=event['increase']
            if not inc or any(k not in counts or type(v)!=int or v<1 for k,v in inc.items()):raise ValueError('invalid reservation')
            counts={k:v+inc.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):raise ValueError('work journal changed')
        if counts!=limits or counts!=row['work'] or max(row['actual_source_packets'],row['actual_independent_packets'])>1600:
            raise ValueError('reference work and finite reservations disagree')
        accounts.append(dict(identity=row['identity'],**counts))
    text=['# Source reference and affine-error comparison','',
        f"{sum(r.get('passed',False) for r in rows)}/6 generated source reference checks passed.",'',
        '| Candidate / removal | Coefficients agree | Old remainder (m/s²) | New affine radius (m/s²) | Ratio |',
        '|---|---|---:|---:|---:|']
    for row in rows:
        if 'model' not in row:continue
        label=('Globe with specified field','Globe with zero field','Flat disc')[row['model']]+(' / profiled' if row['profile'] else ' / zero')
        text.append(f"| {label} | {'Yes' if row['passed'] else 'No'} | {row['original_remainder']:.7g} | {row['affine_radius']:.7g} | {row['radius_ratio']:.6f} |")
    text+=['',f"{sum(r.get('improved',False) for r in rows)}/6 source affine radii improve on the actual saved remainder. "
        f"Elapsed {summary['elapsed_s']:.2f} seconds. Reserved {sum(r['source_packets'] for r in accounts)}/9,600 compiled-source visits "
        f"and {sum(r['independent_packets'] for r in accounts)}/9,600 independent visits.",'',
        'Every source retains all 27 physical columns. Coefficients are compared with an independent quaternion/analytic-Jacobian implementation; '
        'local tests also use complex-step matrix exponentials. Exact packet endpoints retain the native preceding-packet slope. '
        'The affine radius uses the actual compiled-source center and row, not an assumed exact derivative.','',
        'This qualifies a mathematical source component only. The source-only C++ exposure uses unchanged native primitives; '
        'the complete trajectory consumer has not been replaced or qualified. Floating-point execution enclosure, '
        'full position prediction and observational coverage remain unqualified. No aircraft data, protected ESA data or fit was used.','',
        '[Frozen scope](PLAN.md) · [Earlier value preflight](../ilvis0-source-norm-preflight/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,complete=len(accounts)==6,full_native_trajectory_evaluations=0,optimizer_starts=0))
    receipt=runner._load(PUBLIC/'evidence-receipt.json');receipt['artifacts']['accounting.json']=runner._sha(PUBLIC/'accounting.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen six source references, 19,200 reserved visits; zero full trajectories.')
    elif args.package_only:publish();print('Published source reference evidence.')
    else:publication.check(DATA,PUBLIC);print('Verified source reference evidence.')


if __name__=='__main__':main()
