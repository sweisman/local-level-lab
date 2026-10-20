#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frozen complete 7.2-second generated comparison with shared force transforms."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner

DATA=ROOT/'data/ilvis0-transform-cover-20261020';PUBLIC=ROOT/'docs/ilvis0-transform-cover'
OLD=ROOT/'docs/ilvis0-longer-acceleration-cover';PROJECTED=ROOT/'docs/ilvis0-projected-future-bounds'
QUALIFIED=ROOT/'docs/ilvis0-transform-envelope-controls';NATIVE=ROOT/'docs/ilvis0-transform-native-controls'
COMPILER=ROOT/'docs/ilvis0-acceleration-native-controls/manifest.json'
ADAPTER='analysis/lll/ilvis0_transform_prediction.py'
SOURCES=[ADAPTER,'analysis/lll/ilvis0_transform_sector_experiment.py','analysis/tests/ilvis0_transform_cover_worker.py',
    'analysis/tests/test_ilvis0_transform_prediction.py','analysis/tests/ilvis0_control_shards.py',
    'analysis/tests/run_numerical.py','docs/ilvis0-transform-cover/PLAN.md']


def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    if DATA.exists():raise ValueError('complete transform comparison already frozen')
    for directory in (OLD,PROJECTED,QUALIFIED,NATIVE):
        for name,digest in load(directory/'evidence-receipt.json')['artifacts'].items():
            if sha(directory/name)!=digest:raise ValueError('frozen prerequisite evidence changed')
        if not load(directory/'summary.json')['passed']:raise ValueError('prerequisite failed')
    previous=load(OLD/'manifest.json');qualified=load(QUALIFIED/'manifest.json');sources=set(SOURCES)
    if qualified['environment']!=runner.runtime_environment():raise ValueError('qualified numerical environment changed')
    for name,digest in qualified['sources'].items():
        if name.startswith('analysis/lll/'):
            if sha(ROOT/name)!=digest:raise ValueError('qualified computation changed: '+name)
            sources.add(name)
    compilers=load(COMPILER)['compilers']
    for compiler,version in compilers.items():
        if subprocess.check_output([compiler,'--version'],text=True).splitlines()[0]!=version:raise ValueError('native compiler changed')
    tasks=[];inputs={}
    for old in previous['tasks']:
        model=old['payload']['model'];profile=old['payload']['profile'];sector=old['payload']['sector']
        identity=f'transform-full-{model}-{int(profile)}-{sector}';payload=dict(old['payload'],identity=identity,compilers=compilers)
        if payload['packets']!=1600 or payload['future_time']!=7.2:raise ValueError('matched complete input/horizon required')
        key=old['input_key'];source=OLD/previous['inputs'][key]['path']
        if sha(source)!=previous['inputs'][key]['sha256']:raise ValueError('matched generated input changed')
        inputs[key]=str(source.relative_to(ROOT));tasks.append(dict(identity=identity,input_key=key,payload=payload,
            limits=dict(native_calls=3,packet_visits=4800,bound_calls=8,bound_steps=25600)))
    inputs['baseline']=str((PROJECTED/'case-unions.json').relative_to(ROOT))
    inputs['ordinary-baseline']=str((OLD/'case-unions.json').relative_to(ROOT))
    inputs['compiler-reference']=str(COMPILER.relative_to(ROOT))
    if len(tasks)!=48:raise ValueError('complete 48-sector cover required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=5400,environment=runner.runtime_environment())


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);rows=[load(DATA/r['artifact'])['result'] for r in summary['results']]
    old=load(DATA/manifest['inputs']['baseline']['path'])['cases'];ordinary=load(DATA/manifest['inputs']['ordinary-baseline']['path'])['cases'];cases=[]
    for model in range(3):
        for profile in (False,True):
            selected=[r for r in rows if r.get('task',{}).get('model')==model and r.get('task',{}).get('profile')==profile]
            complete=len(selected)==8 and all(r['passed'] for r in selected)
            included=[r for r in selected if not r.get('excluded',False) and 'future_lower_m' in r]
            record=dict(model=model,profile=profile,complete=complete,completed=len(selected),included=len(included),future_time_s=7.2)
            if included:
                lower=[min(r['future_lower_m'][i] for r in included) for i in range(3)]
                upper=[max(r['future_upper_m'][i] for r in included) for i in range(3)];width=[b-a for a,b in zip(lower,upper)]
                prior=next(r['union_width_m'] for r in old if r['model']==model and r['profile']==profile)
                plain=next(r['union_width_m'] for r in ordinary if r['model']==model and r['profile']==profile)
                axes=[2*a<=b for a,b in zip(width,prior)]
                record.update(lower_m=lower,upper_m=upper,union_width_m=width,projected_baseline_width_m=prior,
                    ordinary_baseline_width_m=plain,ratio_to_projected=[a/b for a,b in zip(width,prior)],
                    ratio_to_ordinary=[a/b for a,b in zip(width,plain)],twofold_axes=axes,twofold=complete and all(axes))
            cases.append(record)
    comparison=dict(cases=cases,all_cases_complete=summary['passed'] and all(r['complete'] and r['included'] for r in cases),
        all_cases_twofold=summary['passed'] and all(r.get('twofold',False) for r in cases),
        engineering_threshold='new widths <= 0.5 * projected 7.2-second widths on every case/axis',scientific_decision='abstain')
    runner._replace(DATA/'comparison.json',comparison)
    names={'manifest.json','authorization.json','start.json','start.seal.json','summary.json','completion.json','comparison.json'}
    names.update('source-freeze/'+n for n in manifest['sources']);names.update(r['path'] for r in manifest['inputs'].values())
    for row in summary['results']:
        path=DATA/row['artifact'];names.update((row['artifact'],str(path.with_suffix('.seal.json').relative_to(DATA))));names.update(load(path)['artifacts'])
    for shard in range(4):
        directory=DATA/'shards'/f'{shard:03d}'
        for name in ('done.json','worker.log'):
            if (directory/name).exists():names.add(str((directory/name).relative_to(DATA)))
        for path in (directory/'charges').rglob('*.json'):names.add(str(path.relative_to(DATA)))
    for name in sorted(names):
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    labels=['Globe with specified field','Globe with zero field','Flat disc']
    text=['# Complete common-force-transform prediction comparison','',f"{sum(r['passed'] for r in rows)}/48 sectors pass correctness; state: {summary['state']}.",'',
        f"All six cases meet the preregistered twofold width-reduction target: **{'yes' if comparison['all_cases_twofold'] else 'no'}**.",'',
        'Complete generated prediction widths at 7.2 seconds; all original physical boxes, eight sectors and 51 columns remain. '
        'These are not measured aircraft errors, calibrated intervals or new model preferences.','',
        '| Candidate / removal | Complete | Width N / E / height (m) | Ratio to projected baseline | Twofold target |',
        '|---|---|---:|---:|---|']
    for row in cases:
        widths=', '.join(f'{v:.4f}' for v in row.get('union_width_m',[])) or 'unavailable'
        ratios=', '.join(f'{v:.4f}' for v in row.get('ratio_to_projected',[])) or 'unavailable'
        text.append(f"| {labels[row['model']]} / {'profiled' if row['profile'] else 'zero'} | {'Yes' if row['complete'] else 'No'} | {widths} | {ratios} | {'Yes' if row.get('twofold') else 'No'} |")
    text.extend(['',f"The study charged {summary['charged']['native_calls']} native calls and {summary['charged']['bound_calls']} bounds "
        f"in {summary['elapsed_s']:.1f} seconds. Bound-step reservations count both exact-clock and propagation passes. "
        'No original aircraft reads, observed fits or protected ESA outcomes occur. '
        'Recording-scale usefulness, whole-program numerical treatment and observation-error adequacy remain separate gates.','',
        '[Frozen scope](PLAN.md) · [Joint qualification](../ilvis0-transform-envelope-controls/INTERPRETATION.md) · '
        '[Projected baseline](../ilvis0-projected-future-bounds/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).'])
    (PUBLIC/'README.md').write_text('\n'.join(text)+'\n')
    runner._replace(PUBLIC/'evidence-receipt.json',dict(artifacts={n:sha(PUBLIC/n) for n in names|{'README.md','PLAN.md'}}))


def main():
    parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 48 complete common-transform prediction sectors.')
    elif args.package_only:publish();print('Published complete transform prediction evidence.')
    else:
        runner.verify_completion(DATA)
        for name,digest in load(PUBLIC/'evidence-receipt.json')['artifacts'].items():
            if sha(PUBLIC/name)!=digest:raise ValueError('public transform prediction evidence changed')
        print('Verified complete transform prediction evidence.')


if __name__=='__main__':main()
