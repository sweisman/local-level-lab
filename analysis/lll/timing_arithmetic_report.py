# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read sealed matched diagnostics; never load kernels, fit or forecast."""
import csv
import io
import json
from pathlib import Path


def summarize(identity,converged,setting,*,baseline):
    curves=[]
    for column in setting['derivatives']:
        for step in column['steps']:
            if not step['comparison_scale']>0:raise ValueError('positive comparison scale required')
            curves.append(dict(identity=identity,mode=setting['mode'],parameter=column['parameter'],
                **{k:v for k,v in step.items() if k not in ('difference','signed_error')},
                error_ratio=step['error_norm']/step['comparison_scale']))
    row=dict(identity=identity,mode=setting['mode'],original_fit_converged=converged,
        evaluations=setting['evaluations'],cost=setting['cost'],cost_delta=setting['cost']-baseline['cost'],
        columns=len(setting['jacobian'][0]),derivatives_agree=all(c['error_ratio']<=1 for c in curves),
        maximum_error_ratio=max(c['error_ratio'] for c in curves),fit_labels_changed=False)
    return row,curves


def summarize_full(record,d):
    curves=[]
    for column in d['derivatives']:
        for step in column['steps']:
            scale=1e-8+1e-6*max(step['analytic_norm'],step['difference_norm'])
            curves.append(dict(identity=record['identity'],mode='compensated',
                parameter=d['active_parameters'][column['column']],
                **{k:v for k,v in step.items() if k!='difference'},
                comparison_scale=scale,error_ratio=step['error_norm']/scale))
    signed=d.get('signed_probe') or {}
    row=dict(identity=record['identity'],mode='compensated',original_fit_converged=record['saved_converged'],
        evaluations=d['evaluations'],columns=d['columns'],baseline_cost=d['baseline']['cost'],
        cost=d['cost'],cost_delta=d['cost']-d['baseline']['cost'],repeatable=d['repeatability']['exact'],
        derivatives_agree=all(c['error_ratio']<=1 for c in curves),maximum_error_ratio=max(c['error_ratio'] for c in curves),
        candidate_stopping_passed=d['stopping_probe']['passed'],
        actual_relative_cost_change=d['stopping_probe'].get('actual_cost_change'),
        actual_cost_delta=signed.get('actual_cost_delta'),predicted_cost_delta=signed.get('predicted_cost_delta'),
        fit_labels_changed=False)
    return row,curves


def inspect(root,prefix):
    from lll.studies.closed import ClosedStudy
    from lll.studies.journal import inspect_snapshot
    from lll.stopping_consistency_study import point_identity,POINTS
    from lll.timing_arithmetic_study import configuration
    s=ClosedStudy(root,prefix)
    try:
        cfg=s.input('configuration') if 'configuration' in s.manifest.get('inputs',{}) else configuration()
        if (cfg!=configuration(cfg.get('kind')) or s.manifest['scope']!=cfg['scope']
                or set(s.tasks)!={point_identity(*p) for p in POINTS}):
            raise ValueError('exact four exposed saved-point identities required')
        full=cfg['kind']=='coordinate-full'
        points={p['identity']:p for p in s.input('points')};rows=[];curves=[];failures=[];attempted={'native_calls':0,'packet_visits':0}
        evaluations=0
        for identity in s.tasks:
            if identity not in s.rows:failures.append(dict(identity=identity,reason='unexecuted'));continue
            envelope=s.envelope(identity);paths=envelope['artifacts'];base='artifacts/'+identity+'/'
            if base+'native-prepayment.json' in paths:
                work=s.artifact(identity,'native-prepayment.json')['attempted']
                for key in attempted:attempted[key]+=work[key]
            if base+'diagnostic.json' not in paths:
                failures.append(dict(identity=identity,reason=envelope['result'].get('error','diagnostic incomplete')));continue
            d=s.artifact(identity,'diagnostic.json');point=points[identity]
            journal=inspect_snapshot(s.artifact(identity,'evaluations.sqlite',raw=True),s.completion['manifest_sha256'])
            if (d['evaluations']!=journal['sweeps'] or d['evaluations']>cfg['maximum_evaluations'] or journal['starts']!=1
                    or d['active_parameters']!=point['fit']['active_parameters'] or not d['input_replay_exact']
                    or d['point']!=point['fit']['normalized_parameters'] or d['labels_changed'] or d['nonlinear_fit_starts']
                    or d['source_fit_sha256']!=point['artifact_sha256']['fit.json']
                    or (d['baseline']['cost'] if full else d['settings'][0]['cost'])!=point['fit']['residual_sum_squares']):
                raise ValueError('scope, full columns, exact baseline or evaluation accounting differs')
            evaluations+=d['evaluations']
            if full:
                if (d['candidate_mode']!='compensated' or d['baseline_evaluations']!=1
                        or d['candidate_evaluations']+1!=d['evaluations'] or d['candidate_evaluations']>170
                        or len(d['derivatives'])!=len(d['active_parameters'])):
                    raise ValueError('complete compensated probe or baseline allowance changed')
                row,cc=summarize_full(point,d)
                rows.append(row);curves.extend(cc)
            else:
                if (not d['stopping_probe']['not_executed']
                        or tuple(v['mode'] for v in d['settings'])!=('baseline','boundary','longitude','both')):
                    raise ValueError('matched arithmetic settings changed')
                baseline=d['settings'][0]
                for setting in d['settings']:
                    row,cc=summarize(identity,point['saved_converged'],setting,baseline=baseline)
                    rows.append(row);curves.extend(cc)
        report=dict(manifest_sha256=s.completion['manifest_sha256'],summary_sha256=s.completion['summary_sha256'],
            rows=rows,curves=curves,failures=failures,complete=len(rows) if full else len(rows)//4,selected=4,evaluations=evaluations,
            actual_native=attempted,charged=s.summary['charged'],elapsed_s=s.summary['elapsed_s'],
            framework_updates=s.input('framework-updates'),nonlinear_fit_starts=0,original_reads=0,protected_reads=0,
            labels_changed=False,confidence_calibrated=False,scientific_decision='abstain')
        if full:
            report.update(kind='coordinate-full',candidate_checks_qualified=len(rows)==4 and not failures and
                all(r['repeatable'] and r['derivatives_agree'] and r['candidate_stopping_passed'] for r in rows))
        return report
    finally:s.close()


