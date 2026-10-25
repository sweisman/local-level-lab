# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-array/scalar audit of matched noise paths; never regenerates or fits."""
import math


def verify_curves(errors,sigma,summary):
    def finite(x):return type(x) in (int,float) and math.isfinite(x)
    try:
        n=len(sigma)
        if (not n or len(errors)!=4 or any(len(v)!=n for v in errors)
                or any(len(row)!=3 or any(not finite(x) for x in row) for rows in [sigma,*errors] for row in rows)
                or any(x<0 for row in sigma for x in row)):
            raise ValueError('complete finite matched curves and nonnegative standard deviations required')
        a,b,c,d=errors
        even=[abs((a[i][j]+b[i][j])/2) for i in range(n) for j in range(3)]
        half=[abs((c[i][j]+d[i][j])/2) for i in range(n) for j in range(3)]
        change=[abs((c[i][j]-d[i][j])-(a[i][j]-b[i][j])/2) for i in range(n) for j in range(3)]
        limits=[max(.001,.01*s) for row in sigma for s in row]
        fraction=max(x/y for x,y in zip(even,limits));response=max(x/y for x,y in zip(change,limits))
        expected=dict(passed=fraction<=1 and response<=1,maximum_even_remainder_m=max(even),
            maximum_half_amplitude_even_remainder_m=max(half),maximum_half_response_change_m=max(change),
            maximum_even_remainder_fraction_of_limit=fraction,maximum_half_response_change_fraction_of_limit=response,
            absolute_limit_m=.001,relative_limit=.01,independent_realizations=1,
            finite_sample_check_only=True,global_remainder_bound_established=False,
            confidence_calibrated=False,scientific_decision='abstain')
        for name,values in [('plus_rms_neu_m',a),('minus_rms_neu_m',b)]:
            expected[name]=[math.sqrt(math.fsum(row[j]**2 for row in values)/n) for j in range(3)]
        for name,value in expected.items():
            actual=summary[name]
            if type(value) is float:
                same=finite(actual) and math.isclose(actual,value,rel_tol=1e-10,abs_tol=1e-12)
            elif isinstance(value,list):
                same=len(actual)==3 and all(finite(x) and math.isclose(x,y,rel_tol=1e-10,abs_tol=1e-12)
                    for x,y in zip(actual,value))
            else:same=type(actual) is type(value) and actual==value
            if not same:raise ValueError('saved matched metric or interpretation differs: '+name)
        return expected
    except (KeyError,TypeError,IndexError,OverflowError) as exc:
        raise ValueError('complete saved matched curves and result required') from exc


