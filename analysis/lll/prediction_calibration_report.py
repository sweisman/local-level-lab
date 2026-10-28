# SPDX-License-Identifier: AGPL-3.0-or-later
"""Closed seed-family reporting and a finite calibration-to-validation handoff."""


def method_verification(policy,study,identity,spec,checked):
    """An explicit method auditor may add proof, never change a saved label."""
    provider=getattr(policy,'audit_fit',None)
    if provider is None:return {}
    if not callable(provider):raise ValueError('explicit callable method auditor required')
    evidence=provider(study,identity,spec)
    if (not isinstance(evidence,dict) or type(evidence.get('passed')) is not bool
            or evidence['passed'] is not checked['converged']):
        raise ValueError('independent method verification differs from saved convergence')
    return dict(method_verification=evidence)


def inspect(root,prefix,*,protocol=None):
    from lll.studies.closed import ClosedStudy
    s=ClosedStudy(root,prefix)
    try:
        from types import SimpleNamespace
        from lll.prediction_calibration_study import _protocol
        policy=_protocol(protocol)
        recipe,tasks,population,case_recipe=policy.recipe,policy.tasks,policy.population,policy.case_recipe
        EXCLUDED_SEEDS,SCOPE=policy.EXCLUDED_SEEDS,policy.SCOPE
        from lll.prediction_calibration import aggregate_draws,calibrate,validate
        from lll.independent_noisy_study import SCORE_INPUTS,score_records
        from lll.structured_noisy_publication import native_bindings,inspect_case,native_cache_entries
        from lll.airquantumgrav_inventory import environment
        from lll.studies.artifacts import encoded,digest
        r=s.input('recipe');role=r.get('role');pop=s.input('population');sha=pop['sha256'];env=s.input('qualification-environment')
        if (r!=recipe(role) or s.manifest['scope']!=SCOPE or env!=environment()
                or s.manifest['sources']!=pop['descriptor']['sources'] or pop!=population(s.manifest['sources'],env)
                or s.input('validation-policy')!=recipe('validation')):
            raise ValueError('unchanged closed phase, population, sources, environment and validation policy required')
        for name,expected in s.manifest['sources'].items():s.read('source-freeze/'+name,expected,raw=True)
        expected={v['identity']:v for v in tasks(role,sha)}
        if {k:{a:b for a,b in v.items() if a not in ('index','shard')} for k,v in s.tasks.items()}!=expected:
            raise ValueError('exact closed phase task matrix required')
        bindings=getattr(policy,'native_bindings',native_bindings)(s);rows=[];assets={};interrupted=False
        for identity,task in s.tasks.items():
            p=task['payload'];seed=p['draw_seed'];spec=p['case']
            row=dict(identity=identity,draw_seed=seed,role=role,**spec,complete=False,converged=False,accurate=False)
            if identity not in s.rows:rows.append(dict(row,reason='Not executed or no returned outcome'));continue
            envelope=s.envelope(identity);outcome=envelope['result'];base='artifacts/'+identity+'/'
            interrupted|=(outcome.get('error_type')=='BudgetStopped' or base+'family-futility.json' in envelope['artifacts'])
            draw=dict(seed=seed,role=role,case=spec,population_sha256=sha,
                calibration_draw=role=='calibration',validation_draw=role=='validation',confidence_calibrated=False)
            if base+'draw-identity.json' in envelope['artifacts'] and s.artifact(identity,'draw-identity.json')!=draw:
                raise ValueError('saved draw role or population differs')
            checked=inspect_case(s,identity,payload=spec,r=case_recipe(seed),bindings=bindings)
            marker=s.artifact(identity,'family-outcome.json') if base+'family-outcome.json' in envelope['artifacts'] else None
            if checked is None:
                if marker is not None and marker['complete']:raise ValueError('incomplete outcome carries a completed selection marker')
                rows.append(dict(row,reason=outcome.get('reason','Incomplete forecast')))
            else:
                records={name:s.artifact(identity,name) for name in SCORE_INPUTS};score=score_records(records,seed=seed)
                if (s.artifact(identity,'draw-identity.json')!=draw or encoded(s.artifact(identity,'prediction-score.json'))!=encoded(score)
                        or outcome['draw_seed']!=seed or outcome['role']!=role or outcome['population_sha256']!=sha
                        or outcome['maximum_standardized_error']!=score['maximum_standardized_error'] or outcome['confidence_calibrated']):
                    raise ValueError('saved score, seed or role differs from the independently checked forecast')
                fit=records['fit.json'];expected_marker=dict(manifest_sha256=s.completion['manifest_sha256'],identity=identity,
                    seed=seed,role=role,population_sha256=sha,case=spec,complete=True,converged=checked['converged'],
                    training_cost=fit['residual_sum_squares'],maximum_score=score['maximum_standardized_error'])
                if marker!=expected_marker:raise ValueError('family marker differs from sealed fit and score')
                proof=method_verification(policy,s,identity,spec,checked)
                rows.append(dict(row,complete=True,**checked,**proof,training_cost=fit['residual_sum_squares'],
                    maximum_standardized_error=score['maximum_standardized_error']))
                view=SimpleNamespace(tasks={identity:task},rows=s.rows,envelope=s.envelope,artifact=s.artifact,read=s.read)
                assets.update(native_cache_entries(view))
            # Retain shared sources/kernels, but release each case's raw buffers.
            if hasattr(s,'cache'):
                artifact=s.rows[identity]['artifact'];case_prefix=s.prefix+'/'+base
                for name in tuple(s.cache):
                    if name.startswith(case_prefix) or name==s.prefix+'/'+artifact:del s.cache[name]
                s.envelopes.pop(identity,None)
        draws=aggregate_draws(rows,s.tasks,role=role,population_sha256=sha,excluded_seeds=EXCLUDED_SEEDS)
        full=s.summary['completed']==len(s.tasks) and not interrupted;calibration=validation=None
        if full and role=='calibration':
            calibration=calibrate(draws,coverage=r['coverage'],confidence=r['confidence'],population_sha256=sha,excluded_seeds=EXCLUDED_SEEDS)
        if full and role=='validation':
            options={} if protocol is None else dict(protocol=protocol)
            h=s.input('calibration-handoff');check_handoff(h,population_sha256=sha,**options)
            validation=validate(h['calibration'],draws,confidence=r['confidence'],coverage=r['coverage'],population_sha256=sha)
        return dict(version='prediction-calibration-report-v1',verified=True,role=role,population_sha256=sha,
            total=len(s.tasks),returned_outcomes=s.summary['completed'],complete_forecasts=sum(v['complete'] for v in rows),
            numerically_converged=sum(v['converged'] for v in rows),raw_accuracy=sum(v['accurate'] for v in rows),
            returned_seed_families=len({s.tasks[k]['payload']['draw_seed'] for k in s.rows}),planned_seed_families=len(r['seeds']),
            rows=rows,draws=draws,calibration=calibration,validation=validation,validation_policy=s.input('validation-policy'),
            manifest_sha256=s.completion['manifest_sha256'],summary_sha256=s.completion['summary_sha256'],
            elapsed_s=s.summary['elapsed_s'],prepaid=s.summary['charged'],native_assets=assets,
            cohort_interrupted=interrupted,
            native_calls_during_audit=0,optimizer_starts=0,aircraft_coverage_established=False,scientific_decision='abstain')
    finally:s.close()


