# SPDX-License-Identifier: AGPL-3.0-or-later
"""Hash-checked, saved-only reporting of scalar precision diagnostics."""


def verify_case(problem,result,arrays,*,points,reference,source_converged):
    import numpy as np
    from .ilvis0_precision_value import _whiten
    from .ilvis0_solver_position import physical_residual_step
    from .studies.artifacts import encoded
    expected={f'{precision}-{i}.npz' for precision in ('double','long_double') for i in (0,1)}
    if (set(arrays)!=expected or result['native_calls']!=4 or result['labels_changed'] or not result['passed']
            or result['source_converged']!=source_converged or result['active_parameters']!=list(problem.bounds.active)
            or result['packet_query_visits']!=4*len(problem.dt)*len(problem.gps_times)
            or result['optimizer_starts'] or result['scientific_decision']!='abstain'
            or not result['binary64_reference_exact'] or result['confidence_calibrated']):
        raise ValueError('unchanged complete precision protocol required')
    modes={}
    for precision in ('double','long_double'):
        pair=[arrays[f'{precision}-{i}.npz'] for i in (0,1)]
        for i,a in enumerate(pair):
            keys={'point','coordinates','coordinate_difference','stable_residual'}|({'legacy_residual'} if precision=='double' else set())
            if (set(a)!=keys or any(v.dtype!=np.dtype('float64') or not np.all(np.isfinite(v)) for v in a.values())
                    or a['coordinates'].shape!=problem.gps.shape or a['coordinate_difference'].shape!=problem.gps.shape
                    or a['stable_residual'].shape!=(problem.gps.size,) or not np.array_equal(a['point'],points[i])
                    or not np.array_equal(a['stable_residual'],_whiten(problem,a['coordinate_difference'],'stable'))):
                raise ValueError('complete unchanged finite precision arrays required')
            if precision=='double' and (not np.array_equal(a['legacy_residual'],reference[i])
                    or not np.array_equal(a['legacy_residual'],_whiten(problem,a['coordinate_difference'],'legacy'))
                    or not np.array_equal(a['coordinate_difference'],a['coordinates']-problem.gps)):
                raise ValueError('frozen residual or binary64 coordinate difference differs')
        physical=physical_residual_step(problem,_whiten(problem,pair[1]['coordinate_difference']-pair[0]['coordinate_difference'],'stable'))
        for suffix in (('legacy','stable') if precision=='double' else ('stable',)):
            first,last=(a[suffix+'_residual'] for a in pair);c0=float(first@first);c1=float(last@last)
            label=('long-double' if precision=='long_double' else 'double')+'-'+suffix
            modes[label]=dict(baseline_cost=c0,corrected_cost=c1,relative_cost_change=abs(c1-c0)/max(c0,c1,1.),
                position_rms_neu_m=np.sqrt(np.mean(physical*physical,axis=0)).tolist(),
                position_max_abs_neu_m=np.max(abs(physical),axis=0).tolist())
    if encoded(modes)!=encoded(result['modes']):raise ValueError('saved precision costs or physical changes differ')
    return modes


