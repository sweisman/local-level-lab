#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prepare and publish the longer full prediction control, without numerical imports."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner

NAME='ilvis0-longer-acceleration-cover-20261020'
DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-longer-acceleration-cover'
SHORT=ROOT/'docs/ilvis0-acceleration-cover';DURATION=ROOT/'docs/ilvis0-acceleration-duration-growth'
NATIVE=ROOT/'docs/native-sharded-execution/native-qualification'
ADAPTER='analysis/lll/ilvis0_sharded_prediction.py'
SOURCES=[ADAPTER,'analysis/tests/ilvis0_longer_acceleration_cover.py',
    'analysis/tests/test_ilvis0_sharded_prediction.py','docs/ilvis0-longer-acceleration-cover/PLAN.md']


def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_predecessor(directory):
    receipt=load(directory/'evidence-receipt.json')
    for name,digest in receipt['artifacts'].items():
        if sha(directory/name)!=digest:raise ValueError('predecessor evidence changed: '+name)
    manifest=load(directory/'manifest.json')
    if not load(directory/'summary.json')['passed']:raise ValueError('prerequisite did not pass')
    for name,digest in manifest['sources'].items():
        if name.startswith('analysis/lll/') and sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
    return manifest


def prepare():
    if DATA.exists():raise ValueError('existing study cannot be refrozen')
    short=checked_predecessor(SHORT);duration=checked_predecessor(DURATION);native=checked_predecessor(NATIVE)
    if not load(SHORT/'case-comparison.json')['tenfold_vs_original']:raise ValueError('short usefulness gate failed')
    environment=runner.runtime_environment()
    if native['environment']!=environment:raise ValueError('native compatibility environment changed')
    for compiler,version in duration['compilers'].items():
        if subprocess.check_output([compiler,'--version'],text=True).splitlines()[0]!=version:raise ValueError('compiler changed')
    tasks=[];inputs={}
    for original in short['tasks']:
        payload=dict(original,identity='longer-'+original['identity'],packets=1600,
            training_times=[4*t for t in original['training_times']],future_time=4*original['future_time'],
            maximum_bound_seconds=120.,compilers=duration['compilers'])
        key=f"case-{original['model']}-{int(original['profile'])}"
        record=duration['inputs'][key];source=DURATION/record['path']
        if sha(source)!=record['sha256']:raise ValueError('long generated input changed')
        inputs[key]=str(source.relative_to(ROOT))
        tasks.append(dict(identity=payload['identity'],payload=payload,input_key=key,
            limits=dict(native_calls=3,packet_visits=4800,bound_calls=8,bound_steps=12800)))
    if len(tasks)!=48 or len(inputs)!=6:raise ValueError('complete six-case/eight-sector cover required')
    inputs['short-unions']=str((SHORT/'case-unions.json').relative_to(ROOT))
    sources=set(SOURCES)
    for manifest in (short,duration,native):sources.update(name for name in manifest['sources'] if name.startswith('analysis/lll/'))
    sources.update(('analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py'))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,
        adapter=ADAPTER,workers=4,threads=1,maximum_wall_s=5400,environment=environment)


def publication():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);groups=[]
    old=load(DATA/manifest['inputs']['short-unions']['path'])['cases']
    rows={row['identity']:load(DATA/row['artifact'])['result'] for row in summary['results']}
    for model in range(3):
        for profile in (False,True):
            tasks=[t for t in manifest['tasks'] if t['payload']['model']==model and t['payload']['profile']==profile]
            complete=len(tasks)==8 and all(t['identity'] in rows and rows[t['identity']]['passed'] for t in tasks)
            included=[rows[t['identity']] for t in tasks if t['identity'] in rows and not rows[t['identity']].get('excluded',False) and 'future_lower_m' in rows[t['identity']]]
            record=dict(model=model,profile=profile,complete=complete,completed=sum(t['identity'] in rows for t in tasks),
                included=len(included),future_time_s=7.2)
            if included:
                lower=[min(r['future_lower_m'][axis] for r in included) for axis in range(3)]
                upper=[max(r['future_upper_m'][axis] for r in included) for axis in range(3)]
                width=[b-a for a,b in zip(lower,upper)]
                previous=next(r for r in old if r['case_key']==f'case-{model}-{int(profile)}-400')
                record.update(lower_m=lower,upper_m=upper,union_width_m=width,short_width_m=previous['union_width_m'],
                    width_ratio_to_short=[w/p for w,p in zip(width,previous['union_width_m'])])
            groups.append(record)
    report=dict(cases=groups,all_cases_complete=summary['passed'] and all(r['complete'] and r['included'] for r in groups),
        scientific_decision='abstain',observational_coverage_qualified=False)
    runner._replace(DATA/'case-unions.json',report)
    names={'manifest.json','authorization.json','start.json','start.seal.json','completion.json','summary.json','case-unions.json'}
    names.update('source-freeze/'+name for name in manifest['sources'])
    names.update(r['path'] for r in manifest['inputs'].values())
    for row in summary['results']:
        path=DATA/row['artifact'];envelope=load(path)
        names.update((row['artifact'],str(path.with_suffix('.seal.json').relative_to(DATA))));names.update(envelope['artifacts'])
    for shard in range(manifest['allocation']['workers']):
        directory=DATA/'shards'/f'{shard:03d}'
        for name in ('done.json','worker.log'):
            if (directory/name).exists():names.add(str((directory/name).relative_to(DATA)))
        for path in (directory/'charges').rglob('*.json'):names.add(str(path.relative_to(DATA)))
    for name in sorted(names):
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    passed=sum(row['passed'] for row in summary['results'])
    text=['# Longer complete prediction comparison','',f"{passed}/48 sectors pass; state: {summary['state']}.",'',
        'These are complete generated prediction ranges at 7.2 seconds, using six earlier observations. '
        'They are not aircraft errors, recording-scale confidence intervals or scientific detections.','',
        '| Model | Processing case | Complete | Width N / E / height (m) |','|---|---|---|---:|']
    labels=['Globe with specified field','Globe with zero field','Flat disc']
    for group in groups:
        widths=', '.join(f'{v:.3f}' for v in group['union_width_m']) if 'union_width_m' in group else 'unavailable'
        text.append(f"| {labels[group['model']]} | {'Profiled removal' if group['profile'] else 'Zero removal'} | {'Yes' if group['complete'] else 'No'} | {widths} |")
    text.extend(['',f"The study used {summary['charged']['native_calls']} native evaluations and {summary['charged']['bound_calls']} bounds in {summary['elapsed_s']:.1f} seconds. "
        'All original physical bounds, orientation sectors and 42 columns remain. Longer horizons, numerical error and observational uncertainty still need qualification.','',
        '[Frozen scope](PLAN.md) · [Short comparison](../ilvis0-acceleration-cover/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).'])
    (PUBLIC/'README.md').write_text('\n'.join(text)+'\n')
    runner._replace(PUBLIC/'evidence-receipt.json',dict(artifacts={n:sha(PUBLIC/n) for n in sorted(names|{'README.md','PLAN.md'})}))


def main():
    parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 48 longer prediction sectors; no workers launched.')
    elif args.package_only:publication();print('Published saved longer prediction evidence.')
    else:
        runner.verify_completion(DATA)
        for name,digest in load(PUBLIC/'evidence-receipt.json')['artifacts'].items():
            if sha(PUBLIC/name)!=digest:raise ValueError('published longer evidence changed')
        print('Verified longer prediction freeze and public evidence.')


if __name__=='__main__':main()
