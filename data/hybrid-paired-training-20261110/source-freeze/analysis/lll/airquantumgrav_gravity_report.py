# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit saved generated gravity controls without generating truth or propagating."""
import json
import math


def require_scope(result):
    if (not result['known_corrections_supplied_not_estimated']
            or any(result[k] for k in ('original_reads','protected_reads','observed_starts','confidence_calibrated'))
            or result['scientific_decision']!='abstain'):
        raise ValueError('known-correction software controls cannot establish observed evidence or calibrated confidence')


def case_gate(result,phases,tangent,correction,answer,r):
    import numpy as np
    from lll.airquantumgrav_geographic_controls import position_errors
    from lll.airquantumgrav_geographic_report import error_metrics,_same_metrics
    from lll.airquantumgrav_gravity_controls import checks
    require_scope(result);m=r['queries'];summaries=[]
    times=(r['query_start_s']+np.arange(m)*r['query_step_s']).tolist()
    if answer['times_s']!=times or not answer['known_not_fitted']:raise ValueError('complete unchanged known answers required')
    for phase,hz in zip(phases,r['rates_hz'],strict=True):
        if (phase['rate_hz']!=hz or phase['packets']!=round(hz*r['duration_s']) or phase['times_s']!=times
                or not phase['generated_not_observed'] or np.array(phase['coordinates']).shape!=(m,3)):
            raise ValueError('complete fixed generated support required')
        errors=position_errors(phase['coordinates'],answer,model=result['model'])
        if not np.array_equal(errors,np.asarray(phase['errors_neu_m'])):raise ValueError('saved physical errors differ')
        summary=error_metrics(errors.tolist());_same_metrics(summary,phase['metrics']);summaries.append(summary)
    for summary,key in zip(summaries,('coarse','fine'),strict=True):_same_metrics(summary,result[key])
    columns=[name+'_'+axis for name in ('attitude','velocity','position','gyro_bias','accel_bias','gyro_gain','accel_gain','lever')
        for axis in 'xyz']+['gravity_delta','time_offset','earth_removal']
    point=tangent['normalized_parameters'];jac=np.asarray(tangent['jacobian'],float);coords=np.asarray(tangent['coordinates'],float)
    if (tangent['active_parameters']!=columns or len(point)!=27 or jac.shape!=(3*m,27) or coords.shape!=(m,3)
            or not np.all(np.isfinite(jac)) or not np.all(np.isfinite(coords))
            or any(not math.isfinite(v) or abs(v)>1 for v in point)
            or not correction['known_corrections_supplied_not_estimated']
            or correction['anchor_height_m']!=(1500. if result['height_profile']=='climb' else 3500.)):
        raise ValueError('complete feasible correction vector and derivative columns required')
    for key,value in zip(columns,point,strict=True):
        expected=2*result['removal']-1 if key=='earth_removal' else correction['parameters'][key]/correction['limits'][key]
        if value!=expected:raise ValueError('saved known correction differs from the executed point')
    difference=float(np.max(abs((coords-np.asarray(phases[0]['coordinates']))*[6378137.,6378137.,1.])))
    if (not math.isclose(difference,tangent['value_disagreement_m'],rel_tol=1e-10,abs_tol=1e-12)
            or not math.isclose(difference,result['value_disagreement_m'],rel_tol=1e-10,abs_tol=1e-12)):
        raise ValueError('saved value/tangent agreement differs')
    checked=checks(summaries,value_disagreement_m=difference,all_columns_retained=True,r=r)
    if checked!=result['checks'] or checked['passed']!=result['passed'] or not result['all_columns_retained']:
        raise ValueError('saved accuracy/refinement/column labels differ from frozen rules')
    return dict(passed=checked['passed'],coarse=summaries[0],fine=summaries[1],value_disagreement_m=difference)


