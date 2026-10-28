# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-data analytical qualification audit; never fit or propagate a model."""
import math


def _close(a,b):return math.isfinite(a) and math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-12)


def _cost(r):return math.fsum(v*v for v in r)


def _stationarity(p,r,j):
    norm=max(math.sqrt(_cost(r)),1.);value=0.
    for k,x in enumerate(p):
        g=math.fsum(row[k]*v for row,v in zip(j,r))
        if x<=-1+1e-6 and g>0 or x>=1-1e-6 and g<0:g=0.
        scale=max(math.sqrt(math.fsum(row[k]**2 for row in j)),1.)*norm
        value=max(value,abs(g)/scale)
    return value


def _probe(probe,values,baseline,*,physical_scale=1.):
    if probe.get('cells'):
        for cell in probe['cells']:
            if not cell['linear']['linear_success']:continue
            p,r,j=(cell[k] for k in ('point','residual','jacobian'))
            if not any(v['point']==p and v['residual']==r and v['jacobian']==j for v in values):
                raise ValueError('cell result absent from charged trace')
            delta=[(a-b)*physical_scale for a,b in zip(r,baseline)]
            rms=math.sqrt(math.fsum(v*v for v in delta)/len(delta));maximum=max(map(abs,delta))
            cost=_cost(r);change=abs(cost-_cost(baseline))/max(cost,_cost(baseline),1.)
            stationary=_stationarity(p,r,j)
            if (not _close(cell['actual_cost'],cost) or not _close(cell['relative_cost_change'],change)
                    or not _close(cell['fresh_stationarity'],stationary)
                    or any(not _close(a,b) for a,b in zip(cell['position_rms_neu_m'],[rms,0.,0.]))
                    or any(not _close(a,b) for a,b in zip(cell['position_max_abs_neu_m'],[maximum,0.,0.]))
                    or cell['cost_stable'] is not (change<=1e-8)
                    or cell['stationary'] is not (stationary<=1e-4)
                    or cell['position_stable'] is not (rms<=.001 and maximum<=.01)
                    or cell['passed'] is not (change<=1e-8 and stationary<=1e-4 and rms<=.001 and maximum<=.01)):
                raise ValueError('independent cell cost, stationarity or physical metric differs')
    elif 'actual_cost_change' in probe:
        r=values[-1]['residual'];delta=[a-b for a,b in zip(r,baseline)]
        change=abs(_cost(r)-_cost(baseline))/max(_cost(r),_cost(baseline),1.)
        rms=math.sqrt(math.fsum(v*v for v in delta)/len(delta));maximum=max(map(abs,delta))
        if (not _close(probe['actual_cost_change'],change)
                or any(not _close(a,b) for a,b in zip(probe['position_rms_neu_m'],[rms,0.,0.]))
                or any(not _close(a,b) for a,b in zip(probe['position_max_abs_neu_m'],[maximum,0.,0.]))):
            raise ValueError('legacy verification metrics differ from saved trace')


