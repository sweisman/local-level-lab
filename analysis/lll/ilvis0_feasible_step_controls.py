# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed-radius generated native controls for checked feasible proposals."""
from fractions import Fraction as F


def recipe():
    from lll.ilvis0_feasible_steps import policy
    return dict(radii=[.001,.0005,.00025],identities=36,maximum_native_batches=36,
        maximum_lp_calls=72,maximum_exact_checks=288,maximum_candidate_audits=36,packets=96000,
        maximum_identity_seconds=120.,policy=policy(),future_observations_used=False,
        original_reads=0,observational_coverage_qualified=False)


def validate_recipe(value):
    if value!=recipe():raise ValueError('fixed first-step qualification matrix required')


def audit_saved_probe(problem,origin,proposal,*,sign,radius,native=None):
    """Recompute the primal and nonlinear acceptance from represented saved values."""
    from lll.ilvis0_feasible_steps import audit_step,policy
    from lll.ilvis0_truth_probes import audit_pair
    if type(sign) is not int or sign not in (-1,1):raise ValueError('fixed signed direction required')
    settings=policy()
    if (type(proposal['lp_calls']) is not int or not 0<=proposal['lp_calls']<=2
            or type(proposal['exact_checks']) is not int or not 0<=proposal['exact_checks']<=8):
        raise ValueError('saved proposal exceeds advance reservation')
    audit_pair(problem,origin,origin)
    linear=audit_step(problem,origin,proposal['point'],radius=radius)
    predicted=sign*F(linear.get('linear_north_change_exact','0'))
    if (proposal['audit']['admissible']!=linear['admissible']
            or F(proposal['linear_north_change_exact'])!=F(linear.get('linear_north_change_exact','0'))):
        raise ValueError('saved affine proposal differs from exact reconstruction')
    eligible=(proposal['lp_success'] is True and linear['admissible']
        and predicted>F(settings['minimum_progress_m']))
    if not eligible:
        if native is not None:raise ValueError('native evaluation of rejected proposal')
        return dict(usable=False,native_evaluations=0,linear=linear)
    if native is None:raise ValueError('eligible proposal requires its saved native output')
    if (native['status']!=0 or native['point']!=proposal['point']
            or native['classification']['counter_verified'] is not True):
        raise ValueError('successful matching native probe required')
    record=dict(binding=problem['binding'],times_s=problem['training_s']+[problem['future_s']],
        point=native['point'],prediction=native['prediction'],status=0)
    actual_audit=audit_pair(problem,record,record);margin=F(actual_audit['training_margin_exact'][0])
    actual=sign*(F(record['prediction'][-1][0])-F(origin['prediction'][-1][0]))*F(problem['coordinate_scale'][0])
    ratio=actual/predicted
    usable=(all(actual_audit['training_feasible']) and margin>=F(settings['advance_margin_m'])
        and actual>F(settings['minimum_progress_m']) and ratio>=F(settings['minimum_ratio']))
    return dict(usable=usable,native_evaluations=1,linear=linear,audit=actual_audit,
        predicted_change_exact=str(predicted),actual_change_exact=str(actual),ratio_exact=str(ratio),
        training_margin_exact=str(margin))


def assess(rows):
    expected={(m,p,s,r) for m in range(3) for p in (False,True) for s in (-1,1) for r in recipe()['radii']}
    actual={(row['model'],row['profile'],row['sign'],row['radius']) for row in rows}
    if len(actual)!=len(rows) or not actual<=expected:raise ValueError('duplicate or unknown qualification identity')
    cases=[]
    for m in range(3):
        for p in (False,True):
            for s in (-1,1):
                usable=[row['radius'] for row in rows if (row['model'],row['profile'],row['sign'])==(m,p,s)
                    and row['passed'] and row['usable']]
                cases.append(dict(model=m,profile=p,sign=s,usable_radius=max(usable) if usable else None))
    complete=actual==expected and all(row['passed'] for row in rows)
    return dict(qualified=complete and all(c['usable_radius'] is not None for c in cases),
        complete_checks=complete,covered_directions=sum(c['usable_radius'] is not None for c in cases),cases=cases)


