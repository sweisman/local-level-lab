# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only ESA development reporting; no fit, propagation or original read."""
import itertools
import math


def verify_audit_environment(qualified,audit):
    if any(audit.get(key)!=qualified.get(key) for key in ('python','packages')):
        raise ValueError('restore the qualified Python and numerical-package versions before auditing')


def summarize_starts(rows,r):
    from lll.ilvis0_forecast_publication import primary
    expected=set(itertools.product(r['models'],r['profiles'],r['policies'],range(r['starts'])))
    found=set();groups={key:[] for key in itertools.product(r['models'],r['profiles'],r['policies'])}
    for row in rows:
        key=tuple(row[k] for k in ('model','profile','policy_id','start'))
        if key not in expected or key in found:raise ValueError('one known distinct frozen start required')
        if row['passed'] and (not row['complete'] or not row['converged']):raise ValueError('unfinished or unqualified fit cannot pass')
        found.add(key);groups[key[:3]].append(row)
    primaries=[];lookup={}
    for (model,profile,policy),values in groups.items():
        # Select on training qualification first, even if forecasting later failed.
        candidates=[dict(v,passed=bool(v.get('training_fit_converged',v.get('converged',False))),
            converged=bool(v.get('training_fit_converged',v.get('converged',False)))) for v in values]
        choice=primary(candidates)
        training_choice=next((v for v in values if choice is not None and v['start']==choice['start']),None)
        selected=training_choice if training_choice is not None and training_choice['complete'] and training_choice['passed'] else None
        if selected is not None:
            error=selected['prediction']['total_rms_m']
            if not math.isfinite(error) or error<0:raise ValueError('finite complete later prediction required')
        group=dict(model=model,profile=profile,policy_id=policy,available_starts=len(values),primary=selected,
            training_primary=training_choice,selected_training_start=training_choice['start'] if training_choice is not None else None,
            selection='converged training cost, then declared start order')
        primaries.append(group);lookup[(model,profile,policy)]=selected
    comparisons=[]
    for profile,policy in itertools.product(r['profiles'],r['policies']):
        group={model:lookup[(model,profile,policy)] for model in r['models']}
        case=dict(profile=profile,policy_id=policy,complete=all(v is not None for v in group.values()),
            shape_lower_error_family=None,preferred_model=None,preferred_accuracy=False,field_lower_error_model=None,
            calibrated_decision=False,scientific_decision='abstain')
        if case['complete']:
            errors={model:row['prediction']['total_rms_m'] for model,row in group.items()}
            globe=min(('sphere_rotating','sphere_still'),key=lambda model:(errors[model],r['models'].index(model)))
            flat=errors['flat_still'];best=errors[globe]
            if best<flat:family='globe';preferred=globe
            elif flat<best:family='disc';preferred='flat_still'
            else:family='tie';preferred=None
            adequate=preferred is not None and bool(group[preferred]['accuracy_all_sections'])
            field=None
            if family=='globe' and adequate:
                a,b=errors['sphere_rotating'],errors['sphere_still']
                field='specified_field' if a<b else 'zero_field' if b<a else 'tie'
            case.update(shape_lower_error_family=family,preferred_model=preferred,preferred_accuracy=adequate,
                field_lower_error_model=field,prediction_total_rms_m=errors,
                interpretation='descriptive lower error; accuracy and calibrated confidence are separate')
        comparisons.append(case)
    return dict(primaries=primaries,comparisons=comparisons,
        complete_matched_settings=sum(v['complete'] for v in comparisons),expected_matched_settings=len(comparisons),
        available_primaries=sum(v['primary'] is not None for v in primaries),expected_primaries=len(primaries),
        independent_recordings=1,confidence_calibrated=False,scientific_decision='abstain')


