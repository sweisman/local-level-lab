# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only audit and publication for wider known-answer tangent controls."""


def inspect(root,prefix='data/esa-wide-tangent-controls-20261024'):
    from pathlib import Path
    from lll.studies.closed import ClosedStudy
    study=ClosedStudy(root,prefix)
    try:
        from lll.airquantumgrav_wide_controls import recipe,tasks,qualification_sources,SCOPE,environment
        from lll.airquantumgrav_gravity_controls import construction_limits
        from lll.airquantumgrav_gravity_report import case_gate
        from lll.airquantumgrav_geographic_report import construction_counts
        from lll.airquantumgrav_observation_report import native_accounting
        from lll.airquantumgrav_observed_report import verify_audit_environment
        from lll.studies.artifacts import digest
        from lll.studies.source_binding import verify
        from lll.ilvis0_wide_tangent import derive
        root=Path(root).resolve();r=study.input('recipe');env=study.input('qualification-environment')
        verify_audit_environment(env,environment())
        declared=study.input('qualification-request')['sources']
        if set(declared)!=set(qualification_sources(root)):raise ValueError('qualified source closure changed')
        verify(root,declared=declared,manifest=study.manifest['sources'])
        if (r!=recipe() or study.manifest['scope']!=SCOPE
                or {k:{a:b for a,b in v.items() if a not in ('index','shard')} for k,v in study.tasks.items()}
                !={t['identity']:t for t in tasks()}):raise ValueError('unchanged finite known-answer matrix required')
        parent=ClosedStudy(root,'docs/esa-gravity-controls')
        try:
            proof=study.input('qualified-parent');receipt=parent.read('evidence-receipt.json')
            if (proof['manifest_sha256']!=parent.completion['manifest_sha256']
                    or proof['summary_sha256']!=parent.completion['summary_sha256']
                    or proof['report_sha256']!=receipt['artifacts']['artifacts/publication/verified-report.json']):
                raise ValueError('qualified physical parent binding differs')
        finally:parent.close()
        operations={}
        for shard in range(study.manifest['allocation']['workers']):
            operations.update(native_accounting(study.read(f'shards/{shard:03d}/charges/journal.sqlite',raw=True),
                study.completion['manifest_sha256'],{k for k,v in study.tasks.items() if v['shard']==shard},per_call_visits=None))
        limits=construction_limits(r);rows=[];charges={k:0 for k in study.summary['charged']};binaries={'value':set(),'tangent':set()}
        for identity,task in study.tasks.items():
            if identity not in study.rows:continue
            envelope=study.envelope(identity);result=envelope['result'];artifacts=envelope['artifacts'];counts=operations[identity]
            for name,sha in artifacts.items():study.read(name,sha,raw=True)
            for k in charges:charges[k]+=envelope['charged'][k]
            if (counts['value']+counts['tangent']!=envelope['charged']['native_calls']
                    or counts['packet_visits']!=envelope['charged']['packet_visits']):raise ValueError('native charges differ')
            complete='coarse' in result and 'fine' in result;row=dict(identity=identity,complete=complete,result=result)
            name='artifacts/'+identity+'/construction.sqlite'
            constructed=construction_counts(study.read(name,artifacts[name],raw=True),study.completion['manifest_sha256'],identity,
                limits,complete=complete) if name in artifacts else None
            row['construction']=constructed
            if complete:
                if (constructed is None or constructed!=limits or result['native_calls']!=3
                        or result['constructed_intervals']!=limits['constructed_intervals']
                        or result['generated_samples']!=limits['generated_samples']
                        or counts['value']!=2 or counts['tangent']!=1 or counts['packet_visits']!=task['limits']['packet_visits']):
                    raise ValueError('exact two value and one derivative sweeps required')
                row['checked']=case_gate(result,[study.artifact(identity,f'rate-{hz}.json') for hz in r['rates_hz']],
                    study.artifact(identity,'tangent.json'),study.artifact(identity,'corrections.json'),study.artifact(identity,'answer.json'),r)
                meta=study.artifact(identity,'compilation.json');base='analysis/lll/ilvis0_tangent.cpp'
                source=study.read('source-freeze/'+base,study.manifest['sources'][base],raw=True)
                value,tangent=meta['value'],meta['tangent'];spec=task['payload']
                anchor=None if spec['gravity_model']=='constant' else (1500. if spec['height_profile']=='climb' else 3500.)
                if (value['source_sha256']!=study.manifest['sources']['analysis/lll/ilvis0_native.c']
                        or value['compiler']!=env['compilers']['cc'] or tangent['compiler']!=env['compilers']['c++']
                        or tangent['original_source_sha256']!=digest(source)
                        or tangent['source_sha256']!=digest(derive(source,expected_sha256=digest(source)))
                        or tangent['internal_mantissa_bits']<=53 or tangent['packet_clock_changed']
                        or tangent['gravity_anchor_height_m']!=anchor
                        or tangent['query_fraction']!='binary64-frozen' or tangent['profile_mapping']!='binary64-frozen'
                        or tangent['parameter_products']!='binary64-frozen'
                        or tangent['residual_subtraction']!='before-binary64-cast'):
                    raise ValueError('compiled wider method or fixed physical conventions differ')
                if anchor is not None and (value.get('gravity_model')!='inverse-square-height-v1' or value['gravity_anchor_height_m']!=anchor):
                    raise ValueError('value gravity anchor differs')
                if anchor is None and 'gravity_model' in value:raise ValueError('constant value interface changed')
                for k in binaries:binaries[k].add(meta[k]['binary_sha256'])
            elif result['passed']:raise ValueError('unfinished case cannot qualify')
            rows.append(row)
        if (charges!=study.summary['charged'] or any(len(v)>1 for v in binaries.values())
                or sum(v['value']+v['tangent'] for v in operations.values())!=charges['native_calls']):
            raise ValueError('whole-study native charges or binaries differ')
        complete=[v for v in rows if v['complete']];passed=sum(v['result']['passed'] for v in rows)
        return dict(verified=True,total=48,returned=len(rows),passed=passed,qualified=len(rows)==passed==48,
            rows=rows,charged=charges,elapsed_s=study.summary['elapsed_s'],
            maximum_coarse_3d_m=max((v['checked']['coarse']['maximum_3d_m'] for v in complete),default=None),
            maximum_fine_3d_m=max((v['checked']['fine']['maximum_3d_m'] for v in complete),default=None),
            maximum_value_disagreement_m=max((v['checked']['value_disagreement_m'] for v in complete),default=None),
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            original_reads=0,protected_reads=0,observed_starts=0,solver_qualified=False,confidence_calibrated=False,scientific_decision='abstain')
    finally:study.close()