def source_inputs(root):
    from lll.ilvis0_witness_search import closed_cases
    from lll.studies.closed import ClosedStudy
    records=closed_cases(root,'data/ilvis0-long-staged-feasibility-v2-20261021')
    parent=ClosedStudy(root,'data/ilvis0-nonlinear-witnesses-20261022')
    try:
        matrix={(t['payload']['model'],t['payload']['profile'],t['payload']['sign']):t for t in parent.tasks.values()}
        if len(matrix)!=12 or len(parent.rows)!=12 or not all(r['passed'] for r in parent.rows.values()):
            raise ValueError('twelve closed source searches required')
        for record in records:
            m=record['model'];p=record['profile'];raw=[]
            for s in (-1,1):
                task=matrix[m,p,s];spec=task['payload'];bundle=parent.input(spec['bundle_key'])
                if (bundle!=record['bundle'] or spec['compiler']!=record['compiler']
                        or parent.manifest['inputs'][spec['case_key']]['sha256']!=bundle['problem']['binding']['case_sha256']):
                    raise ValueError('unchanged source problem and compiler required')
                parent.envelope(task['identity'])
                output=parent.artifact(task['identity'],'native-001.json')['output']
                if output['status']!=0 or not output['classification']['counter_verified']:
                    raise ValueError('verified source native batch required')
                raw.append(output)
            if any(raw[0][key]!=raw[1][key] for key in ('point','prediction','jacobian')):
                raise ValueError('paired source batches disagree')
            original=record['bundle']['initial_records']
            if (raw[0]['point']!=record['bundle']['initial']
                    or raw[0]['prediction'][:5]!=[v['prediction'] for v in original]
                    or raw[0]['jacobian'][:5]!=[v['jacobian'] for v in original]):
                raise ValueError('original single/batched source values differ')
            problem=record['bundle']['problem']
            record['bundle']['origin']=dict(binding=problem['binding'],point=raw[0]['point'],
                prediction=raw[0]['prediction'],jacobian=raw[0]['jacobian'],status=0,
                times_s=problem['training_s']+[problem['future_s']])
        return records
    finally:parent.close()


def positive_controls(root,records):
    from lll.studies.closed import ClosedStudy
    from lll.ilvis0_truth_probes import audit_pair
    study=ClosedStudy(root,'data/ilvis0-truth-probes-20261021');cases={r['profile']:r for r in records if r['model']==0}
    checked=[];futures={False:[],True:[]}
    try:
        if len(study.tasks)!=4 or len(study.rows)!=4:raise ValueError('four closed original probe identities required')
        for task in study.tasks.values():
            spec=task['payload'];base=cases[spec['profile']];problem=base['bundle']['problem']
            pointers=study.input(spec['bundle_key']);envelope=study.envelope(task['identity'])
            if (pointers['case']['sha256']!=problem['binding']['case_sha256']
                    or pointers['observations']['sha256']!=base['bundle']['provenance']['training_artifact_sha256']
                    or spec['coordinate_scale']!=problem['coordinate_scale'] or spec['compiler']!=base['compiler']
                    or study.manifest['sources']['analysis/lll/ilvis0_tangent.cpp']!=problem['binding']['source_sha256']):
                raise ValueError('positive control uses a different original problem')
            no_guard=dict(problem,numerical_error_m=[0.]*3)
            truth=[study.reference(ref) for ref in pointers['truth_records']]
            baseline=dict(binding=problem['binding'],point=truth[0]['point'],status=0,
                times_s=problem['training_s']+[problem['future_s']],prediction=[v['prediction'] for v in truth])
            if not all(audit_pair(no_guard,baseline,baseline)['training_feasible']):
                raise ValueError('known initial witness fails original training')
            futures[spec['profile']].append(baseline['prediction'][-1])
            points=study.artifact(task['identity'],'all-points-before-native.json')['points']
            for i in range(3):
                raw=study.artifact(task['identity'],f'native-{i:02d}.json')
                boundary=study.artifact(task['identity'],f'boundary-{i:02d}.json')
                previous=study.artifact(task['identity'],f'comparison-{i:02d}.json')
                if raw['status']!=0 or not boundary['counter_verified'] or raw['point']!=points[i]['point']:
                    raise ValueError('original positive-control native identity changed')
                witness=dict(binding=problem['binding'],times_s=baseline['times_s'],point=raw['point'],
                    prediction=raw['prediction'],status=0)
                original=audit_pair(no_guard,witness,witness)['training_feasible'][0]
                guarded=audit_pair(problem,witness,witness)['training_feasible'][0]
                if original!=previous['nonlinear_training_feasible']:
                    raise ValueError('saved original acceptance label differs from exact reconstruction')
                checked.append(dict(identity=task['identity'],ordinal=i,accepted=original,guarded=guarded))
                if original:futures[spec['profile']].append(raw['prediction'][-1])
        if len(checked)!=12 or sum(r['accepted'] for r in checked)!=6:
            raise ValueError('all twelve original controls, including six rejections, required')
        spreads={}
        for p,values in futures.items():
            scale=cases[p]['bundle']['problem']['coordinate_scale']
            spreads[str(int(p))]=[str((max(F(v[j]) for v in values)-min(F(v[j]) for v in values))*F(scale[j]))
                for j in range(3)]
        return dict(checked=checked,accepted=6,rejected=6,spreads_exact_m=spreads,
            source=study.prefix,manifest_sha256=study.completion['manifest_sha256'],native_calls=0,
            native_source_sha256=study.manifest['sources']['analysis/lll/ilvis0_tangent.cpp'])
    finally:study.close()


