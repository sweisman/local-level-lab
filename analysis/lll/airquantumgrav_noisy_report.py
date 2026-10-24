# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only noisy-control audit; no refitting or truth regeneration."""
import json


def check_case(spec,result,saved,*,r,operations):
    import math
    import numpy as np
    from lll.airquantumgrav_error_policy import build
    from lll.airquantumgrav_training_report import saved_position_errors
    from lll.airquantumgrav_truth import A,E2,DISC_RADIUS
    from lll.airquantumgrav_scoring import sections
    from lll.prediction_audit import training_fit
    from lll.studies.artifacts import digest,encoded
    fit=saved['fit.json'];forecast=saved['forecast.json'];binding=saved['input-binding.json']
    training=saved['training-observations.json'];rows=saved['training-receiver.json'];after=saved['forecast-binding.json']
    answer=saved['scoring-observations.json'];scores=saved['scores.json'];cut=2*r['queries']//3
    times=[r['query_start_s']+i*r['query_step_s'] for i in range(r['queries'])]
    active=[name+'_'+axis for name in ('attitude','velocity','position','gyro_bias','accel_bias','gyro_gain','accel_gain','lever')
        for axis in 'xyz']+['gravity_delta','time_offset']+(['earth_removal'] if spec['profile'] else [])
    checked=training_fit(fit,active=active,maximum_evaluations=r['maximum_evaluations'])
    n=round(r['duration_s']*r['rate_hz']);prefix=binding['training_prefix_packets']
    if (any(result[k]!=v for k,v in spec.items()) or len(rows)!=cut or operations['value']!=0
            or operations['tangent']!=fit['evaluations']+1 or result['native_calls']!=operations['tangent']
            or operations['packet_visits']!=fit['evaluations']*prefix*cut+n*len(times)
            or result['evaluations']!=fit['evaluations'] or result['training_cost']!=fit['residual_sum_squares']
            or result['converged']!=fit['converged'] or forecast['active_parameters']!=active
            or binding['training_receiver_sha256']!=digest(encoded(rows))
            or binding['native_packets']!=n or not 1<=prefix<=n
            or binding['training_epochs']!=cut or binding['prediction_epochs']!=len(times)-cut
            or forecast['times_s']!=times or scores['times_s']!=times
            or forecast['training_epochs']!=cut or forecast['prediction_epochs']!=len(times)-cut
            or training['times_s']!=times[:cut] or training['native_prefix_packets']!=prefix
            or training['training_prefix_sha256']!=binding['training_prefix_sha256']
            or after['full_array_sha256']!=binding['full_array_sha256'] or after['raw_arrays_unchanged'] is not True
            or after['jacobian_shape']!=[len(times)*3,len(active)]):
        raise ValueError('saved noisy inputs, columns, forecasts or native accounting differ')
    coordinates=[[math.radians(v['latitude_deg']),math.radians(v['longitude_deg']),v['height_m']] for v in rows]
    weight=build(rows,policy_id=spec['policy_id']);noise=binding['noise']
    if (training['coordinates']!=coordinates or training['weight_configuration']!=weight.configuration
            or training['weight_descriptor']!=weight.descriptor or training['weight_source_sha256']!=weight.source_sha256
            or noise['settings']!=r['noise'] or noise['noisy_training_receiver_sha256']!=binding['training_receiver_sha256']
            or noise['gravity_anchor_height_m']!=rows[0]['height_m'] or noise['gravity_anchor_source']!='first_noisy_training_receiver_height'
            or binding['gravity_anchor_height_m']!=rows[0]['height_m'] or result['gravity_anchor_height_m']!=rows[0]['height_m']
            or any(noise['measured_raw_array_sha256'][k]!=binding['full_array_sha256'][k] for k in ('theta','dv','dt'))
            or noise['later_receiver_positions_generated'] or not noise['receiver_and_imu_streams_separate']
            or not noise['noise_is_an_assumption_not_measured_archive_error']):
        raise ValueError('training-only noisy initialization or fixed stress assumptions differ')
    for value in (result,training,noise):
        if value['true_initial_state_supplied'] or value['true_calibration_supplied']:
            raise ValueError('true calibration or initial state supplied')
    if (training['prediction_receiver_positions_used'] or forecast['prediction_receiver_positions_used']
            or not forecast['continuous_propagation_without_gps_reset'] or not result['forecast_saved_before_scoring']
            or not result['all_columns_retained'] or result['score_reference']!='generated noiseless physical truth'
            or scores['later_receiver_noise_added'] or any(result[k] for k in ('original_reads','protected_reads','observed_starts','confidence_calibrated'))
            or result['scientific_decision']!='abstain'):
        raise ValueError('generated-only prediction scope changed')
    physical=np.asarray(saved_position_errors(forecast['coordinates'],answer,model=spec['model'],
        constants=dict(A=A,E2=E2,DISC_RADIUS=DISC_RADIUS)))
    if physical.shape!=(len(times),3) or not np.allclose(physical,np.asarray(scores['errors_neu_m']),rtol=0,atol=1e-7):
        raise ValueError('independent saved physical errors differ')
    calculated=sections(scores['errors_neu_m'],cut)
    if any(encoded(calculated[k])!=encoded(scores[k]) or encoded(calculated[k])!=encoded(result[k]) for k in calculated):
        raise ValueError('saved error scores or physical accuracy labels differ')
    accurate=all(v['accuracy']['passed'] for v in calculated.values())
    if result['accuracy_all_sections']!=accurate or result['passed']!=bool(fit['converged'] and accurate):
        raise ValueError('numerical and physical outcomes were relabeled')
    return dict(checked,converged=fit['converged'],accurate=accurate,
        training=calculated['training'],prediction=calculated['prediction'])


