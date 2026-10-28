# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit sealed timing diagnostics; no propagation, fitting or relabeling."""
import math


def kernel_bindings(study):
    """Adapt the diagnostic's environment input name to the shared auditor."""
    from types import SimpleNamespace
    from lll.compensated_prediction_release import native_bindings
    view=SimpleNamespace(manifest=study.manifest,read=study.read,
        input=lambda key:study.input('environment' if key=='qualification-environment' else key))
    return native_bindings(view)


def summarize(record,d):
    from lll.timing_boundary_probe import SPACINGS_S
    if (d['active_parameters']!=record['fit']['active_parameters'] or d['columns']!=27
            or d['source_fit_sha256']!=record['artifact_sha256']['fit.json']
            or d['original_saved_converged']!=record['saved_converged'] or not d['input_replay_exact']
            or d['baseline']['cost']!=record['fit']['residual_sum_squares']
            or not d['repeatability']['exact'] or d['labels_changed'] or d['nonlinear_fit_starts']
            or not 1<=d['evaluations']<=64 or d['stopping_probe']!={'passed':None,'not_executed':True}
            or [(v['spacing_s'],v['side']) for v in d['branches']]!=[(h,k) for h in SPACINGS_S for k in (-1,1)]
            or [v['kind'] for v in d['corrections']]!=['full','time_only','other_only']):
        raise ValueError('scope, complete columns, original labels or exact baseline differ')
    curves=[]
    for branch in d['branches']:
        if not branch['feasible']:continue
        a,b=branch['analytic'],branch['difference']
        if not a or len(a)!=len(b) or any(len(row)!=27 for row in branch['jacobian']):
            raise ValueError('complete saved derivative vectors and Jacobian required')
        an=math.sqrt(math.fsum(v*v for v in a));bn=math.sqrt(math.fsum(v*v for v in b))
        error=math.sqrt(math.fsum((x-y)**2 for x,y in zip(a,b)));scale=1e-8+1e-6*max(an,bn)
        if (not math.isclose(error,branch['error_norm'],rel_tol=1e-10,abs_tol=1e-14)
                or not math.isclose(scale,branch['comparison_scale'],rel_tol=1e-12,abs_tol=1e-16)):
            raise ValueError('saved derivative metric or fixed comparison scale differs')
        curves.append(dict(identity=record['identity'],side=branch['side'],spacing_s=branch['spacing_s'],
                           error_norm=error,comparison_scale=scale,error_ratio=error/scale))
    row=dict(identity=record['identity'],original_fit_converged=record['saved_converged'],
        evaluations=d['evaluations'],columns=27,full_correction_replayed=d['full_correction_replayed'],
        timing_derivatives_agree=bool(curves) and all(v['error_ratio']<=1 for v in curves),
        maximum_error_ratio=max((v['error_ratio'] for v in curves),default=None),labels_changed=False)
    for correction in d['corrections']:
        for key in ('actual_cost_delta','predicted_cost_delta','residual_remainder_norm'):
            row[correction['kind']+'_'+key]=correction[key]
    return row,curves


def inspect(root,prefix):
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import encoded
    from lll.timing_boundary_study import configuration,identities,SCOPE,work_allowance
    from lll.structured_noisy_publication import native_cache_entries
    from lll.compensated_prediction_release import case_recipe
    from lll.structured_noisy_training import limits
    from lll.airquantumgrav_geographic_report import construction_counts
    from lll.airquantumgrav_inventory import environment
    s=ClosedStudy(root,prefix)
    try:
        if (s.input('configuration')!=configuration() or s.manifest['scope']!=SCOPE
                or set(s.tasks)!=set(identities()) or s.input('environment')!=environment()):
            raise ValueError('same finite diagnostic, exact points and numerical environment required')
        for name,sha in s.manifest['sources'].items():s.read('source-freeze/'+name,sha,raw=True)
        points={p['identity']:p for p in s.input('points')};bindings=kernel_bindings(s)
        rows=[];curves=[];failures=[];attempted=dict(native_calls=0,packet_visits=0)
        for identity,task in s.tasks.items():
            if identity not in s.rows:failures.append(dict(identity=identity,reason='unexecuted'));continue
            envelope=s.envelope(identity);base='artifacts/'+identity+'/'
            for name,sha in envelope['artifacts'].items():s.read(name,sha,raw=True)
            point=points[identity];seed=point['payload']['draw_seed']
            if task['limits']!=work_allowance(seed):raise ValueError('frozen native allowance changed')
            if base+'native-prepayment.json' in envelope['artifacts']:
                budget=s.artifact(identity,'native-prepayment.json')
                if budget['prepaid']!={k:envelope['charged'][k] for k in attempted}:
                    raise ValueError('prepaid charges differ from the sealed task')
                for key in attempted:attempted[key]+=budget['attempted'][key]
            if base+'diagnostic.json' not in envelope['artifacts']:
                failures.append(dict(identity=identity,reason=envelope['result'].get('error','diagnostic incomplete')));continue
            d=s.artifact(identity,'diagnostic.json');row,cc=summarize(point,d)
            if (d['point']!=point['fit']['normalized_parameters'] or not envelope['result']['diagnostic_complete']
                    or envelope['result']['evaluations']!=d['evaluations']):
                raise ValueError('saved diagnostic point or result differs')
            count=construction_counts(s.artifact(identity,'evaluations.sqlite',raw=True),s.completion['manifest_sha256'],
                identity,dict(evaluations=64),complete=False)
            if count['evaluations']!=d['evaluations']:raise ValueError('evaluation accounting differs')
            construction_counts(s.artifact(identity,'construction.sqlite',raw=True),s.completion['manifest_sha256'],
                identity,limits(case_recipe(seed),'point')[1],complete=False)
            construction_counts(s.artifact(identity,'worker-build-journal.sqlite',raw=True),
                s.completion['manifest_sha256'],'worker',dict(builds=2))
            for name,value in point['artifacts'].items():
                if encoded(s.artifact(identity,'reconstructed/'+name))!=encoded(value):
                    raise ValueError('original input, training observation or error operator changed')
            meta=s.artifact(identity,'reconstructed/compilation.json');tm=meta['tangent'];nm=meta['noise_bridge']
            if (tm['source_sha256']!=bindings['wide_sha256'] or nm['source_sha256']!=bindings['bridge_sha256']
                    or tm['compiler']!=bindings['compiler'] or nm['compiler']!=bindings['compiler']
                    or tm['internal_mantissa_bits']<=53 or nm['internal_mantissa_bits']<=53):
                raise ValueError('qualified compensated/noise kernel or compiler differs')
            rows.append(row);curves.extend(cc)
        assets=native_cache_entries(s,compilation_name='reconstructed/compilation.json',require_fit_status=False)
        for name,sha in assets.items():s.read(name,sha,raw=True)
        return dict(version='saved-timing-boundary-report-v1',verified=True,selected=4,complete=len(rows),
            rows=rows,curves=curves,failures=failures,evaluations=sum(r['evaluations'] for r in rows),
            actual_native=attempted,charged=s.summary['charged'],elapsed_s=s.summary['elapsed_s'],native_assets=assets,
            manifest_sha256=s.completion['manifest_sha256'],summary_sha256=s.completion['summary_sha256'],
            labels_changed=False,nonlinear_fit_starts=0,native_calls_during_audit=0,confidence_calibrated=False)
    finally:s.close()


