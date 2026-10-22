# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish a finite residual-source derivative audit."""
import argparse
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-residual-source-curvature-20261021';PUBLIC=ROOT/'docs/ilvis0-residual-source-curvature'
SOURCE='analysis/tests/ilvis0_residual_source_curvature_worker.py';PLAN='docs/ilvis0-residual-source-curvature/PLAN.md'
ADAPTER='analysis/lll/ilvis0_residual_source_curvature.py'


def prepare():
    if DATA.exists():raise ValueError('residual-source audit already frozen')
    prior=ROOT/'data/ilvis0-probe-shared-map-audit-20261021';pub=ROOT/'docs/ilvis0-probe-shared-map-audit'
    publication.check(prior,pub);manifest=runner.verify(prior);summary=runner.verify_completion(prior)
    endpoint=ROOT/'data/ilvis0-endpoint-curvature-20261021'
    publication.check(endpoint,ROOT/'docs/ilvis0-endpoint-curvature')
    if summary['completed']!=2 or not summary['passed'] or manifest['environment']!=runner.runtime_environment():
        raise ValueError('complete shared-source audit in identical environment required')
    native=ROOT/'data/ilvis0-density-native-probes-20261021';npub=ROOT/'docs/ilvis0-density-native-probes'
    publication.check(native,npub);nm=runner.verify(native)
    sources={SOURCE,ADAPTER,PLAN,'analysis/tests/test_ilvis0_residual_source_curvature.py',
        'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py'}
    for name,digest in manifest['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('frozen source changed: '+name)
            sources.add(name)
    inputs={};tasks=[];indices=[0,8,28,178,288,292]
    for task in manifest['tasks']:
        profile=task['payload']['profile'];base=runner._load(prior/manifest['inputs'][task['input_key']]['path'])
        envelope=runner._load(prior/'shards'/f"{task['shard']:03d}"/'results'/(task['identity']+'.json'))
        points={}
        for ordinal in range(6):
            path=pub/'artifacts'/task['identity']/f'probe-{ordinal:02d}.json'
            if runner._sha(path)!=envelope['artifacts'][str(path.relative_to(pub))]:raise ValueError('shared probe changed')
            row=runner._load(path);points[row['identity']]=row
        probes=[];hashes=dict(base['input_sha256'])
        for item in base['probes']:
            nt=next(t for t in nm['tasks'] if t['identity']==item['identity'])
            native_envelope=runner._load(native/'shards'/f"{nt['shard']:03d}"/'results'/(nt['identity']+'.json'))
            path=npub/'artifacts'/item['identity']/'native-raw.json'
            if runner._sha(path)!=native_envelope['artifacts'][str(path.relative_to(npub))]:raise ValueError('native derivatives changed')
            record=runner._load(path);old=points[item['identity']]
            if record['status']!=0 or record['point']!=item['point'] or old['point']!=item['point']:
                raise ValueError('unchanged fixed successful point required')
            # Scale to the identical saved coordinate frame, without refitting.
            units=nt['payload']['coordinate_scale']
            jac=[[[float(v)*float(u) for v in row] for row,u in zip(record['jacobian'][i],units,strict=True)] for i in indices]
            probes.append(dict(item,source=old['source'],shared_error_m=old['shared_error_m'],native_jacobian_m=jac))
            hashes[str(path.relative_to(ROOT))]=runner._sha(path)
        bundle=dict(pointer=base['pointer'],reference=base['reference'],maps=base['maps'],probes=probes,input_sha256=hashes)
        path=PUBLIC/f'saved-inputs/case-{int(profile)}.json';runner._write(path,bundle);key=f'case-{int(profile)}'
        inputs[key]=str(path.relative_to(ROOT));tasks.append(dict(identity=f'residual-source-{int(profile)}',input_key=key,
            payload=dict(profile=profile),limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=1,threads=1,maximum_wall_s=120,environment=runner.runtime_environment())


def render(manifest,summary,results):
    tasks=manifest['tasks'];ids=[t['identity'] for t in tasks]
    if (len(tasks)!=2 or len(set(ids))!=2 or not set(results)<=set(ids) or summary['completed']!=len(results)
            or summary['total']!=2 or {t['payload']['profile'] for t in tasks}!={False,True}):
        raise ValueError('complete two-case residual-source diagnostic required')
    expected=dict(probes=6,epochs_per_probe=6,physical_parameter_count=27,source_parameter_count=24,
        native_evaluations=0,original_reads=0,optimizer_starts=0,conditioned_radii_transferred=False,
        numerical_coverage_qualified=False)
    maximum=dict(reference_setups=1,source_jacobian_oracles=7,reference_source_oracles=1,comparisons=6)
    for row in results.values():
        if not row.get('passed'):continue
        if any(row.get(k)!=v for k,v in expected.items()) or row.get('work')!=maximum:
            raise ValueError('passing result lacks complete non-coverage source accounting')
        for field in ('rms_anchored_error_m','rms_corrected_error_m','maximum_corrected_error_m'):
            if not math.isfinite(row.get(field,float('nan'))) or row[field]<0:raise ValueError('finite residual statistics required')
    lines=['# Curvature after the shared calibration terms','',
        f"{sum(bool(r.get('passed')) for r in results.values())}/2 saved-data diagnostics pass.",'',
        '| Processing | Shared-source RMS | With residual derivative correction | Probes improved |',
        '|---|---:|---:|---:|']
    for task in tasks:
        row=results.get(task['identity']);name='Profiled removal' if task['payload']['profile'] else 'Zero removal'
        if row and row.get('passed'):
            lines.append(f"| {name} | {row['rms_anchored_error_m']:.6f} m | {row['rms_corrected_error_m']:.6f} m | {row['probes_improved']}/6 |")
        else:lines.append(f'| {name} | Unavailable | Unavailable | Not complete |')
    lines+=['','All comparisons use the same twelve fixed generated points and six saved epochs. '
        'The correction applies to the error remaining after the 27 physical and 24 shared source '
        'terms, with the source explicitly reanchored at the reference. No point or coefficient is fitted.','',
        'This is **not a certified bound** or an aircraft confidence interval. Known probe derivatives '
        'diagnose the approximation; they are not supplied as unknown aircraft calibration. '
        'The software checks include a higher-order counterexample. No source maps are invented '
        'for other epochs and no old training-conditioned radii are transferred.','',
        'No new native integration, LP proposals or aircraft fitting is performed. Whole-period '
        'coverage, numerical/timing treatment and the aircraft observation-error law remain separate '
        'requirements before new withheld predictions.','',
        '[Frozen scope](PLAN.md) · [Earlier derivative diagnostic](../ilvis0-endpoint-curvature/INTERPRETATION.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md).']
    return '\n'.join(lines)


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);rows={}
    if runner._sha(Path(__file__))!=manifest['sources'][SOURCE]:raise ValueError('frozen report source changed')
    maximum=dict(reference_setups=1,source_jacobian_oracles=7,reference_source_oracles=1,comparisons=6)
    for item in summary['results']:
        envelope=runner._load(DATA/item['artifact']);row=envelope['result'];rows[item['identity']]=row
        counts=dict.fromkeys(maximum,0)
        for name in sorted(n for n in envelope['artifacts'] if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);inc=event['increase']
            if any(k not in counts or type(v) is not int or v<1 for k,v in inc.items()):raise ValueError('invalid source reservation')
            counts={k:v+inc.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>maximum[k] for k,v in counts.items()):raise ValueError('source work mismatch')
        if row.get('passed') and counts!=maximum:raise ValueError('incomplete passing source work')
    publication.publish(DATA,PUBLIC,render(manifest,summary,rows),plan=PLAN)


def main():
    p=argparse.ArgumentParser(description=__doc__);group=p.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','package-only','check'):group.add_argument('--'+name,action='store_true')
    p.add_argument('--reserved-threads',type=int);args=p.parse_args()
    if args.prepare:prepare();print('Frozen two residual-source audits / fourteen source Jacobians / zero native calls.')
    elif args.run:
        if args.reserved_threads is None:p.error('explicit reserved allocation required')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Residual source curvature: '+result['state'])
    elif args.package_only:publish();print('Rendered sealed source audit; no numerical evaluations.')
    else:publication.check(DATA,PUBLIC);print('Verified residual-source derivative evidence.')


if __name__=='__main__':main()
