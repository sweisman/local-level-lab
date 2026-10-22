# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish a finite full-history linear training-density diagnostic."""
import argparse
import math
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-training-density-20261021';PUBLIC=ROOT/'docs/ilvis0-training-density'
PLAN='docs/ilvis0-training-density/PLAN.md';ADAPTER='analysis/lll/ilvis0_training_density.py'
SOURCE='analysis/tests/ilvis0_training_density_worker.py'


def prepare():
    from lll.ilvis0_training_density import recipe,validate_recipe
    if DATA.exists():raise ValueError('training-density diagnostic already frozen')
    previous=ROOT/'data/ilvis0-remainder-native-controls-20261021'
    publication.check(previous,ROOT/'docs/ilvis0-remainder-native-controls')
    qualified=runner.verify(previous);summary=runner.verify_completion(previous)
    if summary['completed']!=12 or not summary['passed']:
        raise ValueError('complete passing native remainder qualification required')
    parent=ROOT/'docs/ilvis0-recording-duration-controls';manifest=runner._load(parent/'manifest.json')
    if qualified['environment']!=runner.runtime_environment() or manifest['environment']!=runner.runtime_environment():
        raise ValueError('same frozen numerical environment required')
    for name,digest in runner._load(parent/'evidence-receipt.json')['artifacts'].items():
        if runner._sha(runner.path_within(parent,name))!=digest:raise ValueError('qualified duration evidence changed')
    sources={PLAN,SOURCE,ADAPTER,'analysis/tests/test_ilvis0_training_density.py',
        'analysis/tests/test_ilvis0_native_box_bounds.py','analysis/tests/ilvis0_control_shards.py',
        'analysis/tests/run_numerical.py'}
    for name,digest in qualified['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
            sources.add(name)
    settings=recipe();validate_recipe(settings);p=PUBLIC/'saved-inputs/recipe.json';runner._write(p,settings)
    inputs=dict(recipe=str(p.relative_to(ROOT)),prerequisite='docs/ilvis0-remainder-native-controls/evidence-receipt.json')
    tasks=[];compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
    for item in manifest['tasks']:
        model=item['payload']['model'];profile=item['payload']['profile'];record=manifest['inputs'][item['input_key']]
        path=parent/record['path']
        if path.parent!=parent/'inputs' or runner._sha(path)!=record['sha256']:
            raise ValueError('qualified generated input reference changed')
        case=runner._load(path);config=case['configuration']
        if len(case['dt'])!=96000 or config['model']!=model or config['profile']!=profile or config['limits'][25]!=1.:
            raise ValueError('unchanged full generated case required')
        pointer=dict(filename=path.name,sha256=record['sha256'],source=str(path.relative_to(ROOT)),
            input_reuse='existing immutable documented generated input; verified before reading')
        key=f'case-{model}-{int(profile)}';p=PUBLIC/f'saved-inputs/{key}.json';runner._write(p,pointer)
        inputs[key]=str(p.relative_to(ROOT));scale=[config['radius'],config['radius']*math.cos(config['initial_c'][0]),1.]
        tasks.append(dict(identity=f'density-{model}-{int(profile)}',input_key='recipe',
            payload=dict(model=model,profile=profile,case_key=key,coordinate_scale=scale,compiler=compiler),
            limits=dict(native_calls=2,packet_visits=28224000,bound_calls=0,bound_steps=0)))
    if len(tasks)!=6:raise ValueError('six distinct physical/processing cases required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=1,threads=1,maximum_wall_s=600,environment=runner.runtime_environment())


def render(manifest,summary,results):
    tasks=manifest['tasks'];ids=[t['identity'] for t in tasks]
    if (len(tasks)!=6 or len(set(ids))!=6 or not set(results)<=set(ids) or summary['completed']!=len(results)
            or summary['total']!=6 or {(t['payload']['model'],t['payload']['profile']) for t in tasks}
            !={(m,p) for m in range(3) for p in (False,True)}):
        raise ValueError('complete declared six-case density diagnostic required')
    required=dict(physical_parameter_count=27,dense_epochs=292,sparse_epochs=5,batch_endpoint_bitwise=True,
        native_evaluations=2,queried_epochs=294,original_reads=0,optimizer_starts=0,nonlinear_coverage_qualified=False)
    for row in results.values():
        if not row.get('passed'):continue
        if any(row.get(k)!=v for k,v in required.items()) or row.get('work')!=dict(queried_epochs=294,lp_proposals=12,exact_supports=36):
            raise ValueError('passing diagnostic lacks complete native/support evidence')
        for name in ('sparse_width_m','dense_width_m'):
            widths=row.get(name,[])
            if len(widths)!=3 or any(not math.isfinite(v) or v<0 for v in widths):raise ValueError('complete finite ranges required')
        if any(a>b for a,b in zip(row['dense_width_m'],row['sparse_width_m'])):
            raise ValueError('dense intersection widened sparse certified range')
    passed=sum(bool(r.get('passed')) for r in results.values())
    lines=['# More training positions: a generated-data diagnostic','',
        f"{passed}/6 software diagnostics pass; {summary['completed']}/6 completed.",'',
        '| Model | Processing | Five epochs: N / E / height | 292 epochs: N / E / height | Linear target met? |',
        '|---|---|---:|---:|---|']
    for task in tasks:
        spec=task['payload'];row=results.get(task['identity']);label=('Specified-field globe','Zero-field globe','Flat disc')[spec['model']]
        if row and row.get('passed'):
            before=' / '.join(f'{v:.3f}' for v in row['sparse_width_m'])+' m'
            after=' / '.join(f'{v:.3f}' for v in row['dense_width_m'])+' m';outcome='Yes' if row['linear_width_useful'] else 'No'
        else:before=after='Unavailable';outcome='Not complete' if row is None else 'Failed'
        lines.append(f"| {label} | {'Profiled removal' if spec['profile'] else 'Zero removal'} | {before} | {after} | {outcome} |")
    lines+=['','These are exactly checked outer bounds for the saved linearized prediction, **not nonlinear '
        'prediction ranges or aircraft confidence intervals**. All 27 physical columns and their original '
        'broad domain remain. Shared errors and nonlinear terms are omitted in this diagnostic.','',
        'The dense set includes every sparse training epoch. Native batch/endpoints agree exactly, and '
        'packet-boundary counters are preserved and checked. The target remains 20 / 20 / 50 m. '
        'A numerical pass and a useful linear width are different outcomes. Neither establishes useful '
        'full-history nonlinear bounds, an observation-error law or scientific significance.','',
        '[Fixed scope](PLAN.md) · [Earlier sparse-training diagnostic](../ilvis0-linear-leverage/INTERPRETATION.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md).']
    return '\n'.join(lines)


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);rows={}
    if runner._sha(Path(__file__))!=manifest['sources'][SOURCE]:raise ValueError('frozen report source changed')
    for item in summary['results']:
        envelope=runner._load(DATA/item['artifact']);row=envelope['result'];rows[item['identity']]=row
        maximum=dict(queried_epochs=294,lp_proposals=12,exact_supports=36);counts=dict.fromkeys(maximum,0)
        for name in sorted(n for n in envelope['artifacts'] if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);inc=event['increase']
            if any(k not in counts or type(v) is not int or v<1 for k,v in inc.items()):raise ValueError('invalid density reservation')
            counts={k:v+inc.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>maximum[k] for k,v in counts.items()):raise ValueError('density work mismatch')
        if row.get('passed') and counts!=maximum:raise ValueError('incomplete passing density accounting')
    publication.publish(DATA,PUBLIC,render(manifest,summary,rows),plan=PLAN)


def main():
    p=argparse.ArgumentParser(description=__doc__);group=p.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','package-only','check'):group.add_argument('--'+name,action='store_true')
    p.add_argument('--reserved-threads',type=int);args=p.parse_args()
    if args.prepare:prepare();print('Frozen six density diagnostics / 12 kernel calls / 72 LP proposals / 600 seconds.')
    elif args.run:
        if args.reserved_threads is None:p.error('explicit reserved threads required')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Training density: '+result['state'])
    elif args.package_only:publish();print('Rendered saved density results; no numerical work.')
    else:publication.check(DATA,PUBLIC);print('Verified density evidence.')


if __name__=='__main__':main()