def build_handoff(report,*,protocol=None):
    from lll.prediction_calibration_study import _protocol
    policy=_protocol(protocol);recipe=policy.recipe;EXCLUDED_SEEDS=policy.EXCLUDED_SEEDS
    from lll.prediction_calibration import calibrate
    if (report.get('verified') is not True or report.get('role')!='calibration'
            or report.get('cohort_interrupted',False) or report['returned_outcomes']!=report['total']
            or report['total']!=24*len(recipe('calibration')['seeds'])):
        raise ValueError('entire closed calibration cohort required; no bounds from unexecuted draws')
    c=recipe('calibration');sha=report['population_sha256']
    calibration=calibrate(report['draws'],coverage=c['coverage'],confidence=c['confidence'],population_sha256=sha,excluded_seeds=EXCLUDED_SEEDS)
    value=dict(version='prediction-calibration-handoff-v1',population_sha256=sha,calibration=calibration,
        validation_policy=report['validation_policy'],evidence=dict(cohort_interrupted=False,
            **{k:report[k] for k in ('total','returned_outcomes','manifest_sha256','summary_sha256')}))
    options={} if protocol is None else dict(protocol=protocol)
    return check_handoff(value,population_sha256=sha,**options)


def check_handoff(value,*,population_sha256,protocol=None):
    from lll.prediction_calibration_study import _protocol,_population_hash
    policy=_protocol(protocol);recipe=policy.recipe;EXCLUDED_SEEDS=policy.EXCLUDED_SEEDS
    from lll.prediction_calibration import calibrate
    from lll.studies.artifacts import encoded
    if (value.get('version')!='prediction-calibration-handoff-v1' or value.get('population_sha256')!=population_sha256
            or value.get('validation_policy')!=recipe('validation')):
        raise ValueError('same frozen population and preregistered validation policy required')
    c=recipe('calibration');e=value['evidence'];saved=value['calibration']
    if (e.get('cohort_interrupted') is not False or e['total']!=24*len(c['seeds']) or e['returned_outcomes']!=e['total']
            or [v['seed'] for v in saved['records']]!=c['seeds']):raise ValueError('full disjoint calibration cohort required')
    _population_hash(e['manifest_sha256']);_population_hash(e['summary_sha256'])
    checked=calibrate(saved['records'],coverage=c['coverage'],confidence=c['confidence'],population_sha256=population_sha256,excluded_seeds=EXCLUDED_SEEDS)
    if checked['threshold'] is None or encoded(checked)!=encoded(saved):raise ValueError('finite independently reproducible calibration threshold required')
    return value


