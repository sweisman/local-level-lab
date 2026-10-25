# SPDX-License-Identifier: AGPL-3.0-or-later
"""Hash-checked saved benchmark reporting; no native work or regeneration."""
import math


def verify_summary(summary,*,training_epochs,prediction_epochs):
    try:
        if (summary['training_epochs']!=training_epochs or summary['prediction_epochs']!=prediction_epochs
                or summary['known_calibration_benchmark'] is not True
                or any(summary[k] is not False for k in ('is_expected_realized_rms','calibration_uncertainty_included',
                    'confidence_calibrated','nonlinear_coverage_established'))
                or summary['scientific_decision']!='abstain'
                or summary['accuracy_limits']!={'horizontal_rms_m':10.,'vertical_rms_m':30.}):
            raise ValueError('unchanged benchmark target, screen and interpretation required')
        rows=summary['marginal_variance_neu_m2']
        if (len(rows)!=prediction_epochs or any(len(v)!=3 or any(type(x) not in (int,float)
                or not math.isfinite(x) or x<0 for x in v) for v in rows)):
            raise ValueError('complete nonnegative physical marginal variances required')
        horizontal=math.fsum(v[0]+v[1] for v in rows)/prediction_epochs
        vertical=math.fsum(v[2] for v in rows)/prediction_epochs
        for name,expected in [('horizontal_expected_squared_rms_m2',horizontal),
                ('vertical_expected_squared_rms_m2',vertical),('sqrt_expected_horizontal_squared_rms_m',math.sqrt(horizontal)),
                ('sqrt_expected_vertical_squared_rms_m',math.sqrt(vertical))]:
            if not math.isclose(summary[name],expected,rel_tol=1e-12,abs_tol=1e-12):
                raise ValueError('saved physical second-moment summary differs')
        endpoint=summary['endpoint_standard_deviation_neu_m']
        if len(endpoint)!=3 or any(not math.isclose(v,math.sqrt(x),rel_tol=1e-12,abs_tol=1e-12)
                for v,x in zip(endpoint,rows[-1])):raise ValueError('saved endpoint uncertainty differs')
        if summary['descriptive_second_moment_exceeds_screen']!=dict(horizontal=horizontal>100,vertical=vertical>900):
            raise ValueError('descriptive screen comparison changed')
    except (KeyError,TypeError,OverflowError) as error:raise ValueError('complete saved benchmark summary required') from error


