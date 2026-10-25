# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit saved training/forecast evidence; never fit or propagate again.

Metadata gates import no numerical library. Full closed-study array inspection
uses NumPy lazily and must run under the numerical guard after worker completion.
"""
import json
import math

from lll.airquantumgrav_geographic_report import error_metrics,_same_metrics,construction_counts
from lll.airquantumgrav_observation_report import native_accounting


def saved_position_errors(prediction,answer,*,model,constants):
    if model not in ('sphere_rotating','sphere_still','flat_still') or not prediction:
        raise ValueError('declared generating geometry and nonempty prediction required')
    names=('position_world_m','body_axes_world','attitude_body_to_local')
    if any(len(answer[k])!=len(prediction) for k in names):raise ValueError('aligned scoring geometry required')
    errors=[]
    for c,p,axes,rotation in zip(prediction,*(answer[k] for k in names),strict=True):
        if (len(c)!=3 or len(p)!=3 or any(not math.isfinite(v) for v in c+p)
                or abs(c[0])>=math.pi/2 or len(axes)!=3 or len(rotation)!=3
                or any(len(row)!=3 or any(not math.isfinite(x) for x in row) for row in axes+rotation)):
            raise ValueError('finite supported coordinates and complete scoring frames required')
        phi,longitude,height=c
        if model=='flat_still':radius=constants['DISC_RADIUS']*(math.pi/2-phi);vertical=height
        else:
            rn=constants['A']/math.sqrt(1-constants['E2']*math.sin(phi)**2)
            radius=(rn+height)*math.cos(phi);vertical=(rn*(1-constants['E2'])+height)*math.sin(phi)
        delta=[radius*math.cos(longitude)-p[0],radius*math.sin(longitude)-p[1],vertical-p[2]]
        local=[math.fsum(axes[j][k]*rotation[i][k]*delta[j] for j in range(3) for k in range(3)) for i in range(3)]
        errors.append([local[0],local[1],-local[2]])
    return errors


def case_gate(result,fit,forecast,scores,recipe):
    n=recipe['queries'];cut=2*n//3
    expected=[name+'_'+a for name in ('attitude','velocity','position','gyro_bias','accel_bias','gyro_gain','accel_gain','lever') for a in 'xyz']
    expected+=['gravity_delta','time_offset']+(['earth_removal'] if result['profile'] else [])
    if (fit['active_parameters']!=expected or forecast['active_parameters']!=expected
            or len(fit['normalized_parameters'])!=len(expected)
            or any(not math.isfinite(x) or abs(x)>1 for x in fit['normalized_parameters'])
            or not result['all_columns_retained']):raise ValueError('complete feasible active nuisance columns required')
    cost=fit['residual_sum_squares'];evaluations=fit['evaluations']
    if (not math.isfinite(cost) or cost<0 or cost!=result['training_cost'] or type(evaluations) is not int
            or not 1<=evaluations<=recipe['maximum_evaluations'] or result['evaluations']!=evaluations
            or fit['converged']!=result['converged']):raise ValueError('saved training cost, work or convergence labels differ')
    if (len(scores['errors_neu_m'])!=n or len(forecast['coordinates'])!=n
            or any(len(v)!=3 or any(not math.isfinite(x) for x in v) for v in forecast['coordinates'])
            or any(result[k]!=v or forecast[k]!=v for k,v in [('training_epochs',cut),('prediction_epochs',n-cut)])
            or not forecast['continuous_propagation_without_gps_reset'] or forecast['prediction_receiver_positions_used']
            or result['true_initial_state_supplied'] or result['true_calibration_supplied']
            or not result['forecast_saved_before_scoring'] or not scores['training_positions_reproduced_for_scoring']):
        raise ValueError('complete training-only prediction binding required')
    sections={name:error_metrics(scores['errors_neu_m'][section]) for name,section in [('training',slice(0,cut)),('prediction',slice(cut,None))]}
    for name,metrics in sections.items():_same_metrics(metrics,scores[name]);_same_metrics(metrics,result[name])
    accuracy={name:{k:v[k]<=limit for k,limit in recipe['accuracy'].items()} for name,v in sections.items()}
    passed=fit['converged'] and all(v for group in accuracy.values() for v in group.values())
    if accuracy!=result['accuracy'] or result['passed']!=passed:raise ValueError('saved training/prediction gate labels differ')
    return dict(passed=passed,converged=fit['converged'],accuracy=accuracy,**sections)


def _raw_arrays(raw,training,recipe):
    import io
    import numpy as np
    from lll.studies.artifacts import digest
    names=('theta','dv','dt','rate_times','angular_rate_rads','specific_force_mps2','times')
    n=round(recipe['duration_s']*recipe['rate_hz']);cut=2*recipe['queries']//3
    with np.load(io.BytesIO(raw),allow_pickle=False) as archive:
        if set(archive.files)!=set(names):raise ValueError('complete raw-only numerical array archive required')
        arrays={k:archive[k] for k in names}
    shapes=dict(theta=(n,3),dv=(n,3),dt=(n,),rate_times=(n+1,),angular_rate_rads=(n+1,3),specific_force_mps2=(n+1,3),times=(recipe['queries'],))
    if any(v.shape!=shapes[k] or v.dtype!=np.dtype('float64') or not np.all(np.isfinite(v)) for k,v in arrays.items()):
        raise ValueError('finite float64 raw/generated arrays with exact shapes required')
    times=recipe['query_start_s']+np.arange(recipe['queries'])*recipe['query_step_s']
    if (not np.array_equal(arrays['times'],times) or not np.array_equal(arrays['rate_times'],np.arange(n+1)/recipe['rate_hz'])
            or not np.array_equal(arrays['dt'],np.diff(arrays['rate_times'])) or np.any(arrays['dt']<=0)
            or np.any(arrays['dt']>1.5/recipe['rate_hz'])):raise ValueError('raw sample ordering or supported timing differs')
    prefix=int(np.searchsorted(np.cumsum(arrays['dt']),times[cut-1]+recipe['limits']['time_offset'],side='left'))+1
    if (training['native_prefix_packets']!=prefix or training['training_epochs']!=cut
            or training['times_s']!=times[:cut].tolist() or training['limits']!=recipe['limits']
            or training['training_sigma_m']!=recipe['training_sigma_m']
            or training['maximum_interval_s']!=1.5/recipe['rate_hz']
            or training['true_initial_state_supplied'] or training['true_calibration_supplied']):
        raise ValueError('exact earlier-only initialization/weight binding required')
    for name in names[:-1]:
        if digest(arrays[name].astype('<f8',copy=False).tobytes())!=training['raw_arrays_sha256'][name]:
            raise ValueError('raw generated array hash differs')
    for name in ('theta','dv','dt'):
        if digest(arrays[name][:prefix].astype('<f8',copy=False).tobytes())!=training['training_prefix_sha256'][name]:
            raise ValueError('raw training prefix differs')
    return prefix


def inspect(root,prefix='data/esa-training-forecast-controls-20261023'):
    from itertools import product
    from lll.studies.closed import ClosedStudy,load_python_reference
    from lll.studies.artifacts import digest,encoded
    study=ClosedStudy(root,prefix);rows=[];native={};shared={};binaries={'value':set(),'tangent':set()}
    try:
        r=study.input('recipe');env=study.input('qualification-environment');n=round(r['duration_s']*r['rate_hz']);cut=2*r['queries']//3
        expected=set(product(r['models'],r['latitudes_deg'],r['profiles'],range(r['starts'])))
        actual={(t['payload']['model'],t['payload']['latitude_deg'],t['payload']['profile'],t['payload']['start']) for t in study.tasks.values()}
        if len(study.tasks)!=24 or len(expected)!=24 or actual!=expected:raise ValueError('complete frozen 24-fit training matrix required')
        path='analysis/lll/airquantumgrav_truth.py';sha=study.manifest['sources'][path]
        geometry=load_python_reference(study.read('source-freeze/'+path,sha,raw=True),name='lll._training_report_geometry_'+sha,sha256=sha)
        constants={k:getattr(geometry,k) for k in ('A','E2','DISC_RADIUS')}
        limits=dict(constructed_intervals=n,generated_samples=n+1+cut+r['queries']);charged={k:0 for k in study.summary['charged']}
        for shard in range(study.manifest['allocation']['workers']):
            assigned={i for i,t in study.tasks.items() if t['shard']==shard}
            native.update(native_accounting(study.read(f'shards/{shard:03d}/charges/journal.sqlite',raw=True),study.completion['manifest_sha256'],assigned))
        for identity,task in study.tasks.items():
            if identity not in study.rows:continue
            envelope=study.envelope(identity);result=envelope['result'];spec=task['payload']
            for k in charged:charged[k]+=envelope['charged'][k]
            for name,sha in envelope['artifacts'].items():study.read(name,sha,raw=True)
            full='converged' in result;journal='artifacts/'+identity+'/construction.sqlite'
            counts=construction_counts(study.read(journal,envelope['artifacts'][journal],raw=True),study.completion['manifest_sha256'],identity,limits,complete=full) if journal in envelope['artifacts'] else None
            operations=native[identity]
            if (operations['value'] or operations['tangent']!=envelope['charged']['native_calls']
                    or operations['packet_visits']!=envelope['charged']['packet_visits']):raise ValueError('native kind/work totals differ')
            row=dict(identity=identity,spec=spec,result=result,complete=full,construction_counts=counts,native=operations)
            if full:
                if any(result[k]!=v for k,v in spec.items()) or counts!=limits:raise ValueError('training identity/construction scope differs')
                training=study.artifact(identity,'training-observations.json');fit=study.artifact(identity,'fit.json')
                forecast=study.artifact(identity,'forecast.json');scores=study.artifact(identity,'scores.json');answer=study.artifact(identity,'scoring-observations.json')
                prefix_packets=_raw_arrays(study.artifact(identity,'raw-inputs.npz',raw=True),training,r)
                calls=fit['evaluations']+1;visits=fit['evaluations']*prefix_packets*cut+n*r['queries']
                if (operations['tangent']!=calls or operations['packet_visits']!=visits or result['native_calls']!=calls
                        or result['constructed_intervals']!=n or result['generated_samples']!=limits['generated_samples']):
                    raise ValueError('actual fitting/forecast work differs from exact raw support')
                times=[r['query_start_s']+i*r['query_step_s'] for i in range(r['queries'])]
                if (forecast['times_s']!=times or scores['times_s']!=times
                        or answer['coordinates'][:cut]!=training['coordinates']):raise ValueError('query/earlier receiver identity differs')
                physical=saved_position_errors(forecast['coordinates'],answer,model=spec['model'],constants=constants)
                if any(abs(a-b)>1e-7 for x,y in zip(physical,scores['errors_neu_m'],strict=True) for a,b in zip(x,y,strict=True)):
                    raise ValueError('saved physical errors differ from independent Cartesian reconstruction')
                row['checked']=case_gate(result,fit,forecast,scores,r)
                key=(spec['model'],spec['latitude_deg'],spec['profile'])
                shared_hashes=dict(raw=digest(study.artifact(identity,'raw-inputs.npz',raw=True)),training=digest(encoded(training)),scoring=digest(encoded(answer)))
                if key in shared and shared[key]!=shared_hashes:raise ValueError('starting points used different raw/receiver observations')
                shared[key]=shared_hashes
                meta=study.artifact(identity,'compilation.json')
                for kind,filename,compiler in [('value','ilvis0_native.c','cc'),('tangent','ilvis0_tangent.cpp','c++')]:
                    if meta[kind]['source_sha256']!=study.manifest['sources']['analysis/lll/'+filename] or meta[kind]['compiler']!=env['compilers'][compiler]:
                        raise ValueError('compiled training source/environment differs')
                    binaries[kind].add(meta[kind]['binary_sha256'])
            elif result['passed']:raise ValueError('unfinished training calculation cannot pass')
            rows.append(row)
        if any(len(v)>1 for v in binaries.values()) or charged!=study.summary['charged']:raise ValueError('compiled binary or total work differs')
        passing=sum(v['result']['passed'] for v in rows);families=[]
        for model in r['models']:
            group=[v for v in rows if v['spec']['model']==model];full=[v for v in group if v['complete']]
            families.append(dict(model=model,returned=len(group),complete=len(full),passed=sum(v['result']['passed'] for v in group),
                converged=sum(v['result']['converged'] for v in full),
                maximum_prediction_horizontal_rms_m=max((v['checked']['prediction']['horizontal_rms_m'] for v in full),default=None),
                maximum_prediction_height_rms_m=max((v['checked']['prediction']['vertical_rms_m'] for v in full),default=None),
                maximum_prediction_spatial_error_m=max((v['checked']['prediction']['maximum_3d_m'] for v in full),default=None)))
        return dict(prefix=prefix,total=24,returned=len(rows),passing=passing,qualified=len(rows)==passing==24,
            families=families,rows=rows,charged=charged,elapsed_s=study.summary['elapsed_s'],
            construction_totals={k:sum((v['construction_counts'] or {}).get(k,0) for v in rows) for k in limits},
            construction_accounting_complete=all(v['construction_counts'] is not None for v in rows),
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            numerical_work=0,original_reads=0,observed_starts=0,true_calibration_supplied=False,
            later_positions_used_in_training=False,confidence_calibrated=False,scientific_decision='abstain')
    finally:study.close()


def render(report):
    labels=dict(sphere_rotating='Globe with specified field',sphere_still='Globe with zero field',flat_still='Tested disc')
    lines=['# Learning calibration and predicting later positions','',
        f"**{report['passing']}/{report['total']} generated fits passed every frozen check.** "
        + ('The declared training/forecast calculation qualified.' if report['qualified'] else 'The complete calculation did not qualify.'),'',
        'Each fit starts from earlier receiver positions and raw generated IMU',
        'channels. It estimates calibration with every declared nuisance parameter',
        'active, then predicts the later path without a receiver reset. Later',
        'positions are exposed only after the forecast is saved. True attitude,',
        'velocity, gravity and calibration are not supplied to the fit.','',
        'These are two-minute generated maneuvering trajectories, not ESA recordings.',
        'They include the declared sensor biases and gains, with no random measurement',
        'noise added. Their small prediction errors are software results, not measured',
        'instrument accuracy.',
        'Every fit uses its generating geometry; this checks estimation and prediction,',
        'not a calibrated three-model decision.','',
        '| Generating geometry | Passed | Converged | Largest later horizontal RMS | Largest later height RMS | Largest later spatial error |',
        '|---|---:|---:|---:|---:|---:|']
    for row in report['families']:
        number=lambda k:'Unavailable' if row[k] is None else f"{row[k]:.6g} m"
        lines.append('| '+' | '.join([labels[row['model']],f"{row['passed']}/8",f"{row['converged']}/8",
            number('maximum_prediction_horizontal_rms_m'),number('maximum_prediction_height_rms_m'),number('maximum_prediction_spatial_error_m')])+' |')
    lines+=['', 'A pass requires the numerical stopping checks, all calibration columns,',
        'horizontal and height RMS at most 0.1 m in both sections, and maximum',
        'spatial error at most 0.5 m. Small errors cannot relabel an unfinished fit.',
        'Neither convergence nor prediction agreement establishes unique calibration.',
        'All starts and failures remain in the evidence.','',
        f"The run used {report['charged']['native_calls']} native calls in {report['elapsed_s']/60:.2f} minutes.",
        'Saved-only verification checks raw array and prefix hashes, identical inputs',
        'across starts, fit labels, actual work and construction journals. It recomputes',
        'physical errors from saved predictions and independent Cartesian answers,',
        'with the frozen geometry constants. It performs no fit or propagation.','',
        'Actual sampling, receiver-error assessment and selection remain open before',
        'observed ESA comparisons. No reserved flight was used and no statistical',
        'confidence or Earth-model detection is claimed.','',
        '[Frozen question and allowance](PLAN.md) · [Known-correction controls](../esa-observation-controls/README.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md)']
    if not report['construction_accounting_complete']:
        lines+=['','Some failed cases lack a sealed construction journal; no complete construction accounting is claimed.']
    return '\n'.join(lines)+'\n'


def publish(root,prefix='data/esa-training-forecast-controls-20261023',output='docs/esa-training-forecast-controls'):
    from pathlib import Path
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic,digest,encoded,safe_path
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('training publication already sealed')
    report=inspect(root,prefix);package(data,public,render(report),plan='docs/esa-training-forecast-controls/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    for name,raw in [('verified-report.json',encoded(report)),('reporter.py',Path(__file__).read_bytes())]:
        name='artifacts/publication/'+name;atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,numerical_work=0)
