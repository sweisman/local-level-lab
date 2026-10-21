#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish two finite generated-prefix cost profiles."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication
from lll.ilvis0_sharded_native import read

DATA=ROOT/'data/ilvis0-taylor-runtime-profile-20261021'
PUBLIC=ROOT/'docs/ilvis0-taylor-runtime-profile'
OLD=ROOT/'docs/ilvis0-taylor-complete-prediction'
QUALIFIED=ROOT/'docs/ilvis0-taylor-joint-controls'
ADAPTER='analysis/lll/ilvis0_taylor_runtime_profile.py'
PLAN='docs/ilvis0-taylor-runtime-profile/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/lll/ilvis0_source_runtime_profile.py',
    'analysis/tests/ilvis0_taylor_runtime_profile_worker.py',
    'analysis/tests/test_ilvis0_taylor_runtime_profile.py',
    'analysis/tests/test_ilvis0_transport_profile.py',
    'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']


def prepare():
    if DATA.exists():raise ValueError('runtime diagnostic already frozen')
    sources=set(SOURCES)
    for directory in (OLD,QUALIFIED):
        for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(runner.path_within(directory,name))!=digest:
                raise ValueError('sealed prerequisite changed')
        manifest=runner._load(directory/'manifest.json')
        if manifest['environment']!=runner.runtime_environment():raise ValueError('numerical environment changed')
        for name,digest in manifest['sources'].items():
            if name.startswith('analysis/lll/'):
                if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
                sources.add(name)
    if not runner._load(QUALIFIED/'summary.json')['passed']:raise ValueError('native controls required')
    if runner._load(OLD/'summary.json')['state']!='terminal':raise ValueError('complete predecessor required')
    previous=runner._load(OLD/'manifest.json');inputs={};tasks=[]
    compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
    for profile in (False,True):
        found=[]
        for key,record in previous['inputs'].items():
            if not key.startswith('case-'):continue
            path=OLD/record['path'];case=read(path)
            if (case['configuration']['model'],case['configuration']['profile'])==(1,profile):found.append(path)
        if len(found)!=1:raise ValueError('unique generated zero-field source required')
        from lll.ilvis0_taylor_runtime_profile import prefix
        prefix(read(found[0]),model=1,profile=profile)
        identity='profile-zero-field-'+('profiled' if profile else 'fixed')
        inputs[identity]=str(found[0].relative_to(ROOT))
        limits=dict(setups=1,source_setups=1,source_steps=128,source_body_bounds=128,
            derivative_setups=1,derivative_steps=128)
        tasks.append(dict(identity=identity,input_key=identity,
            payload=dict(profile=profile,packets=128,maximum_bound_seconds=45.,compiler=compiler,limits=limits),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=1,bound_steps=1024)))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,
        adapter=ADAPTER,workers=1,threads=1,maximum_wall_s=180,environment=runner.runtime_environment())


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA)
    rows=[];accounts=[]
    for item in summary['results']:
        record=runner._load(DATA/item['artifact']);row=record['result'];rows.append(row)
        task=next(t for t in manifest['tasks'] if t['identity']==item['identity'])
        limits=task['payload']['limits'];counts=dict.fromkeys(limits,0)
        for name in sorted(n for n in record['artifacts'] if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);increase=event['increase']
            if not increase or any(k not in counts or type(v)!=int or v<1 for k,v in increase.items()):
                raise ValueError('invalid cost-profile reservation')
            counts={k:v+increase.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):
                raise ValueError('cost-profile allowance changed')
        if 'work' in row and counts!=row['work']:raise ValueError('cost-profile accounting mismatch')
        accounts.append(dict(identity=item['identity'],**counts))
    text=['# Source-derivative propagation costs','',
        f"{sum(r.get('bound_completed',False) for r in rows)}/2 shortened bounds completed.",'',
        '| Processing | Function | Calls | Cumulative seconds |','|---|---|---:|---:|']
    for row in rows:
        if 'profile' not in row:continue
        label='Profiled removal' if row['processing_profile'] else 'Fixed-zero removal'
        for f in row['profile']['functions'][:15]:
            text.append(f"| {label} | {f['file']}:{f['function']} | {f['calls']} | {f['cumulative_s']:.5g} |")
    text+=['',f"Elapsed {summary['elapsed_s']:.2f} seconds; charged {summary['charged']['bound_calls']}/2 bounds "
        f"and {summary['charged']['bound_steps']}/2,048 logical steps.",'',
        'These are new 128-packet diagnostic inputs with their own physical-domain proofs. '
        'They do not reuse full-history training certificates or retry failed regions. '
        'Profiler costs are not full-recording speed, qualified prediction widths or '
        'observational uncertainty. No aircraft data, native trajectory or fitting was used.','',
        '[Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,charged=summary['charged']))
    receipt=runner._load(PUBLIC/'evidence-receipt.json')
    receipt['artifacts']['accounting.json']=runner._sha(PUBLIC/'accounting.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check','run'):group.add_argument('--'+name,action='store_true')
    parser.add_argument('--reserved-threads',type=int);args=parser.parse_args()
    if args.prepare:prepare();print('Frozen two 128-packet cost profiles; one numerical thread, 180 seconds.')
    elif args.run:
        if args.reserved_threads is None:parser.error('--run requires --reserved-threads')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Completed profiles: '+result['state'])
    elif args.package_only:publish();print('Published saved cost profiles.')
    else:publication.check(DATA,PUBLIC);print('Verified cost-profile evidence.')


if __name__=='__main__':main()