def calibration_handoff(root,prefix,*,protocol=None):
    options={} if protocol is None else dict(protocol=protocol)
    return build_handoff(inspect(root,prefix,**options),**options)


def render(report):
    phase=report['role'];lines=[f'# Prediction {phase}','',
        f"**{report['returned_outcomes']}/{report['total']} starts returned outcomes; "
        f"{report['numerically_converged']} pass numerical checks.**",'',
        f"{report['returned_seed_families']}/{report['planned_seed_families']} seed families returned work. "
        'Related settings and starts are not independent trials.','',
        f"{report['raw_accuracy']} raw forecasts pass the unchanged position-error screens.",
        'Each model fits its own generating truth; these are not Earth-model votes.','']
    result=report[phase]
    if result is None:lines.append('Statistical result not computed: the preassigned cohort is incomplete or stopped cooperatively.')
    elif phase=='calibration':
        lines.append('Finite calibration threshold: '+str(result['threshold']) if result['threshold'] is not None
            else 'No finite calibration threshold: unavailable forecasts remain in the cohort.')
    else:
        lines.append(f"Validation passes: {result['passed']}. Failures: {result['failures']}/{result['draws']}; "
            f"one-sided failure upper bound: {result['failure_upper']:.6g}.")
    lines+=['','These calculations apply only to the declared generated population.',
        'They establish neither aircraft error coverage nor Earth-model significance.','',
        '[All planned starts](results.csv) · [Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).']
    return '\n'.join(lines)+'\n'


def result_csv(report):
    import csv,io
    stream=io.StringIO(newline='');fields=['identity','draw_seed','role','law','model','profile','start',
        'complete','converged','accurate','training_cost','maximum_standardized_error','reason']
    writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n');writer.writeheader()
    for row in report['rows']:writer.writerow({k:row.get(k,'') for k in fields})
    return stream.getvalue()


def publish(root,prefix,*,qualification,output=None,protocol=None):
    if qualification is None:raise ValueError('source-bound phase qualification required before publication')
    import json
    from pathlib import Path
    from lll.prediction_calibration_study import qualification_sources,_protocol
    from lll.studies.qualification import checked
    from lll.studies.artifacts import atomic,encoded,digest,safe_path
    from lll.studies.native_publication import include_native_caches
    from lll.airquantumgrav_inventory import environment
    from lll.ilvis0_control_publication import publish as package,check
    root=Path(root).resolve();policy=_protocol(protocol);options={} if protocol is None else dict(protocol=protocol)
    source_provider=getattr(policy,'qualification_sources',qualification_sources)
    request,tests=checked(root,qualification,sources=source_provider(root),environment=environment(),minimum_tests=62,
        required_tests=['test_handoff_rejects_unexecuted_calibration_draws',
            'test_calibration_adapter_metadata_loads_in_real_frozen_namespace',
            'test_validation_futility_stops_at_fifth_distinct_family_not_four']
            +getattr(policy,'required_report_tests',[]))
    report=inspect(root,prefix,**options);output=output or 'docs/prediction-'+report['role']
    data=safe_path(root,prefix);public=safe_path(root,output)
    if public.parent!=root/'docs' or (public/'evidence-receipt.json').exists():raise ValueError('fresh top-level docs publication required')
    plan=getattr(policy,'plan','docs/prediction-score-qualification/EXECUTION_PLAN.md')
    package(data,public,render(report),plan=plan)
    if report['native_assets']:
        include_native_caches(root,data,public,entries=[dict(path=k,sha256=v) for k,v in sorted(report['native_assets'].items())],maximum_bytes=64*1024**2)
    extras={'results.csv':result_csv(report).encode(),'artifacts/publication/verified-report.json':encoded(report),
        'artifacts/publication/qualification-request.json':request,'artifacts/publication/qualification-report.xml':tests}
    if report['calibration'] is not None and report['calibration']['threshold'] is not None:
        extras['calibration-handoff.json']=encoded(build_handoff(report,**options))
    if report['validation'] is not None:extras['validation-result.json']=encoded(report['validation'])
    for name in ('CALIBRATION_PLAN.md','CALIBRATION_TARGETS_PLAN.md','CAMPAIGN_SIZING.md'):
        extras[name]=f'# Related plan\n\nSee [{name}](../prediction-score-qualification/{name}).\n'.encode()
    if (data/'stop-request.json').exists():extras['stop-request.json']=(data/'stop-request.json').read_bytes()
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    for name,raw in extras.items():atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt));check(data,public)
    if encoded(inspect(root,output,**options))!=encoded(report):raise ValueError('publication replay differs from its closed source')
    return dict(publication=output,artifacts=len(receipt['artifacts']),role=report['role'],returned=report['returned_outcomes'],
        native_calls=0,optimizer_starts=0,compaction_pending=True,aircraft_coverage_established=False)
