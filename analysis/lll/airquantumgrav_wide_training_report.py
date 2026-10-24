# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only matched training audit, reusing established physical/error gates."""


def inspect(root,prefix='data/esa-wide-training-controls-20261024'):
    from pathlib import Path
    from lll.studies.closed import ClosedStudy,load_python_reference
    study=ClosedStudy(root,prefix)
    try:
        import numpy as np
        from lll.airquantumgrav_wide_training_controls import recipe,tasks,qualification_sources,construction_limits,SCOPE,environment
        from lll.airquantumgrav_height_report import binding_gate
        from lll.airquantumgrav_training_report import case_gate,saved_position_errors
        from lll.airquantumgrav_geographic_report import construction_counts
        from lll.airquantumgrav_observation_report import native_accounting
        from lll.airquantumgrav_observed_report import verify_audit_environment
        from lll.airquantumgrav_error_policy import build
        from lll.ilvis0_wide_training import bind,SOURCES
        from lll.ilvis0_wide_tangent import derive
        from lll.studies.artifacts import digest,encoded
        from lll.studies.source_binding import verify
        root=Path(root).resolve();r=study.input('recipe');env=study.input('qualification-environment')
        verify_audit_environment(env,environment());declared=study.input('qualification-request')['sources']
        if set(declared)!=set(qualification_sources(root)):raise ValueError('qualified source enumeration changed')
        verify(root,declared=declared,manifest=study.manifest['sources'])
        if (r!=recipe() or study.manifest['scope']!=SCOPE
                or {k:{a:b for a,b in v.items() if a not in ('index','shard')} for k,v in study.tasks.items()}
                !={t['identity']:t for t in tasks()}):raise ValueError('unchanged full training matrix required')
        run,calculate,protocol=bind(expected_sources={n:study.manifest['sources']['analysis/lll/'+n] for n in SOURCES})
        if protocol!=study.input('protocol-binding'):raise ValueError('factory substitution differs from its freeze')
        parent=ClosedStudy(root,'docs/esa-wide-tangent-controls')
        try:
            proof=study.input('qualified-parent');receipt=parent.read('evidence-receipt.json');key='artifacts/publication/verified-report.json'
            report=parent.read(key,receipt['artifacts'][key])
            if (not report['qualified'] or report['passed']!=48
                    or proof['manifest_sha256']!=parent.completion['manifest_sha256']
                    or proof['summary_sha256']!=parent.completion['summary_sha256'] or proof['report_sha256']!=receipt['artifacts'][key]):
                raise ValueError('qualified long-motion parent binding differs')
        finally:parent.close()
        name='analysis/lll/airquantumgrav_truth.py';sha=study.manifest['sources'][name]
        geometry=load_python_reference(study.read('source-freeze/'+name,sha,raw=True),name='lll._wide_training_geometry_'+sha,sha256=sha)
        constants={key:getattr(geometry,key) for key in ('A','E2','DISC_RADIUS')}
        operations={}
        for shard in range(study.manifest['allocation']['workers']):
            operations.update(native_accounting(study.read(f'shards/{shard:03d}/charges/journal.sqlite',raw=True),
                study.completion['manifest_sha256'],{k for k,v in study.tasks.items() if v['shard']==shard},per_call_visits=None))
        limits=construction_limits(r);n=round(r['duration_s']*r['rate_hz']);cut=2*r['queries']//3
        rows=[];shared={};binaries={'value':set(),'tangent':set()};charges={k:0 for k in study.summary['charged']}
        for identity,task in study.tasks.items():
            if identity not in study.rows:continue
            envelope=study.envelope(identity);result=envelope['result'];counts=operations[identity];artifacts=envelope['artifacts']
            for name,sha in artifacts.items():study.read(name,sha,raw=True)
            for k in charges:charges[k]+=envelope['charged'][k]
            if counts['value'] or counts['tangent']!=envelope['charged']['native_calls'] or counts['packet_visits']!=envelope['charged']['packet_visits']:
                raise ValueError('actual native kinds and charges differ')
            complete='converged' in result;row=dict(identity=identity,spec=task['payload'],result=result,complete=complete)
            name='artifacts/'+identity+'/construction.sqlite'
            row['construction']=construction_counts(study.read(name,artifacts[name],raw=True),study.completion['manifest_sha256'],identity,
                limits,complete=complete) if name in artifacts else None
            if complete:
                if any(result[k]!=v for k,v in task['payload'].items()) or row['construction']!=limits:
                    raise ValueError('complete identity and construction work differ')
                if study.artifact(identity,'protocol-binding.json')!=protocol:raise ValueError('case used a different factory substitution')
                fit=study.artifact(identity,'fit.json');forecast=study.artifact(identity,'forecast.json')
                scores=study.artifact(identity,'scores.json');answer=study.artifact(identity,'scoring-observations.json')
                earlier=study.artifact(identity,'training-receiver.json');training=study.artifact(identity,'training-observations.json')
                binding=study.artifact(identity,'input-binding.json');after=study.artifact(identity,'forecast-binding.json')
                meta=study.artifact(identity,'compilation.json');count=binding_gate(binding,after,earlier,training,meta,result,r)
                if (counts['tangent']!=fit['evaluations']+1 or result['native_calls']!=counts['tangent']
                        or counts['packet_visits']!=fit['evaluations']*count*cut+n*r['queries']
                        or result['constructed_intervals']!=n or result['generated_samples']!=limits['generated_samples']):
                    raise ValueError('exact fitting, forecast and construction charges differ')
                weight=build(earlier,policy_id=task['payload']['policy_id'])
                if (training['weight_configuration']!=weight.configuration or training['weight_descriptor']!=weight.descriptor
                        or training['weight_source_sha256']!=weight.source_sha256):raise ValueError('earlier working weights differ')
                times=[r['query_start_s']+i*r['query_step_s'] for i in range(r['queries'])]
                if (forecast['times_s']!=times or scores['times_s']!=times
                        or not np.allclose(answer['coordinates'][:cut],training['coordinates'],rtol=0,atol=2e-14)):
                    raise ValueError('fixed query or earlier receiver coordinates differ')
                physical=saved_position_errors(forecast['coordinates'],answer,model=result['model'],constants=constants)
                if any(abs(a-b)>1e-7 for x,y in zip(physical,scores['errors_neu_m'],strict=True) for a,b in zip(x,y,strict=True)):
                    raise ValueError('independent saved physical errors differ')
                row['checked']=case_gate(result,fit,forecast,scores,r)
                key=(result['model'],result['profile']);common=dict(raw=binding['full_array_sha256'],
                    training=digest(encoded(earlier)),scoring=digest(encoded(answer)),anchor=binding['gravity_anchor_height_m'])
                if key in shared and shared[key]!=common:raise ValueError('starts or policies changed generated observations')
                shared[key]=common
                base='analysis/lll/ilvis0_tangent.cpp';raw=study.read('source-freeze/'+base,study.manifest['sources'][base],raw=True)
                value,tangent=meta['value'],meta['tangent']
                if (value['source_sha256']!=study.manifest['sources']['analysis/lll/ilvis0_native.c']
                        or value['compiler']!=env['compilers']['cc'] or tangent['compiler']!=env['compilers']['c++']
                        or tangent['original_source_sha256']!=digest(raw)
                        or tangent['source_sha256']!=digest(derive(raw,expected_sha256=digest(raw)))
                        or tangent['internal_mantissa_bits']<=53 or tangent['packet_clock_changed']
                        or tangent['residual_subtraction']!='before-binary64-cast'
                        or any(tangent[k]!='binary64-frozen' for k in ('clock_dispatch','profile_mapping','query_fraction','parameter_products'))):
                    raise ValueError('compiled precision method differs from its freeze')
                for k in binaries:binaries[k].add(meta[k]['binary_sha256'])
            elif result['passed']:raise ValueError('unfinished fit cannot qualify')
            rows.append(row)
        if (charges!=study.summary['charged'] or any(len(v)>1 for v in binaries.values())
                or sum(v['tangent'] for v in operations.values())!=charges['native_calls']):raise ValueError('whole-run charges or binaries differ')
        complete=[v for v in rows if v['complete']];passed=sum(v['result']['passed'] for v in rows)
        return dict(verified=True,total=24,returned=len(rows),passed=passed,qualified=len(rows)==passed==24,rows=rows,
            charged=charges,elapsed_s=study.summary['elapsed_s'],
            maximum_prediction_horizontal_rms_m=max((v['checked']['prediction']['horizontal_rms_m'] for v in complete),default=None),
            maximum_prediction_height_rms_m=max((v['checked']['prediction']['vertical_rms_m'] for v in complete),default=None),
            maximum_prediction_spatial_error_m=max((v['checked']['prediction']['maximum_3d_m'] for v in complete),default=None),
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            original_reads=0,protected_reads=0,observed_starts=0,confidence_calibrated=False,scientific_decision='abstain')
    finally:study.close()


