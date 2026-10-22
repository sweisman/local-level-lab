# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and execute the finite staged-native known-answer matrix."""
import argparse,importlib.metadata,importlib.util,subprocess
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-staged-native-controls-20261021';PUBLIC=ROOT/'docs/ilvis0-staged-training-controls'
PLAN='docs/ilvis0-staged-training-controls/PLAN.md';ADAPTER='analysis/lll/ilvis0_staged_native_controls.py'
REPORT='docs/ilvis0-staged-training-controls/build_report.py'


def prepare():
    from lll.ilvis0_staged_native_controls import LIMITS
    if DATA.exists():raise ValueError('staged controls already frozen')
    sources={PLAN,ADAPTER,REPORT,'analysis/lll/ilvis0_staged_native.py','analysis/lll/ilvis0_staged_training.py',
        'analysis/tests/test_ilvis0_staged_training.py','analysis/tests/test_ilvis0_staged_native.py',
        'analysis/tests/test_ilvis0_staged_report.py','analysis/tests/ilvis0_staged_native_worker.py',
        'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py'}
    inputs={};environment=runner.runtime_environment()
    for ordinal,name in enumerate(('ilvis0-direct-joint-controls','ilvis0-recording-duration-controls')):
        directory=ROOT/'docs'/name
        for artifact,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(runner.path_within(directory,artifact))!=digest:raise ValueError('staged prerequisite changed')
        manifest=runner._load(directory/'manifest.json')
        if not runner._load(directory/'summary.json')['passed'] or manifest['environment']!=environment:
            raise ValueError('passing prerequisites in the same environment required')
        for artifact,digest in manifest['sources'].items():
            if artifact.startswith('analysis/lll/') or artifact in ('analysis/tests/test_ilvis0_native_box_bounds.py',
                                                                   'analysis/tests/test_ilvis0_regrouped_history.py'):
                if runner._sha(ROOT/artifact)!=digest:raise ValueError('qualified source changed: '+artifact)
                sources.add(artifact)
        inputs[f'prerequisite-{ordinal}']=str((directory/'evidence-receipt.json').relative_to(ROOT))
    compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0];tasks=[];catalog=[]
    for model in range(3):
        for profile in (False,True):
            identity=f'staged-{model}-{int(profile)}'
            item=dict(identity=identity,model=model,profile=profile,packets=32,dt_s=.005,
                      stage_sizes=[2,2],training_s=[.015,.03,.06,.09],future_s=.13)
            catalog.append(item)
            tasks.append(dict(identity=identity,input_key='catalog',payload=dict(item,limits=LIMITS,compiler=compiler,
                pytest=importlib.metadata.version('pytest')),limits=dict(native_calls=10,packet_visits=320,
                bound_calls=5,bound_steps=1440)))
    path=PUBLIC/'control-catalog.json';runner._write(path,catalog);inputs['catalog']=str(path.relative_to(ROOT))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=1,threads=1,maximum_wall_s=300,environment=environment)


def publish():
    spec=importlib.util.spec_from_file_location('_staged_report',ROOT/REPORT)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.publish()


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','package-only','check'):group.add_argument('--'+name,action='store_true')
    parser.add_argument('--reserved-threads',type=int);args=parser.parse_args()
    if args.prepare:prepare();print('Frozen six staged controls / 60 native calls / 30 bounds / one thread / 300 seconds.')
    elif args.run:
        if args.reserved_threads is None:parser.error('--run requires --reserved-threads')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Staged native controls: '+result['state'])
    elif args.package_only:publish();print('Published sealed staged controls; no numerical work.')
    else:publication.check(DATA,PUBLIC);print('Verified staged-control publication.')


if __name__=='__main__':main()
