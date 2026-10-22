# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite saved-only attribution using all 27+24 source-map columns."""
import argparse
from fractions import Fraction as F
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-probe-shared-map-audit-20261021';PUBLIC=ROOT/'docs/ilvis0-probe-shared-map-audit'
SOURCE='docs/ilvis0-probe-shared-map-audit/build_report.py';PLAN='docs/ilvis0-probe-shared-map-audit/PLAN.md'


def compare(maps,point,source,actual):
    import numpy as np
    matrix=np.asarray(maps,float);p=np.asarray(point,float);g=np.asarray(source,float)
    try:
        truth=[[F(v) if isinstance(v,str) else F(float(v)) for v in row] for row in actual]
        values=np.array(truth,float)
    except (ValueError,TypeError,OverflowError):raise ValueError('finite saved coordinate changes required') from None
    if (matrix.shape!=(6,3,51) or p.shape!=(27,) or g.shape!=(24,) or values.shape!=(6,3)
            or any(not np.all(np.isfinite(v)) for v in (matrix,p,g,values))):
        raise ValueError('complete finite six-epoch 27+24 source maps required')
    vector=list(map(F,map(float,np.r_[p,g])));linear=[];shared=[];blocks=[]
    for epoch,m in enumerate(matrix):
        le=[];se=[];contributions=[]
        for axis,row in enumerate(m):
            row=list(map(F,map(float,row)))
            pieces=[sum((a*b for a,b in zip(row[a0:a1],vector[a0:a1],strict=True)),F(0))
                for a0,a1 in ((0,27),(27,33),(33,42),(42,51))]
            le.append(float(truth[epoch][axis]-pieces[0]));se.append(float(truth[epoch][axis]-sum(pieces,F(0))))
            contributions.append(list(map(float,pieces[1:])))
        linear.append(le);shared.append(se);blocks.append(contributions)
    linear=np.array(linear);shared=np.array(shared)
    rms_linear=float(np.sqrt(np.mean(linear**2)));rms_shared=float(np.sqrt(np.mean(shared**2)))
    return dict(physical_parameter_count=27,source_parameter_count=24,epochs=6,
        maximum_linear_error_m=float(np.max(abs(linear))),maximum_shared_error_m=float(np.max(abs(shared))),
        rms_linear_error_m=rms_linear,rms_shared_error_m=rms_shared,
        rms_ratio=rms_shared/rms_linear if rms_linear else None,
        linear_error_m=linear.tolist(),shared_error_m=shared.tolist(),
        future_block_contributions_m=np.array(blocks[-1]).T.tolist(),conditioned_radii_transferred=False,
        numerical_coverage_qualified=False)


def evaluate(task,context):
    import numpy as np
    from lll.ilvis0_transform_native import make_reference
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_sharded_native import plain
    bundle=runner._load(context.input_path());pointer=bundle['pointer'];name=pointer['filename']
    if name!=Path(name).name:raise ValueError('qualified generated filename required')
    path=context.root.parents[1]/'docs/ilvis0-recording-duration-controls/inputs'/name
    if runner._sha(path)!=pointer['sha256']:raise ValueError('frozen input changed')
    case=runner._load(path);config=case['configuration'];events=0
    if len(case['dt'])!=96000 or config['model']!=0 or config['profile']!=task['payload']['profile']:
        raise ValueError('complete unchanged specified-field source required')
    maximum=dict(reference_setups=1,source_oracles=6,map_comparisons=6)
    def persist(record):
        nonlocal events
        runner._check_continue(context.root,context.manifest);events+=1
        context.save(f'reservation-{events:02d}.json',record)
    budget=Allowance(maximum,persist);budget.reserve(dict(reference_setups=1))
    reference=make_reference(config,case['theta'],case['dv'],case['dt'],lower=-np.ones(27),upper=np.ones(27),center=np.zeros(27))
    if plain(reference.report())!=bundle['reference']:raise ValueError('full source/reference/normalization changed')
    context.save('reference.json',plain(reference.report()));rows=[]
    for ordinal,probe in enumerate(bundle['probes']):
        budget.reserve(dict(source_oracles=1,map_comparisons=1));point=np.array(probe['point'])
        source=reference.normalized_values_at(point)
        result=compare(bundle['maps'],point,source,probe['actual_delta_m'])
        record=dict(identity=probe['identity'],point=probe['point'],source=source.tolist(),**result)
        context.save(f'probe-{ordinal:02d}.json',record);rows.append(record)
    if len(rows)!=6 or budget.counts!=maximum:raise ValueError('six fixed source checks per case required')
    context.save('accounting.json',budget.counts)
    return dict(identity=task['identity'],passed=True,profile=task['payload']['profile'],probes=6,
        source_parameter_count=24,physical_parameter_count=27,epochs_per_probe=6,work=budget.counts,
        maximum_linear_error_m=max(r['maximum_linear_error_m'] for r in rows),
        maximum_shared_error_m=max(r['maximum_shared_error_m'] for r in rows),
        rms_ratios=[r['rms_ratio'] for r in rows],probes_improved=sum(r['rms_shared_error_m']<r['rms_linear_error_m'] for r in rows),
        conditioned_radii_transferred=False,native_evaluations=0,original_reads=0,optimizer_starts=0,
        observational_coverage_qualified=False,scientific_decision='abstain')


