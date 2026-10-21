# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish complete-prefix physical source-value controls."""
import argparse,subprocess
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication
from lll.ilvis0_sharded_native import read

DATA=ROOT/'data/ilvis0-source-value-controls-20261020'
PUBLIC=ROOT/'docs/ilvis0-source-value-controls'
OLD=ROOT/'docs/ilvis0-source-stream-controls'
QUALIFIED=ROOT/'docs/ilvis0-compiled-range-preflight'
ADAPTER='analysis/lll/ilvis0_source_value_controls.py';PLAN='docs/ilvis0-source-value-controls/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/lll/ilvis0_source_value_stream.py',
    'analysis/lll/ilvis0_rotation_roundoff.py','analysis/lll/ilvis0_calibration_roundoff.py',
    'analysis/tests/ilvis0_source_value_worker.py','analysis/tests/test_ilvis0_source_value_stream.py',
    'analysis/tests/test_ilvis0_rotation_roundoff.py','analysis/tests/test_ilvis0_calibration_roundoff.py',
    'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']


def prepare():
    if DATA.exists():raise ValueError('source-value qualification already frozen')
    sources=set(SOURCES)
    for directory in (OLD,QUALIFIED):
        for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(runner.path_within(directory,name))!=digest:raise ValueError('sealed prerequisite changed')
        manifest=runner._load(directory/'manifest.json')
        if not runner._load(directory/'summary.json')['passed'] or manifest['environment']!=runner.runtime_environment():
            raise ValueError('qualified prerequisites and unchanged environment required')
        for name,digest in manifest['sources'].items():
            if name.startswith('analysis/lll/'):
                if runner._sha(ROOT/name)!=digest:raise ValueError('qualified implementation changed: '+name)
                sources.add(name)
    previous=runner._load(OLD/'manifest.json');compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
    tasks=[];inputs={};groups=set()
    for old in previous['tasks']:
        key=old['input_key'];record=previous['inputs'][key];path=OLD/record['path'];bundle=read(path)
        group=(bundle['result']['model'],bundle['result']['profile'])
        if not bundle['result']['passed'] or group in groups:raise ValueError('six unique source groups required')
        groups.add(group);inputs[key]=str(path.relative_to(ROOT));case_key=old['payload']['case_key']
        inputs[case_key]=str((OLD/previous['inputs'][case_key]['path']).relative_to(ROOT))
        tasks.append(dict(identity='physical-'+old['identity'],input_key=key,
            payload=dict(case_key=case_key,compiler=compiler,maximum_seconds=120.,
                limits=dict(setups=1,source_steps=1600,scalar_comparisons=19200,norm_closures=3200)),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=1,bound_steps=3200)))
    if len(tasks)!=6 or groups!={(m,p) for m in range(3) for p in (False,True)}:raise ValueError('complete six-source matrix required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=600,environment=runner.runtime_environment())


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);rows=[];accounts=[]
    for item in summary['results']:
        envelope=runner._load(DATA/item['artifact']);row=envelope['result'];artifacts=envelope['artifacts']
        task=next(t for t in manifest['tasks'] if t['identity']==item['identity'])
        bundle=read(DATA/manifest['inputs'][task['input_key']]['path']);old=bundle['result']
        row=dict(row,identity=task['identity'],model=old['model'],profile=old['profile']);rows.append(row)
        limits=task['payload']['limits'];counts=dict.fromkeys(limits,0)
        for name in sorted(n for n in artifacts if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);increment=event['increase']
            if not increment or any(k not in counts or type(v)!=int or v<1 for k,v in increment.items()):
                raise ValueError('invalid source reservation')
            counts={k:v+increment.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):raise ValueError('source reservation changed')
        if 'work' in row and counts!=row['work']:raise ValueError('completed source work differs from reservations')
        if row.get('passed') and (counts!=limits or row.get('source_steps')!=1600 or row.get('norm_closures')!=3200
                or row.get('scalar_comparisons')!=19200):raise ValueError('incomplete passing source control')
        compilation_path=next((name for name in artifacts if Path(name).name=='compilation.json'),None)
        if compilation_path:
            compilation=runner._load(DATA/compilation_path)
            if compilation['arithmetic']['source_sha256']!=manifest['sources']['analysis/lll/ilvis0_compiled_bounds.cpp']:
                raise ValueError('compiled arithmetic source differs from freeze')
            for name,digest in compilation['source']['sources'].items():
                if digest!=manifest['sources']['analysis/lll/'+name]:raise ValueError('source-reference compiler input differs from freeze')
        accounts.append(dict(identity=task['identity'],**counts,passed=row.get('passed',False)))
    text=['# Complete-prefix physical source-value checks','',
        f"**{sum(row.get('passed',False) for row in rows)}/6 generated sources passed.**",'',
        '| Candidate / removal | Result | Completed source steps | Scalar checks | Norm closures |',
        '|---|---|---:|---:|---:|']
    for row in rows:
        label=('Globe with specified field','Globe with zero field','Flat disc')[row['model']]+(' / profiled' if row['profile'] else ' / zero')
        state='Passed' if row.get('passed') else row.get('reason','Failed')
        text.append(f"| {label} | {state} | {row.get('source_steps',0)} | {row.get('scalar_comparisons',0)} | {row.get('norm_closures',0)} |")
    text+=['',f"Charged {summary['charged']['bound_calls']}/6 complete bounds and {summary['charged']['bound_steps']}/19,200 "
        f"bound steps. Reserved {sum(a['source_steps'] for a in accounts):,}/9,600 source-reference steps, "
        f"{sum(a['scalar_comparisons'] for a in accounts):,}/115,200 comparisons and "
        f"{sum(a['norm_closures'] for a in accounts):,}/19,200 closures. Elapsed {summary['elapsed_s']:.2f} seconds.",'',
        'The reported arithmetic allowances include calibration, rotation-reference and matrix operations. '
        'Each completed comparison uses those allowances directly, without an added numerical margin. '
        'Hashes and selected prefixes preserve both streams. Failed attempts and reservations remain recorded.','',
        'This qualifies physical source values only. Training-derived acceleration constraints, '
        'explicit affine-reference rows and integration into complete position bounds remain separate gates. '
        'The existing trained-adapter point failures are unchanged. No full native trajectory, '
        'aircraft fit, protected ESA data or optimizer entered this study. Whole-program floating-point '
        'enclosure and observational coverage remain unqualified.','',
        '[Frozen scope](PLAN.md) · [Source rounding work](../ilvis0-body-interval/ROUNDING_PLAN.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,charged=summary['charged'],complete=len(accounts)==6,
        full_native_trajectory_evaluations=0,optimizer_starts=0,training_conditioning_installed=False))
    receipt=runner._load(PUBLIC/'evidence-receipt.json');receipt['artifacts']['accounting.json']=runner._sha(PUBLIC/'accounting.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen six physical-source bounds / 19200 bound steps / 115200 scalar checks.')
    elif args.package_only:publish();print('Published physical source-value qualification.')
    else:publication.check(DATA,PUBLIC);print('Verified physical source-value qualification.')


if __name__=='__main__':main()