def inspect(root,prefix,*,parent='docs/noisy-prediction-benchmark'):
    from lll.studies.closed import ClosedStudy
    study=ClosedStudy(root,prefix)  # Closed evidence is required before array imports.
    try:
        import io
        import numpy as np
        from lll.noise_nonlinearity_study import recipe,tasks,limits,SCOPE
        from lll.noise_benchmark_study import limits as parent_limits
        from lll.noise_benchmark_report import inspect as parent_inspect
        from lll.airquantumgrav_geographic_report import construction_counts
        from lll.studies.artifacts import digest
        from lll.ilvis0_noise_step import derive as bridge_source
        from lll.ilvis0_precision_value import derive as scalar_source
        if (study.input('recipe')!=recipe() or study.manifest['scope']!=SCOPE
                or {k:{a:b for a,b in v.items() if a not in ('index','shard')} for k,v in study.tasks.items()}
                    !={v['identity']:v for v in tasks()}):raise ValueError('exact frozen matched-noise recipe required')
        parent_inspect(root,parent);baseline=ClosedStudy(root,parent)
        try:
            critical=['analysis/lll/'+v for v in ('generated_noise_benchmark.py','measurement_noise.py',
                'ilvis0_noise_history.py','linear_point_noise.py','ilvis0_noise_step.py','ilvis0_tangent.cpp',
                'ilvis0_noise_bridge.cpp','state_space_covariance.py','receiver_noise_states.py')]
            hashes=study.manifest['sources']
            if any(hashes[k]!=baseline.manifest['sources'][k] for k in critical):raise ValueError('benchmark source laws differ')
            cpp=study.read('source-freeze/analysis/lll/ilvis0_tangent.cpp',hashes['analysis/lll/ilvis0_tangent.cpp'],raw=True)
            bridge=digest(bridge_source(cpp,study.read('source-freeze/analysis/lll/ilvis0_noise_bridge.cpp',raw=True),
                expected_source_sha256=hashes['analysis/lll/ilvis0_tangent.cpp'],
                expected_bridge_sha256=hashes['analysis/lll/ilvis0_noise_bridge.cpp'],
                expected_wide_loader_sha256=hashes['analysis/lll/ilvis0_wide_tangent.py']))
            scalar=digest(scalar_source(cpp,expected_sha256=hashes['analysis/lll/ilvis0_tangent.cpp'],precision='long_double'))
            compiler=study.input('qualification-environment')['compilers']['c++'];rows=[];assets={};verified_seeds=0
            for identity,task in study.tasks.items():
                row=dict(identity=identity,**task['payload'],complete=False)
                if identity not in study.rows:
                    rows.append(dict(row,reason='No sealed outcome'));continue
                envelope=study.envelope(identity);result=envelope['result']
                for path,sha in envelope['artifacts'].items():study.read(path,sha,raw=True)
                if 'artifacts/'+identity+'/matched-summary.json' not in envelope['artifacts']:
                    rows.append(dict(row,reason=result.get('reason',result.get('error','No complete matched curves'))));continue
                work,construction=limits(task['payload']);bridge_work,_=parent_limits(task['payload'])
                prepaid=study.artifact(identity,'native-prepayment.json')
                if (prepaid['state']!='complete' or prepaid['prepaid']!={k:bridge_work[k] for k in ('native_calls','packet_visits')}
                        or prepaid['attempted']!=prepaid['prepaid']
                        or any(envelope['charged'][k]!=work[k] for k in ('native_calls','packet_visits'))):
                    raise ValueError('complete native work or prepayment differs')
                construction_counts(study.artifact(identity,'construction.sqlite',raw=True),
                    study.completion['manifest_sha256'],identity,construction)
                for label,expected_source,journal in [('compilation.json',bridge,'worker-build-journal.sqlite'),
                        ('scalar-compilation.json',scalar,'scalar-build-journal.sqlite')]:
                    meta=study.artifact(identity,label)
                    source_key='derived_source_sha256' if label.startswith('scalar') else 'source_sha256'
                    if meta[source_key]!=expected_source or meta['compiler']!=compiler:raise ValueError('native source/compiler differs')
                    base=f"shards/{task['shard']:03d}/kernels/"
                    source_name=('precision-value-'+scalar+'.cpp') if label.startswith('scalar') else meta['source_file']
                    binary_name=('precision-value-'+scalar+'.so') if label.startswith('scalar') else meta['binary_file']
                    for name,sha in ((source_name,expected_source),(binary_name,meta['binary_sha256'])):
                        study.read(base+name,sha,raw=True);assets[base+name]=sha
                    journal_name='scalar-builds.sqlite' if label.startswith('scalar') else 'builds.sqlite'
                    assets[base+journal_name]=digest(study.read(base+journal_name,raw=True))
                    construction_counts(study.artifact(identity,journal,raw=True),study.completion['manifest_sha256'],'worker',{'builds':1})
                    if not label.startswith('scalar'):
                        cache=base+str(__import__('pathlib').Path(binary_name).with_suffix('.json'))
                        raw=study.read(cache,raw=True);assets[cache]=digest(raw)
                descriptor=study.artifact(identity,'error-operator.json');old_descriptor=baseline.artifact(identity,'error-operator.json')
                if descriptor!=old_descriptor:raise ValueError('fixed benchmark covariance binding differs')
                context=study.artifact(identity,'nominal-context.json');reference=baseline.artifact(identity,'benchmark.json')
                sigma=context['conditional_standard_deviation_neu_m'];variance=reference['marginal_variance_neu_m2']
                if (len(sigma)!=len(variance) or any(len(a)!=3 or any(not math.isfinite(x) or x<0 or
                        not math.isclose(x*x,y,rel_tol=1e-10,abs_tol=1e-12) for x,y in zip(a,b)) for a,b in zip(sigma,variance))):
                    raise ValueError('conditional error scale differs from verified benchmark')
                matched=study.artifact(identity,'matched-summary.json');seeds=recipe()['seeds'];checked=[]
                if matched['seeds']!=seeds or [v['seed'] for v in matched['rows']]!=seeds:raise ValueError('fixed seed set differs')
                for saved,seed in zip(matched['rows'],seeds):
                    row_seed=study.artifact(identity,f'seed-{seed}.json')
                    if row_seed['seed']!=seed or dict(saved,seed=seed)!=dict(row_seed['summary'],seed=seed):
                        raise ValueError('seed and aggregate result differ')
                    raw=study.artifact(identity,f'seed-{seed}.npz',raw=True)
                    if len(raw)>2*1024**2:raise ValueError('bounded saved error array required')
                    with np.load(io.BytesIO(raw),allow_pickle=False) as arrays:
                        if arrays.files!=['errors_neu_m']:raise ValueError('exact matched error array required')
                        checked.append(verify_curves(arrays['errors_neu_m'].tolist(),sigma,row_seed['summary']))
                    verified_seeds+=1
                passed=all(v['passed'] for v in checked)
                if (result['passed'] is not passed or result['realizations']!=16 or result['passed_realizations']!=sum(v['passed'] for v in checked)
                        or any(result[k] for k in ('prediction_qualified','global_remainder_bound_established','confidence_calibrated',
                            'optimizer_starts','original_reads','protected_reads'))):raise ValueError('saved setting outcome differs')
                rows.append(dict(row,complete=True,passed=passed,realizations=16,passed_realizations=sum(v['passed'] for v in checked),
                    maximum_even_remainder_m=max(v['maximum_even_remainder_m'] for v in checked),
                    maximum_half_response_change_m=max(v['maximum_half_response_change_m'] for v in checked),
                    maximum_even_remainder_fraction_of_limit=max(v['maximum_even_remainder_fraction_of_limit'] for v in checked),
                    maximum_half_response_change_fraction_of_limit=max(v['maximum_half_response_change_fraction_of_limit'] for v in checked)))
            return dict(verified=True,rows=rows,total=4,complete=sum(v['complete'] for v in rows),
                passed_settings=sum(v.get('passed',False) for v in rows),total_realizations=verified_seeds,
                passed_realizations=sum(v.get('passed_realizations',0) for v in rows),elapsed_s=study.summary['elapsed_s'],
                manifest_sha256=study.completion['manifest_sha256'],parent_manifest_sha256=baseline.completion['manifest_sha256'],
                native_assets=[dict(path=k,sha256=v) for k,v in sorted(assets.items())],
                native_calls_during_audit=0,optimizer_starts=0,original_reads=0,protected_reads=0,
                confidence_calibrated=False,global_remainder_bound_established=False,scientific_decision='abstain')
        finally:baseline.close()
    finally:study.close()