def render(report):
    number=lambda k:'Unavailable' if report[k] is None else f"{report[k]:.6g} m"
    return '\n'.join(['# Wider-precision training and prediction controls','',
        f"**{report['passed']}/{report['total']} generated fits pass all frozen checks.**",'',
        'Earlier 800 receiver positions determine initialization, calibration and the',
        'gravity anchor. Later 400 positions score a continuous forecast only after',
        'it is saved. True initial state and calibration are not supplied. Both starts,',
        'both processing cases and both working error assumptions remain in the test.','',
        'The existing procedure supplies the same fit allowance and stopping checks.',
        'Only its explicitly bound problem factory uses the wider calculation.','',
        '| Later prediction check | Largest error |','|---|---:|',
        '| Horizontal RMS | '+number('maximum_prediction_horizontal_rms_m')+' |',
        '| Height RMS | '+number('maximum_prediction_height_rms_m')+' |',
        '| Spatial maximum | '+number('maximum_prediction_spatial_error_m')+' |','',
        'These are generated software controls, not aircraft findings or calibrated',
        'confidence. No protected confirmation flight is opened. All original fit',
        'labels remain unchanged. A revised observed study needs its own freeze.','',
        f"The run charged {report['charged']['native_calls']} native calls in {report['elapsed_s']/60:.2f} minutes.",
        '[Frozen plan](PLAN.md) · [Known-motion gate](../esa-wide-tangent-controls/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).',''])


def publish(root,prefix='data/esa-wide-training-controls-20261024',output='docs/esa-wide-training-controls'):
    import json
    from pathlib import Path
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import safe_path,atomic,digest,encoded
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();public=safe_path(root,output);data=safe_path(root,prefix)
    if (public/'evidence-receipt.json').exists():raise ValueError('wider training publication already sealed')
    report=inspect(root,prefix);package(data,public,render(report),plan='docs/esa-wide-training-controls/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    for name,raw in [('verified-report.json',encoded(report)),('reporter.py',Path(__file__).read_bytes())]:
        name='artifacts/publication/'+name;atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,native_calls=0)
