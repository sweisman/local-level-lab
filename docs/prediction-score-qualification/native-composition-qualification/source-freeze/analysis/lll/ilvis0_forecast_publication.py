# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only retrospective forecast audit; never fit or query a motion kernel."""
import math


def primary(rows):
    eligible=[v for v in rows if v.get('passed') and v.get('converged')]
    if any(not math.isfinite(v['training_cost']) or v['training_cost']<0 for v in eligible):
        raise ValueError('finite nonnegative training costs required')
    return min(eligible,key=lambda v:(v['training_cost'],v['start'])) if eligible else None


def inspect(root,prefix):
    import gzip
    import json
    from lll.studies.closed import ClosedStudy
    from lll.ilvis0_saved_prediction import summarize
    study=ClosedStudy(root,prefix);rows=[];groups={};material={};errors_by_id={}
    try:
        if len(study.tasks)!=72:raise ValueError('complete fixed 72-start definition required')
        for task in study.tasks.values():
            spec=task['payload']
            groups.setdefault((spec['segment_id'],spec['model'],spec['profile'],spec['clock']),[])
        if len(groups)!=36:raise ValueError('complete recording/model/processing/clock matrix required')
        for identity,task in study.tasks.items():
            if identity not in study.rows:continue
            envelope=study.envelope(identity);result=envelope['result'];spec=task['payload']
            for name,sha in envelope['artifacts'].items():study.read(name,sha,raw=True)
            row=dict(result,identity=identity,**{k:spec[k] for k in ('segment_id','profile','clock','start')})
            if 'converged' in result:
                fit=study.artifact(identity,'fit.json');forecast=study.artifact(identity,'forecast.json')
                epochs=study.artifact(identity,'epochs.json');saved=study.artifact(identity,'scores.json')
                sid=spec['segment_id']
                if sid not in material:
                    m=json.loads(gzip.decompress(study.input(sid+'-measurements',raw=True)))
                    truth=study.input(sid+'-scoring');material[sid]=(m,truth)
                m,truth=material[sid];cut=m['layout']['training_epochs']
                gps=m['training_gps']+truth['prediction_gps'];times=m['times'];predicted=forecast['coordinates']
                if (len(gps)!=len(times) or len(predicted)!=len(times) or len(epochs)!=len(times)
                        or forecast['times']!=times or forecast['training_epochs']!=cut
                        or fit['evaluations']!=result['evaluations'] or fit['evaluations']>200
                        or envelope['charged']['native_calls']!=fit['evaluations']+1
                        or forecast['active_parameters']!=fit['active_parameters']
                        or len(fit['active_parameters'])!=26+int(spec['profile'])
                        or result['converged']!=fit['converged']
                        or result['passed']!=bool(fit['converged'])
                        or not math.isfinite(result['training_cost']) or result['training_cost']<0
                        or result['training_cost']!=fit['residual_sum_squares']
                        or not forecast['continuous_propagation_without_gps_reset']
                        or forecast['prediction_receiver_positions_used']):
                    raise ValueError('saved prediction identity, column, timing or charge mismatch')
                for i,(position,observed) in enumerate(zip(predicted,gps,strict=True)):
                    metric=(6378137.+observed[2],(6378137.+observed[2])*math.cos(observed[0]),1.)
                    for j,axis in enumerate(('north','east','up')):
                        expected=(position[j]-observed[j])*metric[j]
                        if not math.isclose(expected,epochs[i][axis+'_direct_error_m'],rel_tol=1e-10,abs_tol=1e-8):
                            raise ValueError('saved epoch error differs from original positions and forecast')
                audit=summarize(epochs,training_epochs=cut,prediction_epochs=len(times)-cut)
                errors_by_id[identity]=[[e[a+'_direct_error_m'] for a in ('north','east','up')] for e in epochs[cut:]]
                for section in ('training','prediction'):
                    for key in ('horizontal_rms_m','vertical_rms_m','maximum_horizontal_m','maximum_absolute_up_m'):
                        if any(not math.isclose(audit[section][key],values[section][key],rel_tol=1e-10,abs_tol=1e-8)
                               for values in (saved,result)):
                            raise ValueError('saved summary differs from epoch errors')
                limits=study.input('recipe')['accuracy_limits']
                checks={k:audit['prediction'][k]<=bound for k,bound in limits.items()}
                expected_screen=dict(passed=all(checks.values()),checks=checks,limits=limits,
                    calibrated_goodness_of_fit=False,scientific_decision='abstain')
                if result['accuracy_screen']!=expected_screen:
                    raise ValueError('saved accuracy label differs from frozen limits and epoch errors')
            key=(spec['segment_id'],spec['model'],spec['profile'],spec['clock'])
            groups.setdefault(key,[]).append(row);rows.append(row)
        primaries=[];sensitivity=[]
        for (sid,model,profile,clock),values in groups.items():
            chosen=primary(values)
            primaries.append(dict(segment_id=sid,model=model,profile=profile,clock=clock,
                available_starts=len(values),primary=chosen,start_selection='converged training cost, then first start'))
            pair=sorted(values,key=lambda v:v['start'])
            difference=dict(segment_id=sid,model=model,profile=profile,clock=clock,available=False)
            if len(pair)==2 and all(v['identity'] in errors_by_id for v in pair):
                a,b=(errors_by_id[v['identity']] for v in pair)
                delta=[[x-y for x,y in zip(u,v,strict=True)] for u,v in zip(a,b,strict=True)]
                difference.update(available=True,
                    rms_neu_m=[math.sqrt(math.fsum(v[j]**2 for v in delta)/len(delta)) for j in range(3)],
                    maximum_abs_neu_m=[max(abs(v[j]) for v in delta) for j in range(3)])
            sensitivity.append(difference)
        return dict(prefix=prefix,total=72,completed=len(rows),
            converged=sum(v.get('converged',False) for v in rows),rows=rows,primaries=primaries,
            charged=study.summary['charged'],elapsed_s=study.summary['elapsed_s'],
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            layouts=study.input('layouts.json'),start_sensitivity=sensitivity,
            numerical_work=0,confidence_calibrated=False,scientific_decision='abstain')
    finally:study.close()