def summarize(row,result,values):
    from lll.timing_stopping_study import work_limits
    n=len(row['reference']['optimum'] if row['kind']=='fit' else row['reference']['point'])
    limit=work_limits(row)
    if (result['identity']!=row['identity'] or result['kind']!=row['kind'] or result['case']!=row['case']
            or result['native_calls'] or result['confidence_calibrated'] or result['scientific_decision']!='abstain'
            or result['evaluations']!=len(values) or not 1<=len(values)<=limit['evaluations']
            or not 0<=result['linear_solves']<=limit['linear_solves']):
        raise ValueError('exact control, finite recorded work and zero native scope required')
    for i,v in enumerate(values,1):
        if (v['number']!=i or len(v['point'])!=n or not v['residual'] or len(v['jacobian'])!=len(v['residual'])
                or any(len(a)!=n for a in v['jacobian']) or any(abs(x)>1 for x in v['point'])
                or any(not math.isfinite(x) for a in [v['point'],v['residual'],*v['jacobian']] for x in a)):
            raise ValueError('complete ordered finite charged value trace required')
    if row['kind']=='fit':
        f=result['fit'];ref=row['reference'];p=f['normalized_parameters'];r=f['local_linearization']['residual']
        j=f['local_linearization']['jacobian'];cost=_cost(r)
        if (not any(v['point']==p and v['residual']==r and v['jacobian']==j for v in values)
                or not _close(f['residual_sum_squares'],cost) or f['evaluations']!=len(values)
                or f['linear_solves']!=result['linear_solves'] or f['near_zero_probe'] is not None):
            raise ValueError('saved final fit, cost or accounting differs')
        objective=abs(cost-ref['cost']);prediction=math.sqrt(math.fsum((a-b)**2 for a,b in zip(r,ref['residual'])))
        parameter=max(abs(a-b) for a,b in zip(p,ref['optimum'])) if ref['unique'] else None
        passed=bool(f['converged'] and f['stability_verified'] and objective<=ref['objective_tolerance']
            and prediction<=ref['prediction_tolerance'] and (not ref['unique'] or parameter<=ref['parameter_tolerance']))
        if (not _close(result['objective_error'],objective) or not _close(result['prediction_error'],prediction)
                or ref['unique'] and not _close(result['identifiable_parameter_error'],parameter)):
            raise ValueError('independently recomputed known-answer errors differ')
        _probe(f['stability_probe'],values,r)
        if (f['stability_verified'] is not f['stability_probe']['passed'] or f['converged'] is not
                bool(f['stability_probe']['passed'] and _stationarity(p,r,j)<=1e-4)):
            raise ValueError('fit stopping label differs from final verified gates')
        accepted=bool(f['converged']);reason=f['termination']
    else:
        ref=row['reference'];p=result['probe'];accepted=p['passed'];reason=p['reason']
        passed=bool(accepted is ref['expected_acceptance'] and result['budget_rejected'] is ref['expected_budget_rejection']
            and reason==ref['expected_reason'])
        _probe(p,values,values[0]['residual'],physical_scale=ref['physical_scale'])
        evidence=(any(c.get('cost_stable') is False for c in p.get('cells',[]))
            if row['case'] in ('ramp_zero','ramp_shifted') else
            any(c.get('position_stable') is False for c in p.get('cells',[]))
            if row['case']=='physical_failure' else
            len(p.get('cells',[]))==len(result['geometry']['cells']) if ref['expected_acceptance'] else True)
        passed=passed and evidence
        if reason=='not_stationary' and _stationarity(values[0]['point'],values[0]['residual'],values[0]['jacobian'])<=1e-4:
            raise ValueError('stationarity rejection is unsupported')
        if reason=='baseline_not_repeatable' and values[0]['residual']==values[1]['residual']:
            raise ValueError('repeat rejection is unsupported')
        if reason=='budget_exhausted_before_solve' and (len(values)!=3 or result['linear_solves']!=0):
            raise ValueError('intentional budget rejection is unsupported')
        objective=prediction=parameter=None
    if result['passed'] is not passed:raise ValueError('saved qualification label differs from independent checks')
    return dict(identity=row['identity'],case=row['case'],kind=row['kind'],qualification_passed=passed,
        accepted=accepted,reason=reason,evaluations=result['evaluations'],linear_solves=result['linear_solves'],
        objective_error=objective,prediction_error=prediction,identifiable_parameter_error=parameter)


