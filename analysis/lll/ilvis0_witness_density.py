# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed-point training-cadence diagnostics; no new optimizer or observations."""
from fractions import Fraction as F
from lll.ilvis0_witness_search import check_reference


def recipe():
    return dict(times_s=list(map(float,range(2,291)))+[438.],training_s=list(map(float,range(2,291))),
        sparse_s=[2.,10.,30.,180.,290.],future_s=438.,packets=96000,identities=18,
        maximum_native_batches=18,maximum_packet_visits=501120000,maximum_identity_seconds=120.,
        training_allowance_m=1.,numerical_guard_m=1e-5,future_observations_used=False,
        observations_created=0,original_reads=0,optimizer_starts=0,observational_coverage_qualified=False)


def validate_recipe(value):
    if value!=recipe():raise ValueError('fixed density diagnostic and finite allowance required')


def interval_overlap(values,times,scale,*,allowance_m,guard_m):
    """Do bounded position predictions admit a shared coordinate-box observation?"""
    import math
    if (len(values)!=3 or not times or any(len(v)!=len(times) for v in values)
            or any(len(row)!=3 for v in values for row in v) or len(scale)!=3
            or any(not math.isfinite(x) for v in values for row in v for x in row)
            or any(not math.isfinite(x) or x<=0 for x in scale)
            or not 0<=guard_m<allowance_m or not math.isfinite(allowance_m)
            or any(not math.isfinite(t) for t in times) or any(b<=a for a,b in zip(times,times[1:]))):
        raise ValueError('complete finite three-point predictions and positive coordinate bounds required')
    allowance=F(allowance_m);guard=F(guard_m);axes=[]
    for j in range(3):
        spans=[(max(F(v[i][j]) for v in values)-min(F(v[i][j]) for v in values))*F(scale[j])
            for i in range(len(times))]
        optimistic=[2*(allowance+guard)-span for span in spans]
        guaranteed=[2*(allowance-guard)-span for span in spans]
        bad=[i for i,width in enumerate(optimistic) if width<0]
        axes.append(dict(could_share_all=not bad,guaranteed_overlap_all=min(guaranteed)>=0,
            disjoint_epochs=len(bad),first_disjoint_s=times[bad[0]] if bad else None,
            maximum_span_exact=str(max(spans)),minimum_optimistic_width_exact=str(min(optimistic)),
            minimum_guaranteed_width_exact=str(min(guaranteed)),
            worst_epoch_s=times[min(range(len(times)),key=guaranteed.__getitem__)]))
    return dict(could_share_all=all(a['could_share_all'] for a in axes),
        guaranteed_overlap_all=all(a['guaranteed_overlap_all'] for a in axes),axes=axes,
        observations_created=0,outer_bound_qualified=False,numerical_guard_qualified=False,
        observational_coverage_qualified=False)


def assess(rows):
    expected={(m,p,r) for m in range(3) for p in (False,True) for r in ('origin','low','high')}
    actual={(r['model'],r['profile'],r['role']) for r in rows}
    if len(actual)!=len(rows) or not actual<=expected:raise ValueError('distinct original density identities required')
    return dict(complete=actual==expected and all(r['passed'] for r in rows),
        completed=len(rows),expected=18,observational_coverage_qualified=False)


