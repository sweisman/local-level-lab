# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and package complete streamed source-reference qualification."""
import argparse
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication

DATA=ROOT/'data/ilvis0-source-stream-controls-20261020';PUBLIC=ROOT/'docs/ilvis0-source-stream-controls'
OLD=ROOT/'docs/ilvis0-source-reference';ADAPTER='analysis/lll/ilvis0_source_stream_controls.py'
PLAN='docs/ilvis0-source-stream-controls/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/lll/ilvis0_source_stream.py','analysis/lll/ilvis0_source_stream.cpp',
    'analysis/lll/ilvis0_source_reference.py','analysis/lll/ilvis0_tangent.cpp',
    'analysis/tests/ilvis0_source_stream_worker.py','analysis/tests/test_ilvis0_source_stream.py',
    'analysis/tests/test_ilvis0_source_norm_preflight.py','analysis/tests/test_ilvis0_native_box_bounds.py',
    'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']


def prepare():
    if DATA.exists():raise ValueError('source stream qualification already frozen')
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
        identity=old_task['identity'];record=next(r for r in summary['results'] if r['identity']==identity)
        result=runner._load(OLD/record['artifact'])['result'];group=(result['model'],result['profile'])
        if not result['passed'] or group in groups:raise ValueError('six unique qualified source references required')
        groups.add(group);case_key=old_task['payload']['case_key']
        inputs[case_key]=str((OLD/previous['inputs'][case_key]['path']).relative_to(ROOT))
        original=runner._load(OLD/previous['inputs'][identity]['path'])
        path=PUBLIC/'saved-inputs'/(identity+'.json')
        runner._write(path,dict(result=result,future=original['future'],range=original['range']))
        inputs[identity]=str(path.relative_to(ROOT))
        limits=dict(setups=1,source_steps=1600,independent_steps=1600,scalar_comparisons=336*1600)
        tasks.append(dict(identity=identity,input_key=identity,payload=dict(case_key=case_key,compiler=compiler,
            reference_center=old_task['payload']['reference_center'],limits=limits),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    if len(tasks)!=6 or groups!={(m,p) for m in range(3) for p in (False,True)}:raise ValueError('all six source groups required')
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
        if counts!=limits or counts!=row['work'] or row['source_steps']!=1600 or row['scalar_comparisons']!=336*1600:
            raise ValueError('stream work and finite reservations disagree')
        accounts.append(dict(identity=row['identity'],**counts))
    text=['# Streaming source-reference qualification','',
        f"{sum(r.get('passed',False) for r in rows)}/6 generated sources pass every midpoint/end reference check.",'',
        '| Candidate / removal | Passed | Maximum value difference (m/s²) | Maximum coefficient difference | State bytes |',
        '|---|---|---:|---:|---:|']
    for row in rows:
        if 'model' not in row:continue
        label=('Globe with specified field','Globe with zero field','Flat disc')[row['model']]+(' / profiled' if row['profile'] else ' / zero')
        text.append(f"| {label} | {'Yes' if row['passed'] else 'No'} | {row['maximum_value_difference']:.7g} | {row['maximum_coefficient_difference']:.7g} | {row['state_bytes']} |")
    text+=['',f"Checked {sum(r.get('source_steps',0) for r in rows):,}/9,600 compiled source steps, "
        f"{sum(r.get('independent_steps',0) for r in rows):,}/9,600 independent steps, and "
        f"{sum(r.get('scalar_comparisons',0) for r in rows):,}/3,225,600 scalar comparisons. "
        f"Elapsed {summary['elapsed_s']:.2f} seconds.",'',
        'The compiled calculation uses unchanged native tangent primitives. The independent calculation '
        'uses quaternion rotations and analytic Jacobians; local controls also use complex-step matrix '
        'exponentials. Both phases of every packet retain all 27 physical columns and the native clock branch. '
        'The fixed-size derivative state avoids a recording-size output tensor.','',
        'Array-stream hashes and selected prefixes are preserved. This qualifies source reference rows only. '
        'The tighter norm-constrained body interval has not yet been connected to full dynamic propagation. '
        'No full native trajectory, aircraft observation, protected ESA data or optimizer was used. '
        'Whole-program floating-point enclosure and observational coverage remain unqualified.','',
        '[Frozen scope](PLAN.md) · [Source reference](../ilvis0-source-reference/README.md) · [Next task](NEXT_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,complete=len(accounts)==6,full_native_trajectory_evaluations=0,optimizer_starts=0))
    receipt=runner._load(PUBLIC/'evidence-receipt.json');receipt['artifacts']['accounting.json']=runner._sha(PUBLIC/'accounting.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen six streams / 19200 source+independent steps / 3225600 scalar checks; zero full trajectories.')
    elif args.package_only:publish();print('Published streaming source evidence.')
    else:publication.check(DATA,PUBLIC);print('Verified streaming source evidence.')


if __name__=='__main__':main()
