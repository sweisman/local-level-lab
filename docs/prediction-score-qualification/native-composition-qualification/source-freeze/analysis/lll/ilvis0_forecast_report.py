# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only audit and publication of the training/forecast software controls."""
import json
import math
from pathlib import Path


def linear_corrections(residual,jacobian,point,*,reserve):
    """Compare two saved linear systems, without evaluating a motion model."""
    import numpy as np
    from scipy.optimize import lsq_linear
    a,r,u=(np.asarray(v,dtype=float) for v in (jacobian,residual,point))
    if (a.ndim!=2 or r.shape!=(len(a),) or u.shape!=(a.shape[1],)
            or any(not np.all(np.isfinite(v)) for v in (a,r,u)) or np.any(abs(u)>1)):
        raise ValueError('complete finite saved tangent and feasible point required')
    reserve();old=lsq_linear(a,-r,bounds=(-1-u,1-u),method='bvls',tol=1e-10,max_iter=100)
    reserve();step,_,rank,singular=np.linalg.lstsq(a,-r,rcond=None)
    return dict(columns=len(u),minimum_norm_rank=int(rank),singular_values=singular.tolist(),
        relative_rank_cutoff=np.finfo(float).eps*max(a.shape),minimum_norm_step=step.tolist(),
        bounded_step=old.x.tolist(),bounded_solve_passed=bool(old.success),
        minimum_norm_inside_bounds=bool(np.all(step>=-1-u) and np.all(step<=1-u)),
        minimum_norm_length=float(np.linalg.norm(step)),bounded_length=float(np.linalg.norm(old.x)),
        minimum_norm_linear_cost=float(np.linalg.norm(r+a@step)**2),
        bounded_linear_cost=float(np.linalg.norm(r+a@old.x)**2),native_calls=0,
        nonlinear_stability_established=False,scientific_decision='abstain')