def inspect(root,prefix='data/esa-noisy-prediction-20261024'):
    from lll.studies.closed import ClosedStudy
    study=ClosedStudy(root,prefix)
    try:
        from pathlib import Path
        from lll.airquantumgrav_noisy_study import recipe,tasks,construction_limits,environment,SCOPE
        from lll.airquantumgrav_geographic_report import construction_counts
        from lll.airquantumgrav_observation_report import native_accounting
        from lll.airquantumgrav_observed_wide_report import verify_compilation
        from lll.ilvis0_wide_training import SOURCES,bind
        from lll.studies.artifacts import digest
        from lll.studies.source_binding import verify
        root=Path(root).resolve();r=study.input('recipe');env=study.input('qualification-environment')
        if (r!=recipe() or env!=environment() or study.manifest['scope']!=SCOPE
                or {k:{a:b for a,b in v.items() if a not in ('index','shard')} for k,v in study.tasks.items()}
                !={t['identity']:t for t in tasks()}):raise ValueError('unchanged finite noisy study required')
        verify(root,declared=study.input('qualification-request')['sources'],manifest=study.manifest['sources'])
        _,_,protocol=bind(expected_sources={n:study.manifest['sources']['analysis/lll/'+n] for n in SOURCES})
        if protocol!=study.input('protocol-binding'):raise ValueError('qualified fitting protocol differs')
        parent=ClosedStudy(root,'docs/esa-wide-training-controls')
        try:
            receipt=parent.read('evidence-receipt.json');key='artifacts/publication/verified-report.json'
            proof=study.input('qualified-parent');report=parent.read(key,receipt['artifacts'][key])
            if (not report['qualified'] or report['passed']!=24 or proof!=dict(manifest_sha256=parent.completion['manifest_sha256'],
                    summary_sha256=parent.completion['summary_sha256'],report_sha256=receipt['artifacts'][key])):
                raise ValueError('noiseless qualification parent differs')
        finally:parent.close()
        operations={}
        for shard in range(study.manifest['allocation']['workers']):
            operations.update(native_accounting(study.read(f'shards/{shard:03d}/charges/journal.sqlite',raw=True),
                study.completion['manifest_sha256'],{k for k,v in study.tasks.items() if v['shard']==shard},per_call_visits=None))
        rows=[];totals={k:0 for k in study.summary['charged']};limits=construction_limits(r);shared={}
        for identity,task in study.tasks.items():
            row=dict(identity=identity,**task['payload'],complete=False,converged=False,accurate=False)
            if identity not in study.rows:
                rows.append(dict(row,reason='No returned outcome'));continue
            envelope=study.envelope(identity);result=envelope['result'];ops=operations[identity]
            for name,sha in envelope['artifacts'].items():study.read(name,sha,raw=True)
            for key in totals:totals[key]+=envelope['charged'][key]
            if ops['value'] or ops['tangent']!=envelope['charged']['native_calls'] or ops['packet_visits']!=envelope['charged']['packet_visits']:
                raise ValueError('native operation kinds and envelope charges differ')
            complete='converged' in result;row.update(complete=complete,reason=result.get('error',result.get('reason')),
                charged_native_calls=ops['tangent'])
            path='artifacts/'+identity+'/construction.sqlite'
            if path in envelope['artifacts']:
                counts=construction_counts(study.read(path,envelope['artifacts'][path],raw=True),
                    study.completion['manifest_sha256'],identity,limits,complete=complete)
                row['construction']=counts
            if complete:
                names=('fit.json','forecast.json','input-binding.json','forecast-binding.json','training-receiver.json',
                    'training-observations.json','scoring-observations.json','scores.json','compilation.json','protocol-binding.json')
                saved={name:study.artifact(identity,name) for name in names}
                checked=check_case(task['payload'],result,saved,r=r,operations=ops);row.update(checked)
                if saved['protocol-binding.json']!=protocol:raise ValueError('case protocol differs')
                binding=saved['input-binding.json'];source='analysis/lll/ilvis0_tangent.cpp'
                verify_compilation(meta=saved['compilation.json'],
                    raw=study.read('source-freeze/'+source,study.manifest['sources'][source],raw=True),
                    sources=study.manifest['sources'],environment=env,anchor=binding['gravity_anchor_height_m'])
                if any(result[k]!=v for k,v in counts.items()):raise ValueError('reported construction totals differ')
                key=(row['model'],row['profile']);raw=binding['full_array_sha256']
                if key in shared and shared[key]!=raw:raise ValueError('matched starts or policies changed sensor-noise realization')
                shared[key]=raw
            rows.append(row)
        if totals!=study.summary['charged']:raise ValueError('whole-study charges differ')
        return dict(verified=True,total=24,complete=sum(v['complete'] for v in rows),
            numerically_converged=sum(v['converged'] for v in rows),accurate=sum(v['accurate'] for v in rows),rows=rows,
            qualified=all(v['complete'] and v['converged'] and v['accurate'] for v in rows),
            elapsed_s=study.summary['elapsed_s'],charged=totals,
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            original_reads=0,protected_reads=0,observed_starts=0,native_calls_during_audit=0,
            confidence_calibrated=False,scientific_decision='abstain')
    finally:study.close()