def inspect(root,prefix='data/esa-height-gravity-controls-20261023'):
    from pathlib import Path
    from lll.studies.closed import ClosedStudy
    study=ClosedStudy(root,prefix)
    try:
        from lll.airquantumgrav_gravity_controls import recipe,tasks,construction_limits
        from lll.airquantumgrav_observation_report import native_accounting
        from lll.airquantumgrav_geographic_report import construction_counts
        from lll.airquantumgrav_observed_report import verify_audit_environment
        from lll.ilvis0_control_shards import runtime_environment
        from lll.studies.artifacts import digest
        r=study.input('recipe');canonical={v['identity']:v for v in tasks()};env=study.input('qualification-environment')
        if r!=recipe() or len(study.tasks)!=48 or set(study.tasks)!=set(canonical):raise ValueError('complete frozen gravity matrix required')
        audit_environment=runtime_environment();verify_audit_environment(env,audit_environment)
        for filename in ('airquantumgrav_gravity_controls.py','airquantumgrav_geographic_controls.py','airquantumgrav_truth.py'):
            name='analysis/lll/'+filename
            if digest((Path(root)/name).read_bytes())!=study.manifest['sources'][name]:raise ValueError('restore frozen scoring dependencies')
        for identity,task in study.tasks.items():
            if {k:v for k,v in task.items() if k not in ('index','shard')}!=canonical[identity]:raise ValueError('task identity differs')
        native={};rows=[];binaries={'value':set(),'tangent':set()};charged={k:0 for k in study.summary['charged']}
        for shard in range(study.manifest['allocation']['workers']):
            identities={identity for identity,task in study.tasks.items() if task['shard']==shard}
            native.update(native_accounting(study.read(f'shards/{shard:03d}/charges/journal.sqlite',raw=True),
                study.completion['manifest_sha256'],identities,per_call_visits=None))
        limits=construction_limits(r)
        for identity,task in study.tasks.items():
            if identity not in study.rows:continue
            envelope=study.envelope(identity);result=envelope['result'];artifacts=envelope['artifacts'];operations=native[identity]
            for name,sha in artifacts.items():study.read(name,sha,raw=True)
            for key in charged:charged[key]+=envelope['charged'][key]
            if (operations['value']+operations['tangent']!=envelope['charged']['native_calls']
                    or operations['packet_visits']!=envelope['charged']['packet_visits']):raise ValueError('native kinds/charges differ')
            complete='coarse' in result and 'fine' in result;journal='artifacts/'+identity+'/construction.sqlite'
            construction=construction_counts(study.read(journal,artifacts[journal],raw=True),study.completion['manifest_sha256'],
                identity,limits,complete=complete) if journal in artifacts else None
            row=dict(identity=identity,spec=task['payload'],complete=complete,result=result,construction=construction)
            if complete:
                if (any(result[k]!=v for k,v in task['payload'].items()) or operations['value']!=2 or operations['tangent']!=1
                        or envelope['charged']!=task['limits'] or result['native_calls']!=3 or construction!=limits
                        or result['constructed_intervals']!=limits['constructed_intervals'] or result['generated_samples']!=limits['generated_samples']):
                    raise ValueError('complete case and native/construction charges differ')
                phases=[study.artifact(identity,f'rate-{hz}.json') for hz in r['rates_hz']]
                row['checked']=case_gate(result,phases,study.artifact(identity,'tangent.json'),
                    study.artifact(identity,'corrections.json'),study.artifact(identity,'answer.json'),r)
                meta=study.artifact(identity,'compilation.json')
                for kind,filename,compiler in [('value','ilvis0_native.c','cc'),('tangent','ilvis0_tangent.cpp','c++')]:
                    value=meta[kind]
                    if (value['source_sha256']!=study.manifest['sources']['analysis/lll/'+filename]
                            or value['compiler']!=env['compilers'][compiler]):raise ValueError('compiled source/environment differs')
                    if task['payload']['gravity_model']=='inverse_square_height':
                        anchor=1500. if task['payload']['height_profile']=='climb' else 3500.
                        if value.get('gravity_model')!='inverse-square-height-v1' or value.get('gravity_anchor_height_m')!=anchor:
                            raise ValueError('compiled gravity mode or anchor differs')
                    elif 'gravity_model' in value:raise ValueError('constant case used a changed gravity interface')
                    binaries[kind].add(value['binary_sha256'])
            elif result['passed']:raise ValueError('unfinished case cannot qualify')
            rows.append(row)
        if (charged!=study.summary['charged'] or any(len(v)>1 for v in binaries.values())
                or sum(v['value']+v['tangent'] for v in native.values())!=charged['native_calls']):raise ValueError('whole-study charges or binaries differ')
        families=[]
        for mode in r['gravity_models']:
            group=[v for v in rows if v['spec']['gravity_model']==mode];full=[v for v in group if v['complete']]
            families.append(dict(gravity_model=mode,returned=len(group),complete=len(full),passed=sum(v['result']['passed'] for v in group),
                maximum_coarse_3d_m=max((v['checked']['coarse']['maximum_3d_m'] for v in full),default=None),
                maximum_fine_3d_m=max((v['checked']['fine']['maximum_3d_m'] for v in full),default=None),
                maximum_value_disagreement_m=max((v['checked']['value_disagreement_m'] for v in full),default=None)))
        passed=sum(v['result']['passed'] for v in rows)
        return dict(verified=True,total=48,returned=len(rows),passed=passed,qualified=len(rows)==passed==48,
            families=families,rows=rows,charged=charged,construction_totals={k:sum((v['construction'] or {}).get(k,0) for v in rows) for k in limits},
            construction_accounting_complete=all(v['construction'] is not None for v in rows),elapsed_s=study.summary['elapsed_s'],
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            audit_environment=audit_environment,native_calls_during_audit=0,observed_starts=0,original_reads=0,protected_reads=0,
            initialization_estimator_qualified=False,confidence_calibrated=False,scientific_decision='abstain')
    finally:study.close()


