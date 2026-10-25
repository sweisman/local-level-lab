# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only audit of a separately frozen wider observed ESA comparison."""
import math


def verify_compilation(*,meta,raw,sources,environment,anchor):
    import re
    from lll.ilvis0_wide_tangent import derive,VERSION
    from lll.studies.artifacts import digest
    value,tangent=meta['value'],meta['tangent'];sha=sources['analysis/lll/ilvis0_tangent.cpp']
    if (digest(raw)!=sha or value['source_sha256']!=sources['analysis/lll/ilvis0_native.c']
            or value['compiler']!=environment['compilers']['cc'] or tangent['compiler']!=environment['compilers']['c++']
            or tangent['version']!=VERSION or tangent['original_source_sha256']!=sha
            or tangent['source_sha256']!=digest(derive(raw,expected_sha256=sha))
            or type(tangent['internal_mantissa_bits']) is not int or tangent['internal_mantissa_bits']<=53
            or tangent['packet_clock_changed'] is not False
            or tangent['residual_subtraction']!='before-binary64-cast'
            or tangent['flags']!=['-O2','-std=c++17','-fPIC','-shared']
            or any(tangent[k]!='binary64-frozen' for k in ('clock_dispatch','profile_mapping','query_fraction','parameter_products'))
            or any(v.get('gravity_model')!='inverse-square-height-v1' or v.get('gravity_anchor_height_m')!=anchor
                or not isinstance(v.get('binary_sha256'),str) or not re.fullmatch('[0-9a-f]{64}',v['binary_sha256'])
                for v in (value,tangent))):
        raise ValueError('compiled wider source, arithmetic, clock, gravity or provenance differs')
    return dict(value=value['binary_sha256'],tangent=tangent['binary_sha256'])


