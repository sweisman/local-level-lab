# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independently recompute sealed proposal metrics, preserving original labels."""
import math


def summarize(record,d):
    from lll.ilvis0_solver_position import POLICY
    from lll.ilvis0_solver_refinement import POLICY as STOPPING
    thresholds=dict(relative_cost=STOPPING['relative_cost_tolerance'],stationarity=STOPPING['stationarity_tolerance'],
        position_rms_m=POLICY['position_rms_tolerance_m'],position_max_m=POLICY['position_max_tolerance_m'])
    fit=record['fit'];baseline=d['baseline'];expected=fit['local_linearization'];source=record['proposals']
    if (d['active_parameters']!=fit['active_parameters'] or len(d['active_parameters'])!=27
            or d['source_fit_sha256']!=record['artifact_sha256']['fit.json']
            or d['original_saved_converged']!=record['saved_converged'] or not d['input_replay_exact']
            or d['point']!=fit['normalized_parameters'] or baseline['cost']!=fit['residual_sum_squares']
            or baseline['residual']!=expected['residual'] or baseline['jacobian']!=expected['jacobian']
            or not d['repeatability']['exact'] or d['labels_changed'] or d['nonlinear_fit_starts']
            or d['stopping_probe']!={'passed':None,'not_executed':True} or d['thresholds']!=thresholds
            or d['maximum_evaluations']!=8 or d['evaluations']!=len(source)+2
            or len(source) not in (3,6) or len(d['proposals'])!=len(source)
            or [r['index'] for r in d['proposals']]!=[p['index'] for p in source]):
        raise ValueError('exact saved baseline, unchanged labels, thresholds and complete coverage required')
    def close(a,b):return math.isfinite(a) and math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-12)
    rows=[];cost=baseline['cost']
    for item,original in zip(d['proposals'],source):
        r=item['residual'];j=item['jacobian'];point=item['point'];physical=item['position_delta_neu_m']
        if (point!=original['point'] or len(r)!=len(baseline['residual']) or len(j)!=len(r)
                or any(len(row)!=27 for row in j) or not physical or len(physical)*3!=len(r)
                or any(len(row)!=3 for row in physical) or len(point)!=27
                or any(not math.isfinite(v) for row in [r,point,*j,*physical] for v in row)):
            raise ValueError('complete finite derivative and physical change arrays required')
        actual=math.fsum(v*v for v in r);predicted=original['predicted_cost']
        remainder=math.sqrt(math.fsum((a-b)**2 for a,b in zip(r,original['predicted_residual'])))
        change=abs(actual-cost)/max(actual,cost,1.)
        rms=[math.sqrt(math.fsum(v[k]**2 for v in physical)/len(physical)) for k in range(3)]
        maximum=[max(abs(v[k]) for v in physical) for k in range(3)]
        rnorm=max(math.sqrt(actual),1.);stationarity=0.
        for k,x in enumerate(point):
            gradient=math.fsum(row[k]*v for row,v in zip(j,r))
            if x<=-1+1e-6 and gradient>0 or x>=1-1e-6 and gradient<0:gradient=0.
            scale=max(math.sqrt(math.fsum(row[k]**2 for row in j)),1.)*rnorm
            stationarity=max(stationarity,abs(gradient)/scale)
        measures=dict(actual_cost=actual,actual_cost_delta=actual-cost,predicted_cost=predicted,
            prediction_cost_error=actual-predicted,relative_cost_change=change,stationarity=stationarity,
            residual_remainder_norm=remainder)
        flags=dict(cost_stable=change<=thresholds['relative_cost'],stationary=stationarity<=thresholds['stationarity'],
            position_stable=all(v<=thresholds['position_rms_m'] for v in rms)
                and all(v<=thresholds['position_max_m'] for v in maximum))
        if (any(not close(item[k],v) for k,v in measures.items())
                or len(item['position_rms_neu_m'])!=3 or len(item['position_max_abs_neu_m'])!=3
                or any(not close(a,b) for a,b in zip(item['position_rms_neu_m'],rms))
                or any(not close(a,b) for a,b in zip(item['position_max_abs_neu_m'],maximum))
                or any(item[k] is not v for k,v in flags.items())):
            raise ValueError('independently recomputed proposal metrics differ')
        rows.append(dict(identity=record['identity'],index=item['index'],**measures,**flags,
            maximum_position_rms_m=max(rms),maximum_position_change_m=max(maximum)))
    return dict(identity=record['identity'],original_fit_converged=record['saved_converged'],
        evaluations=d['evaluations'],proposals=len(rows),labels_changed=False),rows


