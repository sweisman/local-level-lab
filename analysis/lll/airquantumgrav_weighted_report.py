# SPDX-License-Identifier: AGPL-3.0-or-later
"""Closed weighted-control audit; numerical dependencies load only on inspection."""
import itertools
import json
import math


def matrix_summary(rows,r):
    keys=('model','latitude_deg','profile','start','policy_id')
    expected=set(itertools.product(r['models'],r['latitudes_deg'],r['profiles'],range(r['starts']),r['policies']))
    actual=[tuple(row['spec'][k] for k in keys) for row in rows]
    if len(actual)!=len(expected) or len(set(actual))!=len(actual) or set(actual)!=expected:
        raise ValueError('every distinct frozen model/latitude/processing/start/weight setting required')
    complete=sum(row['complete'] for row in rows);passing=sum(row['result']['passed'] for row in rows)
    if any(row['result']['passed'] and not row['complete'] for row in rows):
        raise ValueError('unfinished controls cannot pass')
    return dict(total=len(expected),complete=complete,passing=passing,qualified=complete==passing==len(expected))


def _raw(raw,training,scoring,r):
    import io
    import numpy as np
    from lll.studies.artifacts import digest
    n=round(r['duration_s']*r['rate_hz']);cut=2*r['queries']//3
    names=('theta','dv','dt','rate_times','angular_rate_rads','specific_force_mps2','times')
    with np.load(io.BytesIO(raw),allow_pickle=False) as archive:
        if set(archive.files)!=set(names):raise ValueError('complete generated raw array archive required')
        values={k:archive[k] for k in names}
    shapes=dict(theta=(n,3),dv=(n,3),dt=(n,),rate_times=(n+1,),angular_rate_rads=(n+1,3),specific_force_mps2=(n+1,3),times=(r['queries'],))
    if any(v.shape!=shapes[k] or v.dtype!=np.dtype('float64') or not np.all(np.isfinite(v)) for k,v in values.items()):
        raise ValueError('finite float64 generated arrays and exact shapes required')
    times=r['query_start_s']+np.arange(r['queries'])*r['query_step_s'];t=values['rate_times'];dt=values['dt']
    if (not np.array_equal(values['times'],times) or not np.array_equal(t,np.arange(n+1)/r['rate_hz'])
            or not np.array_equal(dt,np.diff(t)) or np.any(dt<=0) or np.any(dt>1.5/r['rate_hz'])):
        raise ValueError('actual generated time support differs')
    for increment,rate in [('theta','angular_rate_rads'),('dv','specific_force_mps2')]:
        expected=(values[rate][:-1]+values[rate][1:])/2*dt[:,None]
        if not np.array_equal(values[increment],expected):raise ValueError('constructed intervals differ from unchanged generated rates')
    prefix=int(np.searchsorted(np.cumsum(dt),times[cut-1]+r['limits']['time_offset'],side='left'))+1
    coordinates=[[math.radians(math.degrees(c[0])),math.radians(math.degrees(c[1])),c[2]] for c in scoring['coordinates'][:cut]]
    if (training['coordinates']!=coordinates or training['times_s']!=times[:cut].tolist()
            or training['native_prefix_packets']!=prefix or training['training_epochs']!=cut
            or training['prediction_epochs']!=len(times)-cut or training['time_origin_gps_sow_s']!=0.
            or training['prediction_receiver_positions_used'] or training['true_initial_state_supplied'] or training['true_calibration_supplied']):
        raise ValueError('exact earlier-only initialization and query binding required')
    for name in ('theta','dv','dt'):
        if digest(values[name][:prefix].astype('<f8',copy=False).tobytes())!=training['training_prefix_sha256'][name]:
            raise ValueError('unchanged raw training prefix differs')
    return prefix