def prepare():
    import numpy as np
    from lll.ilvis0_training_remainder_audit import scaled_design
    if DATA.exists():raise ValueError('shared-map audit already frozen')
    prior=ROOT/'data/ilvis0-density-native-probes-20261021';pub=ROOT/'docs/ilvis0-density-native-probes'
    publication.check(prior,pub);manifest=runner.verify(prior);summary=runner.verify_completion(prior)
    if summary['completed']!=12 or not summary['passed'] or manifest['environment']!=runner.runtime_environment():
        raise ValueError('complete native probes in unchanged environment required')
    original=ROOT/'data/ilvis0-long-staged-feasibility-v2-20261021';old=runner.verify(original)
    sources={SOURCE,PLAN,'analysis/tests/test_ilvis0_probe_shared_map_audit.py',
        'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py'}
    for name,digest in manifest['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('frozen source changed: '+name)
            sources.add(name)
    inputs={};tasks=[];times=[2.,10.,30.,180.,290.,438.];indices=[0,8,28,178,288,292]
    for profile in (False,True):
        selected=[t for t in manifest['tasks'] if t['payload']['profile']==profile];spec=selected[0]['payload']
        old_task=next(t for t in old['tasks'] if t['payload']['model']==0 and t['payload']['profile']==profile)
        runner._validate_own_results(original,old,old_task['shard'])
        old_identity=old_task['identity'];old_envelope=runner._load(original/'shards'/f"{old_task['shard']:03d}"/'results'/(old_identity+'.json'))
        baseline=runner._load(prior/manifest['inputs'][spec['baseline_key']]['path'])
        pointer=runner._load(prior/manifest['inputs'][spec['case_key']]['path']);hashes={};maps=[]
        if pointer['sha256']!=old['inputs'][old_task['payload']['case_key']]['sha256']:
            raise ValueError('generated source differs between saved studies')
        def old_record(name):
            path=original/'artifacts'/old_identity/name;relative=str(path.relative_to(original));digest=runner._sha(path)
            if old_envelope['artifacts'][relative]!=digest:raise ValueError('sealed old map changed')
            hashes[str(path.relative_to(ROOT))]=digest;return runner._load(path)
        reference=old_record('reference.json');units=spec['coordinate_scale']
        for ordinal,(time_s,index) in enumerate(zip(times,indices,strict=True),1):
            bound=old_record(f'training-bound-{ordinal:02d}.json' if ordinal<6 else 'future-bound.json')
            native=old_record(f'native-{ordinal+5:02d}.json')
            if (bound['time_s']!=time_s or native['time_s']!=time_s or native['point']!=[0.]*27
                    or bound['reference_binding']!=reference['binding']
                    or bound['shared_binding']!=reference['parent']['binding']
                    or bound['acceleration_binding']!=reference['acceleration']['binding']
                    or bound['transform_binding']!=reference['transform']['binding']
                    or not np.array_equal(native['prediction'],baseline['prediction'][index])
                    or not np.array_equal(native['jacobian'],baseline['jacobian'][index])):
                raise ValueError('source/reference/map normalization or zero-center native values changed')
            maps.append(scaled_design(native['jacobian'],bound,units))
        probes=[]
        for task in selected:
            path=prior/'shards'/f"{task['shard']:03d}"/'results'/(task['identity']+'.json');envelope=runner._load(path)
            records={}
            for name in ('fixed-point-before-native.json','native-raw.json'):
                p=prior/'artifacts'/task['identity']/name;relative=str(p.relative_to(prior));digest=runner._sha(p)
                if envelope['artifacts'][relative]!=digest:raise ValueError('sealed probe changed')
                hashes[str(p.relative_to(ROOT))]=digest;records[name]=runner._load(p)
            point=records['fixed-point-before-native.json']['point'];actual=records['native-raw.json']
            if actual['status']!=0 or actual['point']!=point:raise ValueError('unchanged successful fixed probe required')
            delta=[[(F(a)-F(b))*F(u) for a,b,u in zip(actual['prediction'][index],baseline['prediction'][index],units,strict=True)] for index in indices]
            probes.append(dict(identity=task['identity'],point=point,actual_delta_m=[list(map(str,row)) for row in delta]))
        bundle=dict(pointer=pointer,reference=reference,maps=maps,probes=probes,input_sha256=hashes,
            times_s=times,old_conditioned_radii_used=False)
        path=PUBLIC/f'saved-inputs/case-{int(profile)}.json';runner._write(path,bundle);key=f'case-{int(profile)}'
        inputs[key]=str(path.relative_to(ROOT));tasks.append(dict(identity=f'shared-map-{int(profile)}',input_key=key,
            payload=dict(profile=profile),limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=SOURCE,
        workers=1,threads=1,maximum_wall_s=120,environment=runner.runtime_environment())


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);rows=[]
    if runner._sha(Path(__file__))!=manifest['sources'][SOURCE]:raise ValueError('frozen report changed')
    for item in summary['results']:rows.append(runner._load(DATA/item['artifact'])['result'])
    lines=['# What the omitted shared source terms explain','',
        f"{sum(bool(r.get('passed')) for r in rows)}/2 saved-data audits pass.",'',
        '| Processing | Largest linear-only mismatch | Largest 51-column mismatch | Probes with smaller RMS mismatch |',
        '|---|---:|---:|---:|']
    for row in rows:
        if row.get('passed'):
            if (row['work']!=dict(reference_setups=1,source_oracles=6,map_comparisons=6)
                    or row['source_parameter_count']!=24 or row['conditioned_radii_transferred']):
                raise ValueError('complete source checks and non-transfer of radii required')
            lines.append('| '+('Profiled removal' if row['profile'] else 'Zero removal')+
                f" | {row['maximum_linear_error_m']:.3f} m | {row['maximum_shared_error_m']:.3f} m | {row['probes_improved']}/6 |")
        else:lines.append('| Audit failed | Unavailable | Unavailable | Unavailable |')
    lines+=['','All twelve fixed probes are compared at five earlier epochs and the later prediction. '
        'The complete expression retains 27 physical columns and 24 shared nonlinear source terms, '
        'with the original source/reference bindings and normalization. No point is fitted or adjusted.','',
        'These are residuals at saved generated points, not uncertainty bounds. The old '
        'training-conditioned radii are deliberately not transferred: these probes need not belong '
        'to that earlier training region. Improved sampled agreement cannot establish coverage of '
        'unexamined calibrations, an aircraft error law or scientific significance. No native '
        'integration, LP proposals or aircraft fitting is performed.','',
        '[Frozen scope](PLAN.md) · [Fixed-probe results](../ilvis0-density-native-probes/INTERPRETATION.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(lines),plan=PLAN)


def main():
    p=argparse.ArgumentParser(description=__doc__);group=p.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','package-only','check'):group.add_argument('--'+name,action='store_true')
    p.add_argument('--reserved-threads',type=int);args=p.parse_args()
    if args.prepare:prepare();print('Frozen two saved-map audits / twelve source oracles / zero native calls.')
    elif args.run:
        if args.reserved_threads is None:p.error('explicit reserved allocation required')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Shared-map audit: '+result['state'])
    elif args.package_only:publish();print('Rendered sealed map audit; no oracles or native work.')
    else:publication.check(DATA,PUBLIC);print('Verified saved shared-map audit.')


if __name__=='__main__':main()
