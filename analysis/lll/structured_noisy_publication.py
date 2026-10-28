# SPDX-License-Identifier: AGPL-3.0-or-later
"""Closed-study audit and publication, with no native work or regenerated data."""


CASE_ARTIFACTS=('fit.json','forecast.json','input-binding.json','forecast-binding.json','training-receiver.json',
    'training-observations.json','scoring-observations.json','scores.json','compilation.json',
    'forecast-error-diagnostic.json','conditional-scores.json','training-error-operator.json',
    'native-operation-summary.json')


def native_bindings(study):
    """Derive expected native identities from the closed source, never compile."""
    from .studies.artifacts import digest
    from .ilvis0_wide_tangent import derive as wide_source
    from .ilvis0_noise_step import derive as noise_source
    hashes=study.manifest['sources'];cpp='analysis/lll/ilvis0_tangent.cpp'
    bridge='analysis/lll/ilvis0_noise_bridge.cpp';loader='analysis/lll/ilvis0_wide_tangent.py'
    raw=study.read('source-freeze/'+cpp,hashes[cpp],raw=True)
    return dict(wide_sha256=digest(wide_source(raw,expected_sha256=hashes[cpp])),
        bridge_sha256=digest(noise_source(raw,study.read('source-freeze/'+bridge,hashes[bridge],raw=True),
            expected_source_sha256=hashes[cpp],expected_bridge_sha256=hashes[bridge],expected_wide_loader_sha256=hashes[loader])),
        compiler=study.input('qualification-environment')['compilers']['c++'])


def inspect_case(study,identity,*,payload,r,bindings=None):
    """Shared sealed-case physics/accounting checks; retain unfinished outcomes."""
    from .structured_noisy_report import check_case
    from .structured_noisy_training import limits
    from .airquantumgrav_geographic_report import construction_counts
    envelope=study.envelope(identity);result=envelope['result']
    for path,sha in envelope['artifacts'].items():study.read(path,sha,raw=True)
    if 'converged' not in result:return None
    bindings=native_bindings(study) if bindings is None else bindings
    hashes=study.manifest['sources'];wide_sha=bindings['wide_sha256'];bridge_sha=bindings['bridge_sha256']
    cpp='analysis/lll/ilvis0_tangent.cpp';bridge='analysis/lll/ilvis0_noise_bridge.cpp';loader='analysis/lll/ilvis0_wide_tangent.py'
    saved={name:study.artifact(identity,name) for name in CASE_ARTIFACTS}
    tm=saved['compilation.json']['tangent'];nm=saved['compilation.json']['noise_bridge']
    if (tm['source_sha256']!=wide_sha or nm['source_sha256']!=bridge_sha
            or tm['original_source_sha256']!=hashes[cpp] or nm['original_source_sha256']!=hashes[cpp]
            or nm['bridge_source_sha256']!=hashes[bridge] or nm['wide_loader_source_sha256']!=hashes[loader]
            or tm['compiler']!=bindings['compiler'] or nm['compiler']!=bindings['compiler']
            or tm['gravity_anchor_height_m']!=saved['input-binding.json']['gravity_anchor_height_m']
            or tm['internal_mantissa_bits']!=nm['internal_mantissa_bits'] or tm['internal_mantissa_bits']<=53):
        raise ValueError('native source, compilation or gravity anchor differs')
    task=study.tasks[identity];kernel_path=f"shards/{task['shard']:03d}/kernels/"
    study.read(kernel_path+tm.get('binary_file','wide-tangent-'+wide_sha+'.so'),tm['binary_sha256'],raw=True)
    study.read(kernel_path+nm['binary_file'],nm['binary_sha256'],raw=True)
    checked=check_case(payload,result,saved,r=r)
    prepaid=study.artifact(identity,'native-prepayment.json');charge=envelope['charged']
    if (prepaid['state']!='complete' or prepaid['prepaid']!={k:charge[k] for k in ('native_calls','packet_visits')}
            or prepaid['attempted']!={k:saved['native-operation-summary.json'][k] for k in ('native_calls','packet_visits')}):
        raise ValueError('prepaid native work and attempted-operation summary differ')
    _,construction=limits(r,payload['law'])
    construction_counts(study.artifact(identity,'construction.sqlite',raw=True),
        study.completion['manifest_sha256'],identity,construction,complete=True)
    construction_counts(study.artifact(identity,'worker-build-journal.sqlite',raw=True),
        study.completion['manifest_sha256'],'worker',dict(builds=2),complete=True)
    return checked