def render(report):
    if report.get('verified') is not True:raise ValueError('verified saved report required')
    lines=['# Check the noise approximation against nonlinear motion','',
        f"**{report['passed_settings']}/{report['total']} settings pass the fixed finite check.**",'',
        '| Input format | Record length | Matched controls passed | Largest non-reversing error | Result |',
        '|---|---:|---:|---:|---|']
    for row in report['rows']:
        label='Increments' if row['law']=='increment' else 'Rate points'
        if row['complete']:
            values=f"{row['passed_realizations']}/{row['realizations']} | {row['maximum_even_remainder_m']:.6g} m | "+('Pass' if row['passed'] else 'Failed')
        else:values='Unavailable | Unavailable | Incomplete'
        lines.append(f"| {label} | {row['duration_s']/60:g} min | {values} |")
    lines+=['','Each control compares positive, negative and half-sized generated errors.',
        'The non-reversing part and change at half amplitude are checked against the larger',
        'of 1 mm and 1% of the predicted coordinate standard deviation.',
        'Seeds are shared across settings: these are not independent aircraft replications.','',
        'Known calibration, starting state and nominal geometry are supplied. Passing supports',
        'this finite noise approximation; it does not establish uncertainty after fitting',
        'unknown calibration, a global nonlinear bound, actual instrument noise or calibrated confidence.',
        'No aircraft fit, accuracy screen or reserved confirmation group changes.','',
        '[Frozen plan](PLAN.md) · [Construction checks](../noisy-prediction-benchmark/nonlinear-construction-qualification/README.md) ·',
        '[Noise benchmark](../noisy-prediction-benchmark/README.md) · [Next analyses](../NEXT_STEPS.md).']
    return '\n'.join(lines)+'\n'


