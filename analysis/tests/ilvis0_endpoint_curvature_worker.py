# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and render saved endpoint-derivative diagnostics without integration."""
import argparse
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-endpoint-curvature-20261021';PUBLIC=ROOT/'docs/ilvis0-endpoint-curvature'
SOURCE='analysis/tests/ilvis0_endpoint_curvature_worker.py';PLAN='docs/ilvis0-endpoint-curvature/PLAN.md'
ADAPTER='analysis/lll/ilvis0_endpoint_curvature.py'


def prepare():
    if DATA.exists():raise ValueError('endpoint curvature diagnostic already frozen')
    prior=ROOT/'data/ilvis0-probe-shared-map-audit-20261021';pub=ROOT/'docs/ilvis0-probe-shared-map-audit'
    publication.check(prior,pub);manifest=runner.verify(prior);summary=runner.verify_completion(prior)
    native=ROOT/'data/ilvis0-density-native-probes-20261021';native_pub=ROOT/'docs/ilvis0-density-native-probes'
    publication.check(native,native_pub);nm=runner.verify(native)
    if summary['completed']!=2 or not summary['passed'] or manifest['environment']!=runner.runtime_environment():
        raise ValueError('complete saved source audit in unchanged environment required')
    sources={SOURCE,ADAPTER,PLAN,'analysis/tests/test_ilvis0_endpoint_curvature.py',
        'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py'}
    for name,digest in manifest['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('frozen source changed: '+name)
            sources.add(name)
    inputs={};tasks=[]
    for task in manifest['tasks']:
        profile=task['payload']['profile'];identity=task['identity']
        envelope=runner._load(prior/'shards'/f"{task['shard']:03d}"/'results'/(identity+'.json'))
        shared={}
        for ordinal in range(6):
            path=pub/'artifacts'/identity/f'probe-{ordinal:02d}.json';relative=str(path.relative_to(pub))
            if runner._sha(path)!=envelope['artifacts'][relative]:raise ValueError('sealed shared-source comparison changed')
            record=runner._load(path);shared[record['identity']]=dict(path=str(path.relative_to(ROOT)),sha256=runner._sha(path))
        selected=[t for t in nm['tasks'] if t['payload']['profile']==profile]
        spec=selected[0]['payload'];base=nm['inputs'][spec['baseline_key']];path=native_pub/base['path']
        if runner._sha(path)!=base['sha256']:raise ValueError('sealed baseline changed')
        baseline=dict(path=str(path.relative_to(ROOT)),sha256=base['sha256']);probes=[]
        for nt in selected:
            path=native_pub/'artifacts'/nt['identity']/'native-raw.json'
            record=runner._load(native/'shards'/f"{nt['shard']:03d}"/'results'/(nt['identity']+'.json'))
            if runner._sha(path)!=record['artifacts'][str(path.relative_to(native_pub))]:raise ValueError('sealed native derivative changed')
            probes.append(dict(identity=nt['identity'],native=dict(path=str(path.relative_to(ROOT)),sha256=runner._sha(path)),
                shared=shared[nt['identity']]))
        bundle=dict(baseline=baseline,coordinate_scale=spec['coordinate_scale'],probes=probes)
        path=PUBLIC/f'saved-inputs/case-{int(profile)}.json';runner._write(path,bundle);key=f'case-{int(profile)}'
        inputs[key]=str(path.relative_to(ROOT));tasks.append(dict(identity=f'endpoint-curvature-{int(profile)}',
            input_key=key,payload=dict(profile=profile),limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=1,threads=1,maximum_wall_s=120,environment=runner.runtime_environment())


def render(manifest,summary,results):
    tasks=manifest['tasks'];ids=[t['identity'] for t in tasks]
    if (len(tasks)!=2 or len(set(ids))!=2 or not set(results)<=set(ids) or summary['completed']!=len(results)
            or summary['total']!=2 or {t['payload']['profile'] for t in tasks}!={False,True}):
        raise ValueError('complete two-case saved derivative matrix required')
    required=dict(physical_parameter_count=27,probes=6,epochs_per_probe=293,shared_comparison_epochs=6,
        native_evaluations=0,optimizer_starts=0,original_reads=0,numerical_coverage_qualified=False)
    for row in results.values():
        if not row.get('passed'):continue
        if (any(row.get(k)!=v for k,v in required.items())
                or row.get('work')!=dict(comparisons=6,source_crosschecks=6,coordinate_comparisons=5274,column_products=284796)):
            raise ValueError('complete non-coverage derivative checks required')
        for field in ('common_rms_linear_m','common_rms_shared_m','common_rms_endpoint_m','maximum_endpoint_error_m'):
            if not math.isfinite(row.get(field,float('nan'))) or row[field]<0:raise ValueError('finite residual metrics required')
    lines=['# What the saved endpoint derivatives explain','',
        f"{sum(bool(r.get('passed')) for r in results.values())}/2 saved-data diagnostics pass.",'',
        '| Processing | Linear RMS | Shared-source RMS | Endpoint-average RMS | Endpoint improves shared |',
        '|---|---:|---:|---:|---:|']
    for task in tasks:
        row=results.get(task['identity']);label='Profiled removal' if task['payload']['profile'] else 'Zero removal'
        if row and row.get('passed'):
            lines.append(f"| {label} | {row['common_rms_linear_m']:.6f} m | {row['common_rms_shared_m']:.6f} m | "
                f"{row['common_rms_endpoint_m']:.6f} m | {row['endpoint_improves_shared']}/6 |")
        else:lines.append(f'| {label} | Unavailable | Unavailable | Unavailable | Not complete |')
    lines+=['','The table compares the same six saved epochs for all three expressions. Reference and '
        'endpoint-derivative expressions are additionally checked at every one of the 293 epochs. '
        'No shared maps are invented for missing epochs. All 27 physical derivative columns remain.','',
        'The endpoint average approximates a derivative line integral. It is **not a curvature bound** '
        'or a prediction uncertainty interval. Its exactness for quadratic examples does not extend '
        'to arbitrary nonlinear motion; the software checks include a cubic counterexample. '
        'The derivatives at the known generated probes are available here, but are not supplied '
        'as unknown aircraft calibration information.','',
        'Grouped terms describe this directional curvature expression, not unique physical causes. '
        'No coefficients or points are fitted or adjusted, and no new native integration, LP '
        'proposals, source oracles or aircraft fits are performed. All earlier evidence and '
        'whole-period/error-law requirements remain unchanged.','',
        '[Frozen scope](PLAN.md) · [Shared-source diagnostic](../ilvis0-probe-shared-map-audit/INTERPRETATION.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md).']
    return '\n'.join(lines)


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);rows={}
    if runner._sha(Path(__file__))!=manifest['sources'][SOURCE]:raise ValueError('frozen report source changed')
    for item in summary['results']:
        envelope=runner._load(DATA/item['artifact']);row=envelope['result'];rows[item['identity']]=row
        maximum=dict(comparisons=6,source_crosschecks=6,coordinate_comparisons=5274,column_products=284796)
        counts=dict.fromkeys(maximum,0)
        for name in sorted(n for n in envelope['artifacts'] if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);inc=event['increase']
            if any(k not in counts or type(v) is not int or v<1 for k,v in inc.items()):raise ValueError('invalid endpoint reservation')
            counts={k:v+inc.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>maximum[k] for k,v in counts.items()):raise ValueError('endpoint work mismatch')
        if row.get('passed') and counts!=maximum:raise ValueError('incomplete passing endpoint accounting')
    publication.publish(DATA,PUBLIC,render(manifest,summary,rows),plan=PLAN)


def main():
    p=argparse.ArgumentParser(description=__doc__);group=p.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','package-only','check'):group.add_argument('--'+name,action='store_true')
    p.add_argument('--reserved-threads',type=int);args=p.parse_args()
    if args.prepare:prepare();print('Frozen twelve saved derivative comparisons / zero native calls / 120 seconds.')
    elif args.run:
        if args.reserved_threads is None:p.error('explicit reserved allocation required')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Endpoint curvature: '+result['state'])
    elif args.package_only:publish();print('Rendered sealed derivative results; no numerical evaluations.')
    else:publication.check(DATA,PUBLIC);print('Verified endpoint derivative evidence.')


if __name__=='__main__':main()