def inspect(root,prefix,*,definition=None):
    import json
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import encoded
    from lll import timing_stopping_study as original
    from lll.timing_stopping_study import work_limits
    from lll.airquantumgrav_inventory import environment
    from lll.airquantumgrav_geographic_report import construction_counts
    s=ClosedStudy(root,prefix)
    try:
        policy=original if definition is None else definition
        cases=policy.case_table();expected_tasks=policy.tasks()
        if (s.manifest['scope']!=policy.SCOPE or s.input('configuration')!=policy.configuration() or s.input('cases')!=cases
                or s.input('environment')!=environment() or any(s.summary['charged'].values())
                or [{k:v for k,v in t.items() if k not in ('index','shard')} for t in s.manifest['tasks']]!=expected_tasks):
            raise ValueError('exact analytical qualification, environment and zero-native scope required')
        for name,sha in s.manifest['sources'].items():s.read('source-freeze/'+name,sha,raw=True)
        rows=[];failures=[];returned={};charges=dict(evaluations=0,linear_solves=0)
        for case in cases:
            identity=case['identity']
            if identity not in s.rows:failures.append(dict(identity=identity,reason='unexecuted'));continue
            envelope=s.envelope(identity);base='artifacts/'+identity+'/'
            for name,sha in envelope['artifacts'].items():s.read(name,sha,raw=True)
            counts=(construction_counts(s.artifact(identity,'analytical-work.sqlite',raw=True),s.completion['manifest_sha256'],
                identity,work_limits(case),complete=False) if base+'analytical-work.sqlite' in envelope['artifacts']
                else dict(evaluations=0,linear_solves=0))
            for key in charges:charges[key]+=counts[key]
            if base+'control.json' not in envelope['artifacts']:
                failures.append(dict(identity=identity,reason=envelope['result'].get('reason','control incomplete')));continue
            result=s.artifact(identity,'control.json');values=[json.loads(v) for v in s.artifact(identity,'values.jsonl',raw=True).splitlines()]
            if encoded(result)!=encoded(envelope['result']) or any(result[k]!=counts[k] for k in charges):
                raise ValueError('closed result, trace or journal accounting differs')
            rows.append(summarize(case,result,values));returned[identity]=result
        pairs=[]
        for name in dict.fromkeys(c['case'] for c in cases if c['kind']=='fit'):
            group=[c for c in cases if c['kind']=='fit' and c['case']==name];available=[returned[c['identity']] for c in group if c['identity'] in returned]
            ref=group[0]['reference'];agreement=False;maximum_prediction=maximum_cost=None
            if len(available)==4 and all(v['passed'] for v in available):
                rr=[v['fit']['local_linearization']['residual'] for v in available]
                cc=[_cost(r) for r in rr]
                maximum_prediction=max(math.sqrt(math.fsum((x-y)**2 for x,y in zip(a,b))) for a in rr for b in rr)
                maximum_cost=max(cc)-min(cc)
                agreement=maximum_prediction<=2*ref['prediction_tolerance'] and maximum_cost<=2*ref['objective_tolerance']
            pairs.append(dict(case=name,starts=len(available),agreement=agreement,
                maximum_prediction_difference=maximum_prediction,maximum_cost_difference=maximum_cost))
        return dict(version='timing-stopping-qualification-report-v1',verified=True,selected=len(cases),complete=len(rows),
            rows=rows,pairs=pairs,failures=failures,fit_passed=sum(v['qualification_passed'] for v in rows if v['kind']=='fit'),
            controls_correct=sum(v['qualification_passed'] for v in rows if v['kind']=='probe'),
            analytical_qualified=len(rows)==len(cases) and all(v['qualification_passed'] for v in rows) and all(v['agreement'] for v in pairs),
            analytical_charges=charges,native_calls=0,original_reads=0,protected_reads=0,confidence_calibrated=False,
            elapsed_s=s.summary['elapsed_s'],manifest_sha256=s.completion['manifest_sha256'],summary_sha256=s.completion['summary_sha256'])
    finally:s.close()


def render(report):
    lines=['# Analytical qualification of timing-aware stopping','',
        f"{report['fit_passed']}/{4*len(report['pairs'])} fits meet their declared known answers; {report['controls_correct']}/8 direct controls behave as specified.",
        'These are analytical software controls, not aircraft measurements.','',
        '| Known-answer objective | Returned starts | Predicted observations agree |','|---|---:|---|']
    for p in report['pairs']:lines.append(f"| {p['case']} | {p['starts']}/4 | {p['agreement']} |")
    lines+=['','A rejected non-minimum is a successful rejection control, not a converged fit.',
        'All failures remain in the evidence. Numerical software qualification establishes no statistical confidence.',
        'A separate native optimizer qualification is required before another calibration release.','',
        '[Every result](results.csv) · [Start comparisons](pairs.csv) · [Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).']
    return '\n'.join(lines)+'\n'


def publish(root,prefix,*,qualification,output='docs/timing-stopping-qualification',definition=None):
    import json
    from pathlib import Path
    from lll import timing_stopping_study as original
    from lll.studies.qualification import checked
    from lll.studies.artifacts import atomic,encoded,digest
    from lll.airquantumgrav_inventory import environment
    from lll.ilvis0_control_publication import publish as package,check
    from lll.timing_arithmetic_report import csv_bytes
    root=Path(root).resolve();data=root/prefix;public=root/output
    if (public/'evidence-receipt.json').exists():raise ValueError('publication already sealed')
    policy=original if definition is None else definition
    request,tests=checked(root,qualification,sources=policy.sources(root),environment=environment(),minimum_tests=100,
        required_tests=['test_timing_report_independently_checks_expected_fit_and_rejection[fit]',
            'test_timing_report_independently_checks_expected_fit_and_rejection[probe]'])
    report=inspect(root,prefix,definition=definition);package(data,public,render(report),plan=policy.PLAN)
    additions={'results.csv':csv_bytes(report['rows']),'pairs.csv':csv_bytes(report['pairs']),
        'artifacts/publication/verified-report.json':encoded(report),'artifacts/publication/qualification-request.json':request,
        'artifacts/publication/qualification-report.xml':tests}
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    for name,raw in additions.items():atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt));check(data,public)
    if encoded(inspect(root,output,definition=definition))!=encoded(report):raise ValueError('public analytical replay differs')
    return dict(publication=output,artifacts=len(receipt['artifacts']),compaction_pending=True,numerical_work=0)
