# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-array verification for fit-free ESA stopping-resolution probes."""


def verify_sweeps(fit,probe,arrays,*,physical_step):
    import math
    import numpy as np
    from lll.stopping_resolution import FRACTIONS,MAXIMUM_SWEEPS
    from lll.ilvis0_solver_position import verify_stability
    from lll.ilvis0_solver_refinement import projected_stationarity
    from lll.studies.artifacts import encoded
    active=fit['active_parameters'];point=np.asarray(fit['normalized_parameters'],float)
    count=MAXIMUM_SWEEPS if probe['correction_available'] else 2;epochs=probe['epoch_count']
    if (len(arrays)!=count or len(probe['sweeps'])!=count or probe['native_calls']!=count
            or probe['active_parameters']!=active or len(active) not in (26,27) or len(set(active))!=len(active)
            or point.shape!=(len(active),) or not np.all(np.isfinite(point)) or np.any(abs(point)>1)
            or probe['saved_converged']!=fit['converged'] or probe['saved_cost']!=fit['residual_sum_squares']
            or probe['labels_changed'] or probe['optimizer_starts'] or not probe['all_columns_retained']
            or not probe['passed'] or probe['scientific_decision']!='abstain'
            or probe['packet_query_visits']!=count*probe['packet_count']*epochs):
        raise ValueError('unchanged complete source point, columns, labels and finite protocol required')
    for a in arrays:
        if (set(a)!= {'point','residual','jacobian','position_delta_neu_m'}
                or a['point'].shape!=point.shape or a['residual'].shape!=(3*epochs,)
                or a['jacobian'].shape!=(3*epochs,len(point)) or a['position_delta_neu_m'].shape!=(epochs,3)
                or any(v.dtype!=np.dtype('float64') or not np.all(np.isfinite(v)) for v in a.values())
                or np.any(abs(a['point'])>1)):raise ValueError('finite feasible complete saved sweep required')
    if any(not np.array_equal(a['point'],point) for a in arrays[:2]):raise ValueError('both baselines must reuse the exact saved point')
    first,second=arrays[:2];r0,j0=first['residual'],first['jacobian'];base=float(r0@r0)
    direction=arrays[2]['point']-point if count==MAXIMUM_SWEEPS else None
    if (probe['residual_repeat_bitwise_equal']!=bool(np.array_equal(r0,second['residual']))
            or probe['derivative_repeat_bitwise_equal']!=bool(np.array_equal(j0,second['jacobian']))
            or probe['relative_saved_cost_difference']!=abs(base-fit['residual_sum_squares'])/max(base,fit['residual_sum_squares'],1.)
            or (direction is not None and not np.array_equal(direction,np.asarray(probe['normalized_correction'])))):
        raise ValueError('repeat or original-cost binding differs')
    fractions=[None,None]+([1.,*FRACTIONS] if direction is not None else [])
    for index,(a,row,fraction) in enumerate(zip(arrays,probe['sweeps'],fractions,strict=True)):
        if row['index']!=index or row['artifact']!=f'sweep-{index:02d}.npz' or row['fraction']!=fraction:
            raise ValueError('fixed sweep order required')
        requested=point+fraction*direction if index>=3 else None
        if requested is not None and not np.array_equal(a['point'],np.clip(requested,-1.,1.)):
            raise ValueError('saved probe leaves its frozen clipped correction')
        r,j,u=a['residual'],a['jacobian'],a['point'];predicted=r0+j0@(u-point)
        physical=np.asarray(physical_step(r-r0),float);cost=float(r@r);linear=float(predicted@predicted)
        expected=dict(cost=cost,linearized_cost=linear,relative_cost_change=abs(cost-base)/max(cost,base,1.),
            linearized_relative_cost_change=abs(linear-base)/max(linear,base,1.),
            linearization_error_norm=float(np.linalg.norm(r-predicted)),stationarity=projected_stationarity(u,r,j)[0],
            normalized_parameter_step=float(np.linalg.norm(u-point)),
            clipped=bool(requested is not None and not np.array_equal(u,requested)),
            position_rms_neu_m=np.sqrt(np.mean(physical*physical,axis=0)).tolist(),
            position_max_abs_neu_m=np.max(abs(physical),axis=0).tolist())
        if (not np.array_equal(a['position_delta_neu_m'],physical)
                or any(encoded(row[k])!=encoded(v) for k,v in expected.items())
                or not isinstance(row['packet_boundary_epochs'],int) or not 0<=row['packet_boundary_epochs']<=epochs
                or not all(math.isfinite(row[k]) for k in ('cost','stationarity','linearized_cost','linearization_error_norm'))):
            raise ValueError('saved probe metrics or physical differences do not reproduce')
    called=[]
    def fresh(u,fresh=False):
        if not fresh or count!=MAXIMUM_SWEEPS or called or not np.array_equal(u,arrays[2]['point']):
            raise ValueError('unchanged bounded correction does not reproduce')
        called.append(True);a=arrays[2]
        return a['residual'],a['jacobian'],probe['sweeps'][2]['packet_boundary_epochs']
    shared=verify_stability(point,r0,j0,fresh,physical_step)
    if encoded(shared)!=encoded(probe['shared_probe']) or bool(called)!=bool(probe['correction_available']):
        raise ValueError('saved original stopping check does not reproduce')
    return dict(native_calls=count,labels_changed=False,shared_probe=shared,
        residual_repeat_bitwise_equal=probe['residual_repeat_bitwise_equal'],
        derivative_repeat_bitwise_equal=probe['derivative_repeat_bitwise_equal'],
        relative_saved_cost_difference=probe['relative_saved_cost_difference'],
        maximum_relative_cost_change=max(v['relative_cost_change'] for v in probe['sweeps']),
        maximum_linearization_error_norm=max(v['linearization_error_norm'] for v in probe['sweeps']),
        maximum_position_change_m=max(max(v['position_max_abs_neu_m']) for v in probe['sweeps']))