def evaluate(task,context):
    import time
    import numpy as np
    from lll import ilvis0_control_shards as runner
    from lll.ilvis0_witness_search import validate_bundle
    from lll.ilvis0_feasible_steps import propose_step
    from lll.ilvis0_truth_probes import audit_pair
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_density_native_probes import query
    from lll.ilvis0_sharded_native import plain
    started=time.monotonic();settings=runner._load(context.input_path());validate_recipe(settings)
    spec=task['payload'];bundle=runner._load(context.input_path(spec['bundle_key']))
    path=context.input_path(spec['case_key']);case=runner._load(path)
    expected=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp']
    if (bundle['problem']['binding']['case_sha256']!=context.manifest['inputs'][spec['case_key']]['sha256']
            or runner._sha(path)!=bundle['problem']['binding']['case_sha256']
            or bundle['problem']['binding']['source_sha256']!=expected):
        raise ValueError('original source case changed')
    problem=validate_bundle(bundle,case,spec);origin=bundle['origin']
    if spec['radius'] not in settings['radii'] or origin['point']!=bundle['initial']:
        raise ValueError('fixed radius and original source point required')
    positive=runner._load(context.input_path('positive-controls'))
    if (positive['accepted']!=6 or positive['rejected']!=6 or len(positive['checked'])!=12
            or positive['native_source_sha256']!=expected):
        raise ValueError('original accepted and rejected controls must be preserved')
    reservations=0
    def check():
        runner._check_continue(context.root,context.manifest)
        if time.monotonic()-started>=settings['maximum_identity_seconds']:
            raise runner.BudgetStopped('fixed first-step clock allowance exhausted')
    def reserve():
        nonlocal reservations
        check()
        if reservations:raise ValueError('one proposal reservation per probe required')
        reservations+=1
        context.save('proposal-reservation.json',dict(lp_calls=2,exact_checks=8))
    proposal=propose_step(problem,origin,sign=spec['sign'],radius=spec['radius'],reserve=reserve)
    context.save('proposal.json',plain(proposal))
    if reservations!=1 or proposal['lp_calls']>2 or proposal['exact_checks']>8:
        raise ValueError('first-step work exceeded advance reservation')
    base=dict(identity=task['identity'],model=spec['model'],profile=spec['profile'],sign=spec['sign'],
        radius=spec['radius'],passed=True,usable=False,native_evaluations=0,
        lp_calls=proposal['lp_calls'],exact_checks=proposal['exact_checks'],physical_parameter_count=27,
        original_reads=0,future_observations_used=False,observational_coverage_qualified=False,
        numerical_error_bound_qualified=False,scientific_decision='abstain')
    predicted=spec['sign']*F(proposal['linear_north_change_exact'])
    if (not proposal['lp_success'] or not proposal['audit']['admissible']
            or predicted<=F(settings['policy']['minimum_progress_m'])):
        return dict(base,reason='no checked improving affine proposal')
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';directory.mkdir(parents=True,exist_ok=True)
    kernel,metadata=load_tangent(directory)
    if metadata['source_sha256']!=expected or metadata['compiler']!=spec['compiler']:
        raise ValueError('frozen native compiler or source changed')
    context.save('kernel.json',metadata)
    config={k:np.ascontiguousarray(v,float) if k in ('initial_c','initial_v','initial_r','limits') else v
        for k,v in case['configuration'].items()}
    theta,dv,dt=(np.ascontiguousarray(case[k],float) for k in ('theta','dv','dt'))
    times=problem['training_s']+[problem['future_s']];check()
    context.charge(native_calls=1,packet_visits=len(times)*len(dt))
    context.save('point-before-native.json',dict(point=proposal['point'],saved_before_native=True))
    def verify_work(count,visits):
        if count!=6 or visits!=6*settings['packets']:raise ValueError('native work differs from reservation')
    native=query(kernel,config,theta,dv,dt,times,proposal['point'],verify_work,
        lambda raw:context.save('native-raw.json',plain(raw)))
    context.save('native-output.json',plain(native))
    if native['status']!=0 or not native['classification']['counter_verified']:
        raise ValueError('successful classified native probe required')
    record=dict(binding=problem['binding'],times_s=times,point=proposal['point'],
        prediction=native['prediction'].tolist(),status=0)
    audit=audit_pair(problem,record,record);margin=F(audit['training_margin_exact'][0])
    actual=spec['sign']*(F(record['prediction'][-1][0])-F(origin['prediction'][-1][0]))*F(problem['coordinate_scale'][0])
    ratio=actual/predicted
    usable=(all(audit['training_feasible']) and margin>=F(settings['policy']['advance_margin_m'])
        and actual>F(settings['policy']['minimum_progress_m']) and ratio>=F(settings['policy']['minimum_ratio']))
    context.save('candidate-audit.json',dict(record=record,audit=audit,predicted_change_exact=str(predicted),
        actual_change_exact=str(actual),ratio_exact=str(ratio),usable=usable))
    return dict(base,usable=usable,native_evaluations=1,actual_north_change_m=float(actual),
        predicted_north_change_m=float(predicted),ratio_exact=str(ratio),training_margin_exact=str(margin),
        reason='controlled step usable' if usable else 'native step rejected by fixed trust rules')


