# SPDX-License-Identifier: AGPL-3.0-or-later
"""Closed fresh-draw reporting through shared case and score checks."""
from collections import defaultdict


def select_primaries(rows,tasks):
    from lll.ilvis0_forecast_publication import primary
    groups={}
    for task in tasks.values():
        p=task['payload'];s=p['case'];groups.setdefault((p['draw_seed'],s['law'],s['model'],s['profile']),[])
    for row in rows:
        key=(row['draw_seed'],row['law'],row['model'],row['profile'])
        if key not in groups:raise ValueError('declared seed/model group required')
        groups[key].append(row)
    result=[]
    for (seed,law,model,profile),values in sorted(groups.items()):
        candidates=[dict(v,passed=bool(v.get('complete') and v.get('converged'))) for v in values]
        chosen=primary(candidates)
        result.append(dict(draw_seed=seed,law=law,model=model,profile=profile,
            selected_identity=chosen['identity'] if chosen is not None else None,
            selected_start=chosen['start'] if chosen is not None else None,available=chosen is not None,
            selection='qualified training cost, then declared start order'))
    return result


def inspect(root,prefix):
    from lll.studies.closed import ClosedStudy
    study=ClosedStudy(root,prefix)
    try:
        from lll.independent_noisy_study import recipe,tasks,case_recipe,score_records,SCORE_INPUTS,SCOPE
        from lll.structured_noisy_publication import native_bindings,inspect_case
        from lll.studies.artifacts import encoded
        r=recipe()
        if (study.input('recipe')!=r or study.manifest['scope']!=SCOPE
                or {k:{a:b for a,b in v.items() if a not in ('index','shard')} for k,v in study.tasks.items()}
                    !={v['identity']:v for v in tasks()}):raise ValueError('complete frozen pilot matrix and seed roles required')
        bindings=native_bindings(study);rows=[];attempted=0
        for identity,task in study.tasks.items():
            p=task['payload'];seed=p['draw_seed'];spec=p['case']
            row=dict(identity=identity,draw_seed=seed,role=p['role'],**spec,complete=False,converged=False,accurate=False)
            if identity not in study.rows:rows.append(dict(row,reason='No returned outcome'));continue
            envelope=study.envelope(identity);outcome=envelope['result']
            artifact='artifacts/'+identity+'/draw-identity.json'
            if artifact in envelope['artifacts']:
                draw=study.artifact(identity,'draw-identity.json')
                if draw!=dict(seed=seed,role=p['role'],case=spec,calibration_draw=False,validation_draw=False,confidence_calibrated=False):
                    raise ValueError('immutable draw identity or role differs')
            checked=inspect_case(study,identity,payload=spec,r=case_recipe(seed),bindings=bindings)
            if checked is None:
                rows.append(dict(row,reason=outcome.get('reason',outcome.get('error','Incomplete forecast'))));continue
            if artifact not in envelope['artifacts']:raise ValueError('complete case lacks its frozen draw identity')
            records={name:study.artifact(identity,name) for name in SCORE_INPUTS}
            score=score_records(records,seed=seed);saved=study.artifact(identity,'prediction-score.json')
            if (encoded(score)!=encoded(saved) or outcome['draw_seed']!=seed or outcome['role']!=p['role']
                    or outcome['maximum_standardized_error']!=score['maximum_standardized_error']
                    or outcome['confidence_calibrated']):raise ValueError('saved fitted-prediction score or role differs')
            fit=records['fit.json'];attempted+=checked['native_calls']
            rows.append(dict(row,complete=True,**checked,training_cost=fit['residual_sum_squares'],
                maximum_standardized_error=score['maximum_standardized_error'],score=score))
        primaries=select_primaries(rows,study.tasks)
        return dict(verified=True,total=48,returned_outcomes=study.summary['completed'],complete=sum(v['complete'] for v in rows),
            numerically_converged=sum(v['converged'] for v in rows),raw_accuracy=sum(v['accurate'] for v in rows),
            conditional_accuracy=sum(v.get('conditional_prediction',{}).get('accuracy',{}).get('passed',False) for v in rows),
            rows=rows,primaries=primaries,available_primaries=sum(v['available'] for v in primaries),seeds=r['seeds'],
            attempted_native_calls=attempted,elapsed_s=study.summary['elapsed_s'],prepaid=study.summary['charged'],
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            independent_noise_seeds=2,calibration_draws=0,validation_draws=0,observed_starts=0,
            original_reads=0,protected_reads=0,native_calls_during_audit=0,confidence_calibrated=False,
            scientific_decision='abstain')
    finally:study.close()


