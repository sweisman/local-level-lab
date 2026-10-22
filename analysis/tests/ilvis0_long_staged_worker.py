# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and execute the finite long-history staged feasibility matrix."""
import argparse
import importlib.util
import math
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-long-staged-feasibility-20261021'
PUBLIC=ROOT/'docs/ilvis0-long-staged-feasibility'
PLAN='docs/ilvis0-long-staged-feasibility/PLAN.md';ADAPTER='analysis/lll/ilvis0_long_staged.py'
REPORT='docs/ilvis0-long-staged-feasibility/build_report.py'


def prepare():
    from lll.ilvis0_long_staged import limits,recipe,validate_recipe
    if DATA.exists():raise ValueError('full-history feasibility already frozen')
    sources={PLAN,ADAPTER,REPORT,'analysis/tests/ilvis0_long_staged_worker.py',
        'analysis/tests/test_ilvis0_long_staged.py','analysis/tests/test_ilvis0_long_staged_report.py',
        'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py'}
    environment=runner.runtime_environment();inputs={};parents=[]
    for ordinal,name in enumerate(('ilvis0-staged-training-controls-v2','ilvis0-recording-duration-controls')):
        directory=ROOT/'docs'/name
        for artifact,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(runner.path_within(directory,artifact))!=digest:
                raise ValueError('qualified prerequisite changed')
        manifest=runner._load(directory/'manifest.json');parents.append(manifest)
        if not runner._load(directory/'summary.json')['passed'] or manifest['environment']!=environment:
            raise ValueError('passing prerequisites in the same environment required')
        for artifact,digest in manifest['sources'].items():
            if artifact.startswith('analysis/lll/'):
                if runner._sha(ROOT/artifact)!=digest:raise ValueError('qualified source changed: '+artifact)
                sources.add(artifact)
        inputs[f'prerequisite-{ordinal}']=str((directory/'evidence-receipt.json').relative_to(ROOT))
    previous=parents[-1];directory=ROOT/'docs/ilvis0-recording-duration-controls'
    compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
    settings=recipe();validate_recipe(settings);path=PUBLIC/'saved-inputs/recipe.json';runner._write(path,settings)
    inputs['recipe']=str(path.relative_to(ROOT));tasks=[];common=None
    for item in previous['tasks']:
        old=item['payload'];model=old['model'];profile=old['profile']
        source=directory/previous['inputs'][item['input_key']]['path']
        if runner._sha(source)!=previous['inputs'][item['input_key']]['sha256']:
            raise ValueError('qualified full-duration input changed')
        case=runner._load(source);config=case['configuration']
        if (len(case['dt'])!=96000 or config['limits'][25]!=1. or config['model']!=model
                or config['profile']!=profile):raise ValueError('qualified input geometry changed')
        # One fixed frame, established from initial metadata before any outcomes.
        frame=[config['radius'],config['radius']*math.cos(config['initial_c'][0]),1.]
        if common is None:common=frame
        if frame!=common:raise ValueError('common coordinate comparison frame required')
        key=f'case-{model}-{int(profile)}';inputs[key]=str(source.relative_to(ROOT))
        tasks.append(dict(identity=f'long-staged-{model}-{int(profile)}',input_key='recipe',
            payload=dict(model=model,profile=profile,case_key=key,compiler=compiler,limits=limits(),coordinate_scale=common),
            limits=dict(native_calls=12,packet_visits=1152000,bound_calls=6,bound_steps=5184000)))
    if len(tasks)!=6 or {(t['payload']['model'],t['payload']['profile']) for t in tasks}!={(m,p) for m in range(3) for p in (False,True)}:
        raise ValueError('all six distinct candidates required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=2,threads=1,maximum_wall_s=50400,environment=environment)


def publish():
    spec=importlib.util.spec_from_file_location('_long_feasibility_report',ROOT/REPORT)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.publish()


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','package-only','check'):group.add_argument('--'+name,action='store_true')
    parser.add_argument('--reserved-threads',type=int);args=parser.parse_args()
    if args.prepare:prepare();print('Frozen six cases / 72 native calls / 36 bounds / two threads / 14 hours.')
    elif args.run:
        if args.reserved_threads is None:parser.error('--run requires --reserved-threads')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Long-history feasibility: '+result['state'])
    elif args.package_only:publish();print('Published sealed evidence; no numerical work.')
    else:publication.check(DATA,PUBLIC);print('Verified full-history feasibility publication.')


if __name__=='__main__':main()