def inspect(root,prefix='data/esa-observed-development-pilot-20261023'):
    import gzip
    import io
    import json
    from pathlib import Path
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import digest,encoded
    # Reject an unfinished study before importing numerical components.
    study=ClosedStudy(root,prefix)
    try:
        import numpy as np
        from lll.airquantumgrav_observation_report import native_accounting
        from lll.airquantumgrav_scoring import receiver_errors,sections
        for filename in ('airquantumgrav_scoring.py','airquantumgrav_geographic_report.py',
                'ilvis0_prediction_observed.py','models.py'):
            name='analysis/lll/'+filename
            if digest((Path(root)/name).read_bytes())!=study.manifest['sources'][name]:
                raise ValueError('restore the frozen scoring dependencies before reporting')
        from lll.ilvis0_control_shards import runtime_environment
        r=study.input('recipe');layout=study.input('layout');query=study.input('query-layout');weights=study.input('working-errors')
        group=study.input('context')['group_id'];env=study.input('qualification-environment')
        audit_environment=runtime_environment();verify_audit_environment(env,audit_environment)
        training=json.loads(gzip.decompress(study.input('training',raw=True)))
        scoring=json.loads(gzip.decompress(study.input('scoring',raw=True)));cut=layout['training_epochs'];times=query['times_s']
        if (len(study.tasks)!=24 or len(times)!=1200 or cut!=800 or len(training)!=cut or len(scoring)!=len(times)
                or encoded(training)!=encoded(scoring[:cut])
                or not np.array_equal(np.array([v['time_s'] for v in scoring])-query['time_origin_gps_sow_s'],np.array(times))):
            raise ValueError('complete fixed twenty-minute earlier/later inputs required')
        with np.load(io.BytesIO(study.input('interval',raw=True)),allow_pickle=False) as archive:
            arrays={k:archive[k] for k in ('theta','dv','dt')}
        n=layout['native_packets'];prefix_packets=layout['training_prefix_packets']
        if (n!=360028 or arrays['theta'].shape!=(n,3) or arrays['dv'].shape!=(n,3) or arrays['dt'].shape!=(n,)
                or any(v.dtype!=np.dtype('float64') or not np.all(np.isfinite(v)) for v in arrays.values())
                or np.any(arrays['dt']<=0) or np.any(arrays['dt']>r['maximum_interval_s'])
                or prefix_packets!=int(np.searchsorted(np.cumsum(arrays['dt']),times[cut-1]+r['limits']['time_offset'],side='left'))+1):
            raise ValueError('unchanged raw input arrays and exact training prefix required')
        prefix_hashes={k:digest(v[:prefix_packets].astype('<f8',copy=False).tobytes()) for k,v in arrays.items()}
        gps=np.array([[math.radians(row['latitude_deg']),math.radians(row['longitude_deg']),row['height_m']] for row in scoring])
        native={}
        for shard in range(study.manifest['allocation']['workers']):
            assigned={identity for identity,task in study.tasks.items() if task['shard']==shard}
            native.update(native_accounting(study.read(f'shards/{shard:03d}/charges/journal.sqlite',raw=True),
                study.completion['manifest_sha256'],assigned,per_call_visits=None))
        rows=[];errors_by_id={};binaries={'value':set(),'tangent':set()};summed={k:0 for k in study.summary['charged']}
        for identity,task in study.tasks.items():
            spec=task['payload'];operations=native[identity]
            if identity not in study.rows:
                rows.append(dict(identity=identity,**spec,complete=False,passed=False,converged=False,
                    returned=False,reason='No returned fit',charged_native_calls=operations['tangent']))
                continue
            envelope=study.envelope(identity);result=envelope['result'];artifacts=envelope['artifacts']
            for name,sha in artifacts.items():study.read(name,sha,raw=True)
            for key in summed:summed[key]+=envelope['charged'][key]
            if (operations['value'] or operations['tangent']!=envelope['charged']['native_calls']
                    or operations['packet_visits']!=envelope['charged']['packet_visits']):
                raise ValueError('saved native kinds and envelope charges differ')
            complete='converged' in result
            row=dict(result,**spec,identity=identity,complete=complete,returned=True,
                charged_native_calls=operations['tangent'],reason=result.get('error',result.get('reason')))
            active=[name+'_'+axis for name in ('attitude','velocity','position','gyro_bias','accel_bias','gyro_gain','accel_gain','lever')
                for axis in 'xyz']+['gravity_delta','time_offset']+(['earth_removal'] if spec['profile'] else [])
            if complete:
                if any(result[k]!=v for k,v in spec.items()):raise ValueError('result identity differs from its frozen task')
                fit=study.artifact(identity,'fit.json');forecast=study.artifact(identity,'forecast.json')
                earlier=study.artifact(identity,'training-observations.json');saved=study.artifact(identity,'scores.json')
                binding=study.artifact(identity,'input-binding.json');compilation=study.artifact(identity,'compilation.json')
                configuration=weights[spec['policy_id']]['configuration'];calls=fit['evaluations']+1
                visits=fit['evaluations']*prefix_packets*cut+n*len(times)
                if (fit['active_parameters']!=active or forecast['active_parameters']!=active
                        or len(fit['normalized_parameters'])!=len(active)
                        or any(not math.isfinite(v) or abs(v)>1 for v in fit['normalized_parameters'])
                        or type(fit['evaluations']) is not int or not 1<=fit['evaluations']<=r['maximum_evaluations']
                        or fit['evaluations']!=result['evaluations'] or calls!=result['native_calls']
                        or calls!=operations['tangent'] or visits!=operations['packet_visits']
                        or result['passed']!=bool(fit['converged']) or result['converged']!=fit['converged']
                        or not result['all_columns_retained'] or fit['residual_sum_squares']!=result['training_cost']
                        or not math.isfinite(result['training_cost']) or result['training_cost']<0):
                    raise ValueError('saved fit, columns, bounds or exact native work differs')
                if (earlier['training_epochs']!=cut or earlier['prediction_epochs']!=len(times)-cut
                        or earlier['times_s']!=times[:cut] or earlier['coordinates']!=gps[:cut].tolist()
                        or earlier['native_prefix_packets']!=prefix_packets or earlier['training_prefix_sha256']!=prefix_hashes
                        or earlier['weight_configuration']!=configuration or result['weight_configuration']!=configuration
                        or earlier['weight_descriptor']!=weights[spec['policy_id']]['descriptor']
                        or earlier['weight_source_sha256']!=weights[spec['policy_id']]['training_source_sha256']
                        or earlier['time_origin_gps_sow_s']!=query['time_origin_gps_sow_s']
                        or earlier['prediction_receiver_positions_used'] or earlier['true_initial_state_supplied'] or earlier['true_calibration_supplied']
                        or forecast['times_s']!=times or forecast['training_epochs']!=cut or forecast['prediction_epochs']!=len(times)-cut
                        or not forecast['continuous_propagation_without_gps_reset'] or forecast['prediction_receiver_positions_used']
                        or not result['forecast_saved_before_scoring'] or result['training_epochs']!=cut or result['prediction_epochs']!=len(times)-cut
                        or result['group_id']!=group or binding['group_id']!=group or binding['layout']!=layout
                        or binding['input_sha256']!={k:v['sha256'] for k,v in study.manifest['inputs'].items()}
                        or binding['original_reads'] or binding['protected_reads'] or result['original_reads'] or result['protected_reads']):
                    raise ValueError('exact earlier-only training, source identity or saved-forecast boundary differs')
                physical=receiver_errors(forecast['coordinates'],gps);recomputed=sections(physical,cut)
                if (saved['times_s']!=times or saved['receiver_coordinates']!=gps.tolist()
                        or not np.array_equal(np.array(saved['errors_neu_m']),physical)
                        or saved['prediction_receiver_positions_used_in_training']
                        or any(encoded(saved[name])!=encoded(value) or encoded(result[name])!=encoded(value) for name,value in recomputed.items())
                        or result['accuracy_all_sections']!=all(v['accuracy']['passed'] for v in recomputed.values())):
                    raise ValueError('reconstructed physical errors, summaries or accuracy labels differ')
                errors_by_id[identity]=physical[cut:].tolist();row['stop_reason']=fit.get('termination',fit.get('message'))
                row['normalized_parameters']=dict(zip(active,fit['normalized_parameters'],strict=True))
                row['last_training_cost']=fit['residual_sum_squares'];row['fit_saved']=True
                row['training_fit_converged']=fit['converged']
                for kind,filename,compiler in [('value','ilvis0_native.c','cc'),('tangent','ilvis0_tangent.cpp','c++')]:
                    meta=compilation[kind]
                    if meta['source_sha256']!=study.manifest['sources']['analysis/lll/'+filename] or meta['compiler']!=env['compilers'][compiler]:
                        raise ValueError('compiled source or compiler differs from qualification')
                    binaries[kind].add(meta['binary_sha256'])
            else:
                if result['passed']:raise ValueError('unfinished forecast cannot pass')
                row.setdefault('converged',False)
                fit_path='artifacts/'+identity+'/fit.json';row['fit_saved']=fit_path in artifacts
                if row['fit_saved']:
                    partial=study.read(fit_path,artifacts[fit_path])
                    if (partial['active_parameters']!=active or len(partial['normalized_parameters'])!=len(active)
                            or any(not math.isfinite(v) or abs(v)>1 for v in partial['normalized_parameters'])
                            or not math.isfinite(partial['residual_sum_squares']) or partial['residual_sum_squares']<0
                            or type(partial['evaluations']) is not int or not 1<=partial['evaluations']<=r['maximum_evaluations']
                            or not partial['evaluations']<=operations['tangent']<=partial['evaluations']+1):
                        raise ValueError('saved training fit without full forecast has inconsistent bounds or charges')
                    row.update(last_training_cost=partial['residual_sum_squares'],training_cost=partial['residual_sum_squares'],
                        training_fit_converged=partial['converged'],stop_reason=partial.get('termination',partial.get('message')),
                        fit_converged_but_prediction_incomplete=partial['converged'])
            rows.append(row)
        if (summed!=study.summary['charged'] or sum(v['tangent'] for v in native.values())!=study.summary['charged']['native_calls']
                or any(len(v)>1 for v in binaries.values())):raise ValueError('whole-study charges or compiled binaries differ')
        summary=summarize_starts(rows,r);sensitivity=[]
        for primary in summary['primaries']:
            pair=sorted([v for v in rows if all(v[k]==primary[k] for k in ('model','profile','policy_id'))],key=lambda v:v['start'])
            item=dict(model=primary['model'],profile=primary['profile'],policy_id=primary['policy_id'],available=False,
                calibrated_confidence_interval=False)
            if len(pair)==2 and all(v['identity'] in errors_by_id for v in pair):
                a,b=(errors_by_id[v['identity']] for v in pair);delta=[[x-y for x,y in zip(u,v,strict=True)] for u,v in zip(a,b,strict=True)]
                item.update(available=True,rms_neu_m=[math.sqrt(math.fsum(v[j]**2 for v in delta)/len(delta)) for j in range(3)],
                    maximum_absolute_neu_m=[max(abs(v[j]) for v in delta) for j in range(3)],
                    both_numerically_converged=all(v.get('converged',False) for v in pair))
            sensitivity.append(item)
        return dict(**summary,verified=True,total=24,returned=len(study.rows),numerically_converged=sum(v.get('passed',False) for v in rows),
            complete_predictions=sum(v['complete'] for v in rows),rows=rows,start_sensitivity=sensitivity,
            charged=study.summary['charged'],elapsed_s=study.summary['elapsed_s'],
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            primary_selector_source_sha256=digest((Path(root)/'analysis/lll/ilvis0_forecast_publication.py').read_bytes()),
            audit_environment=audit_environment,
            source=study.input('verified-preparation'),group_id=group,calibration_limits=r['limits'],original_reads=0,protected_reads=0,
            observed_starts_during_audit=0,native_calls_during_audit=0)
    finally:study.close()


