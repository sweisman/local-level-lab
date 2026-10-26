# SPDX-License-Identifier: AGPL-3.0-or-later
"""Report sealed saved-point diagnostics; never load a kernel or fit a model."""
import csv
import io
import json
from pathlib import Path


def summarize(record,diagnostic):
    errors=[]
    for row in diagnostic['derivatives']:
        final=row['steps'][-1]
        errors.append(final['error_norm']/(1e-8+1e-6*max(final['analytic_norm'],final['difference_norm'])))
    signed=diagnostic.get('signed_probe') or {}
    return dict(identity=record['identity'],saved_converged=record['saved_converged'],
        diagnostic_complete=True,columns=diagnostic['columns'],evaluations=diagnostic['evaluations'],
        cost=diagnostic['cost'],repeatable=diagnostic['repeatability']['exact'],
        derivative_checks_passed=all(v<=1 for v in errors),maximum_derivative_error_ratio=max(errors),
        probe_passed=diagnostic['stopping_probe']['passed'],
        actual_relative_cost_change=diagnostic['stopping_probe'].get('actual_cost_change'),
        actual_cost_delta=signed.get('actual_cost_delta'),predicted_cost_delta=signed.get('predicted_cost_delta'),
        singular_value_ratio=diagnostic['singular_value_ratio'],labels_changed=False)


def inspect(root,prefix):
    from .studies.closed import ClosedStudy
    from .studies.artifacts import encoded,digest
    from .studies.journal import inspect_snapshot
    from .stopping_consistency_study import POINTS,point_identity,SCOPE
    s=ClosedStudy(root,prefix)
    try:
        if s.manifest['scope']!=SCOPE or len(s.tasks)!=4:raise ValueError('exact four-point diagnostic required')
        points=s.input('points');expected={point_identity(*p) for p in POINTS}
        if set(s.tasks)!=expected or {p['identity'] for p in points}!=expected:
            raise ValueError('saved-point selection changed')
        records={p['identity']:p for p in points};rows=[];coordinates=[]
        totals=dict(evaluations=0,native_calls_attempted=0,packet_visits_attempted=0)
        for identity in s.tasks:
            record=records[identity]
            if identity not in s.rows:
                rows.append(dict(identity=identity,saved_converged=record['saved_converged'],
                    diagnostic_complete=False,reason='unexecuted'));continue
            envelope=s.envelope(identity);names=envelope['artifacts'];base='artifacts/'+identity+'/'
            charged=0
            if base+'evaluations.sqlite' in names:
                raw=s.artifact(identity,'evaluations.sqlite',raw=True)
                journal=inspect_snapshot(raw,s.completion['manifest_sha256'])
                if journal['starts']!=1 or journal['sweeps']>170:
                    raise ValueError('evaluation journal exceeds its frozen start/call allowance')
                charged=journal['sweeps']
            if base+'diagnostic.json' in names:
                d=s.artifact(identity,'diagnostic.json');row=summarize(record,d)
                if (not d['input_replay_exact'] or d['labels_changed'] or d['nonlinear_fit_starts']!=0
                        or d['active_parameters']!=record['fit']['active_parameters']
                        or d['source_fit_sha256']!=record['artifact_sha256']['fit.json']
                        or not 0<d['evaluations']<=170 or charged!=d['evaluations']):
                    raise ValueError('diagnostic source, columns or finite evaluation limits differ')
                totals['evaluations']+=d['evaluations']
                for col in d['derivatives']:
                    for step in col['steps']:
                        coordinates.append(dict(identity=identity,parameter=d['active_parameters'][col['column']],
                            **{k:v for k,v in step.items() if k!='difference'}))
            else:
                row=dict(identity=identity,saved_converged=record['saved_converged'],diagnostic_complete=False,
                    reason=envelope['result'].get('error',envelope['result'].get('error_type','incomplete')))
            if base+'native-prepayment.json' in names:
                b=s.artifact(identity,'native-prepayment.json');attempted=b['attempted']
                if attempted['native_calls']>59954 or attempted['packet_visits']>376512753:
                    raise ValueError('native allowance exceeded')
                totals['native_calls_attempted']+=attempted['native_calls']
                totals['packet_visits_attempted']+=attempted['packet_visits']
            rows.append(row)
        return dict(version='stopping-consistency-report-v1',manifest_sha256=s.completion['manifest_sha256'],
            summary_sha256=s.completion['summary_sha256'],rows=rows,coordinates=coordinates,**totals,
            selected=4,returned=len(s.rows),complete=sum(r['diagnostic_complete'] for r in rows),
            nonlinear_fit_starts=0,original_reads=0,protected_reads=0,labels_changed=False,
            confidence_calibrated=False,scientific_decision='abstain')
    finally:s.close()


def csv_bytes(rows):
    out=io.StringIO(newline='');fields=list(dict.fromkeys(k for row in rows for k in row))
    writer=csv.DictWriter(out,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(rows)
    return out.getvalue().encode()


def render(report):
    lines=['# Why the numerical stopping check failed','',
        f"The bounded diagnostic completed {report['complete']} of four saved-point checks.",
        'It did not fit another model, change an acceptance limit or revise the original results.','',
        '| Saved point | Original fit passed | Repeatable | Derivatives agree at smallest step | Fresh stopping check |',
        '|---|---|---|---|---|']
    for row in report['rows']:
        if row['diagnostic_complete']:
            yn=lambda k:'Yes' if row[k] else 'No'
            lines.append(f"| {row['identity']} | {yn('saved_converged')} | {yn('repeatable')} | {yn('derivative_checks_passed')} | {yn('probe_passed')} |")
        else:lines.append(f"| {row['identity']} | {row['saved_converged']} | Incomplete | Incomplete | Incomplete |")
    lines+=['','Derivative agreement uses the unchanged predeclared software error scale as a diagnostic.',
        'A disagreement on a native problem does not reclassify its fit or establish an alternative optimum.',
        'The signed cost changes, derivative error curves and retained columns are available below.','',
        '[Summary CSV](results.csv) · [Derivative curves CSV](derivatives.csv) ·',
        '[Frozen plan](../PREDICTION_STOPPING_PLAN.md) · [Previous phase](../PREDICTION_PHASE_RESULTS.md).','',
        'No calibrated uncertainty, aircraft result or new Earth-model conclusion follows from these checks.']
    return '\n'.join(lines)+'\n'


def publish(root,prefix,output='docs/prediction-stopping-consistency'):
    from .ilvis0_control_publication import publish as package,check
    from .studies.artifacts import atomic,encoded,digest
    root=Path(root).resolve();data=root/prefix;public=root/output
    if (public/'evidence-receipt.json').exists():raise ValueError('immutable publication already exists')
    report=inspect(root,prefix)
    package(data,public,render(report),plan='docs/PREDICTION_STOPPING_PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    extras={'results.csv':csv_bytes(report['rows']),'derivatives.csv':csv_bytes(report['coordinates']),
        'artifacts/publication/verified-report.json':encoded(report)}
    for name,raw in extras.items():atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt));check(data,public)
    if encoded(inspect(root,output))!=encoded(report):raise ValueError('published replay differs')
    return dict(path=output,complete=report['complete'],returned=report['returned'],
        native_calls=0,nonlinear_fit_starts=0)