def inspect(root,prefix='data/esa-stopping-resolution-20261024'):
    import gzip
    import io
    import json
    import math
    from pathlib import Path
    from types import SimpleNamespace
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import digest,encoded
    study=ClosedStudy(root,prefix)
    try:
        import numpy as np
        from lll.airquantumgrav_resolution import recipe,tasks,qualification_sources,PARENT,SCOPE,MEASUREMENT_KEYS,METADATA,validate_context,environment
        from lll.airquantumgrav_observed_report import verify_audit_environment
        from lll.airquantumgrav_error_policy import build
        from lll.airquantumgrav_observation_report import native_accounting
        from lll.ilvis0_solver_position import physical_residual_step
        from lll.stopping_diagnostics import frozen_policy,components
        if (study.input('recipe')!=recipe() or study.manifest['scope']!=SCOPE
                or {k:{key:value for key,value in v.items() if key not in ('index','shard')} for k,v in study.tasks.items()}
                !={v['identity']:v for v in tasks()}):raise ValueError('unchanged finite diagnostic definition required')
        current={name:digest((Path(root)/name).read_bytes()) for name in qualification_sources(root)}
        if current!=study.manifest['sources']:raise ValueError('restore frozen diagnostic dependencies before reporting')
        expected=set(MEASUREMENT_KEYS)|set(METADATA)|{'context','source-recipe','source-proof','recipe','qualification-environment',
            'qualification-request','qualification-report'}|{'point-'+k for k in study.tasks}
        if set(study.manifest['inputs'])!=expected:raise ValueError('explicit training-only input set required')
        env=study.input('qualification-environment');verify_audit_environment(env,environment())
        source_recipe=study.input('source-recipe');proof=study.input('source-proof')
        parent=ClosedStudy(root,PARENT)
        try:
            receipt=parent.read('evidence-receipt.json');key='artifacts/publication/verified-report.json'
            if (proof['parent_manifest_sha256']!=parent.completion['manifest_sha256']
                    or proof['parent_summary_sha256']!=parent.completion['summary_sha256']
                    or source_recipe!=parent.input('recipe') or proof['parent_training_sha256']!=parent.manifest['inputs']['training']['sha256']
                    or proof['verified_report_sha256']!=receipt['artifacts'][key]
                    or proof['parent_full_interval_sha256']!=parent.manifest['inputs']['interval']['sha256']
                    or proof['parent_source_recipe_sha256']!=parent.manifest['inputs']['recipe']['sha256']
                    or study.manifest['inputs']['source-recipe']['sha256']!=proof['parent_source_recipe_sha256']
                    or study.manifest['inputs']['training']['sha256']!=proof['parent_training_sha256']
                    or study.manifest['inputs']['working-errors']['sha256']!=parent.manifest['inputs']['working-errors']['sha256']):
                raise ValueError('unchanged closed source inputs and gravity model required')
            parent_query=parent.input('query-layout');expected_layout=dict(times_s=parent_query['times_s'][:800],
                time_origin_gps_sow_s=parent_query['time_origin_gps_sow_s'])
            if study.input('layout')!=expected_layout:raise ValueError('original earlier query times and origin required')
            for identity in study.tasks:
                raw=parent.artifact(identity,'fit.json',raw=True)
                if (digest(raw)!=proof['point_sha256'][identity]
                        or study.input('point-'+identity,raw=True)!=raw
                        or parent.artifact(identity,'training-observations.json')['training_prefix_sha256']!=proof['prefix_sha256']):
                    raise ValueError('original fitted point or prefix changed')
        finally:parent.close()
        binding=validate_context(**{key:study.input(key) for key in METADATA})
        if binding!=study.input('context'):raise ValueError('explicit development membership required')
        layout=study.input('layout');training=json.loads(gzip.decompress(study.input('training',raw=True)))
        if len(training)!=800 or len(layout['times_s'])!=800:raise ValueError('earlier800 positions only required')
        with np.load(io.BytesIO(study.input('interval',raw=True)),allow_pickle=False) as a:
            raw_arrays={k:a[k] for k in a.files}
        if (set(raw_arrays)!= {'theta','dv','dt'} or raw_arrays['dt'].shape!=(239867,)
                or raw_arrays['theta'].shape!=(239867,3) or raw_arrays['dv'].shape!=(239867,3)
                or any(v.dtype!=np.dtype('float64') or not np.all(np.isfinite(v)) for v in raw_arrays.values())
                or np.any(raw_arrays['dt']<=0) or np.any(raw_arrays['dt']>source_recipe['maximum_interval_s'])
                or {k:digest(v.astype('<f8',copy=False).tobytes()) for k,v in raw_arrays.items()}!=proof['prefix_sha256']):
            raise ValueError('original finite complete training prefix required')
        ends=np.cumsum(raw_arrays['dt']);times=np.asarray(layout['times_s'])
        if int(np.searchsorted(ends,times[-1]+source_recipe['limits']['time_offset'],side='left'))+1!=len(ends):
            raise ValueError('exact training support required')
        raw_gps=np.array([[math.radians(v['latitude_deg']),math.radians(v['longitude_deg']),v['height_m']] for v in training])
        metrics={};weights=study.input('working-errors')
        for policy in recipe()['policies']:
            w=build(training,policy_id=policy)
            if (not np.array_equal(w.times-layout['time_origin_gps_sow_s'],times)
                    or w.configuration!=weights[policy]['configuration']):raise ValueError('unchanged earlier working covariance required')
            metrics[policy]=(w,SimpleNamespace(gps=raw_gps,cholesky=np.linalg.cholesky(w.dense(maximum_epochs=1024))))
        frozen=frozen_policy(*(study.read('source-freeze/analysis/lll/'+name,study.manifest['sources']['analysis/lll/'+name],raw=True)
            for name in ('ilvis0_solver_refinement.py','ilvis0_solver_position.py')))
        native={}
        for shard in range(study.manifest['allocation']['workers']):
            assigned={k for k,v in study.tasks.items() if v['shard']==shard}
            native.update(native_accounting(study.read(f'shards/{shard:03d}/charges/journal.sqlite',raw=True),
                study.completion['manifest_sha256'],assigned,per_call_visits=None))
        rows=[]
        for identity,task in study.tasks.items():
            row=dict(identity=identity,**task['payload'],complete=False)
            operations=native[identity]
            if operations['value'] or operations['packet_visits']!=operations['tangent']*239867*800:
                raise ValueError('exact tangent-only diagnostic charges required')
            if identity in study.rows:
                envelope=study.envelope(identity);result=envelope['result']
                if envelope['charged']['native_calls']!=operations['tangent']:raise ValueError('result charges differ')
                for name,sha in envelope['artifacts'].items():study.read(name,sha,raw=True)
                probe_path='artifacts/'+identity+'/probe.json'
                if probe_path in envelope['artifacts']:
                    p=study.artifact(identity,'probe.json');fit=study.input('point-'+identity)
                    values=[]
                    for record in p['sweeps']:
                        raw=study.artifact(identity,record['artifact'],raw=True)
                        if digest(raw)!=record['artifact_sha256']:raise ValueError('sweep artifact binding differs')
                        with np.load(io.BytesIO(raw),allow_pickle=False) as a:values.append({k:a[k] for k in a.files})
                    w,metric=metrics[task['payload']['policy_id']]
                    summary=verify_sweeps(fit,p,values,physical_step=lambda d:physical_residual_step(metric,d))
                    if (p['packet_count']!=239867 or p['epoch_count']!=800 or p['native_calls']!=operations['tangent']
                            or not result['raw_arrays_unchanged'] or result['original_reads'] or result['protected_reads']
                            or result['later_receiver_reads'] or result['group_id']!=binding['group_id']
                            or any(encoded(result[k])!=encoded(v) for k,v in p.items())):raise ValueError('diagnostic result differs from saved probe')
                    input_binding=study.artifact(identity,'input-binding.json');earlier=study.artifact(identity,'training-binding.json')
                    compilation=study.artifact(identity,'compilation.json');anchor=training[0]['height_m']
                    if (input_binding['input_sha256']!={k:v['sha256'] for k,v in study.manifest['inputs'].items()}
                            or input_binding['point_sha256']!=proof['point_sha256'][identity]
                            or input_binding['prefix_sha256']!=proof['prefix_sha256']
                            or earlier['prefix_sha256']!=proof['prefix_sha256'] or earlier['epochs']!=800 or earlier['packets']!=239867
                            or earlier['times_s']!=layout['times_s'] or earlier['training_rows_sha256']!=digest(encoded(training))
                            or earlier['gravity_anchor_height_m']!=anchor or earlier['gravity_anchor_source']!='first_training_receiver_height'
                            or earlier['later_positions_used'] or earlier['weight_configuration']!=w.configuration
                            or earlier['weight_source_sha256']!=w.source_sha256 or earlier['weight_descriptor']!=w.descriptor):
                        raise ValueError('earlier-only input or weight binding differs')
                    for kind,name,compiler in [('value','ilvis0_native.c','cc'),('tangent','ilvis0_tangent.cpp','c++')]:
                        meta=compilation[kind]
                        if (meta['source_sha256']!=study.manifest['sources']['analysis/lll/'+name] or meta['compiler']!=env['compilers'][compiler]
                                or meta.get('gravity_model')!='inverse-square-height-v1' or meta.get('gravity_anchor_height_m')!=anchor):
                            raise ValueError('compiled height-gravity variant differs')
                    row.update(summary,complete=True,source_converged=fit['converged'],source_cost=fit['residual_sum_squares'],
                        fresh_cost=p['sweeps'][0]['cost'],correction_available=p['correction_available'],
                        original_components=components(fit,frozen),
                        replay_components=components(dict(fit,stability_probe=p['shared_probe'],near_zero_probe=None),frozen))
                else:row['reason']=result.get('error',result.get('reason','unfinished diagnostic'))
            rows.append(row)
        if sum(v['tangent'] for v in native.values())!=study.summary['charged']['native_calls']:raise ValueError('whole-run charges differ')
        return dict(verified=True,total=24,complete=sum(v['complete'] for v in rows),rows=rows,
            charged=study.summary['charged'],elapsed_s=study.summary['elapsed_s'],
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            parent_manifest_sha256=proof['parent_manifest_sha256'],parent_summary_sha256=proof['parent_summary_sha256'],
            original_reads=0,protected_reads=0,optimizer_starts=0,native_calls_during_audit=0,
            labels_changed=False,confidence_calibrated=False,scientific_decision='abstain')
    finally:study.close()