def probe_tasks(records):
    tasks=[]
    for record in records:
        model=record['model'];profile=record['profile'];name=f'{model}-{int(profile)}'
        for sign in (-1,1):
            for index,radius in enumerate(recipe()['radii']):
                direction='negative' if sign<0 else 'positive'
                tasks.append(dict(identity=f'step-{name}-{direction}-{index}',input_key='recipe',
                    limits=dict(native_calls=1,packet_visits=6*96000,bound_calls=0,bound_steps=0),
                    payload=dict(model=model,profile=profile,sign=sign,radius=radius,compiler=record['compiler'],
                        case_key='case-'+name,bundle_key='bundle-'+name)))
    return tasks


def prepare(root,identity='ilvis0-feasible-step-controls-20261022'):
    from pathlib import Path
    from lll.ilvis0_receipt_journal import encoded,durable_write
    from lll.studies.artifacts import safe_path,digest
    from lll.studies.dependencies import source_closure
    from lll.studies.runtime import Definition
    root=Path(root).resolve();records=source_inputs(root);positive=positive_controls(root,records)
    adapter='analysis/lll/ilvis0_feasible_step_controls.py'
    sources=source_closure(root,[adapter,'analysis/lll/ilvis0_tangent.cpp',
        'analysis/tests/test_ilvis0_feasible_step_controls.py','analysis/tests/test_ilvis0_feasible_steps.py',
        'analysis/tests/test_ilvis0_witness_search.py','analysis/tests/test_ilvis0_truth_probes.py',
        'analysis/tests/test_ilvis0_native_box_bounds.py','analysis/tests/test_study_closed.py',
        'docs/ilvis0-feasible-step-controls/PLAN.md'])
    expected=records[0]['bundle']['problem']['binding']['source_sha256']
    if digest((root/'analysis/lll/ilvis0_tangent.cpp').read_bytes())!=expected:
        raise ValueError('unchanged native source required')
    base=safe_path(root,'data/ilvis0-source-point-development/feasible-step-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():
        raise ValueError('fresh input directory and study identity required')
    base.mkdir(parents=True);inputs={};tasks=probe_tasks(records)
    def save(key,value,raw=False):
        path=base/(key+'.json');durable_write(path,value if raw else encoded(value))
        inputs[key]=path.relative_to(root).as_posix()
    save('recipe',recipe());save('positive-controls',positive)
    for record in records:
        model=record['model'];profile=record['profile'];name=f'{model}-{int(profile)}'
        save('case-'+name,record['case_bytes'],raw=True);save('bundle-'+name,record['bundle'])
    definition=dict(id=identity,adapter=adapter,sources=sources,inputs=inputs,tasks=tasks,
        workers=4,threads=1,maximum_wall_s=600.)
    durable_write(base/'definition.json',encoded(definition));manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+identity,identities=len(tasks),sources=len(manifest['sources']),
        limits=manifest['limits'],allocation=manifest['allocation'])