def render(report):
    labels=dict(sphere_rotating='Globe + specified field',sphere_still='Globe + zero field',flat_still='Tested disc')
    source=report['source'];lines=['# ESA: predicting the later flight','',
        f"**{report['numerically_converged']}/{report['total']} starts supplied qualified fits and complete forecasts; "
        f"{report['complete_matched_settings']}/{report['expected_matched_settings']} matched comparisons are complete.**",'',
        'Every setting needs qualified predictions from all three candidates. A',
        'missing fit leaves that comparison unresolved; it does not support either',
        'geometry. The tables retain every start and physical-accuracy failure.','',
        f"The one selected interval lasts {source['duration_s']/60:.1f} minutes, averages "
        f"{source['mean_query_speed_kmh']:.1f} km/h near {source['mean_query_latitude_deg']:.2f}° N, "
        f"and contains {source['raw_points']:,} original IMU samples.",
        'An IMU is an inertial measurement unit containing gyroscopes and accelerometers.',
        'Earlier 800 receiver positions train calibration; later 400 check a',
        'continuous IMU forecast. They do not adjust its calibration or path.','',
        '| Working errors | Removal case | Candidate | Selected start | Later horizontal RMS | Later height RMS | Prediction accuracy |',
        '|---|---|---|---:|---:|---:|---|']
    for group in report['primaries']:
        row=group['primary'];policy='Short memory' if group['policy_id']=='reported-short-v1' else 'Persistent'
        fields=[policy,'Profiled' if group['profile'] else 'Zero',labels[group['model']]]
        if row is None:
            chosen=group['selected_training_start']
            fields += [str(chosen) if chosen is not None else '—','Unavailable','Unavailable',
                'Selected training start failed prediction' if chosen is not None else 'No qualified training fit']
        else:
            p=row['prediction'];fields += [str(row['start']),f"{p['horizontal_rms_m']:.6g} m",f"{p['vertical_rms_m']:.6g} m",
                'Passed' if p['accuracy']['passed'] else 'Failed']
        lines.append('| '+' | '.join(fields)+' |')
    lines+=['','RMS describes a typical error size. Height matters alongside horizontal',
        'position. Selection uses converged training cost alone, even when another',
        'start has a smaller later error. If the selected training fit cannot',
        'produce a complete forecast, the comparison retains that failure rather',
        'than switching starts. Both starts remain in the full CSV.','',
        '| Working errors | Removal case | Lower-error shape family | Preferred model passes training and prediction accuracy | Field comparison |',
        '|---|---|---|---|---|']
    for case in report['comparisons']:
        policy='Short memory' if case['policy_id']=='reported-short-v1' else 'Persistent'
        family={'globe':'Globe','disc':'Tested disc','tie':'Tie',None:'Incomplete numerical comparison'}[case['shape_lower_error_family']]
        accuracy='Yes' if case['preferred_accuracy'] else 'No' if case['complete'] else 'Unavailable'
        field={'specified_field':'Specified field has lower error','zero_field':'Zero field has lower error','tie':'Tie',None:'Not assessed'}[case['field_lower_error_model']]
        lines.append(f"| {policy} | {'Profiled' if case['profile'] else 'Zero'} | {family} | {accuracy} | {field} |")
    lines+=['','These are descriptive comparisons of later total three-dimensional RMS,',
        'not calibrated likelihood tests. The shape stage compares the better globe',
        'candidate with the disc. Field ranking follows only a complete globe',
        'preference whose selected model passes physical accuracy in both sections.','',
        'Accuracy requires horizontal RMS ≤10 m, height RMS ≤30 m, maximum horizontal',
        'error ≤50 m and maximum absolute height error ≤150 m. A preferred but inaccurate',
        'model is not an adequate flight reconstruction. Numerical convergence, physical',
        'accuracy and calibrated confidence are separate.','',
        f"The run used {report['charged']['native_calls']:,} native calculations in {report['elapsed_s']/3600:.2f} hours.",
        'The saved-data audit verifies source and input hashes, exact earlier/later',
        'boundaries, every calibration column, repeated source inputs, compiled kernels,',
        'physical errors and all charges. It performs no fit or propagation.','',
        'The 24 starts and four matched settings reuse one development recording.',
        'They are not independent replications. Both receiver-error cases are working',
        'assumptions; rate sampling and upstream processing remain explicitly modeled',
        'assumptions. No confidence level, field cause or solar-versus-sidereal rate',
        'distinction is established here. Seven confirmation groups stay protected,',
        'and the original NASA findings remain unchanged.','',
        '[Every start and its errors](fits.csv) · [Matched comparisons](comparisons.csv) · '
        '[Frozen fitting plan](FIT_PLAN.md) · [Prepared interval](../esa-development-pilot-preparation/README.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md)']
    return '\n'.join(lines)+'\n'