def prepare(root,identity='ilvis0-witness-density-20261022'):
    from pathlib import Path
    from lll.ilvis0_witness_publication import inspect_first_steps
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import safe_path,encoded,atomic,digest
    from lll.studies.dependencies import source_closure
    from lll.studies.runtime import Definition
    root=Path(root).resolve();prefix='data/ilvis0-feasible-step-controls-20261022'
    previous=inspect_first_steps(root,prefix)
    if not previous['controls']['assessment']['qualified']:
        raise ValueError('close and qualify first-step controls before density diagnosis')
    base=safe_path(root,'data/ilvis0-source-point-development/density-witness-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh finite study required')
    adapter='analysis/lll/ilvis0_witness_density.py'
    sources=source_closure(root,[adapter,'analysis/lll/ilvis0_tangent.cpp',
        'analysis/tests/test_ilvis0_witness_density.py','analysis/tests/test_ilvis0_witness_search.py',
        'analysis/tests/test_ilvis0_truth_probes.py','analysis/tests/test_ilvis0_native_box_bounds.py',
        'docs/ilvis0-witness-density/PLAN.md'])
    study=ClosedStudy(root,prefix);inputs={};tasks=[]
    def save(key,value,raw=False):
        path=base/(key+'.json');atomic(path,value if raw else encoded(value))
        inputs[key]=path.relative_to(root).as_posix()
    try:
        base.mkdir(parents=True);save('recipe',recipe())
        for case in previous['cases']:
            m=case['model'];p=case['profile'];name=f'{m}-{int(p)}'
            task=next(t for t in study.tasks.values() if (t['payload']['model'],t['payload']['profile'])==(m,p))
            spec=task['payload'];bundle=study.input(spec['bundle_key']);raw=study.input(spec['case_key'],raw=True)
            if digest(raw)!=case['problem']['binding']['case_sha256']:raise ValueError('unchanged source case required')
            save('case-'+name,raw,raw=True);save('bundle-'+name,bundle)
            pair=case['spread']['axes'][0]['pair']
            for role,point_id in zip(('origin','low','high'),['origin']+pair,strict=True):
                key='point-'+name+'-'+role
                save(key,dict(record=case['points'][point_id],source_identity=point_id,
                    source_study=prefix,source_manifest_sha256=study.completion['manifest_sha256']))
                tasks.append(dict(identity='dense-'+name+'-'+role,input_key='recipe',
                    payload=dict(model=m,profile=p,role=role,compiler=spec['compiler'],
                        case_key='case-'+name,bundle_key='bundle-'+name,point_key=key),
                    limits=dict(native_calls=1,packet_visits=290*96000,bound_calls=0,bound_steps=0)))
        definition=dict(id=identity,adapter=adapter,sources=sources,inputs=inputs,tasks=tasks,
            workers=4,threads=1,maximum_wall_s=600.)
        atomic(base/'definition.json',encoded(definition));manifest=Definition.from_dict(definition,root).prepare(root)
        return dict(path='data/'+identity,identities=len(tasks),sources=len(manifest['sources']),
            limits=manifest['limits'],allocation=manifest['allocation'])
    finally:study.close()


def evaluate(task,context):
    from lll.ilvis0_control_shards import _load
    from lll.ilvis0_witness_search import evaluate_fixed
    validate_recipe(_load(context.input_path()));return evaluate_fixed(task,context)