def remainder_components(errors,sigma):
    """Describe saved even terms and paired moments; never change a gate."""
    try:
        n=len(sigma)
        if (not n or len(errors)!=4 or any(len(v)!=n for v in errors)
                or any(len(row)!=3 or any(type(x) not in (int,float) or not math.isfinite(x) for x in row)
                    for rows in [sigma,*errors] for row in rows) or any(x<0 for row in sigma for x in row)):
            raise ValueError('complete finite matched curves and nonnegative deviations required')
        a,b,c,d=errors;axes={}
        for j,name in enumerate(('north','east','up')):
            even=[(a[i][j]+b[i][j])/2 for i in range(n)]
            half=[(c[i][j]+d[i][j])/2 for i in range(n)]
            fractions=[abs(v)/max(.001,.01*sigma[i][j]) for i,v in enumerate(even)]
            worst=max(range(n),key=lambda i:fractions[i])
            axes[name]=dict(maximum_even_remainder_m=max(abs(v) for v in even),
                maximum_remainder_fraction_of_limit=fractions[worst],worst_epoch_index=worst,
                maximum_quadratic_scaling_discrepancy_m=max(abs(v-4*w) for v,w in zip(even,half)))
        moment=lambda js:math.fsum((a[i][j]**2+b[i][j]**2)/2 for i in range(n) for j in js)/n
        predicted=lambda js:math.fsum(sigma[i][j]**2 for i in range(n) for j in js)/n
        return dict(axes=axes,paired_horizontal_mean_squared_error_m2=moment((0,1)),
            paired_height_mean_squared_error_m2=moment((2,)),predicted_horizontal_mean_squared_error_m2=predicted((0,1)),
            predicted_height_mean_squared_error_m2=predicted((2,)),independent_realizations=1,
            parameter_uncertainty_included=False,labels_changed=False,confidence_calibrated=False)
    except (TypeError,IndexError,OverflowError) as exc:raise ValueError('complete matched curves required') from exc


