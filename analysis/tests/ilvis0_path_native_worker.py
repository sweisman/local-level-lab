# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze, execute and publish six finite one-packet adapter controls."""
import argparse
import math
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-path-native-controls-20261021';PUBLIC=ROOT/'docs/ilvis0-path-native-controls'
SOURCE='analysis/tests/ilvis0_path_native_worker.py';ADAPTER='analysis/lll/ilvis0_path_native_controls.py'
PLAN='docs/ilvis0-path-native-controls/PLAN.md'


def prepare():
    from lll.ilvis0_path_native_controls import recipe,validate_recipe
    if DATA.exists():raise ValueError('one-packet adapter study already frozen')
    parent=ROOT/'data/ilvis0-remainder-native-controls-20261021'
    pub=ROOT/'docs/ilvis0-remainder-native-controls'
    publication.check(parent,pub);manifest=runner.verify(parent);summary=runner.verify_completion(parent)
    environment=runner.runtime_environment()
    if not summary['passed'] or summary['completed']!=12 or manifest['environment']!=environment:
        raise ValueError('passing prefix controls in identical environment required')
    sources={SOURCE,ADAPTER,PLAN,'analysis/tests/test_ilvis0_path_native_controls.py',
        'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py',
        'analysis/lll/ilvis0_training_density.py'}
    for name,digest in manifest['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
            sources.add(name)
    for name in ('path_jets','path_geometry','path_motion','path_packets','calibration_path','piecewise_trapezoid'):
        sources.update((f'analysis/lll/ilvis0_{name}.py',f'analysis/tests/test_ilvis0_{name}.py'))
    settings=recipe();validate_recipe(settings)
    path=PUBLIC/'saved-inputs/recipe.json';runner._write(path,settings)
    inputs=dict(recipe=str(path.relative_to(ROOT)),prerequisite=str((pub/'evidence-receipt.json').relative_to(ROOT)))
    tasks=[];compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
    for item in manifest['tasks']:
        payload=item['payload']
        if payload['scope']!='physical':continue
        old=manifest['inputs'][payload['case_key']];original=pub/old['path']
        if runner._sha(original)!=old['sha256']:raise ValueError('qualified prefix input changed')
        prior=runner._load(original);config=prior['configuration'];model=payload['model'];profile=payload['profile']
        if len(prior['dt'])!=800 or config['model']!=model or config['profile']!=profile:
            raise ValueError('qualified prefix/model required')
        case={k:prior[k] for k in ('configuration','center')}
        case.update({k:prior[k][:1] for k in ('theta','dv','dt')})
        case['provenance']=dict(parent_sha256=old['sha256'],first_packet_bitwise=True,
            full_configuration_preserved=True,scope='generated adapter controls',original_reads=0)
        key=f'case-{model}-{int(profile)}';target=PUBLIC/f'saved-inputs/{key}.json';runner._write(target,case)
        inputs[key]=str(target.relative_to(ROOT));scale=[config['radius'],config['radius']*math.cos(config['initial_c'][0]),1.]
        tasks.append(dict(identity=f'path-native-{model}-{int(profile)}',input_key='recipe',
            payload=dict(case_key=key,model=model,profile=profile,compiler=compiler,coordinate_scale=scale),
            limits=dict(native_calls=1,packet_visits=1,bound_calls=27,bound_steps=27)))
    if len(tasks)!=6:raise ValueError('six distinct physical/processing identities required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=1,threads=1,maximum_wall_s=1200,environment=environment)


def render(manifest,summary,rows):
    tasks=manifest['tasks'];ids=[t['identity'] for t in tasks]
    if (len(tasks)!=6 or len(set(ids))!=6 or summary['total']!=6 or summary['completed']!=len(rows)
            or not set(rows)<=set(ids) or {(t['payload']['model'],t['payload']['profile']) for t in tasks}
            !={(m,p) for m in range(3) for p in (False,True)}):
        raise ValueError('complete six-case declared matrix required')
    for row in rows.values():
        if row.get('passed'):
            required=dict(physical_columns=27,native_evaluations=1,interval_packet_steps=27,
                original_reads=0,optimizer_starts=0,position_checks=81,derivative_checks=81,
                whole_history_qualified=False,observational_coverage_qualified=False,higher_order_native_reference=False)
            if any(row.get(k)!=v for k,v in required.items()):raise ValueError('complete passing accounting required')
            for key in ('maximum_position_gap_m','maximum_derivative_gap_m'):
                if not math.isfinite(row.get(key,float('nan'))) or not 0<=row[key]<=1e-6:
                    raise ValueError('fixed finite comparison tolerance required')
    passed=sum(bool(r.get('passed')) for r in rows.values())
    lines=['# Native packet adapter comparison','',f'**{passed}/6 generated controls pass.**','',
        '| Model | Processing | Result | Position gap | First-derivative gap |',
        '|---|---|---|---:|---:|']
    labels={0:'Globe + field',1:'Globe, zero field',2:'Flat disc'}
    for task in tasks:
        spec=task['payload'];row=rows.get(task['identity']);label='Profiled removal' if spec['profile'] else 'Zero removal'
        if row and row.get('passed'):
            lines.append(f"| {labels[spec['model']]} | {label} | Pass | {row['maximum_position_gap_m']:.3g} m | {row['maximum_derivative_gap_m']:.3g} m |")
        else:lines.append(f"| {labels[spec['model']]} | {label} | {'Failed' if row else 'Not complete'} | — | — |")
    lines+=['','Each case checks the same generated first packet and all 27 physical '
        'parameter directions. The one-micrometre tolerance compares software values and '
        'first derivatives, not sensor accuracy. No aircraft fits or original recordings are read.','',
        'The first-order native reference does not independently verify second or third '
        'derivatives; those retain separate known-answer checks. These controls do not '
        'qualify full-history prediction ranges, complete clock/rotation branches, native '
        'execution-error bounds or an observational error law.','',
        '[Frozen limits](PLAN.md) · [Trajectory components](../ilvis0-path-motion/README.md) · '
        '[Remaining prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md).']
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
    if args.prepare:prepare();print('Frozen six cases / six native queries / 162 interval steps / 20 minutes.')
    elif args.run:
        if args.reserved_threads is None:parser.error('explicit reserved allocation required')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Packet adapter: '+result['state'])
    elif args.package_only:publish();print('Published sealed packet-adapter evidence; no evaluations.')
    else:publication.check(DATA,PUBLIC);print('Verified packet-adapter evidence.')


if __name__=='__main__':main()
