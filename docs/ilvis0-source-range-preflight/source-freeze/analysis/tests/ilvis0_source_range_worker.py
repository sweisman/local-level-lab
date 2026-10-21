# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and package six actual-baseline transport comparisons."""
import argparse,subprocess
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication
from lll.ilvis0_sharded_native import read

DATA=ROOT/'data/ilvis0-source-range-preflight-20261020';PUBLIC=ROOT/'docs/ilvis0-source-range-preflight'
OLD=ROOT/'docs/ilvis0-source-stream-controls';PARENT=ROOT/'docs/ilvis0-conditioned-native-controls'
QUALIFIED=ROOT/'docs/ilvis0-source-native-v2-controls'
COMPARED=ROOT/'docs/ilvis0-compiled-range-preflight'
ADAPTER='analysis/lll/ilvis0_source_range_preflight.py';PLAN='docs/ilvis0-source-range-preflight/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/tests/ilvis0_source_range_worker.py','analysis/tests/test_ilvis0_transport_range_preflight.py',
    'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']


def prepare():
    if DATA.exists():raise ValueError('transport range preflight already frozen')
    sources=set(SOURCES)
    for directory in (OLD,PARENT,QUALIFIED,COMPARED):
        for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(runner.path_within(directory,name))!=digest:raise ValueError('sealed prerequisite changed')
        manifest=runner._load(directory/'manifest.json')
        if not runner._load(directory/'summary.json')['passed'] or manifest['environment']!=runner.runtime_environment():
            raise ValueError('qualified prerequisite and environment required')
        for name,digest in manifest['sources'].items():
            if name.startswith('analysis/lll/'):
                if runner._sha(ROOT/name)!=digest:raise ValueError('qualified implementation changed: '+name)
                sources.add(name)
    previous=runner._load(OLD/'manifest.json');parents=runner._load(PARENT/'manifest.json')
    tasks=[];inputs={};groups=set()
    compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
    baseline_summary=runner._load(COMPARED/'summary.json')
    for old_task in previous['tasks']:
        identity=old_task['identity'];key=old_task['input_key'];record=previous['inputs'][key]
        path=OLD/record['path'];bundle=read(path);group=(bundle['result']['model'],bundle['result']['profile'])
        if not bundle['result']['passed'] or group in groups:raise ValueError('six unique qualified source groups required')
        groups.add(group);inputs[identity]=str(path.relative_to(ROOT));case_key=old_task['payload']['case_key']
        inputs[case_key]=str((OLD/previous['inputs'][case_key]['path']).relative_to(ROOT))
        parent=next(t for t in parents['tasks'] if t['identity']==identity)
        parent_path=PARENT/parents['inputs'][parent['input_key']]['path'];conditioning_key='conditioning-'+identity
        parent_bundle=read(parent_path)
        if parent_bundle['projection']['input_binding']!=bundle['future']['bound']['conditioning']['input_binding']:
            raise ValueError('source and typed conditioning identity mismatch')
        inputs[conditioning_key]=str(parent_path.relative_to(ROOT))
        prior=next(r for r in baseline_summary['results'] if r['identity']==identity)
        prior_envelope=runner._load(COMPARED/prior['artifact'])
        if not prior_envelope['result']['passed']:raise ValueError('qualified compatible baseline required')
        bound_path=next(name for name in prior_envelope['artifacts'] if Path(name).name=='bound.json')
        baseline_key='baseline-'+identity;inputs[baseline_key]=str((COMPARED/bound_path).relative_to(ROOT))
        tasks.append(dict(identity=identity,input_key=identity,payload=dict(case_key=case_key,conditioning_key=conditioning_key,
            baseline_key=baseline_key,compiler=compiler,
            maximum_bound_seconds=120.,limits=dict(setups=1,exact_supports=6,source_steps=1600,source_body_bounds=1600)),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=1,bound_steps=6400)))
    if len(tasks)!=6 or groups!={(m,p) for m in range(3) for p in (False,True)}:raise ValueError('six complete groups required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=600,environment=runner.runtime_environment())


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA)
    rows=[runner._load(DATA/r['artifact'])['result'] for r in summary['results']];accounts=[]
    for record,row in zip(summary['results'],rows,strict=True):
        artifacts=runner._load(DATA/record['artifact'])['artifacts']
        task=next(t for t in manifest['tasks'] if t['identity']==record['identity'])
        original=read(DATA/manifest['inputs'][task['input_key']]['path'])['result']
        row.update(identity=task['identity'],model=original['model'],profile=original['profile'])
        limits=task['payload']['limits'];counts=dict.fromkeys(limits,0)
        for name in sorted(n for n in artifacts if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);inc=event['increase']
            if not inc or any(k not in counts or type(v)!=int or v<1 for k,v in inc.items()):raise ValueError('invalid reservation')
            counts={k:v+inc.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):raise ValueError('work journal changed')
        if 'work' in row and counts!=row['work']:raise ValueError('support/setup accounting mismatch')
        support_path=next((name for name in artifacts if Path(name).name=='conditioning.json'),None)
        verified=runner._load(DATA/support_path)['supports_verified'] if support_path else 0
        if verified>counts['exact_supports']:raise ValueError('verified work lacks reservation')
        arithmetic_path=next((name for name in artifacts if Path(name).name=='arithmetic.json'),None)
        if arithmetic_path and runner._load(DATA/arithmetic_path)['source_sha256']!=manifest['sources']['analysis/lll/ilvis0_compiled_bounds.cpp']:
            raise ValueError('compiled source mismatch')
        source_path=next((name for name in artifacts if Path(name).name=='source-compilation.json'),None)
        if source_path:
            for name,digest in runner._load(DATA/source_path)['sources'].items():
                if digest!=manifest['sources']['analysis/lll/'+name]:raise ValueError('compiled source-reference input mismatch')
        if row.get('source_reference_steps',0)>counts['source_steps'] or row.get('source_body_bounds',0)>counts['source_body_bounds']:
            raise ValueError('source work lacks reservation')
        accounts.append(dict(identity=task['identity'],**counts,verified_supports=verified,passed=row.get('passed',False)))
    text=['# Actual-baseline transport preflight','',
        f"{sum(r.get('passed',False) for r in rows)}/6 source/reference comparisons passed.",'',
        '| Candidate / removal | Matched | Best saved N / E / height allowance (m) | Fresh allowance (m) | Retained minimum (m) |',
        '|---|---|---:|---:|---:|']
    for row in rows:
        if 'model' not in row:continue
        label=('Globe with specified field','Globe with zero field','Flat disc')[row['model']]+(' / profiled' if row['profile'] else ' / zero')
        display=lambda name:' / '.join(f'{v:.6g}' for v in (row.get(name) or [])) or 'unavailable'
        text.append(f"| {label} | {'Yes' if row['passed'] else 'No'} | {display('baseline_remainder_m')} | {display('fresh_remainder_m')} | {display('retained_remainder_m')} |")
    text+=['',f"Charged {summary['charged']['bound_calls']}/6 bounds and {summary['charged']['bound_steps']}/38,400 world/source packet-steps. "
        f"Elapsed {summary['elapsed_s']:.2f} seconds. Preserved {sum(r['exact_supports'] for r in accounts)}/36 exact support verifications.",'',
        f"Reserved {sum(r['source_steps'] for r in accounts):,}/9,600 compiled source steps and "
        f"{sum(r['source_body_bounds'] for r in accounts):,}/9,600 rounded body bounds separately from full trajectory evaluations.",'',
        'This measures native unshared error allowances on the actual saved source domains. '
        'It does not recompute complete sector unions or qualify a future-range target. '
        'The qualified rounded body-source interval is installed. '
        'No full trajectory oracle, LP, aircraft observation, protected ESA data or optimizer was used.','',
        '[Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,charged=summary['charged'],complete=len(accounts)==6,exact_supports_reserved=sum(r['exact_supports'] for r in accounts),exact_supports_verified=sum(r['verified_supports'] for r in accounts),source_steps_reserved=sum(r['source_steps'] for r in accounts),source_body_bounds_reserved=sum(r['source_body_bounds'] for r in accounts),new_native_evaluations=0,optimizer_starts=0))
    receipt=runner._load(PUBLIC/'evidence-receipt.json');receipt['artifacts']['accounting.json']=runner._sha(PUBLIC/'accounting.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen six bounds / 38400 bound steps / 36 support verifications; zero native trajectories.')
    elif args.package_only:publish();print('Published actual-baseline transport preflight.')
    else:publication.check(DATA,PUBLIC);print('Verified actual-baseline transport preflight.')


if __name__=='__main__':main()