def inspect(root,prefix):
    import struct
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import digest
    from lll.noise_benchmark_study import recipe,tasks,limits,SCOPE
    from lll.airquantumgrav_geographic_report import construction_counts,error_metrics
    from lll.ilvis0_noise_step import derive
    study=ClosedStudy(root,prefix)
    try:
        r=study.input('recipe');expected={v['identity']:v for v in tasks()}
        actual={k:{a:b for a,b in v.items() if a not in ('index','shard')} for k,v in study.tasks.items()}
        if r!=recipe() or actual!=expected or study.manifest['scope']!=SCOPE:raise ValueError('exact frozen benchmark required')
        env=study.input('qualification-environment');hashes=study.manifest['sources'];rows=[];attempted=0
        source=digest(derive(study.read('source-freeze/analysis/lll/ilvis0_tangent.cpp',raw=True),
            study.read('source-freeze/analysis/lll/ilvis0_noise_bridge.cpp',raw=True),
            expected_source_sha256=hashes['analysis/lll/ilvis0_tangent.cpp'],
            expected_bridge_sha256=hashes['analysis/lll/ilvis0_noise_bridge.cpp'],
            expected_wide_loader_sha256=hashes['analysis/lll/ilvis0_wide_tangent.py']))
        for identity,task in study.tasks.items():
            payload=task['payload'];row=dict(identity=identity,**payload,complete=False)
            if identity not in study.rows:rows.append(dict(row,reason='No sealed outcome'));continue
            envelope=study.envelope(identity);result=envelope['result']
            for path,sha in envelope['artifacts'].items():study.read(path,sha,raw=True)
            if not result.get('known_calibration_benchmark'):
                rows.append(dict(row,reason=result.get('reason','No saved benchmark')));continue
            s=study.artifact(identity,'benchmark.json');d=study.artifact(identity,'error-operator.json')
            c=study.artifact(identity,'nominal-context.json');p=study.artifact(identity,'native-prepayment.json')
            meta=study.artifact(identity,'compilation.json');work,construction=limits(payload)
            m=119 if payload['duration_s']==120 else 1200;cut=2*m//3;n=round(300*payload['duration_s'])
            verify_summary(s,training_epochs=cut,prediction_epochs=m-cut)
            if (meta['source_sha256']!=source or meta['compiler']!=env['compilers']['c++']
                    or meta['original_source_sha256']!=hashes['analysis/lll/ilvis0_tangent.cpp']
                    or p['state']!='complete' or p['prepaid']!={k:work[k] for k in ('native_calls','packet_visits')}
                    or p['prepaid']!={k:envelope['charged'][k] for k in ('native_calls','packet_visits')}
                    or not n<=p['attempted']['native_calls']<=n+m
                    or p['attempted']['native_calls']!=p['attempted']['packet_visits']
                    or d['operator_configuration']!=s['error_operator_configuration']
                    or d['prediction_target']!='physical_position' or d['receiver_observation_epochs']!=cut
                    or d['law']!=payload['law'] or d['model']!='sphere_rotating'
                    or any(d[k] is not True for k in ('oracle_nominal_future_geometry_used','initial_state_is_known','calibration_is_known'))
                    or any(result[k] for k in ('prediction_qualified','confidence_calibrated','optimizer_starts','random_draws','original_reads','protected_reads'))):
                raise ValueError('native binding, charged work or oracle interpretation differs')
            base=f"shards/{task['shard']:03d}/kernels/"
            study.read(base+meta['source_file'],meta['source_sha256'],raw=True)
            study.read(base+meta['binary_file'],meta['binary_sha256'],raw=True)
            construction_counts(study.artifact(identity,'construction.sqlite',raw=True),
                study.completion['manifest_sha256'],identity,construction)
            construction_counts(study.artifact(identity,'worker-build-journal.sqlite',raw=True),
                study.completion['manifest_sha256'],'worker',{'builds':1})
            names=('receiver_coordinates','integrated_coordinates','nominal_metric','mean_nominal_errors_neu_m')
            if len(c['times_s'])!=m or c['times_s']!=[.5+i for i in range(m)]:raise ValueError('complete frozen query grid required')
            for key in names:
                if len(c[key])!=m or any(len(v)!=3 or any(not math.isfinite(x) for x in v) for v in c[key]):
                    raise ValueError('complete finite saved nominal context required')
            errors=[]
            for truth,mean,units,saved in zip(*(c[k] for k in names)):
                values=[(a-b)*u for a,b,u in zip(mean,truth,units)]
                if any(u<=0 for u in units) or any(not math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-9) for a,b in zip(values,saved)):
                    raise ValueError('saved nominal integration check differs')
                errors.append(values)
            for key,values in [('times',c['times_s']),('nominal_receiver',[v for row in c['receiver_coordinates'] for v in row])]:
                if digest(b''.join(struct.pack('<d',x) for x in values))!=d['input_hashes'][key]:raise ValueError('nominal input hash differs')
            if not math.isclose(error_metrics(errors)['maximum_3d_m'],result['mean_nominal_maximum_3d_error_m'],
                    rel_tol=1e-10,abs_tol=1e-9):raise ValueError('mean integration score differs')
            attempted+=p['attempted']['native_calls']
            rows.append(dict(row,complete=True,horizontal_scale_m=s['sqrt_expected_horizontal_squared_rms_m'],
                vertical_scale_m=s['sqrt_expected_vertical_squared_rms_m'],
                endpoint_standard_deviation_neu_m=s['endpoint_standard_deviation_neu_m'],
                descriptive_second_moment_exceeds_screen=s['descriptive_second_moment_exceeds_screen']))
        return dict(verified=True,total=len(expected),complete=sum(v['complete'] for v in rows),rows=rows,
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            native_calls_attempted=attempted,elapsed_s=study.summary['elapsed_s'],
            original_reads=0,protected_reads=0,optimizer_starts=0,native_calls_during_audit=0,
            prediction_qualified=False,confidence_calibrated=False,scientific_decision='abstain')
    finally:study.close()