def inspect(root,prefix):
    from .studies.closed import ClosedStudy
    from .structured_noisy_training import SCOPE,recipe,tasks
    study=ClosedStudy(root,prefix)
    try:
        r=study.input('recipe')
        if r!=recipe() or study.manifest['scope']!=SCOPE:raise ValueError('frozen recipe or scope differs')
        expected={t['identity']:t for t in tasks(r)}
        if {k:{a:b for a,b in v.items() if a not in ('index','shard')} for k,v in study.tasks.items()}!=expected:
            raise ValueError('frozen task matrix differs')
        bindings=native_bindings(study);rows=[];attempted=0
        for identity,task in study.tasks.items():
            row=dict(identity=identity,**task['payload'],complete=False,converged=False,accurate=False)
            if identity not in study.rows:rows.append(dict(row,reason='No returned outcome'));continue
            checked=inspect_case(study,identity,payload=task['payload'],r=r,bindings=bindings)
            if checked is None:
                result=study.envelope(identity)['result']
                rows.append(dict(row,reason=result.get('reason','Interrupted')));continue
            attempted+=checked['native_calls'];rows.append(dict(row,complete=True,**checked))
        return dict(verified=True,total=len(expected),complete=sum(r['complete'] for r in rows),
            numerically_converged=sum(r['converged'] for r in rows),raw_accuracy=sum(r['accurate'] for r in rows),
            conditional_accuracy=sum(r.get('conditional_prediction',{}).get('accuracy',{}).get('passed',False) for r in rows),
            qualified=all(r['complete'] and r['converged'] and r['accurate']
                and r['conditional_prediction']['accuracy']['passed'] for r in rows),
            rows=rows,attempted_native_calls=attempted,prepaid=study.summary['charged'],
            elapsed_s=study.summary['elapsed_s'],original_reads=0,protected_reads=0,native_calls_during_audit=0,
            confidence_calibrated=False,scientific_decision='abstain')
    finally:study.close()


def _checked_report(report):
    rows=report.get('rows',[])
    if (report.get('verified') is not True or len(rows)!=report.get('total')
            or sum(r['complete'] for r in rows)!=report['complete']
            or sum(r['converged'] for r in rows)!=report['numerically_converged']
            or sum(r['accurate'] for r in rows)!=report['raw_accuracy']):
        raise ValueError('verified report with matching case counts required')
    return rows


def render(report):
    rows=_checked_report(report);n=report['total'];complete=[r for r in rows if r['complete']]
    def span(key):
        values=[r['prediction'][key] for r in complete]
        return 'unavailable' if not values else f'{min(values):.2f}–{max(values):.2f} m'
    boundary=sum(any(abs(v)>=1-1e-6 for v in r.get('normalized_parameters',{}).values()) for r in complete)
    lines=['# Noisy calibration and later-position prediction','',
        f"**{report['raw_accuracy']}/{n} raw forecasts meet the physical error limits; "
        f"{report['numerically_converged']}/{n} pass the numerical stopping checks.**",'',
        f"Later horizontal RMS is {span('horizontal_rms_m')}; height RMS is {span('vertical_rms_m')}.",
        f"All {report['conditional_accuracy']}/{n} earlier-error-conditioned forecasts also meet the physical screen.",'',
        'The study uses generated two-minute turning and climbing records with known IMU and receiver errors.',
        'Calibration uses 79 earlier positions; 40 later positions are withheld until the forecasts are saved.',
        'Both recorded-increment and endpoint-shared rate-sample error formats are tested.',
        'Each candidate predicts its own generating truth: these are not Earth-model votes.','',
        f'{boundary}/{len(complete)} completed fits reach at least one calibration boundary.',
        'The unrestricted linear uncertainty calculation cannot certify those boundary cases.',
        'Accurate point forecasts therefore do not establish calibrated confidence.','',
        '**The complete prediction/uncertainty gate is not qualified.** All numerical failures and',
        'unsupported calibration cases remain recorded. The original twenty-minute noisy failure',
        'and the 53-stretch findings are unchanged.','',
        '[Complete results CSV](results.csv) · [Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md)','',
        '| Case | Numerical pass | Later horizontal RMS | Later height RMS | Calibration diagnostic |',
        '|---|---|---:|---:|---|']
    for row in rows:
        if row['complete']:
            fields=[row['identity'],'Yes' if row['converged'] else 'No',
                f"{row['prediction']['horizontal_rms_m']:.3f} m",f"{row['prediction']['vertical_rms_m']:.3f} m",
                row['linear_calibration_status'].replace('_',' ')]
        else:fields=[row['identity'],'Unavailable','Unavailable','Unavailable',row.get('reason','No saved fit')]
        lines.append('| '+' | '.join(fields)+' |')
    lines+=['',f"Wall time: {report['elapsed_s']/60:.2f} minutes. "
        f"Attempted native calls: {report['attempted_native_calls']:,}; "
        f"prepaid allowance: {report['prepaid']['native_calls']:,}.",'',
        'The error-conditioned physical-position target omits future receiver-error contributions.',
        'No later receiver coordinates choose weights or corrections. Original aircraft and',
        'protected confirmation recordings are not inputs.','',
        '[Software qualification](../integrated-noise-covariance/shared-native-protocol-qualification/README.md) ·',
        '[Reproducibility](../REPRODUCIBILITY.md).']
    return '\n'.join(lines)+'\n'