def inspect(root,prefix='data/esa-observed-wide-pilot-20261024'):
    from lll.studies.closed import ClosedStudy
    study=ClosedStudy(root,prefix)  # Reject unfinished data before numerical imports.
    try:
        import gzip
        import io
        import json
        from pathlib import Path
        import numpy as np
        from lll.airquantumgrav_observed_wide import recipe,tasks,qualification_sources,SCOPE,UNCHANGED_INPUTS,require_qualification
        from lll.airquantumgrav_inventory import environment,METADATA,validate_context
        from lll.airquantumgrav_observed_height import verify_baseline
        from lll.airquantumgrav_observed_height_report import verify_gravity,matched_changes
        from lll.airquantumgrav_observed_report import verify_audit_environment,summarize_starts
        from lll.airquantumgrav_observation_report import native_accounting
        from lll.airquantumgrav_scoring import receiver_errors,sections
        from lll.ilvis0_wide_observed import bind,SOURCES
        from lll.prediction_audit import complete_prediction,training_fit,start_sensitivity
        from lll.studies.artifacts import digest,encoded
        from lll.studies.source_binding import verify
        root=Path(root).resolve();r=study.input('recipe');env=study.input('qualification-environment')
        audit_environment=environment();verify_audit_environment(env,audit_environment)
        declared=study.input('qualification-request')['sources']
        if set(declared)!=set(qualification_sources(root)):raise ValueError('qualified source enumeration changed')
        verify(root,declared=declared,manifest=study.manifest['sources'])
        layout=study.input('layout');query=study.input('query-layout')
        if (r!=recipe(maximum_wall_s=r['maximum_wall_s']) or study.manifest['scope']!=SCOPE
                or {k:{a:b for a,b in v.items() if a not in ('index','shard')} for k,v in study.tasks.items()}
                !={t['identity']:t for t in tasks(layout)}):raise ValueError('unchanged finite observed revision required')
        require_qualification(study.input('qualified-controls'))
        parent=ClosedStudy(root,'docs/esa-wide-training-controls')
        try:
            receipt=parent.read('evidence-receipt.json');name='artifacts/publication/verified-report.json'
            controls=parent.read(name,receipt['artifacts'][name]);require_qualification(controls)
            if (study.input('qualified-controls')!=controls or study.input('qualified-parent')!=dict(
                    manifest_sha256=parent.completion['manifest_sha256'],summary_sha256=parent.completion['summary_sha256'],
                    report_sha256=receipt['artifacts'][name])):raise ValueError('qualified training parent binding differs')
        finally:parent.close()
        baseline=ClosedStudy(root,'docs/esa-observed-height-pilot')
        try:
            receipt=baseline.read('evidence-receipt.json');name='artifacts/publication/verified-report.json'
            old=baseline.read(name,receipt['artifacts'][name])
            selector=digest((root/'analysis/lll/ilvis0_forecast_publication.py').read_bytes())
            verify_baseline(old,baseline.completion,selector_sha256=selector)
            baseline_binding=dict(manifest_sha256=baseline.completion['manifest_sha256'],
                summary_sha256=baseline.completion['summary_sha256'],report_sha256=receipt['artifacts'][name],
                unchanged_input_sha256={key:baseline.manifest['inputs'][key]['sha256'] for key in UNCHANGED_INPUTS})
            if (study.input('baseline-binding')!=baseline_binding or baseline_binding['unchanged_input_sha256']
                    !={key:study.manifest['inputs'][key]['sha256'] for key in UNCHANGED_INPUTS}):
                raise ValueError('original measurements or earlier/later split changed')
        finally:baseline.close()
        calculate,protocol=bind(expected_sources={n:study.manifest['sources']['analysis/lll/'+n] for n in SOURCES})
        if protocol!=study.input('protocol-binding'):raise ValueError('explicit precision substitution differs')
        group=validate_context(**{key:study.input(key) for key in METADATA})
        if group!=study.input('context'):raise ValueError('development membership changed')
        training=json.loads(gzip.decompress(study.input('training',raw=True)))
        scoring=json.loads(gzip.decompress(study.input('scoring',raw=True)))
        times=query['times_s'];cut=layout['training_epochs'];weights=study.input('working-errors')
        if (len(times)!=1200 or cut!=800 or len(training)!=cut or len(scoring)!=len(times)
                or query['training_epochs']!=cut or query['prediction_epochs']!=400
                or encoded(training)!=encoded(scoring[:cut])
                or not np.array_equal(np.array([v['time_s'] for v in scoring])-query['time_origin_gps_sow_s'],np.array(times))):
            raise ValueError('complete fixed earlier/later observations required')
        with np.load(io.BytesIO(study.input('interval',raw=True)),allow_pickle=False) as archive:
            arrays={k:archive[k] for k in ('theta','dv','dt')}
        n=layout['native_packets'];prefix_packets=layout['training_prefix_packets']
        if (n!=360028 or arrays['theta'].shape!=(n,3) or arrays['dv'].shape!=(n,3) or arrays['dt'].shape!=(n,)
                or any(v.dtype!=np.dtype('float64') or not np.all(np.isfinite(v)) for v in arrays.values())
                or np.any(arrays['dt']<=0) or np.any(arrays['dt']>r['maximum_interval_s'])
                or prefix_packets!=int(np.searchsorted(np.cumsum(arrays['dt']),times[cut-1]+r['limits']['time_offset'],side='left'))+1):
            raise ValueError('complete unchanged raw arrays and training prefix required')
        hashes={k:digest(v[:prefix_packets].astype('<f8',copy=False).tobytes()) for k,v in arrays.items()}
        gps=np.array([[math.radians(v['latitude_deg']),math.radians(v['longitude_deg']),v['height_m']] for v in scoring])
        anchor=training[0]['height_m'];native={}
        for shard in range(study.manifest['allocation']['workers']):
            native.update(native_accounting(study.read(f'shards/{shard:03d}/charges/journal.sqlite',raw=True),
                study.completion['manifest_sha256'],{k for k,v in study.tasks.items() if v['shard']==shard},per_call_visits=None))
        rows=[];errors_by_id={};binaries={'value':set(),'tangent':set()};charged={k:0 for k in study.summary['charged']}
        source='analysis/lll/ilvis0_tangent.cpp';raw=study.read('source-freeze/'+source,study.manifest['sources'][source],raw=True)
        for identity,task in study.tasks.items():
            spec=task['payload'];operations=native[identity]
            if identity not in study.rows:
                rows.append(dict(identity=identity,**spec,complete=False,passed=False,converged=False,
                    returned=False,reason='No returned fit',charged_native_calls=operations['tangent']))
                continue
            envelope=study.envelope(identity);result=envelope['result'];artifacts=envelope['artifacts']
            for name,sha in artifacts.items():study.read(name,sha,raw=True)
            for key in charged:charged[key]+=envelope['charged'][key]
            if (operations['value'] or operations['tangent']!=envelope['charged']['native_calls']
                    or operations['packet_visits']!=envelope['charged']['packet_visits']):raise ValueError('native kinds or charges differ')
            complete='converged' in result
            row=dict(result,**spec,identity=identity,complete=complete,returned=True,
                charged_native_calls=operations['tangent'],reason=result.get('error',result.get('reason')))
            active=[name+'_'+axis for name in ('attitude','velocity','position','gyro_bias','accel_bias','gyro_gain','accel_gain','lever')
                for axis in 'xyz']+['gravity_delta','time_offset']+(['earth_removal'] if spec['profile'] else [])
            if complete:
                if study.artifact(identity,'protocol-binding.json')!=protocol:raise ValueError('case precision substitution differs')
                fit=study.artifact(identity,'fit.json');forecast=study.artifact(identity,'forecast.json')
                earlier=study.artifact(identity,'training-observations.json');saved=study.artifact(identity,'scores.json')
                binding=study.artifact(identity,'input-binding.json');compilation=study.artifact(identity,'compilation.json')
                weight=weights[spec['policy_id']]
                expected=dict(active=active,maximum_evaluations=r['maximum_evaluations'],times=times,cut=cut,
                    training_coordinates=gps[:cut].tolist(),prefix_packets=prefix_packets,prefix_sha256=hashes,
                    configuration=weight['configuration'],descriptor=weight['descriptor'],weight_sha256=weight['training_source_sha256'],
                    time_origin_s=query['time_origin_gps_sow_s'],group=group['group_id'],layout=layout,
                    input_sha256={k:v['sha256'] for k,v in study.manifest['inputs'].items()},
                    packet_visits=fit['evaluations']*prefix_packets*cut+n*len(times))
                row.update(complete_prediction(spec=spec,result=result,fit=fit,forecast=forecast,earlier=earlier,
                    binding=binding,operations=operations,expected=expected))
                physical=receiver_errors(forecast['coordinates'],gps);scores=sections(physical,cut)
                if (saved['times_s']!=times or saved['receiver_coordinates']!=gps.tolist()
                        or not np.array_equal(np.array(saved['errors_neu_m']),physical)
                        or saved['prediction_receiver_positions_used_in_training']
                        or any(encoded(saved[k])!=encoded(v) or encoded(result[k])!=encoded(v) for k,v in scores.items())
                        or result['accuracy_all_sections']!=all(v['accuracy']['passed'] for v in scores.values())):
                    raise ValueError('saved physical errors, summaries or adequacy labels differ')
                errors_by_id[identity]=physical[cut:].tolist()
                if any(result[k]!=v for k,v in dict(gravity_model=r['gravity_model'],gravity_anchor_height_m=anchor,
                        gravity_anchor_source=r['gravity_anchor_source']).items()):raise ValueError('result gravity differs')
            else:
                if result['passed']:raise ValueError('unfinished forecast cannot pass')
                row.setdefault('converged',False);name='artifacts/'+identity+'/fit.json';row['fit_saved']=name in artifacts
                if row['fit_saved']:
                    fit=study.read(name,artifacts[name]);row.update(training_fit(fit,active=active,maximum_evaluations=r['maximum_evaluations']))
                    if not fit['evaluations']<=operations['tangent']<=fit['evaluations']+1:raise ValueError('incomplete forecast charges differ')
                    row['training_cost']=fit['residual_sum_squares'];row['fit_converged_but_prediction_incomplete']=fit['converged']
            cm='artifacts/'+identity+'/compilation.json'
            if cm in artifacts:
                compilation=study.read(cm,artifacts[cm])
                verify_gravity(study.artifact(identity,'gravity-binding.json'),compilation,anchor=anchor)
                binary=verify_compilation(meta=compilation,raw=raw,sources=study.manifest['sources'],environment=env,anchor=anchor)
                for kind,sha in binary.items():binaries[kind].add(sha)
            rows.append(row)
        if (charged!=study.summary['charged'] or sum(v['tangent'] for v in native.values())!=charged['native_calls']
                or any(len(v)>1 for v in binaries.values())):raise ValueError('whole-study charges or binaries differ')
        summary=summarize_starts(rows,r)
        report=dict(**summary,verified=True,total=24,returned=len(study.rows),numerically_converged=sum(v['passed'] for v in rows),
            complete_predictions=sum(v['complete'] for v in rows),rows=rows,start_sensitivity=start_sensitivity(rows,errors_by_id),
            charged=charged,elapsed_s=study.summary['elapsed_s'],
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            primary_selector_source_sha256=selector,audit_environment=audit_environment,
            source=study.input('verified-preparation'),group_id=group['group_id'],calibration_limits=r['limits'],
            gravity_model=r['gravity_model'],gravity_anchor_height_m=anchor,baseline_binding=baseline_binding,
            original_measurements_and_split_unchanged=True,original_reads=0,protected_reads=0,
            observed_starts_during_audit=0,native_calls_during_audit=0)
        report['matched_baseline_changes']=matched_changes(report,old)
        return report
    finally:study.close()


