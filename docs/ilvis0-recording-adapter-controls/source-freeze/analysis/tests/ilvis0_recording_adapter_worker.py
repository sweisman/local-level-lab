# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish old-recording/current-API compatibility controls."""
import argparse,gzip,json,subprocess
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-recording-adapter-controls-20261021';PUBLIC=ROOT/'docs/ilvis0-recording-adapter-controls'
OLD=ROOT/'docs/ilvis0-recording-scale-bounds'
PLAN='docs/ilvis0-recording-adapter-controls/PLAN.md';ADAPTER='analysis/lll/ilvis0_recording_adapter_controls.py'


def prepare():
    from lll.ilvis0_legacy_recording import convert,MODELS
    if DATA.exists():raise ValueError('recording adapter controls already frozen')
    original=runner._load(OLD/'manifest.json');environment=runner.runtime_environment()
    for name,digest in runner._load(OLD/'evidence-receipt.json')['artifacts'].items():
        if runner._sha(runner.path_within(OLD,name))!=digest:raise ValueError('historical recording evidence changed')
    if (original['environment']['python']!=environment['python']
            or original['environment']['executable']!=environment['executable']
            or any(original['environment']['packages'][name]!=version for name,version in environment['packages'].items())):
        raise ValueError('numerical environment differs from the original input study')
    qualified=ROOT/'docs/ilvis0-three-source-complete'
    for name,digest in runner._load(qualified/'evidence-receipt.json')['artifacts'].items():
        if runner._sha(runner.path_within(qualified,name))!=digest:raise ValueError('short-example qualification changed')
    qualification=runner._load(qualified/'manifest.json')
    if not runner._load(qualified/'comparison.json')['qualified'] or qualification['environment']!=environment:
        raise ValueError('qualified current method in the same environment required')
    sources={PLAN,ADAPTER,'analysis/lll/ilvis0_legacy_recording.py',
        'analysis/tests/test_ilvis0_legacy_recording.py','analysis/tests/ilvis0_recording_adapter_worker.py',
        'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py'}
    for name,digest in qualification['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
            sources.add(name)
    for name in ('analysis/tests/ilvis0_history_worker.py','analysis/tests/ilvis0_geographic_worker.py',
                 'analysis/tests/ilvis0_channel_envelope_worker.py','analysis/lll/ilvis0_tangent.cpp'):
        if runner._sha(ROOT/name)!=original['sources'][name]:raise ValueError('legacy API source changed: '+name)
        sources.add(name)
    tasks=[];inputs={};compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
    for model,name in enumerate(MODELS):
        source=OLD/original['inputs'][name+'-broad']['path'];digest=runner._sha(source)
        if digest!=original['inputs'][name+'-broad']['sha256']:raise ValueError('original generated input changed')
        with gzip.open(source,'rt') as stream:legacy=json.load(stream)
        key='legacy-'+str(model);inputs[key]=str(source.relative_to(ROOT))
        for profile in (False,True):
            case=convert(legacy,profile=profile,source_sha256=digest)
            identity=f'recording-api-{model}-{int(profile)}';path=PUBLIC/'saved-inputs'/(identity+'.json')
            runner._write(path,case);case_key=identity+'-case';inputs[case_key]=str(path.relative_to(ROOT))
            tasks.append(dict(identity=identity,input_key=key,payload=dict(case_key=case_key,model=model,profile=profile,compiler=compiler),
                limits=dict(native_calls=4,packet_visits=192000,bound_calls=0,bound_steps=0)))
    inputs['legacy-manifest']=str((OLD/'manifest.json').relative_to(ROOT))
    inputs['legacy-receipt']=str((OLD/'evidence-receipt.json').relative_to(ROOT))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=1,threads=1,maximum_wall_s=120,environment=environment)


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA)
    rows=[runner._load(DATA/item['artifact'])['result'] for item in summary['results']]
    if summary['charged']['native_calls']>24 or summary['charged']['bound_calls']:
        raise ValueError('recording API comparison exceeded its scope')
    text=['# Four-minute recording format compatibility','',
        f"{sum(r.get('passed',False) for r in rows)}/6 API cases passed; elapsed {summary['elapsed_s']:.2f} seconds.",'',
        f"Charged {summary['charged']['native_calls']}/24 native queries, zero interval bounds. "
        'Each case retains all 48,000 original generated packets and compares two fixed parameter points '
        'through the legacy and current callers, including every Jacobian column and warning bit.','',
        'The same kernel implements both callers. This is a format/API check, not independent physical '
        'validation, useful four-minute bounds or observational coverage. The original fixed-clock limitation '
        'is retained; no short-history training certificate was transferred.','',
        '[Frozen scope](PLAN.md) · [Earlier four-minute outcome](../ilvis0-recording-scale-bounds/INTERPRETATION.md) · '
        '[Next gates](../ilvis0-three-source-complete/NEXT_PLAN.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check','run'):group.add_argument('--'+name,action='store_true')
    parser.add_argument('--reserved-threads',type=int);args=parser.parse_args()
    if args.prepare:prepare();print('Frozen six recording API controls / 24 native queries / one thread / 120 seconds.')
    elif args.run:
        if args.reserved_threads is None:parser.error('--run requires --reserved-threads')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Recording API controls: '+result['state'])
    elif args.package_only:publish();print('Published recording API controls.')
    else:publication.check(DATA,PUBLIC);print('Verified recording API controls.')


if __name__=='__main__':main()