def inspect(root,prefix):
    from lll.studies.closed import ClosedStudy
    from lll.timing_cell_native_study import configuration,identities,SCOPE,work_allowance
    from lll.timing_boundary_report import kernel_bindings
    from lll.saved_point_audit import audit_point
    from lll.structured_noisy_publication import native_cache_entries
    from lll.airquantumgrav_inventory import environment
    s=ClosedStudy(root,prefix)
    try:
        if (s.input('configuration')!=configuration() or s.manifest['scope']!=SCOPE
                or set(s.tasks)!=set(identities()) or s.input('environment')!=environment()):
            raise ValueError('exact four-point physical diagnostic and environment required')
        for name,sha in s.manifest['sources'].items():s.read('source-freeze/'+name,sha,raw=True)
        points={p['identity']:p for p in s.input('points')};bindings=kernel_bindings(s)
        rows=[];proposals=[];failures=[];attempted=dict(native_calls=0,packet_visits=0)
        for identity in s.tasks:
            if identity not in s.rows:failures.append(dict(identity=identity,reason='unexecuted'));continue
            d,charged=audit_point(s,points[identity],maximum_evaluations=8,work_allowance=work_allowance,bindings=bindings)
            for key in attempted:attempted[key]+=charged[key]
            if d is None:failures.append(dict(identity=identity,reason='diagnostic incomplete'));continue
            row,pp=summarize(points[identity],d);rows.append(row);proposals.extend(pp)
        assets=native_cache_entries(s,compilation_name='reconstructed/compilation.json',require_fit_status=False)
        for name,sha in assets.items():s.read(name,sha,raw=True)
        return dict(version='saved-timing-cell-native-report-v1',verified=True,selected=4,complete=len(rows),
            rows=rows,proposals=proposals,failures=failures,evaluations=sum(r['evaluations'] for r in rows),
            actual_native=attempted,charged=s.summary['charged'],elapsed_s=s.summary['elapsed_s'],native_assets=assets,
            manifest_sha256=s.completion['manifest_sha256'],summary_sha256=s.completion['summary_sha256'],
            labels_changed=False,nonlinear_fit_starts=0,native_calls_during_audit=0,confidence_calibrated=False)
    finally:s.close()


def render(report):
    lines=['# Physical evaluation of the saved timing-cell proposals','',
        f"Completed {report['complete']}/4 points and {len(report['proposals'])}/18 proposals using {report['evaluations']} evaluations.",
        'Every physical timing side and saved spacing is retained. No model was refitted or previous label changed.','',
        '| Point | Original fit passed | Proposals | Evaluations |','|---|---|---|---|']
    for i,row in enumerate(report['rows'],1):
        lines.append(f"| {i} | {row['original_fit_converged']} | {row['proposals']} | {row['evaluations']} |")
    lines+=['','Cost, stationarity and actual position-change screens are reported separately.',
        'Passing them here does not qualify a complete optimizer or establish statistical confidence.','',
        '[Point summary](results.csv) · [All proposals](proposals.csv) · [Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).']
    return '\n'.join(lines)+'\n'


def publish(root,prefix,*,qualification,output='docs/saved-timing-cell-native'):
    import json
    from pathlib import Path
    from lll.timing_cell_native_study import sources,PLAN
    from lll.studies.qualification import checked
    from lll.airquantumgrav_inventory import environment
    from lll.studies.artifacts import atomic,encoded,digest
    from lll.studies.native_publication import include_native_caches
    from lll.ilvis0_control_publication import publish as package,check
    from lll.timing_arithmetic_report import csv_bytes
    root=Path(root).resolve();data=root/prefix;public=root/output
    if (public/'evidence-receipt.json').exists():raise ValueError('publication already sealed')
    request,tests=checked(root,qualification,sources=sources(root),environment=environment(),minimum_tests=50,
        required_tests=['test_native_cell_report_recomputes_metrics_without_relabeling_failed_fits',
            'test_capture_binding_exits_before_any_fit_or_forecast'])
    report=inspect(root,prefix);package(data,public,render(report),plan=PLAN)
    if report['native_assets']:include_native_caches(root,data,public,
        entries=[dict(path=k,sha256=v) for k,v in sorted(report['native_assets'].items())],maximum_bytes=64*1024**2)
    additions={'results.csv':csv_bytes(report['rows']),'proposals.csv':csv_bytes(report['proposals']),
        'artifacts/publication/verified-report.json':encoded(report),
        'artifacts/publication/qualification-request.json':request,'artifacts/publication/qualification-report.xml':tests}
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    for name,raw in additions.items():atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt));check(data,public)
    if encoded(inspect(root,output))!=encoded(report):raise ValueError('public saved replay differs')
    return dict(publication=output,artifacts=len(receipt['artifacts']),compaction_pending=True,native_calls=0,nonlinear_fit_starts=0)