def render(report):
    from lll.airquantumgrav_observed_report import render as original
    text=original(report).replace('# ESA: predicting the later flight','# ESA: wider-precision prediction',1)
    explanation=('The original measurements, earlier/later split, height-gravity law,\n'
        'calibration bounds, starts, stopping checks and accuracy limits are unchanged.\n'
        'Only the explicitly qualified numerical calculation uses wider precision.\n'
        'Every failed fit remains visible; earlier failed results are not relabeled.\n\n')
    return text.replace('\n\n','\n\n'+explanation,1).replace('[Frozen fitting plan](FIT_PLAN.md)','[Frozen fitting plan](PLAN.md)')


def publish(root,prefix='data/esa-observed-wide-pilot-20261024',output='docs/esa-observed-wide-pilot'):
    import csv
    import io
    import json
    from pathlib import Path
    from lll.airquantumgrav_observed_report import csv_tables
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import safe_path,atomic,digest,encoded
    from lll.studies.closed import ClosedStudy
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();public=safe_path(root,output);data=safe_path(root,prefix)
    if (public/'evidence-receipt.json').exists():raise ValueError('wider observed publication already sealed')
    report=inspect(root,prefix)
    study=ClosedStudy(root,prefix)
    try:plan_hash=study.manifest['sources']['docs/esa-observed-wide-pilot/PLAN.md']
    finally:study.close()
    if digest((public/'PLAN.md').read_bytes())!=plan_hash:raise ValueError('preserved plan differs')
    package(data,public,render(report));receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    stream=io.StringIO(newline='');rows=report['matched_baseline_changes']
    writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    receipt['artifacts']['PLAN.md']=plan_hash
    for name,raw in [('artifacts/publication/verified-report.json',encoded(report)),
            ('artifacts/publication/reporter.py',Path(__file__).read_bytes()),
            ('baseline-changes.csv',stream.getvalue().encode()),*csv_tables(report).items()]:
        atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,original_reads=0,native_calls=0)