def prepare_tangent_diagnosis(root,identity='ilvis0-forecast-tangent-audit-20261023'):
    from lll.studies.artifacts import atomic,encoded,safe_path
    from lll.studies.closed import ClosedStudy
    from lll.studies.dependencies import source_closure
    from lll.studies.runtime import Definition
    root=Path(root).resolve();base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh audit identity required')
    parent=ClosedStudy(root,'data/ilvis0-training-forecast-controls-v3-20261023')
    try:
        values=[]
        for model in range(3):
            for profile in (False,True):
                name=f'forecast-{model}-{int(profile)}-nominal_200Hz-0'
                fit=parent.artifact(name,'fit.json');local=fit['local_linearization']
                values.append((name,dict(local=local,parent=parent.prefix,
                    parent_manifest_sha256=parent.completion['manifest_sha256'],
                    fit_sha256=parent.envelope(name)['artifacts']['artifacts/'+name+'/fit.json'])))
        base.mkdir(parents=True);inputs={};tasks=[]
        for name,value in values:
            path=base/(name+'.json');atomic(path,encoded(value));inputs[name]=path.relative_to(root).as_posix()
            tasks.append(dict(identity=name,input_key=name,payload=dict(maximum_linear_solves=2),
                limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
        sources=source_closure(root,['analysis/lll/ilvis0_forecast_report.py',
            'analysis/tests/test_ilvis0_forecast_report.py','docs/ilvis0-training-forecast-controls/MINIMUM_NORM_PLAN.md'])
        definition=dict(id=identity,adapter='analysis/lll/ilvis0_forecast_report.py',sources=sources,
            inputs=inputs,tasks=tasks,workers=1,threads=4,maximum_wall_s=60.)
        atomic(base/'definition.json',encoded(definition));manifest=Definition.from_dict(definition,root).prepare(root)
        return dict(path='data/'+identity,identities=6,maximum_linear_solves=12,allocation=manifest['allocation'])
    finally:parent.close()


def evaluate(task,context):
    from lll.studies.journal import Journal
    from lll.studies.artifacts import digest
    source=json.loads(context.input_path().read_bytes());local=source['local']
    if task['payload']['maximum_linear_solves']!=2:raise ValueError('fixed two-solve audit required')
    journal=Journal(context.directory/'linear-solves.sqlite',freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={task['identity']:dict(linear_solves=2)})
    journal.start(task['identity'])
    report=linear_corrections(local['residual'],local['jacobian'],local['normalized_parameters'],
        reserve=lambda:journal.reserve(task['identity'],'linear_solves',1))
    context.save('linear-corrections.json',report)
    return dict(passed=True,diagnostic=report,source=source,linear_solves=2,native_calls=0,
        nonlinear_stability_established=False,scientific_decision='abstain')


def inspect(root,prefix):
    from lll.studies.closed import ClosedStudy
    study=ClosedStudy(root,prefix);rows=[];forecasts={}
    try:
        r=study.input('recipe')
        for identity,task in study.tasks.items():
            envelope=study.envelope(identity);result=envelope['result'];row=dict(result,identity=identity)
            for name,sha in envelope['artifacts'].items():study.read(name,sha,raw=True)
            if 'converged' not in result:
                row.update(task['payload']);rows.append(row);continue
            fit=study.artifact(identity,'fit.json');forecast=study.artifact(identity,'forecast.json')
            errors=forecast['coordinate_errors'];cut=forecast['training_epochs']
            if (len(errors)!=len(r['times_s']) or cut!=2*len(errors)//3
                    or any(len(e)!=3 or any(not math.isfinite(v) for v in e) for e in errors)
                    or forecast['active_parameters']!=fit['active_parameters']
                    or len(fit['active_parameters'])!=26+int(task['payload']['profile'])
                    or fit['evaluations']!=result['evaluations']
                    or envelope['charged']['native_calls']!=fit['evaluations']+1
                    or fit['evaluations']>r['maximum_evaluations']
                    or result['converged']!=fit['converged']):
                raise ValueError('saved forecast, columns or charge record differs')
            checks={}
            for name,section in [('training',errors[:cut]),('prediction',errors[cut:])]:
                rms=[math.sqrt(math.fsum(e[j]**2 for e in section)/len(section)) for j in range(3)]
                maximum=[max(abs(e[j]) for e in section) for j in range(3)]
                checks[name]=dict(rms_neu_m=rms,maximum_abs_neu_m=maximum)
                if any(not math.isclose(v,w,rel_tol=1e-10,abs_tol=1e-15)
                    for key,values in checks[name].items() for v,w in zip(values,result[name][key],strict=True)):
                    raise ValueError('saved forecast errors differ from epoch series')
            expected=bool(fit['converged'] and fit['residual_sum_squares']<=r['maximum_training_cost']
                and all(max(v['rms_neu_m'])<=r['position_rms_m'] and max(v['maximum_abs_neu_m'])<=r['position_max_m']
                    for v in checks.values()) and result['all_active_columns_retained'])
            if result['passed']!=expected:raise ValueError('saved qualification label differs from frozen checks')
            row['reason']=fit['stability_probe'].get('reason',fit['message'])
            forecasts[identity]=errors[cut:];rows.append(row)
        pairs=[];grouped={}
        for row in rows:
            spec=study.tasks[row['identity']]['payload'];key=(spec['model'],spec['profile'],spec['clock'])
            grouped.setdefault(key,{})[spec['start']]=row
        for (model,profile,clock),values in grouped.items():
            if set(values)!={0,1}:raise ValueError('both frozen starts required')
            a,b=(values[i] for i in (0,1));pair=dict(model=model,profile=profile,clock=clock,
                both_passed=bool(a['passed'] and b['passed']))
            if a['identity'] in forecasts and b['identity'] in forecasts:
                x,y=(forecasts[v['identity']] for v in (a,b))
                pair['forecast_difference_rms_neu_m']=[math.sqrt(math.fsum((e[j]-f[j])**2
                    for e,f in zip(x,y,strict=True))/len(x)) for j in range(3)]
                pair['training_cost_difference']=abs(a['training_cost']-b['training_cost'])
            pairs.append(pair)
        passing=sum(v['passed'] for v in rows)
        return dict(total=len(study.tasks),passing=passing,converged=sum(v.get('converged',False) for v in rows),
            rows=rows,pairs=pairs,complete=len(rows)==len(study.tasks)==24 and passing==24,
            native_calls=study.summary['charged']['native_calls'],numerical_work=0,
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            original_reads=0,observed_starts=0,observational_coverage_qualified=False,scientific_decision='abstain')
    finally:study.close()


def render(report):
    labels=dict(sphere_rotating='Globe + field',sphere_still='Globe, zero field',flat_still='Stationary disc')
    lines=['# Training-only forecast controls','',
        f"**{report['passing']}/{report['total']} fits passed the complete software checks.** "
        + ('The procedure qualified on these controls.' if report['complete'] else 'The procedure did not qualify.'),
        '',f"{report['converged']}/{len(report['rows'])} saved fits passed the numerical stopping checks. "
        f"The run charged {report['native_calls']:,} native calculations.",
        '', 'No aircraft observations were used. These are short generated tracks with '
        'known answers, not Earth-model detections or calibrated confidence intervals.',
        '', 'Small forecast errors do not qualify a failed stopping check.',
        '', '| Model | Removal profiled | Clock | Start | Stopping check | Largest later axis RMS (mm) |',
        '|---|---|---|---:|---|---:|']
    for row in report['rows']:
        error=max(row['prediction']['rms_neu_m'])*1000 if 'prediction' in row else None
        lines.append('| '+' | '.join([labels.get(row['model'],str(row['model'])),str(row['profile']),row['clock'],
            str(row['start']),'Passed' if row.get('converged') else 'Unfinished',f'{error:.6g}' if error is not None else 'Not calculated'])+' |')
    lines+=['', 'The saved audit also compares both starts on each identical track. '
        'Forecast differences describe numerical sensitivity; they are not uncertainty bounds. '
        'Failures remain unchanged and this completed allowance cannot be restarted.',
        '', '[Frozen question and limits](PLAN.md) · [Pilot inventory](../ilvis0-prediction-pilot-preparation/README.md) · '
        '[Prediction protocol](../PREDICTION_VALIDATION.md)']
    return '\n'.join(lines)+'\n'


def publish(root,prefix='data/ilvis0-training-forecast-controls-v3-20261023',output='docs/ilvis0-training-forecast-controls',*,
            plan='docs/ilvis0-training-forecast-controls/PLAN.md'):
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic,encoded,digest,safe_path
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();public=safe_path(root,output);data=safe_path(root,prefix)
    if (public/'evidence-receipt.json').exists():raise ValueError('closed publication is already sealed')
    report=inspect(root,prefix);package(data,public,render(report),plan=plan)
    receipt=json.loads((public/'evidence-receipt.json').read_bytes());name='artifacts/publication/forecast-audit.json'
    raw=encoded(report);atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    name='artifacts/publication/forecast-report-source.py';raw=Path(__file__).read_bytes()
    atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,numerical_work=0)