def inspect(root,prefix='data/esa-weighted-training-controls-20261023'):
    from pathlib import Path
    from lll.studies.closed import ClosedStudy,load_python_reference
    from lll.studies.artifacts import digest,encoded
    from lll.airquantumgrav_geographic_report import construction_counts
    from lll.airquantumgrav_observation_report import native_accounting
    from lll.airquantumgrav_error_policy import build
    from lll.airquantumgrav_weighted_controls import fixture_rows
    study=ClosedStudy(root,prefix);parent=ClosedStudy(root,'docs/esa-training-forecast-controls')
    rows=[];native={};shared={};weight_keys={};binaries={'value':set(),'tangent':set()}
    try:
        # Use the preserved parent reporter's independent physical and fit gates.
        receipt=parent.read('evidence-receipt.json');name='artifacts/publication/reporter.py';sha=receipt['artifacts'][name]
        reference=load_python_reference(parent.read(name,sha,raw=True),name='lll._weighted_training_reference_'+sha,sha256=sha)
        for filename in ('airquantumgrav_geographic_report.py','airquantumgrav_observation_report.py',
                'airquantumgrav_error_policy.py','airquantumgrav_weighted_controls.py','ilvis0_error_model.py','models.py'):
            name='analysis/lll/'+filename
            if digest((Path(root)/name).read_bytes())!=study.manifest['sources'][name]:
                raise ValueError('restore qualified audit dependencies before reporting')
        name='analysis/lll/airquantumgrav_truth.py';sha=study.manifest['sources'][name]
        truth=load_python_reference(study.read('source-freeze/'+name,sha,raw=True),name='lll._weighted_truth_reference_'+sha,sha256=sha)
        constants={k:getattr(truth,k) for k in ('A','E2','DISC_RADIUS')}
        r=study.input('recipe');env=study.input('qualification-environment');n=round(r['duration_s']*r['rate_hz']);cut=2*r['queries']//3
        limits=dict(constructed_intervals=n,generated_samples=n+1+cut+r['queries']);charged={k:0 for k in study.summary['charged']}
        for shard in range(study.manifest['allocation']['workers']):
            assigned={i for i,t in study.tasks.items() if t['shard']==shard}
            native.update(native_accounting(study.read(f'shards/{shard:03d}/charges/journal.sqlite',raw=True),
                study.completion['manifest_sha256'],assigned,per_call_visits=None))
        for identity,task in study.tasks.items():
            if identity not in study.rows:
                rows.append(dict(identity=identity,spec=task['payload'],complete=False,
                    result=dict(passed=False,reason='no returned fit'),returned=False))
                continue
            envelope=study.envelope(identity);result=envelope['result'];spec=task['payload'];full='converged' in result
            for k in charged:charged[k]+=envelope['charged'][k]
            for name,sha in envelope['artifacts'].items():study.read(name,sha,raw=True)
            journal='artifacts/'+identity+'/construction.sqlite'
            counts=construction_counts(study.read(journal,envelope['artifacts'][journal],raw=True),study.completion['manifest_sha256'],
                identity,limits,complete=full) if journal in envelope['artifacts'] else None
            operations=native[identity]
            if (operations['value'] or operations['tangent']!=envelope['charged']['native_calls']
                    or operations['packet_visits']!=envelope['charged']['packet_visits']):raise ValueError('native kind or total charges differ')
            row=dict(identity=identity,spec=spec,result=result,complete=full,construction_counts=counts,native=operations,returned=True)
            if full:
                if any(result[k]!=v for k,v in spec.items()) or counts!=limits:raise ValueError('identity or construction scope differs')
                training=study.artifact(identity,'training-observations.json');fit=study.artifact(identity,'fit.json')
                forecast=study.artifact(identity,'forecast.json');scores=study.artifact(identity,'scores.json');answer=study.artifact(identity,'scoring-observations.json')
                raw=study.artifact(identity,'raw-inputs.npz',raw=True);prefix_packets=_raw(raw,training,answer,r)
                calls=fit['evaluations']+1;visits=fit['evaluations']*prefix_packets*cut+n*r['queries']
                if (operations['tangent']!=calls or operations['packet_visits']!=visits or result['native_calls']!=calls
                        or result['constructed_intervals']!=n or result['generated_samples']!=limits['generated_samples']):
                    raise ValueError('actual fitting and forecast work differs')
                times=[r['query_start_s']+i*r['query_step_s'] for i in range(r['queries'])]
                if forecast['times_s']!=times or scores['times_s']!=times:raise ValueError('fixed query schedule differs')
                weight=build(fixture_rows(answer['coordinates'][:cut],times[:cut]),policy_id=spec['policy_id'])
                if (training['weight_configuration']!=weight.configuration or result['weight_configuration']!=weight.configuration
                        or training['weight_descriptor']!=weight.descriptor or training['weight_source_sha256']!=weight.source_sha256):
                    raise ValueError('earlier-only working weights differ')
                physical=reference.saved_position_errors(forecast['coordinates'],answer,model=spec['model'],constants=constants)
                if any(abs(a-b)>1e-7 for x,y in zip(physical,scores['errors_neu_m'],strict=True) for a,b in zip(x,y,strict=True)):
                    raise ValueError('independently reconstructed Cartesian errors differ')
                row['checked']=reference.case_gate(result,fit,forecast,scores,r)
                key=(spec['model'],spec['latitude_deg'],spec['profile']);inputs=dict(raw=digest(raw),scoring=digest(encoded(answer)))
                if key in shared and shared[key]!=inputs:raise ValueError('weights or starts changed the generated observations')
                shared[key]=inputs;key=(*key,spec['policy_id'])
                if key in weight_keys and weight_keys[key]!=weight.configuration:raise ValueError('starts changed the training weights')
                weight_keys[key]=weight.configuration
                meta=study.artifact(identity,'compilation.json')
                for kind,filename,compiler in [('value','ilvis0_native.c','cc'),('tangent','ilvis0_tangent.cpp','c++')]:
                    if meta[kind]['source_sha256']!=study.manifest['sources']['analysis/lll/'+filename] or meta[kind]['compiler']!=env['compilers'][compiler]:
                        raise ValueError('compiled source/environment differs')
                    binaries[kind].add(meta[kind]['binary_sha256'])
            elif result['passed']:raise ValueError('unfinished result cannot pass')
            rows.append(row)
        if charged!=study.summary['charged'] or any(len(v)>1 for v in binaries.values()):raise ValueError('total charges or binaries differ')
        summary=matrix_summary(rows,r);families=[]
        for policy,model in itertools.product(r['policies'],r['models']):
            group=[row for row in rows if row['spec']['policy_id']==policy and row['spec']['model']==model]
            complete=[row for row in group if row['complete']]
            families.append(dict(policy_id=policy,model=model,total=len(group),passed=sum(row['result']['passed'] for row in group),
                converged=sum(row['result']['converged'] for row in complete),
                maximum_prediction_spatial_error_m=max((row['result']['prediction']['maximum_3d_m'] for row in complete),default=None)))
        return dict(**summary,returned=len(study.rows),rows=rows,families=families,charged=charged,elapsed_s=study.summary['elapsed_s'],
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            preserved_parent_reporter_sha256=receipt['artifacts']['artifacts/publication/reporter.py'],
            original_reads=0,observed_starts=0,protected_reads=0,confidence_calibrated=False,scientific_decision='abstain')
    finally:study.close();parent.close()