def render(report):
    lines=['# Gravity controls during climbs and descents','',
        f"**{report['passed']}/{report['total']} generated cases pass the frozen checks.** "
        +('The tested known-correction calculation qualifies.' if report['qualified'] else 'The full calculation does not qualify.'),'',
        'These twenty-minute tracks are generated independently from analytic Cartesian geometry.',
        'They climb or descend through 2 km while turning. All three candidates, both latitude signs,',
        'both removal cases and both gravity laws are retained. Initial state and sensor/antenna',
        'corrections are supplied exactly; no calibration is fitted.','',
        '| Gravity assumption | Passed | Largest 300 Hz spatial error | Largest 600 Hz spatial error | Value/derivative disagreement |',
        '|---|---:|---:|---:|---:|']
    for row in report['families']:
        label='Constant magnitude' if row['gravity_model']=='constant' else 'Declared height dependence'
        number=lambda key:'Unavailable' if row[key] is None else f"{row[key]:.6g} m"
        lines.append('| '+' | '.join([label,f"{row['passed']}/24",number('maximum_coarse_3d_m'),number('maximum_fine_3d_m'),
            number('maximum_value_disagreement_m')])+' |')
    lines+=['','Each resolution must meet horizontal and height RMS ≤1 m and maximum spatial error ≤5 m.',
        'The finer maximum must be at most 0.4 times the coarse maximum plus 0.001 m.',
        'Value and derivative predictions must agree within 0.001 m, retaining all 27 nuisance columns.',
        'These are software acceptance targets, not measured instrument precision or calibrated uncertainty.','',
        f"The run charges {report['charged']['native_calls']:,} native calls in {report['elapsed_s']/60:.2f} minutes.",
        f"Construction journals retain {report['construction_totals']['constructed_intervals']:,} increments and "
        f"{report['construction_totals']['generated_samples']:,} generated samples.",
        'The saved-only audit checks hashes, complete physical errors, derivatives, labels and charges.',
        'It does not generate truth again, propagate, fit or open an original recording.','',
        'The height-dependent law is the same declared force-law sensitivity for every geometry.',
        'It does not provide independent curvature evidence or establish the cause of the ESA pilot errors.',
        'Longer training-only calibration and forecast controls remain necessary before a revised observed fit.',
        'Seven ESA confirmation groups and the original NASA results remain unchanged.','',
        '[Frozen question and limits](PLAN.md) · [Implementation](IMPLEMENTATION.md) · '
        '[Saved-data diagnosis](../esa-development-diagnosis/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md)']
    if not report['construction_accounting_complete']:lines+=['','Some failed cases lack a sealed construction journal; the listed construction totals are incomplete.']
    return '\n'.join(lines)+'\n'


def publish(root,prefix='data/esa-height-gravity-controls-20261023',output='docs/esa-gravity-controls'):
    from pathlib import Path
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic,digest,encoded,safe_path
    from lll.studies.publication import archive_publication
    from lll.studies.closed import ClosedStudy
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('gravity publication is already sealed')
    report=inspect(root,prefix);package(data,public,render(report),plan='docs/esa-gravity-controls/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_bytes());study=ClosedStudy(root,prefix)
    try:
        name='docs/esa-gravity-controls/IMPLEMENTATION.md';raw=(public/'IMPLEMENTATION.md').read_bytes()
        if digest(raw)!=study.manifest['sources'][name]:raise ValueError('frozen implementation changed')
        receipt['artifacts']['IMPLEMENTATION.md']=digest(raw)
    finally:study.close()
    for name,raw in [('verified-report.json',encoded(report)),('reporter.py',Path(__file__).read_bytes())]:
        name='artifacts/publication/'+name;atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,native_calls=0,original_reads=0)