def inspect(root,prefix='data/esa-precision-diagnostic-v2-20261024'):
    from pathlib import Path
    from .studies.closed import ClosedStudy
    study=ClosedStudy(root,prefix)
    try:
        import gzip
        import io
        import json
        import numpy as np
        from .airquantumgrav_precision import recipe,tasks,sources,required_tests,PARENT,SCOPE,environment,METADATA,validate_context
        import math
        from types import SimpleNamespace
        from .airquantumgrav_error_policy import build
        from .ilvis0_estimator import MotionProblem
        from .airquantumgrav_observed_report import verify_audit_environment
        from .airquantumgrav_observation_report import native_accounting
        from .ilvis0_precision_value import derive
        from .studies.artifacts import digest,encoded
        from .studies.source_binding import verify
        root=Path(root).resolve();env=study.input('qualification-environment')
        verify_audit_environment(env,environment())
        request=study.input('qualification-request')
        if set(sources(root))!=set(request['sources']):raise ValueError('qualified source enumeration changed')
        verify(root,declared=request['sources'],manifest=study.manifest['sources'])
        if request['environment']!=env:raise ValueError('qualified environment binding differs')
        # Check the frozen passing report without requiring a preparation copy.
        import xml.etree.ElementTree as ET
        tree=ET.fromstring(study.input('qualification-report',raw=True));cases=list(tree.iter('testcase'));suites=list(tree.iter('testsuite'))
        identities=[(c.attrib.get('classname',''),c.attrib['name']) for c in cases]
        if (not suites or len(cases)<len(required_tests()) or len(set(identities))!=len(cases)
                or not set(required_tests())<={c.attrib['name'] for c in cases}
                or any(c.find(k) is not None for c in cases for k in ('failure','error','skipped'))
                or any(int(s.attrib.get(k,0)) for s in suites for k in ('errors','failures','skipped'))):
            raise ValueError('complete passing source-bound precision checks required')
        if (study.input('recipe')!=recipe() or study.manifest['scope']!=SCOPE
                or {k:{a:b for a,b in v.items() if a not in ('index','shard')} for k,v in study.tasks.items()}
                !={v['identity']:v for v in tasks()}):raise ValueError('unchanged precision scope required')
        proof=study.input('source-proof');parent=ClosedStudy(root,PARENT)
        try:
            receipt=parent.read('evidence-receipt.json')
            if (proof['manifest_sha256']!=parent.completion['manifest_sha256']
                    or proof['summary_sha256']!=parent.completion['summary_sha256']
                    or proof['report_sha256']!=receipt['artifacts']['artifacts/publication/verified-report.json']):
                raise ValueError('closed parent binding differs')
            for key,sha in proof['inputs'].items():
                if study.manifest['inputs'][key]['sha256']!=sha:raise ValueError('source input hash differs')
                if key.startswith('reference-'):
                    identity=key[len('reference-'):]
                    with np.load(io.BytesIO(study.input(key,raw=True)),allow_pickle=False) as a:
                        points=a['points'];reference=a['residuals']
                    for i,index in enumerate((0,2)):
                        with np.load(io.BytesIO(parent.artifact(identity,f'sweep-{index:02d}.npz',raw=True)),allow_pickle=False) as a:
                            if not np.array_equal(points[i],a['point']) or not np.array_equal(reference[i],a['residual']):
                                raise ValueError('original source points or residuals differ')
                elif study.input(key,raw=True)!=parent.input(key,raw=True):raise ValueError('unchanged earlier input required')
        finally:parent.close()
        binding=validate_context(**{key:study.input(key) for key in METADATA})
        if binding!=study.input('context'):raise ValueError('development membership differs')
        rows=json.loads(gzip.decompress(study.input('training',raw=True)));layout=study.input('layout')
        with np.load(io.BytesIO(study.input('interval',raw=True)),allow_pickle=False) as a:material={k:a[k] for k in ('theta','dv','dt')}
        if len(material['dt'])!=recipe()['packets'] or len(rows)!=recipe()['epochs']:raise ValueError('earlier support differs')
        charges={}
        for shard in range(study.manifest['allocation']['workers']):
            charges.update(native_accounting(study.read(f'shards/{shard:03d}/charges/journal.sqlite',raw=True),
                study.completion['manifest_sha256'],{k for k,v in study.tasks.items() if v['shard']==shard},per_call_visits=None))
        gps=np.array([[math.radians(v['latitude_deg']),math.radians(v['longitude_deg']),v['height_m']] for v in rows])
        factors={};working=study.input('working-errors')
        for policy in recipe()['policies']:
            weights=build(rows,policy_id=policy)
            if (weights.configuration!=working[policy]['configuration']
                    or not np.array_equal(weights.times-layout['time_origin_gps_sow_s'],layout['times_s'])):
                raise ValueError('unchanged earlier receiver covariance required')
            factors[policy]=np.linalg.cholesky(weights.dense(maximum_epochs=1024))
        reports=[]
        for identity,task in study.tasks.items():
            spec=task['payload'];row=dict(identity=identity,**spec,complete=False);operations=charges[identity]
            if operations['tangent'] or operations['packet_visits']!=operations['value']*len(rows)*len(material['dt']):
                raise ValueError('value-only exact charges required')
            if identity in study.rows:
                envelope=study.envelope(identity);result=envelope['result']
                for name,sha in envelope['artifacts'].items():study.read(name,sha,raw=True)
                key='artifacts/'+identity+'/precision.json'
                if key in envelope['artifacts']:
                    fit=study.input('point-'+identity)
                    # Saved-array auditing needs two shared covariance factors,
                    # not twelve copies of a native problem and its packet arrays.
                    problem=SimpleNamespace(gps=gps,cholesky=factors[spec['policy_id']],dt=material['dt'],
                        gps_times=layout['times_s'],bounds=SimpleNamespace(active=fit['active_parameters']))
                    problem.whiten=lambda d,p=problem:MotionProblem.whiten(p,d)
                    with np.load(io.BytesIO(study.input('reference-'+identity,raw=True)),allow_pickle=False) as a:
                        points=a['points'];reference=a['residuals']
                    saved=study.artifact(identity,'precision.json');arrays={}
                    for record in saved['artifacts']:
                        raw=study.artifact(identity,record['artifact'],raw=True)
                        if digest(raw)!=record['sha256']:raise ValueError('precision array binding differs')
                        with np.load(io.BytesIO(raw),allow_pickle=False) as a:arrays[record['artifact']]={k:a[k] for k in a.files}
                    modes=verify_case(problem,saved,arrays,points=points,reference=reference,source_converged=fit['converged'])
                    if (operations['value']!=4 or envelope['charged']['native_calls']!=4
                            or any(encoded(result[k])!=encoded(v) for k,v in saved.items())
                            or result['group_id']!=binding['group_id']):raise ValueError('precision result or charges differ')
                    bound=study.artifact(identity,'input-binding.json')
                    if (bound['group_id']!=binding['group_id'] or bound['original_reads'] or bound['protected_reads']
                            or bound['later_receiver_reads'] or bound['inputs']!=proof['inputs']
                            or bound['source_proof_sha256']!=study.manifest['inputs']['source-proof']['sha256']):
                        raise ValueError('training-only input evidence differs')
                    for precision in ('double','long_double'):
                        meta=study.artifact(identity,'compilation-'+precision+'.json');name='analysis/lll/ilvis0_tangent.cpp'
                        base=study.read('source-freeze/'+name,study.manifest['sources'][name],raw=True)
                        if (meta['source_sha256']!=digest(base) or meta['compiler']!=env['compilers']['c++']
                                or meta['derived_source_sha256']!=digest(derive(base,expected_sha256=digest(base),precision=precision))
                                or meta['gravity_anchor_height_m']!=rows[0]['height_m'] or meta['clock_mantissa_bits']!=53
                                or meta['profile_mapping']!='binary64-frozen' or meta['clock_dispatch']!='binary64-frozen'
                                or (precision=='double' and meta['mantissa_bits']!=53)
                                or (precision=='long_double' and meta['mantissa_bits']<=53)):
                            raise ValueError('compiled precision or fixed clock differs')
                    row.update(complete=True,source_converged=fit['converged'],modes=modes)
                else:row['reason']=result.get('error',result.get('reason','unfinished diagnostic'))
            reports.append(row)
        if sum(v['value'] for v in charges.values())!=study.summary['charged']['native_calls']:
            raise ValueError('whole precision charge total differs')
        return dict(verified=True,total=24,complete=sum(r['complete'] for r in reports),rows=reports,
            charged=study.summary['charged'],elapsed_s=study.summary['elapsed_s'],
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            optimizer_starts=0,original_reads=0,protected_reads=0,labels_changed=False,scientific_decision='abstain')
    finally:study.close()