def inspect(root,prefix):
    from pathlib import Path
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import digest
    study=ClosedStudy(root,prefix);rows=[];outputs={};cases=[]
    try:
        settings=study.input('recipe');validate_recipe(settings)
        for function in (interval_overlap,check_reference):
            path=Path(function.__code__.co_filename).resolve();name=path.relative_to(study.root).as_posix()
            if digest(path.read_bytes())!=study.manifest['sources'][name]:raise ValueError('frozen audit source changed')
        for identity,task in study.tasks.items():
            spec=task['payload'];row=study.rows.get(identity);base={k:spec[k] for k in ('model','profile','role')}
            if row is None:continue
            env=study.envelope(identity);result=env['result']
            for name,sha in env['artifacts'].items():study.read(name,sha,raw=True)
            rows.append(dict(base,passed=result['passed'],identity=identity))
            if not result['passed']:continue
            if any(result[k]!=v for k,v in base.items()):raise ValueError('density identity changed')
            bundle=study.input(spec['bundle_key']);source=study.input(spec['point_key'])['record']
            native=study.artifact(identity,'native-output.json');kernel=study.artifact(identity,'kernel.json')
            before=study.artifact(identity,'point-before-native.json')
            if (native['status']!=0 or native['classification']['counter_verified'] is not True
                    or native['point']!=source['point'] or before!=dict(point=source['point'],saved_before_native=True)
                    or bundle['problem']['binding']['case_sha256']!=study.manifest['inputs'][spec['case_key']]['sha256']
                    or kernel['source_sha256']!=study.manifest['sources']['analysis/lll/ilvis0_tangent.cpp']
                    or kernel['compiler']!=spec['compiler']):raise ValueError('density source or fixed point differs')
            check_reference(source,native,settings['times_s'])
            outputs[spec['model'],spec['profile'],spec['role']]=native['prediction']
        for m in range(3):
            for p in (False,True):
                keys=[(m,p,r) for r in ('origin','low','high')]
                if not all(k in outputs for k in keys):
                    cases.append(dict(model=m,profile=p,complete=False));continue
                spec=next(t['payload'] for t in study.tasks.values()
                    if (t['payload']['model'],t['payload']['profile'])==(m,p))
                bundle=study.input(spec['bundle_key']);scale=bundle['problem']['coordinate_scale']
                overlap=interval_overlap([outputs[k][:-1] for k in keys],settings['training_s'],scale,
                    allowance_m=settings['training_allowance_m'],guard_m=settings['numerical_guard_m'])
                cases.append(dict(model=m,profile=p,complete=True,overlap=overlap))
        return dict(assessment=assess(rows),cases=cases,rows=rows,manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],numerical_work=0,
            observational_coverage_qualified=False,source_study='data/ilvis0-feasible-step-controls-20261022')
    finally:study.close()


def render(report):
    names=['Globe + field','Globe, zero field','Stationary disc']
    text=['# Do more frequent earlier positions exclude the accepted alternatives?','',
        'This generated-data diagnostic reevaluates 18 existing calibrations without fitting them. '
        'It adds prediction times at one-second spacing from 2 to 290 seconds. No receiver observations are invented.',
        '',f"**{report['assessment']['completed']}/18 fixed predictions completed.** All passing records preserve "
        'the original sparse epoch values exactly.',
        '', '| Model | Processing case | Shared observation possible at every sampled training epoch? | '
        'Minimum north overlap (m) | Minimum east overlap (m) | Minimum height overlap (m) |',
        '|---|---|---|---:|---:|---:|']
    for c in report['cases']:
        if c['complete']:
            overlap=c['overlap'];answer='Yes' if overlap['could_share_all'] else 'No'
            values=[f"{float(F(a['minimum_optimistic_width_exact'])):.4f}" for a in overlap['axes']]
        else:answer='Incomplete';values=['—']*3
        text.append('| '+' | '.join([names[c['model']],'Profiled removal' if c['profile'] else 'Zero removal',answer]+values)+' |')
    text+=['', 'The original calibration and both accepted north-extreme alternatives each receive '
        'a ±1 m coordinate interval, expanded by the declared 0.00001 m numerical guard. '
        'A negative overlap means no common coordinate could satisfy all three at that epoch, even with '
        'that extra guard. Nonnegative overlap leaves their coexistence possible; it does not predict '
        'the noise an actual receiver would produce.',
        '', 'This tests only these fixed alternatives at sampled times. It is not a new outer prediction '
        'bound, a continuous-time guarantee, an aircraft error law or an Earth-model comparison. '
        '**V01 remains unqualified.** The 53-stretch findings are unchanged.',
        '', '[Frozen method and limits](PLAN.md) · [Accepted alternatives](../ilvis0-feasible-step-controls/INTERPRETATION.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md)']
    return '\n'.join(text)+'\n'


def publish(root,prefix,output='docs/ilvis0-witness-density'):
    from pathlib import Path
    import json
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic,encoded,digest,safe_path
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('publication already sealed')
    report=inspect(root,prefix);package(data,public,render(report),plan='docs/ilvis0-witness-density/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_text());name='artifacts/publication/comparison.json'
    raw=encoded(report);atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,numerical_work=0)
