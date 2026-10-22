# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze, execute and publish four one-step generated ambiguity repairs."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-training-repair-20261021';PUBLIC=ROOT/'docs/ilvis0-training-repair'
PARENT=ROOT/'data/ilvis0-truth-probes-20261021'
SOURCE='analysis/tests/ilvis0_training_repair_worker.py';ADAPTER='analysis/lll/ilvis0_training_repair.py'
PLAN='docs/ilvis0-training-repair/PLAN.md'


def prepare():
    from lll.ilvis0_training_repair import recipe,validate_recipe
    if DATA.exists():raise ValueError('repair diagnostic already frozen')
    publication.check(PARENT,ROOT/'docs/ilvis0-truth-probes')
    manifest=runner.verify(PARENT);summary=runner.verify_completion(PARENT);environment=runner.runtime_environment()
    if not summary['passed'] or summary['completed']!=4 or manifest['environment']!=environment:
        raise ValueError('complete original probes in identical environment required')
    sources={SOURCE,ADAPTER,PLAN,'analysis/tests/test_ilvis0_training_repair.py',
        'analysis/tests/test_ilvis0_training_repair_publication.py','analysis/tests/ilvis0_control_shards.py',
        'analysis/tests/run_numerical.py'}
    for name,digest in manifest['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
            sources.add(name)
    settings=recipe();validate_recipe(settings);path=PUBLIC/'saved-inputs/recipe.json';runner._write(path,settings)
    inputs=dict(recipe=str(path.relative_to(ROOT)));tasks=[]
    results={r['identity']:r for r in summary['results']}
    for task in manifest['tasks']:
        spec=task['payload'];identity=task['identity'];envelope=runner._load(PARENT/results[identity]['artifact'])
        if not envelope['result']['passed']:raise ValueError('complete fixed seed required')
        def artifact(name):
            path=PARENT/'artifacts'/identity/name;key=str(path.relative_to(PARENT))
            if runner._sha(path)!=envelope['artifacts'][key]:raise ValueError('sealed seed changed')
            return dict(path=str(path.relative_to(ROOT)),sha256=envelope['artifacts'][key])
        seed=artifact('native-02.json');points=runner._load(ROOT/artifact('all-points-before-native.json')['path'])
        raw=runner._load(ROOT/seed['path'])
        if points['points'][2]['scale_exact']!='1/10' or points['points'][2]['point']!=raw['point']:
            raise ValueError('preselected original scale1/10 seed required')
        original=manifest['inputs'][spec['bundle_key']];path=PARENT/original['path']
        if runner._sha(path)!=original['sha256']:raise ValueError('original bundle changed')
        pointer=dict(original_bundle=dict(path=str(path.relative_to(ROOT)),sha256=original['sha256']),seed=seed)
        target=PUBLIC/f'saved-inputs/{identity}.json';runner._write(target,pointer)
        inputs[identity]=str(target.relative_to(ROOT))
        tasks.append(dict(identity=f'repair-{int(spec["profile"])}-{spec["sign"]}',input_key='recipe',
            payload=dict(bundle_key=identity,profile=spec['profile'],sign=spec['sign'],
                coordinate_scale=spec['coordinate_scale'],compiler=spec['compiler']),
            limits=dict(native_calls=1,packet_visits=576000,bound_calls=0,bound_steps=0)))
    if len(tasks)!=4:raise ValueError('four fixed generated seeds required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=1,threads=1,maximum_wall_s=600,environment=environment)


def render(manifest,summary,rows):
    from lll.ilvis0_ray_probes import sampled_span
    tasks=manifest['tasks'];ids=[t['identity'] for t in tasks]
    if (len(tasks)!=4 or len(set(ids))!=4 or summary['total']!=4 or summary['completed']!=len(rows)
            or not set(rows)<=set(ids) or {(t['payload']['profile'],t['payload']['sign']) for t in tasks}
            !={(p,s) for p in (False,True) for s in (-1,1)}):
        raise ValueError('complete declared four-case matrix required')
    for row in rows.values():
        if row.get('passed'):
            required=dict(physical_parameter_count=27,linear_solves=1,original_observations_used=True,
                future_observations_used=False,future_prediction_constraint_used=True,
                original_reads=0,optimizer_starts=0,nonlinear_coverage_qualified=False,
                observational_coverage_qualified=False)
            if any(row.get(k)!=v for k,v in required.items()):raise ValueError('complete diagnostic accounting required')
            if type(row.get('proposal_valid')) is not bool or row.get('native_evaluations')!=int(row['proposal_valid']):
                raise ValueError('one native evaluation per valid proposal required')
            if row['proposal_valid'] and not isinstance(row.get('candidate'),dict):raise ValueError('nonlinear result required')
    done=sum(bool(r.get('passed')) for r in rows.values())
    lines=['# One-step check of training-compatible alternatives','',f'**{done}/4 numerical diagnostics complete.**','',
        'These generated probes preserve the original five noisy training observations '
        'and physical bounds. One linear repair is proposed per preselected seed. '
        'Only the subsequent nonlinear training check establishes feasibility.','',
        '| Processing | Feasible new points | Sampled N spread | Sampled E spread | Sampled height spread |',
        '|---|---:|---:|---:|---:|']
    for profile in (False,True):
        candidates=[r['candidate'] for r in rows.values() if r.get('passed') and r.get('proposal_valid')
            and r['profile']==profile];span=sampled_span(candidates);w=span['width_m']
        lines.append(f"| {'Profiled removal' if profile else 'Zero removal'} | {span['feasible_points']}/2 | {w[0]:.3f} m | {w[1]:.3f} m | {w[2]:.3f} m |")
    lines+=['','Spreads include the original truth. These are sampled separations, not '
        'outer bounds. The original 20/20/50 m width targets are unchanged.','',
        'The proposal deliberately constrains its computed future north prediction '
        'to remain near the seed. It uses no future observation. This is a '
        'counterexample search, not an unbiased held-out prediction test.','',
        'All failures are preserved. There are no iterated repairs, new aircraft '
        'fits or changes to existing studies. No statistical confidence level or '
        'aircraft error law is established.','',
        '[Frozen limits](PLAN.md) · [Original probes](../ilvis0-truth-probes/INTERPRETATION.md) · '
        '[Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md).']
    return '\n'.join(lines)


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);rows={}
    if runner._sha(Path(__file__))!=manifest['sources'][SOURCE]:raise ValueError('frozen report changed')
    for item in summary['results']:
        envelope=runner._load(DATA/item['artifact']);rows[item['identity']]=envelope['result']
    publication.publish(DATA,PUBLIC,render(manifest,summary,rows),plan=PLAN)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','package-only','check'):group.add_argument('--'+name,action='store_true')
    parser.add_argument('--reserved-threads',type=int);args=parser.parse_args()
    if args.prepare:prepare();print('Frozen four one-step repairs / four native batches / 600 seconds.')
    elif args.run:
        if args.reserved_threads is None:parser.error('explicit reserved allocation required')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Training repair: '+result['state'])
    elif args.package_only:publish();print('Published sealed repair evidence; no numerical work.')
    else:publication.check(DATA,PUBLIC);print('Verified training-repair evidence.')


if __name__=='__main__':main()
