# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze duration/clock API controls before complete-horizon bound work."""
import argparse,subprocess
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-recording-duration-controls-20261021';PUBLIC=ROOT/'docs/ilvis0-recording-duration-controls'
PARENT=ROOT/'docs/ilvis0-recording-adapter-controls'
PLAN='docs/ilvis0-recording-duration-controls/PLAN.md';ADAPTER='analysis/lll/ilvis0_recording_duration_controls.py'


def prepare():
    from lll.ilvis0_recording_fixture import extend
    if DATA.exists():raise ValueError('duration controls already frozen')
    original=runner._load(PARENT/'manifest.json');environment=runner.runtime_environment()
    for name,digest in runner._load(PARENT/'evidence-receipt.json')['artifacts'].items():
        if runner._sha(runner.path_within(PARENT,name))!=digest:raise ValueError('parent recording evidence changed')
    if not runner._load(PARENT/'summary.json')['passed'] or original['environment']!=environment:
        raise ValueError('qualified parent in the same environment required')
    sources={PLAN,ADAPTER,'analysis/lll/ilvis0_recording_fixture.py','analysis/tests/test_ilvis0_recording_fixture.py',
        'analysis/tests/ilvis0_recording_duration_worker.py','analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py'}
    for name,digest in original['sources'].items():
        if name.startswith('analysis/lll/') or name.startswith('analysis/tests/ilvis0_'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
            sources.add(name)
    tasks=[];inputs={};compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
    for item in original['tasks']:
        spec=item['payload'];model=spec['model'];profile=spec['profile']
        parent_path=PARENT/original['inputs'][spec['case_key']]['path'];digest=runner._sha(parent_path)
        if digest!=original['inputs'][spec['case_key']]['sha256']:raise ValueError('qualified parent case changed')
        case=extend(runner._load(parent_path),packets=96000,clock_offset_s=1.,parent_sha256=digest)
        identity=f'duration-api-{model}-{int(profile)}';path=PUBLIC/'saved-inputs'/(identity+'.json')
        runner._write(path,case);inputs[identity]=str(path.relative_to(ROOT))
        parent_key=identity+'-parent';inputs[parent_key]=str(parent_path.relative_to(ROOT))
        legacy_key=item['input_key'];inputs[legacy_key]=str((PARENT/original['inputs'][legacy_key]['path']).relative_to(ROOT))
        tasks.append(dict(identity=identity,input_key=identity,
            payload=dict(parent_key=parent_key,legacy_key=legacy_key,model=model,profile=profile,compiler=compiler),
            limits=dict(native_calls=4,packet_visits=384000,bound_calls=0,bound_steps=0)))
    if len(tasks)!=6:raise ValueError('all three candidates and processing variants required')
    inputs['parent-manifest']=str((PARENT/'manifest.json').relative_to(ROOT))
    inputs['parent-receipt']=str((PARENT/'evidence-receipt.json').relative_to(ROOT))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=1,threads=1,maximum_wall_s=600,environment=environment)


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA)
    rows=[runner._load(DATA[item['artifact']])['result'] for item in summary['results']]
    if (summary['charged']['native_calls']>24 or summary['charged']['packet_visits']>2304000
            or summary['charged']['bound_calls']):raise ValueError('duration comparison exceeded its scope')
    text=['# Eight-minute input and clock handling','',
        f"{sum(r.get('passed',False) for r in rows)}/6 API cases pass; elapsed {summary['elapsed_s']:.2f} seconds.",'',
        'Each generated history contains 96,000 packets, retaining its original 48,000-packet prefix '
        'bit for bit. The newly declared clock limit is ±1 second; all other physical settings are preserved.','',
        '| Candidate | Processing | API agreement | Clock derivative retained |','|---|---|---|---|']
    for task,row in zip(manifest['tasks'],rows,strict=True):
        spec=task['payload'];label=('Specified-field globe','Zero-field globe','Flat disc')[spec['model']]
        valid=row.get('passed',False)
        text.append(f"| {label} | {'Profiled removal' if spec['profile'] else 'Zero removal'} | "
            f"{'Exact' if valid else 'Failed'} | {'Yes' if valid else 'Unsupported'} |")
    text+=['',f"Charged {summary['charged']['native_calls']}/24 native queries, no interval bounds or optimizer starts. "
        'The queries at 438 and 478 seconds retain full clock support. All 27 Jacobian columns and warning '
        'bits are compared between callers of the same compiled kernel.','',
        'This is input/API qualification, not independent physical validation, useful nonlinear prediction '
        'ranges or an established observation-error law. No aircraft recordings or protected ESA outcomes '
        'were inspected, and no earlier study was resumed.','',
        '[Frozen scope](PLAN.md) · [Full-horizon requirements](../ilvis0-three-source-complete/NEXT_PLAN.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check','run'):group.add_argument('--'+name,action='store_true')
    parser.add_argument('--reserved-threads',type=int);args=parser.parse_args()
    if args.prepare:prepare();print('Frozen six duration/clock cases / 24 calls / 2,304,000 visits / one thread / 600 seconds.')
    elif args.run:
        if args.reserved_threads is None:parser.error('--run requires --reserved-threads')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Duration/clock controls: '+result['state'])
    elif args.package_only:publish();print('Published duration/clock controls.')
    else:publication.check(DATA,PUBLIC);print('Verified duration/clock controls.')


if __name__=='__main__':main()
