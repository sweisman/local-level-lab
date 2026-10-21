# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and package two shortened generated-data runtime probes."""
import argparse,subprocess
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication
from lll.ilvis0_sharded_native import read

DATA=ROOT/'data/ilvis0-source-runtime-profile-20261020';PUBLIC=ROOT/'docs/ilvis0-source-runtime-profile'
OLD=ROOT/'docs/ilvis0-source-range-preflight';QUALIFIED=ROOT/'docs/ilvis0-source-native-v2-controls'
ADAPTER='analysis/lll/ilvis0_source_runtime_profile.py';PLAN='docs/ilvis0-source-runtime-profile/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/tests/ilvis0_source_runtime_profile_worker.py','analysis/tests/test_ilvis0_transport_profile.py',
    'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']


def prepare():
    if DATA.exists():raise ValueError('runtime profile already frozen')
    sources=set(SOURCES)
    for directory in (OLD,QUALIFIED):
        for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(runner.path_within(directory,name))!=digest:raise ValueError('sealed prerequisite changed')
        manifest=runner._load(directory/'manifest.json')
        if manifest['environment']!=runner.runtime_environment():raise ValueError('profiling environment changed')
        for name,digest in manifest['sources'].items():
            if name.startswith('analysis/lll/'):
                if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
                sources.add(name)
    if not runner._load(QUALIFIED/'summary.json')['passed']:raise ValueError('qualified candidate required')
    previous=runner._load(OLD/'manifest.json');tasks=[];inputs={}
    compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
    for model in (0,1):
        found=[]
        for old in previous['tasks']:
            bundle=read(OLD/previous['inputs'][old['input_key']]['path'])
            if bundle['result']['model']==model and not bundle['result']['profile']:found.append(old)
        if len(found)!=1:raise ValueError('unique fixed zero-removal source required')
        record=previous['inputs'][found[0]['payload']['case_key']];path=OLD/record['path'];case=read(path)
        if len(case['dt'])!=1600 or any(v!=.005 for v in case['dt'][:128]):raise ValueError('fixed prefix clock required')
        identity=f'profile-model-{model}';inputs[identity]=str(path.relative_to(ROOT))
        tasks.append(dict(identity=identity,input_key=identity,payload=dict(model=model,packets=128,maximum_bound_seconds=45.,compiler=compiler,limits=dict(setups=1,source_steps=128,source_body_bounds=128)),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=1,bound_steps=512)))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=1,threads=4,maximum_wall_s=120,environment=runner.runtime_environment())


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA)
    rows=[runner._load(DATA/r['artifact'])['result'] for r in summary['results']]
    accounts=[]
    for item,row in zip(summary['results'],rows,strict=True):
        envelope=runner._load(DATA/item['artifact'])
        task=next(t for t in manifest['tasks'] if t['identity']==item['identity'])
        limits=task['payload']['limits'];counts=dict.fromkeys(limits,0)
        for name in sorted(n for n in envelope['artifacts'] if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);increase=event['increase']
            if not increase or any(k not in counts or type(v)!=int or v<1 for k,v in increase.items()):raise ValueError('invalid profile reservation')
            counts={k:v+increase.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):raise ValueError('profile reservation changed')
        if 'work' in row and counts!=row['work']:raise ValueError('profile work and reservation differ')
        accounts.append(dict(identity=task['identity'],**counts))
    text=['# Runtime profiles of generated prefixes','',
        f"{sum(r.get('bound_completed',False) for r in rows)}/2 shortened bounds completed; both retain their profiling outcomes.",'',
        '| Candidate | Function | Calls | Cumulative seconds |','|---|---|---:|---:|']
    for row in rows:
        if 'profile' not in row:continue
        label=('Specified field','Zero field')[row['model']]
        for function in row['profile']['functions'][:12]:
            text.append(f"| {label} | {function['file']}:{function['function']} | {function['calls']} | {function['cumulative_s']:.5g} |")
    text+=['',f"Charged {summary['charged']['bound_calls']}/2 bounds and {summary['charged']['bound_steps']}/1,024 world/source packet-steps. "
        f"Elapsed {summary['elapsed_s']:.2f} seconds.",'',
        f"Reserved {sum(r['source_steps'] for r in accounts)}/256 source-reference steps and "
        f"{sum(r['source_body_bounds'] for r in accounts)}/256 rounded body bounds.",'',
        'These profiles locate implementation costs on shortened generated inputs. '
        'They preserve the clock range and use new physical-domain proofs; they do not '
        'transfer full-history training information to changed sources. Profiler times '
        'are not full-recording performance or numerical-qualification evidence. '
        'No native trajectory, observation, LP or optimizer was used.','',
        '[Frozen scope](PLAN.md) · [Saved-baseline comparison](../ilvis0-source-range-preflight/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,charged=summary['charged'],complete=len(accounts)==2,
        full_native_trajectory_evaluations=0,optimizer_starts=0))
    receipt=runner._load(PUBLIC/'evidence-receipt.json');receipt['artifacts']['accounting.json']=runner._sha(PUBLIC/'accounting.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen two 128-packet profiles / two bounds / 1024 bound steps; no native trajectories.')
    elif args.package_only:publish();print('Published finite runtime profiles.')
    else:publication.check(DATA,PUBLIC);print('Verified runtime profile evidence.')


if __name__=='__main__':main()