def _checked(report):
    rows=report.get('rows',[])
    if (report.get('verified') is not True or len(rows)!=report.get('total')
            or sum(v['complete'] for v in rows)!=report['complete']
            or sum(v['converged'] for v in rows)!=report['numerically_converged']
            or sum(v['accurate'] for v in rows)!=report['raw_accuracy'] or report['confidence_calibrated']):
        raise ValueError('verified complete inventory with unchanged labels required')
    return rows


def render(report):
    rows=_checked(report);by_id={v['identity']:v for v in rows}
    lines=['# Fitted predictions with fresh noise','',
        f"**{report['numerically_converged']}/{report['total']} starts pass numerical checks; "
        f"{report['complete']}/{report['total']} complete forecasts are available.**",'',
        'Each candidate is fitted to its own generating truth: these are not Earth-model votes.',
        'The two fresh seeds are diagnostic draws. Settings and starts sharing a seed',
        'are dependent; this is not a collection of independent flights.',
        'Prediction uncertainty is not calibrated. No tail threshold or detection is inferred.','',
        '| Seed | Numerical passes | Raw physical screen passes | Conditional physical screen passes |',
        '|---|---:|---:|---:|']
    for seed in report['seeds']:
        subset=[v for v in rows if v['draw_seed']==seed]
        lines.append(f"| {seed} | {sum(v['converged'] for v in subset)}/{len(subset)} | "
            f"{sum(v['accurate'] for v in subset)}/{len(subset)} | "
            f"{sum(v.get('conditional_prediction',{}).get('accuracy',{}).get('passed',False) for v in subset)}/{len(subset)} |")
    lines+=['','Primary starts use qualified training cost and declared order, never later errors.',
        'The error/noise score is the maximum over the entire later block. Its covariance',
        'treats fitted calibration as known; the score is not a confidence level.','',
        '| Seed / input / model / processing | Primary start | Raw horizontal RMS | Conditional horizontal RMS | Maximum error/noise score |',
        '|---|---:|---:|---:|---:|']
    for group in report['primaries']:
        label=f"{group['draw_seed']} / {group['law']} / {group['model']} / {int(group['profile'])}"
        if group['available']:
            v=by_id[group['selected_identity']]
            fields=f"{v['start']} | {v['prediction']['horizontal_rms_m']:.3f} m | "
            fields+=f"{v['conditional_prediction']['horizontal_rms_m']:.3f} m | {v['maximum_standardized_error']:.3f}"
        else:fields='Unavailable | Unavailable | Unavailable | Unavailable'
        lines.append(f'| {label} | {fields} |')
    lines+=['','[Every start, including failures](results.csv) · [Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).',
        '', 'The original calibration bounds, accuracy screens and earlier failures remain unchanged.',
        'No aircraft observations or reserved ESA groups were used.']
    return '\n'.join(lines)+'\n'


