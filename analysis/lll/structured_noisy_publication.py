# SPDX-License-Identifier: AGPL-3.0-or-later
"""Closed-study audit and publication, with no native work or regenerated data."""


def inspect(root,prefix):
    from .studies.closed import ClosedStudy
    from .structured_noisy_training import SCOPE,recipe,tasks,limits
    from .structured_noisy_report import check_case
    from .airquantumgrav_geographic_report import construction_counts
    from .studies.artifacts import digest
    from .ilvis0_wide_tangent import derive as wide_source
    from .ilvis0_noise_step import derive as noise_source
    study=ClosedStudy(root,prefix)
    try:
        r=study.input('recipe')
        env=study.input('qualification-environment');hashes=study.manifest['sources']
        cpp='analysis/lll/ilvis0_tangent.cpp';bridge='analysis/lll/ilvis0_noise_bridge.cpp';loader='analysis/lll/ilvis0_wide_tangent.py'
        raw=study.read('source-freeze/'+cpp,hashes[cpp],raw=True)
        wide_sha=digest(wide_source(raw,expected_sha256=hashes[cpp]))
        bridge_sha=digest(noise_source(raw,study.read('source-freeze/'+bridge,hashes[bridge],raw=True),
            expected_source_sha256=hashes[cpp],expected_bridge_sha256=hashes[bridge],expected_wide_loader_sha256=hashes[loader]))
        if r!=recipe() or study.manifest['scope']!=SCOPE:raise ValueError('frozen recipe or scope differs')
        expected={t['identity']:t for t in tasks(r)}
        if {k:{a:b for a,b in v.items() if a not in ('index','shard')} for k,v in study.tasks.items()}!=expected:
            raise ValueError('frozen task matrix differs')
        rows=[];attempted=0
        names=('fit.json','forecast.json','input-binding.json','forecast-binding.json','training-receiver.json',
            'training-observations.json','scoring-observations.json','scores.json','compilation.json',
            'forecast-error-diagnostic.json','conditional-scores.json','training-error-operator.json',
            'native-operation-summary.json')
        for identity,task in study.tasks.items():
            row=dict(identity=identity,**task['payload'],complete=False,converged=False,accurate=False)
            if identity not in study.rows:rows.append(dict(row,reason='No returned outcome'));continue
            envelope=study.envelope(identity);result=envelope['result']
            for path,sha in envelope['artifacts'].items():study.read(path,sha,raw=True)
            if 'converged' not in result:
                rows.append(dict(row,reason=result.get('reason','Interrupted')));continue
            saved={name:study.artifact(identity,name) for name in names}
            tm=saved['compilation.json']['tangent'];nm=saved['compilation.json']['noise_bridge']
            if (tm['source_sha256']!=wide_sha or nm['source_sha256']!=bridge_sha
                    or tm['original_source_sha256']!=hashes[cpp] or nm['original_source_sha256']!=hashes[cpp]
                    or nm['bridge_source_sha256']!=hashes[bridge] or nm['wide_loader_source_sha256']!=hashes[loader]
                    or tm['compiler']!=env['compilers']['c++'] or nm['compiler']!=env['compilers']['c++']
                    or tm['gravity_anchor_height_m']!=saved['input-binding.json']['gravity_anchor_height_m']
                    or tm['internal_mantissa_bits']!=nm['internal_mantissa_bits'] or tm['internal_mantissa_bits']<=53):
                raise ValueError('native source, compilation or gravity anchor differs')
            kernel_path=f"shards/{task['shard']:03d}/kernels/"
            study.read(kernel_path+'wide-tangent-'+wide_sha+'.so',tm['binary_sha256'],raw=True)
            study.read(kernel_path+nm['binary_file'],nm['binary_sha256'],raw=True)
            checked=check_case(task['payload'],result,saved,r=r)
            prepaid=study.artifact(identity,'native-prepayment.json');charge=envelope['charged']
            if (prepaid['state']!='complete' or prepaid['prepaid']!={k:charge[k] for k in ('native_calls','packet_visits')}
                    or prepaid['attempted']!={k:saved['native-operation-summary.json'][k] for k in ('native_calls','packet_visits')}):
                raise ValueError('prepaid native work and attempted-operation summary differ')
            _,construction=limits(r,task['payload']['law'])
            construction_counts(study.artifact(identity,'construction.sqlite',raw=True),
                study.completion['manifest_sha256'],identity,construction,complete=True)
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
