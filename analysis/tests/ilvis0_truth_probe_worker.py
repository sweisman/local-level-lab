# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and check ambiguity against the original perturbed observations."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-truth-probes-20261021';PUBLIC=ROOT/'docs/ilvis0-truth-probes'
PARENT=ROOT/'data/ilvis0-long-staged-feasibility-v2-20261021'
SOURCE='analysis/tests/ilvis0_truth_probe_worker.py';ADAPTER='analysis/lll/ilvis0_truth_probes.py'
HELPER='docs/ilvis0-long-staged-feasibility-v2/audit_linear_leverage.py'
PLAN='docs/ilvis0-truth-probes/PLAN.md'


def prepare():
    from lll.ilvis0_truth_probes import recipe,validate_recipe
    if DATA.exists():raise ValueError('actual-fixture diagnostic already frozen')
    manifest=runner.verify(PARENT);environment=runner.runtime_environment()
    leverage=runner.verify(ROOT/'data/ilvis0-linear-leverage-20261021')
    if (not runner.verify_completion(ROOT/'data/ilvis0-linear-leverage-20261021')['passed']
            or runner._sha(ROOT/HELPER)!=leverage['sources'][HELPER] or manifest['environment']!=environment):
        raise ValueError('qualified unchanged LP helper and original environment required')
    sources={SOURCE,ADAPTER,PLAN,HELPER,'analysis/tests/test_ilvis0_truth_probes.py',
        'analysis/tests/test_ilvis0_truth_publication.py','analysis/tests/ilvis0_control_shards.py',
        'analysis/tests/run_numerical.py','analysis/lll/ilvis0_density_native_probes.py',
        'analysis/lll/ilvis0_training_density.py','analysis/lll/ilvis0_ray_probes.py'}
    sources.update(name for name in manifest['sources'] if name.startswith('analysis/lll/'))
    settings=recipe();validate_recipe(settings);path=PUBLIC/'saved-inputs/recipe.json';runner._write(path,settings)
    inputs=dict(recipe=str(path.relative_to(ROOT)));tasks=[]
    for task in manifest['tasks'][:2]:
        if task['payload']['model']!=0:raise ValueError('fixed first two specified-field cases required')
        runner._validate_own_results(PARENT,manifest,task['shard'])
        identity=task['identity'];path=PARENT/'shards'/format(task['shard'],'03d')/'results'/(identity+'.json')
        envelope=runner._load(path)
        if not all(envelope['result'].get(k) is True for k in ('numerical_checks_passed','known_truth_retained','future_truth_contained')):
            raise ValueError('sealed valid original forward calculations required; width failure remains preserved')
        def artifact(name):
            path=PARENT/'artifacts'/identity/name;relative=str(path.relative_to(PARENT))
            if runner._sha(path)!=envelope['artifacts'][relative]:raise ValueError('sealed original artifact changed')
            return dict(path=str(path.relative_to(ROOT)),sha256=envelope['artifacts'][relative])
        original_case=manifest['inputs'][task['payload']['case_key']];case_path=PARENT/original_case['path']
        if runner._sha(case_path)!=original_case['sha256']:raise ValueError('original full-history input changed')
        bundle=dict(case=dict(path=str(case_path.relative_to(ROOT)),sha256=original_case['sha256']),
            observations=artifact('training-observations.json'),
            truth_records=[artifact('native-'+str(i).zfill(2)+'.json') for i in (1,2,3,4,5,12)])
        path=PUBLIC/f'saved-inputs/{identity}.json';runner._write(path,bundle)
        inputs[identity]=str(path.relative_to(ROOT))
        for sign in (-1,1):
            tasks.append(dict(identity=f'truth-probe-{int(task["payload"]["profile"])}-{sign}',input_key='recipe',
                payload=dict(bundle_key=identity,profile=task['payload']['profile'],sign=sign,
                    coordinate_scale=task['payload']['coordinate_scale'],compiler=task['payload']['compiler']),
                limits=dict(native_calls=3,packet_visits=1728000,bound_calls=0,bound_steps=0)))
    if len(tasks)!=4:raise ValueError('four fixed identities required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=1,threads=1,maximum_wall_s=600,environment=environment)


def render(manifest,summary,rows):
    from lll.ilvis0_ray_probes import sampled_span
    tasks=manifest['tasks'];ids=[t['identity'] for t in tasks]
    if (len(tasks)!=4 or len(set(ids))!=4 or summary['total']!=4 or summary['completed']!=len(rows)
            or not set(rows)<=set(ids) or {(t['payload']['profile'],t['payload']['sign']) for t in tasks}
            !={(p,s) for p in (False,True) for s in (-1,1)}):
        raise ValueError('complete declared four-task matrix required')
    required=dict(physical_parameter_count=27,training_epochs=5,native_evaluations=3,queried_epochs=18,
        all_points_saved_before_outcomes=True,original_observations_used=True,original_reads=0,optimizer_starts=0,
        nonlinear_coverage_qualified=False,observational_coverage_qualified=False)
    for row in rows.values():
        if row.get('passed'):
            if any(row.get(k)!=v for k,v in required.items()) or len(row.get('candidates',[]))!=3:
                raise ValueError('complete fixed candidate accounting required')
            if [c['scale_exact'] for c in row['candidates']]!=['1/50','1/20','1/10']:
                raise ValueError('all three predeclared scales required')
    complete=sum(bool(r.get('passed')) for r in rows.values())
    feasible=sum(c['nonlinear_training_feasible'] for r in rows.values() if r.get('passed') for c in r['candidates'])
    lines=['# Ambiguity under the original long-study observations','',
        f'**{complete}/4 numerical tasks complete; {feasible}/12 calibrations meet the actual training constraints.**','',
        'These cases use the original nonzero truth and stored perturbed observations, '
        'not the earlier zero-reference fixture. Every candidate is checked at all '
        'five original training times before its later displacement is interpreted.','',
        '| Processing | Feasible calibrations | Sampled N spread | Sampled E spread | Sampled height spread |',
        '|---|---:|---:|---:|---:|']
    for profile in (False,True):
        selected=[c for t in tasks if t['payload']['profile']==profile and t['identity'] in rows
            and rows[t['identity']].get('passed') for c in rows[t['identity']]['candidates']]
        span=sampled_span(selected);w=span['width_m'];label='Profiled removal' if profile else 'Zero removal'
        lines.append(f"| {label} | {span['feasible_points']}/6 | {w[0]:.3f} m | {w[1]:.3f} m | {w[2]:.3f} m |")
    lines+=['','Spreads include the known truth. They are sampled numerical separations, '
        'not outer uncertainty bounds. The original width targets remain 20/20/50 m. '
        'A small sampled spread does not establish those targets over the whole domain.','',
        '| Processing | North objective | Scale | Training maximum | Future N / E / height change | Feasible |',
        '|---|---|---:|---:|---|---|']
    for task in tasks:
        spec=task['payload'];row=rows.get(task['identity']);label='Profiled' if spec['profile'] else 'Zero'
        sign='Positive' if spec['sign']>0 else 'Negative'
        if row and row.get('passed'):
            for c in row['candidates']:
                future=' / '.join(f'{v:.3f}' for v in c['future_change_m'])+' m'
                lines.append(f"| {label} | {sign} | {c['scale_exact']} | {max(c['training_max_axis_m']):.3f} m | {future} | {'Yes' if c['nonlinear_training_feasible'] else 'No'} |")
        else:lines.append(f'| {label} | {sign} | — | Unavailable | Unavailable | Not complete |')
    lines+=['','All points are saved before new outcomes. LP feasibility is only a '
        'proposal check; the nonlinear predictions determine the reported training '
        'label. Every scale is retained, including failures. No candidate causes a '
        'retry, a changed limit or an update to the running study.','',
        'There are no new aircraft fits or original-data reads. These results do '
        'not establish native floating-point execution error, an aircraft error law, '
        'statistical significance or a change to the 53-stretch findings.','',
        '[Frozen limits](PLAN.md) · [Earlier zero-reference diagnostic](../ilvis0-ray-probes/INTERPRETATION.md) · '
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
    if args.prepare:prepare();print('Frozen four LP identities / twelve native batches / 600 seconds.')
    elif args.run:
        if args.reserved_threads is None:parser.error('explicit reserved allocation required')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Actual-fixture diagnostic: '+result['state'])
    elif args.package_only:publish();print('Published sealed actual-fixture evidence; no numerical work.')
    else:publication.check(DATA,PUBLIC);print('Verified actual-fixture evidence.')


if __name__=='__main__':main()
