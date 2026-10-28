# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit native regressions using shared input, forecast and cache verifiers."""
import math


def replays_exact(points,replayed,*,expected_count=4):
    if type(expected_count) is not int or expected_count<1:
        raise ValueError('explicit positive original-reference count required')
    ids=[p['identity'] for p in points]
    return (len(ids)==expected_count and len(set(ids))==expected_count
            and len(replayed)==expected_count and len(set(replayed))==expected_count
            and set(replayed)==set(ids))


def audit_verification(fit,*,expected_columns=27):
    from lll.timing_stopping_report import _cost,_close,_stationarity
    n=expected_columns
    if (type(n) is not int or n not in (26,27)
            or fit['version']!='ilvis0-timing-cell-verification-v1' or len(fit['active_parameters'])!=n
            or fit['maximum_evaluations']!=200 or not 1<=fit['evaluations']<=200
            or not 0<=fit['linear_solves']<=620 or fit['final_verification_reserve']!=36):
        raise ValueError('full columns and unchanged complete optimizer allowance required')
    r=fit['local_linearization']['residual'];j=fit['local_linearization']['jacobian'];u=fit['normalized_parameters']
    if (len(u)!=n or len(j)!=len(r) or not r or any(len(a)!=n for a in j)
            or any(not math.isfinite(x) for a in [u,r,*j] for x in a) or any(abs(v)>1 for v in u)
            or not _close(_cost(r),fit['residual_sum_squares'])):raise ValueError('finite complete final linearization required')
    near=fit['near_zero_probe'];probe=fit['stability_probe'];ordinary=fit['ordinary_stability_probe'] if near is not None else probe
    if fit['linear_solves']!=fit['optimizer_linear_solves']+ordinary.get('linear_solves',0):
        raise ValueError('main and verification linear operation counts differ')
    if near is not None:
        passed=bool(near['passed'] and max(near['computed_costs'])<=1e-8 and max(near['stationarity'])<=1e-4
            and max(near['position_rms_neu_m'])<=.001 and max(near['position_max_abs_neu_m'])<=.01)
        if fit['converged'] is not passed:raise ValueError('near-zero verified label differs')
        return dict(passed=passed,cells=0,columns=n,mode='existing_near_zero')
    if not probe['passed']:
        if fit['converged'] or fit['stability_verified']:raise ValueError('failed verification cannot converge')
        return dict(passed=False,cells=len(probe.get('cells',[])),columns=n,reason=probe.get('reason','failed'))
    cells=probe.get('cells',[])
    if (not 1<=len(cells)<=17 or len(fit['timing_geometry'])!=1
            or len(fit['timing_geometry'][0]['cells'])!=len(cells) or probe['linear_solves']!=len(cells)):
        raise ValueError('every local timing cell must be retained')
    cost=_cost(r)
    for cell in cells:
        rr,jj,p=(cell[k] for k in ('residual','jacobian','point'));delta=cell['position_delta_neu_m']
        if (not cell['linear']['linear_success'] or len(rr)!=len(r) or len(jj)!=len(r)
                or len(p)!=n or any(len(a)!=n for a in jj) or len(delta)*3!=len(r)
                or any(len(a)!=3 for a in delta)
                or any(not math.isfinite(x) for a in [rr,p,*jj,*delta] for x in a)):
            raise ValueError('complete finite cell derivatives and actual physical changes required')
        actual=_cost(rr);change=abs(actual-cost)/max(actual,cost,1.);stationarity=_stationarity(p,rr,jj)
        rms=[math.sqrt(math.fsum(v[k]**2 for v in delta)/len(delta)) for k in range(3)]
        maximum=[max(abs(v[k]) for v in delta) for k in range(3)]
        flags=dict(cost_stable=change<=1e-8,stationary=stationarity<=1e-4,
            position_stable=max(rms)<=.001 and max(maximum)<=.01)
        if (not _close(cell['actual_cost'],actual) or not _close(cell['relative_cost_change'],change)
                or not _close(cell['fresh_stationarity'],stationarity)
                or len(cell['position_rms_neu_m'])!=3 or len(cell['position_max_abs_neu_m'])!=3
                or any(not _close(a,b) for a,b in zip(cell['position_rms_neu_m'],rms))
                or any(not _close(a,b) for a,b in zip(cell['position_max_abs_neu_m'],maximum))
                or any(cell[k] is not v for k,v in flags.items()) or cell['passed'] is not all(flags.values())):
            raise ValueError('cell metric differs from independent arithmetic')
    passed=all(c['passed'] for c in cells) and _stationarity(u,r,j)<=1e-4
    if fit['converged'] is not passed or fit['stability_verified'] is not passed:
        raise ValueError('final convergence differs from complete timing verification')
    return dict(passed=passed,cells=len(cells),columns=n,mode='all_local_timing_cells')