def csv_tables(report):
    import csv
    import io
    def encode(rows,fields):
        stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
        return stream.getvalue().encode()
    selected={group['training_primary']['identity'] for group in report['primaries'] if group['training_primary'] is not None}
    fields=('identity','group_id','model','profile','policy_id','start','returned','complete','converged','training_fit_converged','selected_primary',
        'stop_reason','failure_reason','last_training_cost','charged_native_calls','training_horizontal_rms_m','training_vertical_rms_m',
        'training_total_rms_m','prediction_horizontal_rms_m','prediction_vertical_rms_m','prediction_total_rms_m',
        'prediction_maximum_horizontal_m','prediction_maximum_absolute_up_m','training_accuracy','prediction_accuracy',
        'duration_s','mean_ground_speed_kmh','mean_latitude_deg','imu_source_file','imu_source_sha256',
        'gyro_bias_x_dph','gyro_bias_y_dph','gyro_bias_z_dph','gyro_gain_x','gyro_gain_y','gyro_gain_z')
    rows=[];source=report['source'];reference=source['source_references']['imu']
    for row in report['rows']:
        item={k:row.get(k) for k in ('identity','model','profile','policy_id','start','returned','complete','converged','charged_native_calls')}
        item.update(group_id=report['group_id'],selected_primary=row['identity'] in selected,
            training_fit_converged=row.get('training_fit_converged',row.get('converged',False)),failure_reason=row.get('reason'),
            stop_reason=row.get('stop_reason',row.get('reason')),last_training_cost=row.get('last_training_cost',row.get('training_cost')),
            duration_s=source['duration_s'],mean_ground_speed_kmh=source['mean_query_speed_kmh'],mean_latitude_deg=source['mean_query_latitude_deg'],
            imu_source_file=reference['filename'],imu_source_sha256=reference['sha256'])
        if row['complete']:
            for name in ('training','prediction'):
                for key in ('horizontal_rms_m','vertical_rms_m','total_rms_m'):item[name+'_'+key]=row[name][key]
                item[name+'_accuracy']=row[name]['accuracy']['passed']
            for key in ('maximum_horizontal_m','maximum_absolute_up_m'):item['prediction_'+key]=row['prediction'][key]
            for axis in 'xyz':
                key='gyro_bias_'+axis;item[key+'_dph']=math.degrees(row['normalized_parameters'][key]*report['calibration_limits'][key])*3600
                key='gyro_gain_'+axis;item[key]=row['normalized_parameters'][key]*report['calibration_limits'][key]
        rows.append(item)
    comparisons=[]
    for case in report['comparisons']:
        item={k:case[k] for k in ('profile','policy_id','complete','shape_lower_error_family','preferred_model','preferred_accuracy','field_lower_error_model')}
        item.update({model+'_prediction_total_rms_m':value for model,value in case.get('prediction_total_rms_m',{}).items()})
        comparisons.append(item)
    return {'fits.csv':encode(rows,fields),'comparisons.csv':encode(comparisons,
        ('profile','policy_id','complete','shape_lower_error_family','preferred_model','preferred_accuracy','field_lower_error_model',
         'sphere_rotating_prediction_total_rms_m','sphere_still_prediction_total_rms_m','flat_still_prediction_total_rms_m'))}


