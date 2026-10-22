# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish nonlinear tests of twelve fixed affine proposals."""
import argparse
from fractions import Fraction as F
import math
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-density-native-probes-20261021';PUBLIC=ROOT/'docs/ilvis0-density-native-probes'
PLAN='docs/ilvis0-density-native-probes/PLAN.md';SOURCE='analysis/tests/ilvis0_density_native_probe_worker.py'
ADAPTER='analysis/lll/ilvis0_density_native_probes.py'
HELPER='docs/ilvis0-long-staged-feasibility-v2/audit_linear_leverage.py'


def prepare():
    if DATA.exists():raise ValueError('fixed native-probe study already frozen')
    parent=ROOT/'data/ilvis0-training-density-20261021';published=ROOT/'docs/ilvis0-training-density'
    publication.check(parent,published);manifest=runner.verify(parent);summary=runner.verify_completion(parent)
    if summary['completed']!=6 or not summary['passed'] or manifest['environment']!=runner.runtime_environment():
        raise ValueError('complete passing density diagnostics in the same environment required')
    leverage=runner.verify(ROOT/'data/ilvis0-linear-leverage-20261021')
    if runner._sha(ROOT/HELPER)!=leverage['sources'][HELPER]:raise ValueError('qualified primal helper changed')
    sources={PLAN,SOURCE,ADAPTER,HELPER,'analysis/tests/test_ilvis0_density_native_probes.py',
        'analysis/tests/test_ilvis0_native_box_bounds.py','analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py'}
    for name,digest in manifest['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('frozen predecessor source changed: '+name)
            sources.add(name)
    inputs=dict(recipe=str((published/manifest['inputs']['recipe']['path']).relative_to(ROOT)),
        prerequisite='docs/ilvis0-training-density/evidence-receipt.json')
    compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0];tasks=[]
    for item in manifest['tasks']:
        spec=item['payload']
        if spec['model']!=0:continue
        profile=spec['profile'];key=f'case-{int(profile)}';baseline=f'baseline-{int(profile)}'
        record=manifest['inputs'][spec['case_key']];inputs[key]=str((published/record['path']).relative_to(ROOT))
        if runner._sha(ROOT/inputs[key])!=record['sha256']:raise ValueError('case pointer changed')
        path=published/'artifacts'/item['identity']/'native-batch.json'
        envelope=runner._load(parent/'shards'/f"{item['shard']:03d}"/'results'/(item['identity']+'.json'))
        if runner._sha(path)!=envelope['artifacts'][str(path.relative_to(published))]:
            raise ValueError('sealed zero-expansion baseline changed')
        inputs[baseline]=str(path.relative_to(ROOT))
        for axis in range(3):
            for sign in (-1,1):
                tasks.append(dict(identity=f'native-probe-{int(profile)}-{axis}-'+('minus' if sign<0 else 'plus'),
                    input_key='recipe',payload=dict(profile=profile,axis=axis,sign=sign,case_key=key,
                        baseline_key=baseline,coordinate_scale=spec['coordinate_scale'],compiler=compiler),
                    limits=dict(native_calls=1,packet_visits=28128000,bound_calls=0,bound_steps=0)))
    if len(tasks)!=12:raise ValueError('twelve distinct fixed native proposals required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=1,threads=1,maximum_wall_s=600,environment=runner.runtime_environment())


def render(manifest,summary,results):
    tasks=manifest['tasks'];ids=[t['identity'] for t in tasks]
    if (len(tasks)!=12 or len(set(ids))!=12 or not set(results)<=set(ids) or summary['completed']!=len(results)
            or summary['total']!=12 or {(t['payload']['profile'],t['payload']['axis'],t['payload']['sign']) for t in tasks}
            !={(p,a,s) for p in (False,True) for a in range(3) for s in (-1,1)}):
        raise ValueError('complete finite native proposal matrix required')
    expected=dict(affine_feasible=True,physical_parameter_count=27,training_epochs=292,queried_epochs=293,
        point_saved_before_native=True,native_evaluations=1,original_reads=0,optimizer_starts=0,
        future_used_for_training_gate=False,nonlinear_coverage_qualified=False)
    for task in tasks:
        row=results.get(task['identity'])
        if row is None or not row.get('passed'):continue
        if (any(row.get(k)!=v for k,v in expected.items())
                or row.get('work')!=dict(lp_proposals=1,exact_primal_checks=2,queried_epochs=293)):
            raise ValueError('passing native probe lacks its complete saved checks')
        for name in ('training_max_axis_m','future_change_m','linear_future_change_m'):
            values=row.get(name,[])
            if len(values)!=3 or any(not math.isfinite(v) for v in values):raise ValueError('finite complete axis metrics required')
        exact=row.get('training_max_axis_exact',[])
        if len(exact)!=3 or any(F(v)<0 for v in exact) or row.get('nonlinear_training_feasible')!=all(F(v)<=1 for v in exact):
            raise ValueError('nonlinear training label disagrees with exact comparison')
    passing=sum(bool(r.get('passed')) for r in results.values())
    feasible=sum(bool(r.get('passed') and r.get('nonlinear_training_feasible')) for r in results.values())
    lines=['# Do the large linear changes survive the full model?','',
        f'{passing}/12 numerical diagnostics pass; {feasible}/12 proposed calibrations satisfy nonlinear training constraints.',
        '', '| Processing | Target direction | Outcome | Largest training change | Later N / E / height change |',
        '|---|---|---|---:|---:|']
    for task in tasks:
        spec=task['payload'];row=results.get(task['identity']);direction=('N','E','height')[spec['axis']]+(' −' if spec['sign']<0 else ' +')
        if row and row.get('passed'):
            outcome='Training feasible' if row['nonlinear_training_feasible'] else 'Rejected by nonlinear training'
            train=f"{max(row['training_max_axis_m']):,.3f} m";later=' / '.join(f'{v:,.3f}' for v in row['future_change_m'])+' m'
        else:outcome='Not started' if row is None else 'Software/native failure';train=later='Unavailable'
        lines.append(f"| {'Profiled removal' if spec['profile'] else 'Zero removal'} | {direction} | {outcome} | {train} | {later} |")
    lines+=['', 'Every proposal was selected from saved Jacobians, checked exactly, contracted by the fixed '
        '0.99 factor and saved before the nonlinear outcome. The training check uses only the 292 earlier '
        'positions and the unchanged ±1 m allowance. The later displacement cannot decide that label.','',
        'This is a generated-data diagnostic around the saved zero-expansion reference, not an aircraft '
        'fit or the separate long-record run’s perturbed training data. Rejected sampled points do not '
        'prove unique prediction or permit removal of unexamined parameter regions. No uncertainty '
        'coverage, observation-error law or scientific significance is established.','',
        '[Frozen scope](PLAN.md) · [Training-density results](../ilvis0-training-density/INTERPRETATION.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md).']
    return '\n'.join(lines)


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);rows={}
    if runner._sha(Path(__file__))!=manifest['sources'][SOURCE]:raise ValueError('report source changed from freeze')
    for item in summary['results']:
        envelope=runner._load(DATA/item['artifact']);row=envelope['result'];rows[item['identity']]=row
        maximum=dict(lp_proposals=1,exact_primal_checks=2,queried_epochs=293);counts=dict.fromkeys(maximum,0)
        for name in sorted(n for n in envelope['artifacts'] if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);inc=event['increase']
            if any(k not in counts or type(v) is not int or v<1 for k,v in inc.items()):raise ValueError('invalid probe reservation')
            counts={k:v+inc.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>maximum[k] for k,v in counts.items()):raise ValueError('probe reservation changed')
        if row.get('passed') and counts!=maximum:raise ValueError('incomplete passing probe accounting')
    publication.publish(DATA,PUBLIC,render(manifest,summary,rows),plan=PLAN)


def main():
    p=argparse.ArgumentParser(description=__doc__);group=p.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','package-only','check'):group.add_argument('--'+name,action='store_true')
    p.add_argument('--reserved-threads',type=int);args=p.parse_args()
    if args.prepare:prepare();print('Frozen twelve proposals / twelve native batches / 600 seconds.')
    elif args.run:
        if args.reserved_threads is None:p.error('explicit reserved allocation required')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Native proposal checks: '+result['state'])
    elif args.package_only:publish();print('Rendered sealed native probes; no numerical work.')
    else:publication.check(DATA,PUBLIC);print('Verified native proposal evidence.')


if __name__=='__main__':main()