def describe_failures(fit,*,time_scale):
    """Describe saved failed cells without evaluating any proposed point again."""
    if not math.isfinite(time_scale) or time_scale<=0:raise ValueError('declared positive timing scale required')
    column=fit['active_parameters'].index('time_offset');point=fit['normalized_parameters'][column]
    rows=[]
    for c in fit['stability_probe'].get('cells',[]):
        if c['passed']:continue
        g=fit['timing_geometry'][0]['cells'][c['index']]
        rows.append(dict(cell_index=c['index'],reason=c.get('reason','fresh_cell_not_stable'),
            anchor_distance_s=abs(g['anchor']-point)*time_scale,anchor_s=g['anchor']*time_scale,
            fitted_offset_s=point*time_scale,cell_lower_s=g['lower']*time_scale,cell_upper_s=g['upper']*time_scale,
            relative_cost_change=c.get('relative_cost_change'),cost_limit=1e-8,
            cost_stable=c.get('cost_stable'),stationary=c.get('stationary'),position_stable=c.get('position_stable'),
            maximum_position_rms_m=max(c.get('position_rms_neu_m',[0.])),
            maximum_position_change_m=max(c.get('position_max_abs_neu_m',[0.]))))
    return rows


def inspect(root,prefix,*,definition=None):
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import encoded
    from lll import timing_optimizer_native_study as original
    from lll.timing_optimizer_native_study import case_recipe,computational_payload,reference_count
    from lll.compensated_prediction_release import native_bindings
    from lll.structured_noisy_publication import inspect_case,native_cache_entries
    from lll.coordinate_optimizer_report import compare_starts
    from lll.airquantumgrav_geographic_report import construction_counts
    from lll.airquantumgrav_inventory import environment
    s=ClosedStudy(root,prefix)
    try:
        policy=original if definition is None else definition
        actual=[{k:v for k,v in t.items() if k not in ('index','shard')} for t in s.manifest['tasks']]
        if (s.manifest['scope']!=policy.SCOPE or actual!=policy.tasks() or s.input('configuration')!=policy.configuration()
                or s.input('qualification-environment')!=environment()):raise ValueError('same finite four-case regression required')
        policy.verify_gate(s.input('analytical-gate'),s.input('analytical-binding'),s.manifest['sources'],environment())
        for name,sha in s.manifest['sources'].items():s.read('source-freeze/'+name,sha,raw=True)
        bindings=native_bindings(s);points=s.input('points');old={p['identity']:p for p in points}
        key_for=getattr(policy,'pair_key',lambda task:task['payload']['draw_seed'])
        pair_fields=getattr(policy,'pair_metadata',lambda key:dict(seed=key))
        payload_for=getattr(policy,'computational_payload',computational_payload)
        required=getattr(policy,'require_original_match',True)
        rows=[];groups={key_for(t):{} for t in policy.tasks()};failures=[];verification_failures=[]
        attempted=dict(native_calls=0,packet_visits=0);linear=0;replayed=[]
        for identity,task in s.tasks.items():
            if identity not in s.rows:failures.append(dict(identity=identity,reason='unexecuted'));continue
            envelope=s.envelope(identity);base='artifacts/'+identity+'/'
            for name,sha in envelope['artifacts'].items():s.read(name,sha,raw=True)
            if base+'native-prepayment.json' in envelope['artifacts']:
                for k,v in s.artifact(identity,'native-prepayment.json')['attempted'].items():attempted[k]+=v
            if base+'timing-linear.sqlite' in envelope['artifacts']:
                charged=construction_counts(s.artifact(identity,'timing-linear.sqlite',raw=True),s.completion['manifest_sha256'],
                    identity,dict(linear_solves=620),complete=False)['linear_solves'];linear+=charged
            else:charged=0
            payload=task['payload'];spec=payload['case'];r=getattr(policy,'case_recipe',case_recipe)(payload['draw_seed'])
            checked=inspect_case(s,identity,payload=spec,r=r,bindings=bindings)
            if checked is None:
                failures.append(dict(identity=identity,reason=envelope['result'].get('reason','incomplete')));continue
            fit=s.artifact(identity,'fit.json');verification=audit_verification(fit,
                expected_columns=getattr(policy,'column_count',lambda spec:27)(spec))
            verification_failures.extend(dict(identity=identity,**v) for v in describe_failures(fit,time_scale=r['limits']['time_offset']))
            if fit['linear_solves']!=charged:raise ValueError('saved linear accounting differs')
            replay=s.artifact(identity,'original-binding-replay.json')
            expected=[p for p in old.values() if payload_for(p['payload'])==payload]
            original=expected[0] if len(expected)==1 else None
            if (len(expected)>1 or required and original is None or not replay['exact'] or replay['original_labels_changed']
                    or replay['original_identity']!=(original['identity'] if original else None)
                    or replay['original_fit_converged']!=(original['saved_converged'] if original else None)
                    or not required and replay.get('matched_identities')!=[p['identity'] for p in expected]
                    or original is not None and any(encoded(s.artifact(identity,n))!=encoded(v) for n,v in original['artifacts'].items())):
                raise ValueError('original inputs, weights, identities or labels changed')
            if original is not None:replayed.append(original['identity'])
            passed=bool(checked['converged'] and checked['accurate'] and verification['passed'])
            if passed!=envelope['result']['passed']:raise ValueError('numerical/physical qualification label differs')
            forecast=s.artifact(identity,'forecast.json');training=s.artifact(identity,'training-observations.json')
            groups[key_for(task)][spec['start']]=dict(fit=fit,forecast=forecast,training=training,
                binding=s.artifact(identity,'input-binding.json'))
            rows.append(dict(identity=identity,seed=payload['draw_seed'],start=spec['start'],passed=passed,
                converged=fit['converged'],original_fit_converged=original['saved_converged'] if original else None,
                verification_reason=fit['stability_probe'].get('reason'),
                cost=fit['residual_sum_squares'],evaluations=fit['evaluations'],linear_solves=charged,cells=verification['cells'],
                prediction_horizontal_rms_m=envelope['result']['prediction']['horizontal_rms_m'],
                prediction_height_rms_m=envelope['result']['prediction']['vertical_rms_m'],original_labels_changed=False,
                **getattr(policy,'row_metadata',lambda task:{})(task)))
        pairs=[dict(**pair_fields(k),**compare_starts(v)) for k,v in groups.items()]
        exact=replays_exact(points,replayed,expected_count=reference_count(policy))
        assets=native_cache_entries(s,require_fit_status=False)
        for name,sha in assets.items():s.read(name,sha,raw=True)
        return dict(version='timing-optimizer-native-regression-report-v1',verified=True,selected=len(s.tasks),complete=len(rows),
            rows=rows,pairs=pairs,failures=failures,verification_failures=verification_failures,
            native_qualified=len(rows)==len(s.tasks) and not failures and exact
                and all(v['passed'] for v in rows) and all(v['passed'] for v in pairs),
            original_binding_replays_exact=exact,actual_native=attempted,linear_solves=linear,native_assets=assets,
            elapsed_s=s.summary['elapsed_s'],manifest_sha256=s.completion['manifest_sha256'],summary_sha256=s.completion['summary_sha256'],
            original_labels_changed=False,original_reads=0,protected_reads=0,confidence_calibrated=False,native_calls_during_audit=0)
    finally:s.close()