def inspect(root,prefix):
    from pathlib import Path
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import digest
    from lll.ilvis0_truth_probes import audit_pair
    from lll.ilvis0_feasible_steps import audit_step
    study=ClosedStudy(root,prefix)
    try:
        settings=study.input('recipe');validate_recipe(settings)
        for function in (audit_pair,audit_step,audit_saved_probe):
            path=Path(function.__code__.co_filename).resolve();name=path.relative_to(study.root).as_posix()
            if digest(path.read_bytes())!=study.manifest['sources'][name]:
                raise ValueError('audit source differs from completed freeze; restore its frozen version')
        positive=study.input('positive-controls');source=study.manifest['sources']['analysis/lll/ilvis0_tangent.cpp']
        if (positive['accepted']!=6 or positive['rejected']!=6 or len(positive['checked'])!=12
                or positive['native_source_sha256']!=source):
            raise ValueError('original accepted and rejected controls required')
        rows=[];native_total=lp_total=exact_total=0
        for identity,task in study.tasks.items():
            spec=task['payload'];row=study.rows.get(identity)
            base={k:spec[k] for k in ('model','profile','sign','radius')}
            if row is None:
                rows.append(dict(base,identity=identity,passed=False,usable=False,reason='Not completed'));continue
            env=study.envelope(identity);result=env['result']
            for name,sha in env['artifacts'].items():study.read(name,sha,raw=True)
            if not result['passed']:
                rows.append(dict(base,identity=identity,passed=False,usable=False,
                    reason=result.get('reason','Failed execution')));continue
            if any(result[k]!=v for k,v in base.items()):raise ValueError('probe identity changed')
            bundle=study.input(spec['bundle_key']);problem=bundle['problem'];origin=bundle['origin']
            if (problem['binding']['case_sha256']!=study.manifest['inputs'][spec['case_key']]['sha256']
                    or problem['binding']['source_sha256']!=source
                    or (problem['binding']['model'],problem['binding']['profile'])!=(spec['model'],spec['profile'])
                    or origin['point']!=bundle['initial']):
                raise ValueError('saved probe uses a different source problem')
            reservation=study.artifact(identity,'proposal-reservation.json')
            if reservation!=dict(lp_calls=2,exact_checks=8):raise ValueError('advance reservation changed')
            proposal=study.artifact(identity,'proposal.json');native=None
            path='artifacts/'+identity+'/native-output.json'
            if path in env['artifacts']:
                native=study.artifact(identity,'native-output.json');kernel=study.artifact(identity,'kernel.json')
                if kernel['compiler']!=spec['compiler'] or kernel['source_sha256']!=source:
                    raise ValueError('native probe compiler or source differs')
                before=study.artifact(identity,'point-before-native.json')
                if before!=dict(point=proposal['point'],saved_before_native=True):raise ValueError('native point differs')
            check=audit_saved_probe(problem,origin,proposal,sign=spec['sign'],radius=spec['radius'],native=native)
            if (result['usable']!=check['usable'] or result['native_evaluations']!=check['native_evaluations']
                    or result['lp_calls']!=proposal['lp_calls'] or result['exact_checks']!=proposal['exact_checks']):
                raise ValueError('saved step outcome differs from exact reconstruction')
            if native is not None:
                saved=study.artifact(identity,'candidate-audit.json')
                for key in ('audit','predicted_change_exact','actual_change_exact','ratio_exact','usable'):
                    if saved[key]!=check[key]:raise ValueError('saved nonlinear audit differs')
            native_total+=check['native_evaluations'];lp_total+=proposal['lp_calls'];exact_total+=proposal['exact_checks']
            rows.append(dict(base,identity=identity,passed=True,usable=check['usable'],reason=result['reason'],
                native_evaluations=check['native_evaluations'],linear=check['linear'],
                actual_change_exact=check.get('actual_change_exact'),ratio_exact=check.get('ratio_exact'),
                training_margin_exact=check.get('training_margin_exact')))
        if (len(study.tasks)!=36 or native_total>36 or lp_total>72 or exact_total>288):
            raise ValueError('fixed qualification matrix or work allowance changed')
        return dict(assessment=assess(rows),rows=rows,native_evaluations=native_total,lp_calls=lp_total,
            exact_checks=exact_total,positive_controls=positive,manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],numerical_work=0,
            observational_coverage_qualified=False,aircraft_fits_authorized=False)
    finally:study.close()