def result_csv(report):
    import csv,io
    rows=_checked_report(report);stream=io.StringIO(newline='')
    fields=['identity','law','model','profile','start','complete','numerical_pass','raw_accuracy',
        'raw_horizontal_rms_m','raw_height_rms_m','conditional_horizontal_rms_m','conditional_height_rms_m',
        'linear_calibration_status','parameters_at_bounds']
    writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n');writer.writeheader()
    for r in rows:
        row={k:r[k] for k in ('identity','law','model','profile','start','complete')}
        row.update(numerical_pass=r['converged'],raw_accuracy=r['accurate'])
        if r['complete']:
            row.update(raw_horizontal_rms_m=r['prediction']['horizontal_rms_m'],
                raw_height_rms_m=r['prediction']['vertical_rms_m'],
                conditional_horizontal_rms_m=r['conditional_prediction']['horizontal_rms_m'],
                conditional_height_rms_m=r['conditional_prediction']['vertical_rms_m'],
                linear_calibration_status=r['linear_calibration_status'],
                parameters_at_bounds=';'.join(k for k,v in r.get('normalized_parameters',{}).items() if abs(v)>=1-1e-6))
        writer.writerow(row)
    return stream.getvalue()


def publication_sources(root):
    from .studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/structured_noisy_publication.py',
        'analysis/tests/test_structured_noisy_publication.py','analysis/lll/studies/native_publication.py',
        'analysis/tests/test_native_publication.py','analysis/lll/studies/qualification.py',
        'docs/structured-noisy-training/PLAN.md'])


def native_cache_entries(study,*,compilation_name='compilation.json',require_fit_status=True):
    """Select only the explicitly bound caches used by complete saved cases."""
    import json
    from pathlib import Path
    from .studies.artifacts import digest
    entries={}
    for identity,task in study.tasks.items():
        if identity not in study.rows:continue
        envelope=study.envelope(identity)
        if require_fit_status and 'converged' not in envelope['result']:continue
        if not require_fit_status and 'artifacts/'+identity+'/'+compilation_name not in envelope['artifacts']:continue
        meta=study.artifact(identity,compilation_name);tm=meta['tangent'];nm=meta['noise_bridge']
        base=f"shards/{task['shard']:03d}/kernels/"
        entries[base+tm.get('source_file','wide-tangent-'+tm['source_sha256']+'.cpp')]=tm['source_sha256']
        entries[base+tm.get('binary_file','wide-tangent-'+tm['source_sha256']+'.so')]=tm['binary_sha256']
        entries[base+nm['source_file']]=nm['source_sha256'];entries[base+nm['binary_file']]=nm['binary_sha256']
        modern=[nm]+([tm] if 'cache_sha256' in tm else [])
        for meta in modern:
            cache=base+str(Path(meta['binary_file']).with_suffix('.json'))
            raw=study.read(cache,raw=True);value=json.loads(raw)
            if any(value[k]!=meta[k] for k in ('source_sha256','binary_sha256','compiler','compiler_executable',
                    'flags','cache_sha256','source_file','binary_file')):
                raise ValueError('native cache binding differs from the saved compilation')
            entries[cache]=digest(raw)
        entries[base+'builds.sqlite']=digest(study.read(base+'builds.sqlite',raw=True))
    return entries


def publish(root,prefix,output='docs/structured-noisy-training',*,qualification):
    import json
    from pathlib import Path
    from .studies.closed import ClosedStudy
    from .studies.artifacts import atomic,digest,encoded,safe_path
    from .studies.native_publication import include_native_caches
    from .ilvis0_control_publication import publish as package
    from .studies.publication import archive_publication
    from .studies.qualification import checked
    from .airquantumgrav_inventory import environment
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('publication is already sealed')
    request,tests=checked(root,qualification,sources=publication_sources(root),environment=environment(),
        required_tests=['test_render_separates_accuracy_numerical_failure_and_calibration_limits',
            'test_render_refuses_an_unverified_result','test_result_csv_preserves_both_starts_and_the_failed_case',
            'test_native_publication_adds_only_explicit_closed_cache_files'],minimum_tests=16)
    report=inspect(root,prefix);study=ClosedStudy(root,prefix)
    try:
        entries=native_cache_entries(study)
    finally:study.close()
    package(data,public,render(report),plan='docs/structured-noisy-training/PLAN.md')
    if entries:include_native_caches(root,data,public,
        entries=[dict(path=n,sha256=sha) for n,sha in sorted(entries.items())],maximum_bytes=64*1024**2)
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    additions={'artifacts/publication/verified-report.json':encoded(report),'results.csv':result_csv(report).encode(),
        'artifacts/publication/qualification-request.json':request,'artifacts/publication/qualification-report.xml':tests}
    for name in ('analysis/lll/structured_noisy_publication.py','analysis/lll/studies/native_publication.py',
                 'analysis/tests/test_structured_noisy_publication.py'):
        additions['artifacts/publication/source/'+name]=(root/name).read_bytes()
    for name,raw in additions.items():
        atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    compacted=archive_publication(root,data,public)
    restored=inspect(root,output)
    if encoded(restored)!=encoded(report):raise ValueError('archived saved-data audit differs after publication')
    return dict(compacted,complete=report['complete'],numerically_converged=report['numerically_converged'],
        raw_accuracy=report['raw_accuracy'],conditional_accuracy=report['conditional_accuracy'],
        qualified=report['qualified'],publication_artifacts=len(receipt['artifacts']))