def render(report):
    lines=['# Why the ESA stopping checks fail','',
        f"**{report['complete']}/{report['total']} fixed-point diagnostics completed and verified.**",'',
        'These are probes around the already saved calibrations, not new fits.',
        'Only the earlier 800 receiver observations and their IMU support are used.',
        'Every original convergence label and accuracy limit stays unchanged.','',
        '| Candidate | Removal case | Working errors | Source start | Original numerical pass | Fresh repeat identical | Replayed stopping checks |',
        '|---|---|---|---:|---|---|---|']
    labels=dict(sphere_rotating='Globe + field',sphere_still='Globe + zero field',flat_still='Disc')
    for row in report['rows']:
        prefix=[labels[row['model']],'Profiled' if row['profile'] else 'Zero',
            'Short memory' if row['policy_id']=='reported-short-v1' else 'Persistent',str(row['start'])]
        if not row['complete']:fields=prefix+['Unavailable','Unavailable','Incomplete diagnostic']
        else:
            replay=row['replay_components'];status=', '.join(replay['failed_components']) or 'All satisfied' if replay['available'] else 'Unavailable correction'
            fields=prefix+['Yes' if row['source_converged'] else 'No',
                'Yes' if row['residual_repeat_bitwise_equal'] and row['derivative_repeat_bitwise_equal'] else 'No',status]
        lines.append('| '+' | '.join(fields)+' |')
    lines+=['','The replay column explains the fresh local check. It does not replace',
        'the original numerical label or add an accepted model comparison.',
        'The accompanying table also retains cost changes, position changes and',
        'linearization differences for every source point.','',
        'Repeated native calculations and scaled bounded corrections can identify',
        'reproducibility or local resolution problems. They do not by themselves',
        'prove a roundoff bound, a global optimum or instrument accuracy.','',
        f"The run charged {report['charged']['native_calls']:,} native sweeps in {report['elapsed_s']/60:.2f} minutes.",
        'The saved-array audit recomputes costs, all-column stationarity, the unchanged',
        'bounded correction and physical position differences, with no trajectory propagation.',
        'Seven confirmation groups remain protected.','',
        '[Every source point](fixed-points.csv) · [Frozen plan](PLAN.md) · '
        '[Original comparison](../esa-observed-height-pilot/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    return '\n'.join(lines)+'\n'


def publish(root,prefix='data/esa-stopping-resolution-20261024',output='docs/esa-stopping-resolution'):
    import csv
    import io
    import json
    from pathlib import Path
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic,digest,encoded,safe_path
    from lll.studies.closed import ClosedStudy
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();public=safe_path(root,output);data=safe_path(root,prefix)
    if (public/'evidence-receipt.json').exists():raise ValueError('diagnostic publication already sealed')
    report=inspect(root,prefix);study=ClosedStudy(root,prefix)
    try:expected=study.manifest['sources']['docs/esa-stopping-resolution/PLAN.md']
    finally:study.close()
    if digest((public/'PLAN.md').read_bytes())!=expected:raise ValueError('preserved plan differs')
    fields=('identity','model','profile','policy_id','start','complete','source_converged','source_cost','fresh_cost',
        'residual_repeat_bitwise_equal','derivative_repeat_bitwise_equal','relative_saved_cost_difference',
        'maximum_relative_cost_change','maximum_linearization_error_norm','maximum_position_change_m','correction_available')
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
    writer.writerows({k:row.get(k) for k in fields} for row in report['rows'])
    package(data,public,render(report));receipt=json.loads((public/'evidence-receipt.json').read_bytes());receipt['artifacts']['PLAN.md']=expected
    for name,raw in [('artifacts/publication/verified-report.json',encoded(report)),
            ('artifacts/publication/reporter.py',Path(__file__).read_bytes()),('fixed-points.csv',stream.getvalue().encode())]:
        atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,native_calls=0)