def render(report):
    assessment=report['assessment'];labels=['Globe + field','Globe, zero field','Stationary disc']
    lookup={(r['model'],r['profile'],r['sign'],r['radius']):r for r in report['rows']}
    state='Qualified first-step controls' if assessment['qualified'] else 'First-step controls not qualified'
    text=['# Checked local steps for training-compatible alternatives','',state+'.','',
        f"Usable steps were found in **{assessment['covered_directions']}/12 directions**. "
        'Each direction tests three fixed step sizes, keeping the original 27 calibration coordinates and bounds.',
        '',f"Saved work: {report['native_evaluations']}/36 native batches, {report['lp_calls']}/72 linear programs "
        f"and {report['exact_checks']}/288 exact proposal checks. Reporting performs no new integrations.",
        '', '| Model | Processing case | North direction | Radius .001 | Radius .0005 | Radius .00025 |',
        '|---|---|---|---|---|---|']
    for m in range(3):
        for p in (False,True):
            for s in (-1,1):
                outcomes=[]
                for radius in recipe()['radii']:
                    row=lookup.get((m,p,s,radius))
                    outcomes.append('Not completed' if row is None or not row['passed'] else
                        'Usable' if row['usable'] else 'Rejected')
                text.append('| '+' | '.join([labels[m],'Profiled removal' if p else 'Zero removal',
                    'Negative' if s<0 else 'Positive']+outcomes)+' |')
    spreads=report['positive_controls']['spreads_exact_m']
    text+=['','## What this establishes','',
        'These are generated trajectories, not aircraft results. A usable step must satisfy the actual earlier '
        'position limits and make the predicted directional progress. A rejected step remains in the record.',
        '',f"Earlier accepted probes remain valid: their north spreads are **{float(F(spreads['0'][0])):.2f} m** "
        f"and **{float(F(spreads['1'][0])):.2f} m**. All six accepted and six rejected original labels were rechecked "
        'without a new native evaluation.',
        '', 'Passing this trial qualifies only the first-step component. It does not establish a complete optimizer, '
        'outer prediction bounds, a calibrated error model or adequate aircraft predictions. **V01 remains '
        'unqualified.** The 53-stretch numerical findings are unchanged.',
        '', '[Frozen method and limits](PLAN.md) · [Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md)']
    return '\n'.join(text)+'\n'


def publish(root,prefix,output='docs/ilvis0-feasible-step-controls'):
    from pathlib import Path
    import json
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import safe_path,atomic,encoded,digest
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('publication already sealed')
    report=inspect(root,prefix)
    package(data,public,render(report),plan='docs/ilvis0-feasible-step-controls/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_text());name='artifacts/publication/comparison.json'
    content=encoded(report);atomic(public/name,content);receipt['artifacts'][name]=digest(content)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,numerical_work=0)