def remainder_diagnosis(root,prefix):
    """Saved-only localization and error-budget supplement to the sealed report."""
    verified=inspect(root,prefix)
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import digest
    import io
    import numpy as np
    study=ClosedStudy(root,prefix)
    try:
        rows=[]
        for setting in verified['rows']:
            if not setting['complete']:continue
            identity=setting['identity'];context=study.artifact(identity,'nominal-context.json')
            sigma=context['conditional_standard_deviation_neu_m'];details=[]
            for seed in range(26102500,26102516):
                with np.load(io.BytesIO(study.artifact(identity,f'seed-{seed}.npz',raw=True)),allow_pickle=False) as z:
                    details.append(dict(seed=seed,**remainder_components(z['errors_neu_m'].tolist(),sigma)))
            axes={axis:dict(failing_seed_count=sum(v['axes'][axis]['maximum_remainder_fraction_of_limit']>1 for v in details),
                maximum_even_remainder_m=max(v['axes'][axis]['maximum_even_remainder_m'] for v in details),
                maximum_quadratic_scaling_discrepancy_m=max(v['axes'][axis]['maximum_quadratic_scaling_discrepancy_m'] for v in details))
                for axis in ('north','east','up')}
            moments={key:math.fsum(v[key] for v in details)/len(details) for key in
                ('paired_horizontal_mean_squared_error_m2','paired_height_mean_squared_error_m2',
                 'predicted_horizontal_mean_squared_error_m2','predicted_height_mean_squared_error_m2')}
            rows.append(dict(identity=identity,original_passed=setting['passed'],axes=axes,**moments,
                horizontal_empirical_to_predicted_second_moment_ratio=moments['paired_horizontal_mean_squared_error_m2']/moments['predicted_horizontal_mean_squared_error_m2'],
                height_empirical_to_predicted_second_moment_ratio=moments['paired_height_mean_squared_error_m2']/moments['predicted_height_mean_squared_error_m2']))
        return dict(verified=True,rows=rows,manifest_sha256=verified['manifest_sha256'],
            input_hashes={name:digest(raw) for name,raw in study.cache.items()},
            labels_changed=False,known_calibration=True,independent_seeds_per_setting=16,seeds_shared_across_settings=True,
            native_calls=0,optimizer_starts=0,original_reads=0,protected_reads=0,confidence_calibrated=False)
    finally:study.close()


def metadata_environment():
    import sys
    from importlib.metadata import version
    return dict(python=sys.version,numpy_parser=version('numpy'),
        scope='saved arrays and scalar checks; no compilation, fitting or noise generation')


def publication_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/noise_nonlinearity_report.py','analysis/tests/test_noise_nonlinearity_report.py',
        'analysis/lll/studies/native_publication.py','analysis/lll/studies/qualification.py'])


def publish(root,prefix,*,qualification,output='docs/noise-nonlinearity'):
    if qualification is None:raise ValueError('source-bound saved-report qualification required')
    import json
    from pathlib import Path
    from lll.studies.artifacts import safe_path,atomic,encoded,digest
    from lll.studies.qualification import checked
    from lll.studies.native_publication import include_native_caches
    from lll.ilvis0_control_publication import publish as package
    root=Path(root).resolve();public=safe_path(root,output);data=safe_path(root,prefix)
    if (public/'evidence-receipt.json').exists():raise ValueError('closed publication already sealed')
    request,tests=checked(root,qualification,sources=publication_sources(root),environment=metadata_environment(),minimum_tests=12,
        required_tests=['test_saved_nonlinearity_recomputes_matched_metrics_with_scalar_arithmetic',
            'test_nonlinearity_audit_requires_closed_study_before_array_import',
            'test_nonlinearity_report_preserves_failed_settings_and_finite_scope'])
    report=inspect(root,prefix)
    package(data,public,render(report),plan='docs/noisy-prediction-benchmark/NONLINEAR_PLAN.md')
    if report['native_assets']:include_native_caches(root,data,public,entries=report['native_assets'],maximum_bytes=64*1024**2)
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    additions={'artifacts/publication/verified-report.json':encoded(report),
        'artifacts/publication/qualification-request.json':request,'artifacts/publication/qualification-report.xml':tests,
        'artifacts/publication/source/analysis/lll/noise_nonlinearity_report.py':Path(__file__).read_bytes(),
        'artifacts/publication/source/analysis/tests/test_noise_nonlinearity_report.py':
            (root/'analysis/tests/test_noise_nonlinearity_report.py').read_bytes()}
    for name,raw in additions.items():atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    if encoded(inspect(root,output))!=encoded(report):raise ValueError('publication audit differs')
    return dict(publication=output,artifacts=len(receipt['artifacts']),passed_settings=report['passed_settings'],
        native_calls=0,optimizer_starts=0,compaction_pending=True,confidence_calibrated=False)