def result_csv(report):
    import csv,io
    rows=_checked(report);stream=io.StringIO(newline='')
    primary_ids={v['selected_identity'] for v in report['primaries'] if v['available']}
    fields=['identity','draw_seed','role','law','model','profile','start','complete','numerical_pass','raw_accuracy',
        'training_primary','training_cost','raw_horizontal_rms_m','raw_height_rms_m','conditional_horizontal_rms_m',
        'conditional_height_rms_m','maximum_standardized_error','reason']
    writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n');writer.writeheader()
    for row in rows:
        out={k:row[k] for k in ('identity','draw_seed','role','law','model','profile','start','complete')}
        out.update(numerical_pass=row['converged'],raw_accuracy=row['accurate'],training_primary=row['identity'] in primary_ids,
            reason=row.get('reason',''))
        if row['complete']:
            out.update(training_cost=row['training_cost'],raw_horizontal_rms_m=row['prediction']['horizontal_rms_m'],
                raw_height_rms_m=row['prediction']['vertical_rms_m'],
                conditional_horizontal_rms_m=row['conditional_prediction']['horizontal_rms_m'],
                conditional_height_rms_m=row['conditional_prediction']['vertical_rms_m'],
                maximum_standardized_error=row['maximum_standardized_error'])
        writer.writerow(out)
    return stream.getvalue()


def publication_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/independent_noisy_report.py','analysis/tests/test_independent_noisy_report.py',
        'analysis/lll/structured_noisy_publication.py','analysis/tests/test_structured_noisy_publication.py',
        'analysis/lll/studies/native_publication.py','analysis/lll/studies/qualification.py'])


def audit_environment(root,prefix):
    from lll.studies.closed import ClosedStudy
    from lll.airquantumgrav_inventory import environment
    study=ClosedStudy(root,prefix)
    try:return dict(environment(),closed_pilot_manifest_sha256=study.completion['manifest_sha256'])
    finally:study.close()


def publish(root,prefix,*,qualification,output='docs/independent-noisy-training-pilot'):
    if qualification is None:raise ValueError('source-bound closed-results qualification required')
    import json
    from pathlib import Path
    from lll.studies.artifacts import atomic,encoded,digest,safe_path
    from lll.studies.closed import ClosedStudy
    from lll.studies.qualification import checked
    from lll.studies.native_publication import include_native_caches
    from lll.structured_noisy_publication import native_cache_entries
    from lll.ilvis0_control_publication import publish as package,check
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('closed pilot publication already sealed')
    request,tests=checked(root,qualification,sources=publication_sources(root),environment=audit_environment(root,prefix),
        minimum_tests=17,required_tests=['test_previous_numeric_replay_after_shared_audit_extraction_is_unchanged',
            'test_closed_pilot_numeric_replay_preserves_all_seeds_and_returned_outcomes',
            'test_fresh_primary_selection_uses_training_cost_and_retains_empty_group',
            'test_shared_native_cache_entries_reject_changed_cache_binding'])
    report=inspect(root,prefix);study=ClosedStudy(root,prefix)
    try:assets=native_cache_entries(study)
    finally:study.close()
    package(data,public,render(report),plan='docs/prediction-score-qualification/PIPELINE_PILOT.md')
    if assets:include_native_caches(root,data,public,entries=[dict(path=k,sha256=v) for k,v in sorted(assets.items())],
        maximum_bytes=64*1024**2)
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    extras={'results.csv':result_csv(report).encode(),'artifacts/publication/verified-report.json':encoded(report),
        'artifacts/publication/qualification-request.json':request,'artifacts/publication/qualification-report.xml':tests}
    for name in ('analysis/lll/independent_noisy_report.py','analysis/tests/test_independent_noisy_report.py',
            'analysis/lll/structured_noisy_publication.py','analysis/tests/test_structured_noisy_publication.py'):
        extras['artifacts/publication/source/'+name]=(root/name).read_bytes()
    for name,raw in extras.items():atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt));check(data,public)
    if encoded(inspect(root,output))!=encoded(report):raise ValueError('closed publication audit differs')
    return dict(publication=output,artifacts=len(receipt['artifacts']),returned=report['returned_outcomes'],
        numerically_converged=report['numerically_converged'],native_calls=0,optimizer_starts=0,
        compaction_pending=True,confidence_calibrated=False)