def csv_bytes(rows):
    text=io.StringIO(newline='');fields=list(dict.fromkeys(k for row in rows for k in row))
    writer=csv.DictWriter(text,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(rows)
    return text.getvalue().encode()


def render(report):
    if report.get('kind')=='coordinate-full':
        lines=['# Complete compensated derivative and stopping diagnostic','',
            f"Completed {report['complete']}/4 fixed-point diagnostics; {report['evaluations']} evaluations.",
            'Original fits keep their original labels. These are diagnostics, not new fitted optima.','',
            '| Example | Original fit | Derivatives agree at all steps | New stopping probe |',
            '|---|---|---|---|']
        for i,r in enumerate(report['rows'],1):
            lines.append(f"| {i} | {r['original_fit_converged']} | {r['derivatives_agree']} | {r['candidate_stopping_passed']} |")
        lines+=['','Every original nuisance column and every failure remains in the result records.',
            'Passing a local stopping probe does not establish a fitted optimum or calibrated uncertainty.','',
            '[Results CSV](results.csv) · [All derivative curves](derivatives.csv) · [Frozen plan](PLAN.md) ·',
            '[Small arithmetic controls](../coordinate-precision-controls/INTERPRETATION.md) · [Next analyses](../NEXT_STEPS.md).']
        return '\n'.join(lines)+'\n'
    lines=['# Timing and coordinate arithmetic at four saved points','',
        f"Completed {report['complete']}/4 saved-point diagnostics with {report['evaluations']} residual-and-derivative evaluations.",
        'No model was refitted and no previous fit label was changed.','',
        '| Example | Original fit | Timing checks: original → boundary change | Gyro-offset checks: original → both changes |',
        '|---|---|---|---|']
    for number,identity in enumerate(dict.fromkeys(r['identity'] for r in report['rows']),1):
        rows=[r for r in report['rows'] if r['identity']==identity]
        def score(mode,parameter):
            selected=[c for c in report['curves'] if c['identity']==identity and c['mode']==mode and c['parameter']==parameter]
            return str(sum(c['error_ratio']<=1 for c in selected))+'/'+str(len(selected))
        original='Passed' if rows[0]['original_fit_converged'] else 'Failed'
        lines.append(f"| {number} | {original} | {score('baseline','time_offset')} → {score('boundary','time_offset')} | {score('baseline','gyro_bias_z')} → {score('both','gyro_bias_z')} |")
    if report['failures']:
        lines+=['','Incomplete diagnostics:']+['- '+r['identity']+': '+r['reason'] for r in report['failures']]
    lines+=['','Agreement here concerns the timing and gyro-Z-offset derivative comparisons at three fixed steps.',
        'Every nuisance column remains in the saved matrices. These are not new stopping decisions,',
        'qualified optima, uncertainty thresholds or flight findings.','',
        '[Summary CSV](results.csv) · [Derivative curves](derivatives.csv) · [Frozen plan](PLAN.md) ·',
        '[Previous small controls](../timing-precision-controls/INTERPRETATION.md) · [Next analyses](../NEXT_STEPS.md).']
    return '\n'.join(lines)+'\n'


def publish(root,prefix='data/saved-point-timing-arithmetic-20261026',output='docs/saved-point-timing-arithmetic'):
    from lll.ilvis0_control_publication import publish as package,check
    from lll.studies.artifacts import atomic,encoded,digest
    root=Path(root).resolve();data=root/prefix;public=root/output
    if (public/'evidence-receipt.json').exists():raise ValueError('immutable publication already exists')
    report=inspect(root,prefix)
    plan='docs/SAVED_POINT_COORDINATE_PLAN.md' if report.get('kind')=='coordinate-full' else 'docs/SAVED_POINT_TIMING_PLAN.md'
    package(data,public,render(report),plan=plan)
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    extras={'results.csv':csv_bytes(report['rows']),'derivatives.csv':csv_bytes(report['curves']),
        'artifacts/publication/verified-report.json':encoded(report),
        'artifacts/publication/reporter-source.py':Path(__file__).read_bytes(),
        'artifacts/publication/reporter-tests.py':Path(__file__).parents[1].joinpath('tests/test_timing_arithmetic_report.py').read_bytes()}
    if (public/'INTERPRETATION.md').is_file():extras['INTERPRETATION.md']=(public/'INTERPRETATION.md').read_bytes()
    for name,raw in extras.items():atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt));check(data,public)
    if encoded(inspect(root,output))!=encoded(report):raise ValueError('published diagnostic replay differs')
    return dict(path=output,complete=report['complete'],native_calls=0,nonlinear_fit_starts=0)