def render(report):
    number=lambda k:'Unavailable' if report[k] is None else f"{report[k]:.6g} m"
    return '\n'.join(['# Wider-precision long motion controls','',
        f"**{report['passed']}/{report['total']} known-answer cases pass.**",'',
        'The twenty-minute generated tracks turn and climb or descend. All three',
        'physical models, both latitude signs, both processing cases and both gravity',
        'laws are retained. Initial state and calibration are supplied, not fitted.',
        'The unchanged value calculation and the wider tangent retain all 27 columns.','',
        '| Check | Largest error |','|---|---:|',
        '| 300 Hz spatial error | '+number('maximum_coarse_3d_m')+' |',
        '| 600 Hz spatial error | '+number('maximum_fine_3d_m')+' |',
        '| Value/tangent agreement | '+number('maximum_value_disagreement_m')+' |','',
        'This is not a solver qualification. It checks known motion and corrections;',
        'calibration estimation and stopping still need their own matched controls.',
        'No aircraft recording or protected confirmation group is opened.','',
        f"The run charged {report['charged']['native_calls']} native calls in {report['elapsed_s']/60:.2f} minutes.",
        '[Frozen plan](PLAN.md) · [Precision diagnostic](../esa-precision-diagnostic/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).',''])


def publish(root,prefix='data/esa-wide-tangent-controls-20261024',output='docs/esa-wide-tangent-controls'):
    import json
    from pathlib import Path
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import safe_path,atomic,digest,encoded
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('wide controls publication already sealed')
    report=inspect(root,prefix);package(data,public,render(report),plan='docs/esa-wide-tangent-controls/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    for name,raw in [('verified-report.json',encoded(report)),('reporter.py',Path(__file__).read_bytes())]:
        name='artifacts/publication/'+name;atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,native_calls=0)
