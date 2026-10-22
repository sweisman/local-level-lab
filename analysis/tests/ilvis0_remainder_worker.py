# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and run twelve conditional-remainder native software controls."""
import argparse
import importlib.util
import math
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-remainder-native-controls-20261021'
PUBLIC=ROOT/'docs/ilvis0-remainder-native-controls'
PLAN='docs/ilvis0-remainder-native-controls/PLAN.md'
ADAPTER='analysis/lll/ilvis0_remainder_controls.py'
REPORT='docs/ilvis0-remainder-native-controls/build_report.py'


def prepare():
    from lll.ilvis0_remainder_controls import limits,recipe,validate_recipe
    if DATA.exists():raise ValueError('conditional-remainder study already frozen')
    sources={PLAN,ADAPTER,REPORT,'analysis/tests/ilvis0_remainder_worker.py',
        'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py',
        'analysis/lll/ilvis0_conditional_remainder.py','analysis/lll/ilvis0_remainder_native.py',
        'analysis/lll/ilvis0_remainder_interface.py','analysis/lll/ilvis0_packet_boundary_flags.py',
        'analysis/tests/test_ilvis0_remainder_candidate_sources.py','analysis/tests/test_ilvis0_remainder_interface.py',
        'analysis/tests/test_ilvis0_remainder_controls.py','analysis/tests/test_ilvis0_remainder_report.py',
        'analysis/tests/test_ilvis0_conditional_remainder.py','analysis/tests/test_ilvis0_native_box_bounds.py'}
    parent=ROOT/'docs/ilvis0-recording-duration-controls'
    for name,digest in runner._load(parent/'evidence-receipt.json')['artifacts'].items():
        if runner._sha(runner.path_within(parent,name))!=digest:raise ValueError('qualified input publication changed')
    manifest=runner._load(parent/'manifest.json');environment=runner.runtime_environment()
    if not runner._load(parent/'summary.json')['passed'] or manifest['environment']!=environment:
        raise ValueError('passing duration controls in identical environment required')
    # Use the active study's unchanged source closure; do not write or merge it.
    original=runner.verify(ROOT/'data/ilvis0-long-staged-feasibility-v2-20261021')
    for name,digest in original['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('existing source changed: '+name)
            sources.add(name)
    settings=recipe();validate_recipe(settings);path=PUBLIC/'saved-inputs/recipe.json';runner._write(path,settings)
    inputs=dict(recipe=str(path.relative_to(ROOT)),prerequisite=str((parent/'evidence-receipt.json').relative_to(ROOT)))
    tasks=[];compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
    for item in manifest['tasks']:
        old=item['payload'];m=old['model'];p=old['profile'];record=manifest['inputs'][item['input_key']]
        source=parent/record['path']
        if runner._sha(source)!=record['sha256']:raise ValueError('duration input changed')
        full=runner._load(source);config=full['configuration']
        if len(full['dt'])!=96000 or config['limits'][25]!=1. or config['model']!=m or config['profile']!=p:
            raise ValueError('qualified generated input or broad clock changed')
        case={k:full[k] for k in ('configuration','center')}
        case.update({k:full[k][:800] for k in ('theta','dv','dt')})
        case['provenance']=dict(parent_sha256=record['sha256'],prefix_packets=800,bitwise_prefix=True,
            configuration_preserved=True,scope='generated software controls',original_reads=0)
        target=PUBLIC/f'saved-inputs/case-{m}-{int(p)}.json';runner._write(target,case)
        key=f'case-{m}-{int(p)}';inputs[key]=str(target.relative_to(ROOT))
        scale=[config['radius'],config['radius']*math.cos(config['initial_c'][0]),1.]
        for scope in ('physical','conditioned'):
            tasks.append(dict(identity=f'remainder-{m}-{int(p)}-{scope}',input_key='recipe',
                payload=dict(model=m,profile=p,scope=scope,case_key=key,compiler=compiler,
                    coordinate_scale=scale,limits=limits(scope)),
                limits=dict(native_calls=4,packet_visits=3200,bound_calls=2,bound_steps=14400)))
    if len(tasks)!=12:raise ValueError('twelve distinct fixed identities required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=1,threads=1,maximum_wall_s=4800,environment=environment)


def publish():
    spec=importlib.util.spec_from_file_location('_remainder_saved_report',ROOT/REPORT)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.publish()


def main():
    p=argparse.ArgumentParser(description=__doc__);group=p.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','package-only','check'):group.add_argument('--'+name,action='store_true')
    p.add_argument('--reserved-threads',type=int);args=p.parse_args()
    if args.prepare:prepare();print('Frozen 12 identities / 48 native queries / 24 bounds / one thread / 80 minutes.')
    elif args.run:
        if args.reserved_threads is None:p.error('--run requires --reserved-threads')
        outcome=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Conditional remainder: '+outcome['state'])
    elif args.package_only:publish();print('Published saved controls; no numerical work.')
    else:publication.check(DATA,PUBLIC);print('Verified saved conditional-remainder evidence.')


if __name__=='__main__':main()