def render(report):
    lines=['# Two-sided timing diagnostic at saved points','',
        f"Completed {report['complete']}/4 diagnostics with {report['evaluations']} residual/Jacobian evaluations.",
        'No model was refitted and no previous convergence label changed.','',
        '| Example | Original fit | Full correction replays | Within-branch derivatives agree |',
        '|---|---|---|---|']
    for i,row in enumerate(report['rows'],1):
        lines.append(f"| {i} | {row['original_fit_converged']} | {row['full_correction_replayed']} | {row['timing_derivatives_agree']} |")
    if report['failures']:lines+=['','Incomplete diagnostics:']+['- '+v['identity']+': '+v['reason'] for v in report['failures']]
    lines+=['','These checks separate timing branches from other nonlinear calibration effects.',
        'They establish no new fitted optimum, uncertainty threshold or aircraft finding.','',
        '[Summary CSV](results.csv) · [Derivative comparisons](derivatives.csv) · [Frozen plan](PLAN.md) ·',
        '[Next analyses](../NEXT_STEPS.md).']
    return '\n'.join(lines)+'\n'


def publish(root,prefix,*,qualification,output='docs/saved-timing-boundary'):
    import json
    from pathlib import Path
    from lll.timing_boundary_study import sources,PLAN
    from lll.studies.qualification import checked
    from lll.airquantumgrav_inventory import environment
    from lll.studies.artifacts import atomic,encoded,digest
    from lll.studies.native_publication import include_native_caches
    from lll.ilvis0_control_publication import publish as package,check
    from lll.timing_arithmetic_report import csv_bytes
    root=Path(root).resolve();data=root/prefix;public=root/output
    if (public/'evidence-receipt.json').exists():raise ValueError('publication already sealed')
    request,tests=checked(root,qualification,sources=sources(root),environment=environment(),minimum_tests=20,
        required_tests=['test_boundary_report_keeps_failed_labels_separate_from_derivative_agreement',
                        'test_capture_binding_exits_before_any_fit_or_forecast'])
    report=inspect(root,prefix);package(data,public,render(report),plan=PLAN)
    if report['native_assets']:include_native_caches(root,data,public,
        entries=[dict(path=k,sha256=v) for k,v in sorted(report['native_assets'].items())],maximum_bytes=64*1024**2)
    additions={'results.csv':csv_bytes(report['rows']),'derivatives.csv':csv_bytes(report['curves']),
        'artifacts/publication/verified-report.json':encoded(report),
        'artifacts/publication/qualification-request.json':request,'artifacts/publication/qualification-report.xml':tests,
        'artifacts/publication/reporter-source.py':Path(__file__).read_bytes(),
        'artifacts/publication/reporter-test.py':(root/'analysis/tests/test_timing_boundary_report.py').read_bytes()}
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    for name,raw in additions.items():atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt));check(data,public)
    if encoded(inspect(root,output))!=encoded(report):raise ValueError('public replay differs from closed data')
    return dict(publication=output,artifacts=len(receipt['artifacts']),compaction_pending=True,native_calls=0,nonlinear_fit_starts=0)