def render(report):
    labels=dict(sphere_rotating='Globe with specified field',sphere_still='Globe with zero field',flat_still='Tested disc')
    lines=['# Training and prediction with both working error cases','',
        f"**{report['passing']}/{report['total']} generated fits pass the frozen checks.** "
        +('The weighted calculation qualifies.' if report['qualified'] else 'The complete weighted calculation does not qualify.'),'',
        'Both receiver-error cases use the same common fitting/forecast pipeline',
        'planned for the observed ESA pilot. Calibration uses earlier positions only;',
        'later positions are opened after the continuous forecast is saved.',
        'The examples include turns, climbs and sensor/calibration errors, with no',
        'random measurement noise. They are software controls, not ESA observations.','',
        '| Working error case | Generating geometry | Passed | Converged | Largest later spatial error |',
        '|---|---|---:|---:|---:|']
    for row in report['families']:
        error='Unavailable' if row['maximum_prediction_spatial_error_m'] is None else f"{row['maximum_prediction_spatial_error_m']:.6g} m"
        lines.append(f"| {row['policy_id']} | {labels[row['model']]} | {row['passed']}/{row['total']} | {row['converged']}/{row['total']} | {error} |")
    lines+=['','Every pass requires numerical completion, every nuisance column, training',
        'and later horizontal/height RMS at most 0.1 m, and maximum spatial error',
        'at most 0.5 m. Failed or unfinished cases retain their original labels.',
        'No recovery of unique calibration or actual instrument precision is claimed.','',
        f"The study used {report['charged']['native_calls']:,} native calculations in {report['elapsed_s']/60:.2f} minutes.",
        'Saved-only verification reconciles original generated arrays, training',
        'prefixes, earlier-only weights, compiled sources, independent Cartesian',
        'position errors and all charged work. It performs no new fit or propagation.','',
        'Observed ESA fitting still requires its separate finite pilot definition.',
        'The actual error model is uncalibrated, and seven confirmation groups',
        'remain protected. The NASA findings are unchanged.','',
        '[Frozen question and allowance](PLAN.md) · [Prepared interval](../esa-development-pilot-preparation/README.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md)']
    return '\n'.join(lines)+'\n'


def publish(root,prefix='data/esa-weighted-training-controls-20261023',output='docs/esa-weighted-training-controls'):
    from pathlib import Path
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic,digest,encoded,safe_path
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('weighted-control publication already sealed')
    report=inspect(root,prefix);package(data,public,render(report),plan='docs/esa-weighted-training-controls/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    for name,raw in [('verified-report.json',encoded(report)),('reporter.py',Path(__file__).read_bytes())]:
        name='artifacts/publication/'+name;atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,native_calls=0)