def render(report):
    lines=['# Native regressions of timing-aware stopping','',
        f"Completed {report['complete']}/{report['selected']} original-start fits; {sum(r['passed'] for r in report['rows'])} pass numerical and physical checks.",
        'These generated-data regressions add no aircraft observation or statistical confidence claim.','',
        '| Case | Earlier fit passed | New fit passed | Evaluations | Later horizontal RMS | Later height RMS |',
        '|---|---|---|---:|---:|---:|']
    for i,r in enumerate(report['rows'],1):
        lines.append(f"| {i} | {r['original_fit_converged']} | {r['passed']} | {r['evaluations']} | "
            f"{r['prediction_horizontal_rms_m']:.3f} m | {r['prediction_height_rms_m']:.3f} m |")
    lines+=['','Earlier results retain their original labels. Every input, weight and charged operation is preserved.',
        'Broader optimizer qualification remains a separate gate; calibration does not restart automatically.','',
        '[All fits](results.csv) · [Failed checks](verification-failures.csv) · [Start comparisons](pairs.csv) ·',
        '[Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).']
    return '\n'.join(lines)+'\n'


def publish(root,prefix,*,qualification,output='docs/timing-optimizer-regression',definition=None):
    import json
    from pathlib import Path
    from lll import timing_optimizer_native_study as original
    from lll.studies.qualification import checked
    from lll.studies.artifacts import atomic,encoded,digest
    from lll.studies.native_publication import include_native_caches
    from lll.airquantumgrav_inventory import environment
    from lll.ilvis0_control_publication import publish as package,check
    from lll.timing_arithmetic_report import csv_bytes
    root=Path(root).resolve();data=root/prefix;public=root/output
    if (public/'evidence-receipt.json').exists():raise ValueError('publication already sealed')
    policy=original if definition is None else definition
    request,tests=checked(root,qualification,sources=policy.sources(root),environment=environment(),minimum_tests=100,
        required_tests=['test_native_timing_verification_audit_recomputes_full_cell_metrics',
            'test_timing_native_bound_protocol_keeps_original_start_and_failed_fit']
            +getattr(policy,'required_report_tests',[]))
    report=inspect(root,prefix,definition=definition);package(data,public,render(report),plan=policy.PLAN)
    if report['native_assets']:include_native_caches(root,data,public,
        entries=[dict(path=k,sha256=v) for k,v in sorted(report['native_assets'].items())],maximum_bytes=64*1024**2)
    additions={'results.csv':csv_bytes(report['rows']),'pairs.csv':csv_bytes(report['pairs']),
        'verification-failures.csv':csv_bytes(report['verification_failures']),
        'artifacts/publication/verified-report.json':encoded(report),'artifacts/publication/qualification-request.json':request,
        'artifacts/publication/qualification-report.xml':tests,
        'artifacts/publication/reporter-source.py':Path(__file__).read_bytes(),
        'artifacts/publication/reporter-test.py':(root/'analysis/tests/test_timing_optimizer_native_report.py').read_bytes()}
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    for name,raw in additions.items():atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt));check(data,public)
    if encoded(inspect(root,output,definition=definition))!=encoded(report):raise ValueError('public saved replay differs')
    return dict(publication=output,artifacts=len(receipt['artifacts']),compaction_pending=True,native_calls=0)
