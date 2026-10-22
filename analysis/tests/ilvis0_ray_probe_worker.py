# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and check twelve training-selected nonlinear ray proposals."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-ray-probes-20261021';PUBLIC=ROOT/'docs/ilvis0-ray-probes'
SOURCE='analysis/tests/ilvis0_ray_probe_worker.py';ADAPTER='analysis/lll/ilvis0_ray_probes.py'
PLAN='docs/ilvis0-ray-probes/PLAN.md'


def prepare():
    from lll.ilvis0_ray_probes import recipe,validate_recipe
    if DATA.exists():raise ValueError('ray diagnostic already frozen')
    prior=ROOT/'data/ilvis0-density-native-probes-20261021';pub=ROOT/'docs/ilvis0-density-native-probes'
    publication.check(prior,pub);manifest=runner.verify(prior);summary=runner.verify_completion(prior)
    environment=runner.runtime_environment()
    if not summary['passed'] or summary['completed']!=12 or manifest['environment']!=environment:
        raise ValueError('complete original nonlinear probes in unchanged environment required')
    sources={SOURCE,ADAPTER,PLAN,'analysis/tests/test_ilvis0_ray_probes.py',
        'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py'}
    for name,digest in manifest['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('prior source changed: '+name)
            sources.add(name)
    settings=recipe();validate_recipe(settings);path=PUBLIC/'saved-inputs/recipe.json';runner._write(path,settings)
    inputs=dict(recipe=str(path.relative_to(ROOT)),prerequisite=str((pub/'evidence-receipt.json').relative_to(ROOT)))
    tasks=[]
    for task in manifest['tasks']:
        spec=task['payload'];identity=task['identity'];bundle={}
        envelope=runner._load(prior/'shards'/f"{task['shard']:03d}"/'results'/(identity+'.json'))
        if not envelope['result']['passed']:raise ValueError('complete sealed original probe required')
        for key,filename in (('native','native-raw.json'),('point','fixed-point-before-native.json')):
            path=pub/'artifacts'/identity/filename;relative=str(path.relative_to(pub))
            if runner._sha(path)!=envelope['artifacts'][relative]:raise ValueError('sealed prior artifact changed')
            bundle[key]=dict(path=str(path.relative_to(ROOT)),sha256=runner._sha(path))
        for key,old in (('baseline','baseline_key'),('case_pointer','case_key')):
            record=manifest['inputs'][spec[old]];path=pub/record['path']
            if runner._sha(path)!=record['sha256']:raise ValueError('original input pointer changed')
            bundle[key]=dict(path=str(path.relative_to(ROOT)),sha256=record['sha256'])
        path=PUBLIC/f'saved-inputs/{identity}.json';runner._write(path,bundle)
        inputs[identity]=str(path.relative_to(ROOT))
        tasks.append(dict(identity='ray-'+identity,input_key='recipe',payload=dict(bundle_key=identity,
            profile=spec['profile'],axis=spec['axis'],sign=spec['sign'],compiler=spec['compiler'],
            coordinate_scale=spec['coordinate_scale']),limits=dict(native_calls=1,packet_visits=28128000,
                bound_calls=0,bound_steps=0)))
    if (len(tasks)!=12 or {(t['payload']['profile'],t['payload']['axis'],t['payload']['sign']) for t in tasks}
            !={(p,a,s) for p in (False,True) for a in range(3) for s in (-1,1)}):
        raise ValueError('all twelve fixed original rays required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=1,threads=1,maximum_wall_s=600,environment=environment)


def render(manifest,summary,rows):
    from lll.ilvis0_ray_probes import sampled_span
    tasks=manifest['tasks'];ids=[t['identity'] for t in tasks]
    if (len(tasks)!=12 or len(set(ids))!=12 or summary['total']!=12 or summary['completed']!=len(rows)
            or not set(rows)<=set(ids)):
        raise ValueError('complete declared twelve-ray matrix required')
    required=dict(physical_parameter_count=27,native_evaluations=1,training_epochs=292,queried_epochs=293,
        point_saved_before_native=True,original_reads=0,optimizer_starts=0,nonlinear_coverage_qualified=False,
        observational_coverage_qualified=False)
    for row in rows.values():
        if row.get('passed') and any(row.get(k)!=v for k,v in required.items()):
            raise ValueError('complete passing ray accounting required')
    complete=sum(bool(r.get('passed')) for r in rows.values())
    feasible=sum(bool(r.get('passed') and r['nonlinear_training_feasible']) for r in rows.values())
    lines=['# Can training-compatible calibrations predict different later positions?','',
        f'**{complete}/12 numerical checks complete; {feasible}/12 proposed points satisfy nonlinear training.**','',
        '| Processing | Feasible points | Sampled N spread | Sampled E spread | Sampled height spread |',
        '|---|---:|---:|---:|---:|']
    for profile in (False,True):
        selected=[rows[t['identity']] for t in tasks if t['payload']['profile']==profile and t['identity'] in rows]
        span=sampled_span(selected);w=span['width_m'];label='Profiled removal' if profile else 'Zero removal'
        lines.append(f"| {label} | {span['feasible_points']}/6 | {w[0]:.3f} m | {w[1]:.3f} m | {w[2]:.3f} m |")
    lines+=['','These are spreads between sampled feasible numerical trajectories and the '
        'zero reference, **not outer uncertainty bounds**. The original width targets are '
        '20 m north, 20 m east and 50 m height. A small sampled spread does not prove '
        'those targets achievable over the entire parameter domain.','',
        '| Processing | Ray | Actual training maximum | Future N / E / height change | Feasible |',
        '|---|---|---:|---|---|']
    for task in tasks:
        spec=task['payload'];row=rows.get(task['identity']);label='Profiled' if spec['profile'] else 'Zero'
        axis=('N','E','height')[spec['axis']]+(' +' if spec['sign']>0 else ' −')
        if row and row.get('passed'):
            changes=' / '.join(f'{v:.3f}' for v in row['future_change_m'])+' m'
            lines.append(f"| {label} | {axis} | {max(row['training_max_axis_m']):.3f} m | {changes} | {'Yes' if row['nonlinear_training_feasible'] else 'No'} |")
        else:lines.append(f'| {label} | {axis} | Unavailable | Unavailable | Not complete |')
    lines+=['','Each point is chosen from earlier saved training quantities, frozen before '
        'one new full-model query, and checked against the unchanged ±1-metre training '
        'allowance. The quadratic proposal heuristic cannot establish feasibility; only '
        'the reported nonlinear check determines that label. Every original direction '
        'is retained; no new outcome causes a retry.','',
        'These generated zero-reference cases are separate from the active long-record '
        'study with perturbed training observations. They do not establish aircraft '
        'uncertainty, native execution-error bounds, scientific significance or a change '
        'to the 53-stretch findings.','',
        '[Frozen scope](PLAN.md) · [Original nonlinear probes](../ilvis0-density-native-probes/README.md) · '
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
    if args.prepare:prepare();print('Frozen twelve rays / twelve full native batches / 600 seconds.')
    elif args.run:
        if args.reserved_threads is None:parser.error('explicit reserved allocation required')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Ray diagnostic: '+result['state'])
    elif args.package_only:publish();print('Rendered sealed ray results; no numerical work.')
    else:publication.check(DATA,PUBLIC);print('Verified nonlinear ray evidence.')


if __name__=='__main__':main()