def render(report):
    lines=['# Prediction with known measurement errors','',
        f"**{report['complete']}/24 forecasts returned; {report['numerically_converged']} passed numerical checks; "
        f"{report['accurate']} meet physical accuracy.**",'',
        'These are generated controls with receiver and IMU noise, including slowly changing bias.',
        'Their declared noise levels are not measured instrument specifications. There are no observed aircraft inputs.',
        'Each candidate is tested against its own generating truth; these are not votes for a physical model.','',
        '| Generating candidate | Removal | Receiver errors | Start | Numerical pass | Physical pass | Later horizontal RMS | Later height RMS |',
        '|---|---|---|---:|---|---|---:|---:|']
    for row in report['rows']:
        fields=[row['model'],'Profiled' if row['profile'] else 'Zero',row['policy_id'],str(row['start'])]
        if row['complete']:
            fields += [str(row['converged']),str(row['accurate']),f"{row['prediction']['horizontal_rms_m']:.6g} m",f"{row['prediction']['vertical_rms_m']:.6g} m"]
        else:fields+=['Unavailable','Unavailable','Unavailable','Unavailable']
        lines.append('| '+' | '.join(fields)+' |')
    lines+=['',f"Elapsed time: {report['elapsed_s']/60:.2f} minutes; charged native calls: {report['charged']['native_calls']}.",'',
        'Errors are applied before initialization. Calibration uses noisy earlier positions only; later truth is opened',
        'after the continuous IMU forecast is saved. Accuracy uses the existing observed-prediction limits, including height.',
        'The earlier noiseless software accuracy targets and results remain unchanged.','',
        'This is a robustness check under explicit assumptions, not calibrated confidence or an estimate of archive noise.',
        'The receiver-only fitting weights remain fixed; this does not validate them as a complete IMU prediction-error law.',
        'All failures and charges remain preserved. Seven confirmation groups and the 53-stretch findings are unchanged.','',
        '[Frozen plan](PLAN.md) · [Earlier error diagnostic](../esa-error-structure/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md)']
    return '\n'.join(lines)+'\n'


def publish(root,prefix='data/esa-noisy-prediction-20261024',output='docs/esa-noisy-prediction'):
    from pathlib import Path
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic,digest,encoded,safe_path
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('noisy publication already sealed')
    report=inspect(root,prefix);package(data,public,render(report),plan='docs/esa-noisy-prediction/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    for name,raw in [('verified-report.json',encoded(report)),('reporter.py',Path(__file__).read_bytes())]:
        name='artifacts/publication/'+name;atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,native_calls=0,original_reads=0)