def publish(root,prefix='data/esa-observed-development-pilot-20261023',output='docs/esa-development-pilot'):
    import json
    from pathlib import Path
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic,digest,encoded,safe_path
    from lll.studies.closed import ClosedStudy
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('observed publication already sealed')
    report=inspect(root,prefix)
    # Preserve the existing methodology PLAN.md; the finite plan is FIT_PLAN.md.
    package(data,public,render(report));receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    study=ClosedStudy(root,prefix);prepared=ClosedStudy(root,'docs/esa-development-pilot-preparation')
    try:
        for name,expected in [('FIT_PLAN.md',study.manifest['sources']['docs/esa-development-pilot/FIT_PLAN.md']),
            ('PLAN.md',prepared.manifest['sources']['docs/esa-development-pilot/PLAN.md'])]:
            if digest((public/name).read_bytes())!=expected:raise ValueError('preserved public plan differs from its frozen source')
            receipt['artifacts'][name]=expected
    finally:study.close();prepared.close()
    selector=(root/'analysis/lll/ilvis0_forecast_publication.py').read_bytes()
    if digest(selector)!=report['primary_selector_source_sha256']:raise ValueError('selector changed during reporting')
    additions=[('artifacts/publication/verified-report.json',encoded(report)),
        ('artifacts/publication/reporter.py',Path(__file__).read_bytes()),
        ('artifacts/publication/source-freeze/analysis/lll/ilvis0_forecast_publication.py',selector),*csv_tables(report).items()]
    for name,raw in additions:atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,original_reads=0,native_calls=0)