def render(report):
    if report.get('verified') is not True:raise ValueError('verified saved benchmark report required')
    lines=['# How much prediction error comes from the assumed noise?','',
        f"**{report['complete']}/{report['total']} benchmark settings completed and verified.**",'',
        'The calculation supplies known calibration, initial state and nominal trajectory.',
        'It computes the expected error scale under the declared noise, without fitting or random draws.','',
        '| Input-error format | Record length | Horizontal error scale | Height error scale |',
        '|---|---:|---:|---:|']
    for row in report['rows']:
        label='Recorded increments' if row['law']=='increment' else 'Sampled rates'
        values=[f"{row['horizontal_scale_m']:.2f} m",f"{row['vertical_scale_m']:.2f} m"] if row['complete'] else ['Unavailable','Unavailable']
        lines.append(f"| {label} | {row['duration_s']/60:g} min | "+' | '.join(values)+' |')
    lines+=['','The scale is the square root of the expected squared RMS, obtained from the marginal covariance.',
        'It is not a measured flight error or the expected value of a realized RMS.',
        'The 10 m horizontal / 30 m height screen and all earlier failures remain unchanged.','',
        'Completing this benchmark does not qualify nonlinear coverage, another aircraft fit or an Earth-model detection.',
        'The nominal future geometry is an oracle assumption and cannot enter the actual prediction protocol.',
        '', '[Frozen execution plan](EXECUTION_PLAN.md) · [Construction checks](construction-qualification/README.md) ·',
        '[Next analyses](../NEXT_STEPS.md).']
    return '\n'.join(lines)+'\n'


def metadata_environment():
    import sys
    return dict(python=sys.version,scope='saved-data metadata and scalar checks; no numerical library calls')


def publication_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/noise_benchmark_report.py','analysis/tests/test_noise_benchmark_report.py',
        'analysis/lll/studies/native_publication.py','analysis/lll/studies/qualification.py',
        'docs/noisy-prediction-benchmark/EXECUTION_PLAN.md'])


def publish(root,prefix,*,qualification,output='docs/noisy-prediction-benchmark'):
    if qualification is None:raise ValueError('source-bound saved-report qualification required')
    import json
    from pathlib import Path
    from lll.studies.artifacts import safe_path,atomic,encoded,digest
    from lll.studies.qualification import checked
    from lll.studies.closed import ClosedStudy
    from lll.studies.native_publication import include_native_caches
    from lll.ilvis0_control_publication import publish as package
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('closed benchmark publication already sealed')
    request,tests=checked(root,qualification,sources=publication_sources(root),environment=metadata_environment(),
        minimum_tests=10,required_tests=['test_saved_noise_summary_is_recomputed_without_numerical_imports',
            'test_noise_report_render_preserves_missing_cases_and_distinguishes_expected_scale',
            'test_noise_report_requires_closed_study_before_any_numerical_import'])
    report=inspect(root,prefix);study=ClosedStudy(root,prefix);entries={}
    try:
        for identity,task in study.tasks.items():
            if identity not in study.rows:continue
            name='artifacts/'+identity+'/compilation.json'
            if name not in study.envelope(identity)['artifacts']:continue
            meta=study.artifact(identity,'compilation.json');base=f"shards/{task['shard']:03d}/kernels/"
            entries[base+meta['source_file']]=meta['source_sha256']
            entries[base+meta['binary_file']]=meta['binary_sha256']
            cache=base+str(Path(meta['binary_file']).with_suffix('.json'))
            raw=study.read(cache,raw=True);binding=json.loads(raw)
            if any(binding[k]!=meta[k] for k in ('source_sha256','binary_sha256','compiler','compiler_executable',
                    'flags','cache_sha256','source_file','binary_file')):
                raise ValueError('saved native cache differs from compilation binding')
            entries[cache]=digest(raw);entries[base+'builds.sqlite']=digest(study.read(base+'builds.sqlite',raw=True))
        plan=study.read('source-freeze/docs/noisy-prediction-benchmark/EXECUTION_PLAN.md',raw=True)
    finally:study.close()
    package(data,public,render(report),plan='docs/noisy-prediction-benchmark/PLAN.md')
    if entries:include_native_caches(root,data,public,
        entries=[dict(path=k,sha256=v) for k,v in sorted(entries.items())],maximum_bytes=64*1024**2)
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    additions={'EXECUTION_PLAN.md':plan,'artifacts/publication/verified-report.json':encoded(report),
        'artifacts/publication/qualification-request.json':request,'artifacts/publication/qualification-report.xml':tests,
        'artifacts/publication/source/analysis/lll/noise_benchmark_report.py':Path(__file__).read_bytes(),
        'artifacts/publication/source/analysis/tests/test_noise_benchmark_report.py':
            (root/'analysis/tests/test_noise_benchmark_report.py').read_bytes()}
    for name,raw in additions.items():atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    if encoded(inspect(root,output))!=encoded(report):raise ValueError('published saved audit differs')
    return dict(publication=output,artifacts=len(receipt['artifacts']),complete=report['complete'],
        compaction_pending=True,native_calls=0,optimizer_starts=0,prediction_qualified=False)