def render(report):
    labels=('Globe, specified field','Globe, zero field','Stationary disc')
    names={v['segment_id']:chr(65+i) for i,v in enumerate(report['layouts'])}
    lines=['# Predicting the later flight','',
        f"**{report['converged']}/{report['completed']} returned fits passed their numerical stopping checks.** "
        f"The frozen definition contains {report['total']} starts.",'',
        'Each model calibrates on earlier receiver positions and IMU increments, then',
        'predicts later positions from the continuous IMU stream without a GPS reset.',
        'Later GPS positions only score the saved forecast. Height counts alongside',
        'horizontal error. Start selection uses converged training cost alone.','',
        'These are retrospective development results. Accuracy screens are descriptive;',
        'neither a small error nor a relative advantage establishes calibrated significance.','',
        '| Stretch | Source recording | IMU format code | GPS fixes |',
        '|---|---|---:|---:|']
    for v in report['layouts']:
        lines.append(f"| {names[v['segment_id']]} | {v['filename']} | {v['imu_type']} | {v['receiver_epochs']} |")
    lines += ['',
        '| Stretch | Candidate | Removal | Clock | Primary start | Later horizontal RMS, m | Later height RMS, m | Accuracy screen |',
        '|---|---|---|---|---:|---:|---:|---|']
    for group in report['primaries']:
        row=group['primary']
        fields=[names.get(group['segment_id'],group['segment_id']),labels[group['model']],
            'Profiled' if group['profile'] else 'None',group['clock']]
        if row is None:fields+=['—','Unavailable','Unavailable','No qualified primary']
        else:
            error=row['prediction'];fields += [str(row['start']),f"{error['horizontal_rms_m']:.6g}",
                f"{error['vertical_rms_m']:.6g}",'Passed' if row['accuracy_screen']['passed'] else 'Failed']
        lines.append('| '+' | '.join(fields)+' |')
    lines+=['',f"The run charged {report['charged']['native_calls']:,} native calculations. "
        'Unfinished and failed starts remain in the sealed evidence, including alternatives',
        'to each displayed primary. Differences between starts describe sensitivity,',
        'not a confidence interval. A smaller horizontal error cannot excuse an',
        'implausible height reconstruction.','',
        '[Selection and splits](../ilvis0-prediction-pilot-preparation/README.md) · '
        '[Scientific plan](PLAN.md) · [Packaging correction](../ilvis0-prediction-pilot-preparation/LOADER_REPAIR.md) · '
        '[Prediction protocol](../PREDICTION_VALIDATION.md)']
    return '\n'.join(lines)+'\n'


def publish(root,prefix,output):
    import json
    from pathlib import Path
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic,digest,encoded,safe_path
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();public=safe_path(root,output);data=safe_path(root,prefix)
    if (public/'evidence-receipt.json').exists():raise ValueError('publication already sealed')
    report=inspect(root,prefix)
    package(data,public,render(report),plan='docs/ilvis0-prediction-pilot-preparation/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    for name,raw in [('report.json',encoded(report)),('reporter.py',Path(__file__).read_bytes())]:
        name='artifacts/publication/'+name;atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,numerical_work=0)
