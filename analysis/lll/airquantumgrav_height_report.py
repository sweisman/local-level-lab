# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only long height-training audit; no fitting, propagation or regeneration."""
import json
import math
import re


def require_scope(result):
    if (any(result[k] for k in ('original_reads','protected_reads','observed_starts','true_initial_state_supplied',
            'true_calibration_supplied','confidence_calibrated','raw_arrays_retained'))
            or result['gravity_anchor_source']!='first_training_receiver_height' or result['scientific_decision']!='abstain'):
        raise ValueError('generated training-only scope and earlier receiver gravity anchor required')


def binding_gate(binding,after,rows,training,compilation,result,r):
    from lll.studies.artifacts import digest,encoded
    from lll.airquantumgrav_height_training import prefix_limit
    require_scope(result);n=round(r['duration_s']*r['rate_hz']);cut=2*r['queries']//3
    times=[r['query_start_s']+i*r['query_step_s'] for i in range(r['queries'])]
    keys={'theta','dv','dt','rate_times','angular_rate_rads','specific_force_mps2','times'}
    anchor=rows[0]['height_m'];prefix=binding['training_prefix_packets'];active=26+int(result['profile'])
    if (len(rows)!=cut or [v['time_s'] for v in rows]!=times[:cut]
            or binding['native_packets']!=n or binding['generated_rate_points']!=n+1
            or type(prefix) is not int or not 1<=prefix<=prefix_limit(r)
            or binding['training_epochs']!=cut or binding['prediction_epochs']!=r['queries']-cut
            or binding['gravity_anchor_source']!='first_training_receiver_height'
            or binding['gravity_anchor_height_m']!=anchor or result['gravity_anchor_height_m']!=anchor
            or binding['training_receiver_sha256']!=digest(encoded(rows)) or binding['raw_arrays_retained']
            or not binding['raw_arrays_are_deterministic_generated_not_observed']
            or not binding['raw_regeneration_requires_frozen_source_environment_recipe']
            or binding['original_reads'] or binding['protected_reads']):raise ValueError('training data or gravity anchor binding differs')
    if (set(binding['full_array_sha256'])!=keys or set(binding['training_prefix_sha256'])!={'theta','dv','dt'}
            or after['full_array_sha256']!=binding['full_array_sha256'] or not after['raw_arrays_unchanged']
            or after['jacobian_shape']!=[3*r['queries'],active]
            or any(not re.fullmatch('[0-9a-f]{64}',v) for v in [*binding['full_array_sha256'].values(),
                *binding['training_prefix_sha256'].values(),after['jacobian_sha256']])):
        raise ValueError('full generated input, prefix or derivative hashes differ')
    expected=[[math.radians(v['latitude_deg']),math.radians(v['longitude_deg']),v['height_m']] for v in rows]
    if (training['native_prefix_packets']!=prefix or training['training_prefix_sha256']!=binding['training_prefix_sha256']
            or training['times_s']!=times[:cut] or training['coordinates']!=expected
            or training['training_epochs']!=cut or training['prediction_epochs']!=r['queries']-cut
            or training['true_initial_state_supplied'] or training['true_calibration_supplied']
            or training['prediction_receiver_positions_used'] or training['time_origin_gps_sow_s']!=0.):
        raise ValueError('fit did not retain the exact earlier-only input boundary')
    for metadata in compilation.values():
        if metadata.get('gravity_model')!='inverse-square-height-v1' or metadata.get('gravity_anchor_height_m')!=anchor:
            raise ValueError('compiled gravity anchor differs from earlier receiver data')
    return prefix


def inspect(root,prefix='data/esa-height-training-controls-20261023'):
    from pathlib import Path
    from lll.studies.closed import ClosedStudy,load_python_reference
    study=ClosedStudy(root,prefix)
    try:
        import numpy as np
        from lll.airquantumgrav_height_training import recipe,tasks,construction_limits
        from lll.airquantumgrav_training_report import case_gate,saved_position_errors
        from lll.airquantumgrav_geographic_report import construction_counts
        from lll.airquantumgrav_observation_report import native_accounting
        from lll.airquantumgrav_observed_report import verify_audit_environment
        from lll.airquantumgrav_error_policy import build
        from lll.ilvis0_control_shards import runtime_environment
        from lll.studies.artifacts import digest,encoded
        r=study.input('recipe');canonical={v['identity']:v for v in tasks()};env=study.input('qualification-environment')
        if r!=recipe() or set(study.tasks)!=set(canonical) or len(canonical)!=24:raise ValueError('complete fixed height-training matrix required')
        audit_environment=runtime_environment();verify_audit_environment(env,audit_environment)
        for filename in ('airquantumgrav_height_training.py','airquantumgrav_training_report.py','airquantumgrav_error_policy.py'):
            name='analysis/lll/'+filename
            if digest((Path(root)/name).read_bytes())!=study.manifest['sources'][name]:raise ValueError('restore frozen reporting dependencies')
        name='analysis/lll/airquantumgrav_truth.py';sha=study.manifest['sources'][name]
        geometry=load_python_reference(study.read('source-freeze/'+name,sha,raw=True),name='lll._height_report_geometry_'+sha,sha256=sha)
        constants={key:getattr(geometry,key) for key in ('A','E2','DISC_RADIUS')}
        native={};rows=[];shared={};binaries={'value':set(),'tangent':set()};charged={k:0 for k in study.summary['charged']}
        for shard in range(study.manifest['allocation']['workers']):
            identities={i for i,t in study.tasks.items() if t['shard']==shard}
            native.update(native_accounting(study.read(f'shards/{shard:03d}/charges/journal.sqlite',raw=True),
                study.completion['manifest_sha256'],identities,per_call_visits=None))
        limits=construction_limits(r);n=round(r['duration_s']*r['rate_hz']);cut=2*r['queries']//3
        for identity,task in study.tasks.items():
            if {k:v for k,v in task.items() if k not in ('index','shard')}!=canonical[identity]:raise ValueError('task differs from fixed declaration')
            if identity not in study.rows:continue
            envelope=study.envelope(identity);result=envelope['result'];artifacts=envelope['artifacts'];operations=native[identity]
            for name,sha in artifacts.items():study.read(name,sha,raw=True)
            for key in charged:charged[key]+=envelope['charged'][key]
            if operations['value'] or operations['tangent']!=envelope['charged']['native_calls'] or operations['packet_visits']!=envelope['charged']['packet_visits']:
                raise ValueError('actual native kinds or envelope charges differ')
            complete='converged' in result;journal='artifacts/'+identity+'/construction.sqlite'
            construction=construction_counts(study.read(journal,artifacts[journal],raw=True),study.completion['manifest_sha256'],identity,
                limits,complete=complete) if journal in artifacts else None
            row=dict(identity=identity,spec=task['payload'],result=result,complete=complete,construction=construction)
            if complete:
                if any(result[k]!=v for k,v in task['payload'].items()) or construction!=limits:raise ValueError('identity or complete construction work differs')
                fit=study.artifact(identity,'fit.json');forecast=study.artifact(identity,'forecast.json')
                scores=study.artifact(identity,'scores.json');answer=study.artifact(identity,'scoring-observations.json')
                earlier=study.artifact(identity,'training-receiver.json');training=study.artifact(identity,'training-observations.json')
                binding=study.artifact(identity,'input-binding.json');after=study.artifact(identity,'forecast-binding.json')
                meta=study.artifact(identity,'compilation.json')
                count=binding_gate(binding,after,earlier,training,meta,result,r)
                visits=fit['evaluations']*count*cut+n*r['queries']
                if (operations['tangent']!=fit['evaluations']+1 or result['native_calls']!=operations['tangent']
                        or operations['packet_visits']!=visits or result['constructed_intervals']!=n
                        or result['generated_samples']!=limits['generated_samples']):raise ValueError('exact fitting/forecast charges differ')
                weight=build(earlier,policy_id=task['payload']['policy_id'])
                if (training['weight_configuration']!=weight.configuration or training['weight_descriptor']!=weight.descriptor
                        or training['weight_source_sha256']!=weight.source_sha256):raise ValueError('earlier-only working weights differ')
                times=[r['query_start_s']+i*r['query_step_s'] for i in range(r['queries'])]
                if forecast['times_s']!=times or scores['times_s']!=times or not np.allclose(answer['coordinates'][:cut],
                        training['coordinates'],rtol=0,atol=2e-14):raise ValueError('fixed query or earlier receiver coordinates differ')
                physical=saved_position_errors(forecast['coordinates'],answer,model=result['model'],constants=constants)
                if any(abs(a-b)>1e-7 for x,y in zip(physical,scores['errors_neu_m'],strict=True) for a,b in zip(x,y,strict=True)):
                    raise ValueError('independent saved physical errors differ')
                row['checked']=case_gate(result,fit,forecast,scores,r)
                key=(result['model'],result['profile']);value=dict(raw=binding['full_array_sha256'],
                    training=digest(encoded(earlier)),scoring=digest(encoded(answer)),anchor=binding['gravity_anchor_height_m'])
                if key in shared and shared[key]!=value:raise ValueError('policies or starts used different generated observations')
                shared[key]=value
                for kind,filename,compiler in [('value','ilvis0_native.c','cc'),('tangent','ilvis0_tangent.cpp','c++')]:
                    value=meta[kind]
                    if value['source_sha256']!=study.manifest['sources']['analysis/lll/'+filename] or value['compiler']!=env['compilers'][compiler]:
                        raise ValueError('compiled source or compiler differs')
                    binaries[kind].add(value['binary_sha256'])
            elif result['passed']:raise ValueError('unfinished training case cannot qualify')
            rows.append(row)
        if (charged!=study.summary['charged'] or any(len(v)>1 for v in binaries.values())
                or sum(v['tangent'] for v in native.values())!=charged['native_calls']):raise ValueError('whole-study native charges or binaries differ')
        families=[]
        for model in r['models']:
            group=[v for v in rows if v['spec']['model']==model];full=[v for v in group if v['complete']]
            families.append(dict(model=model,returned=len(group),passed=sum(v['result']['passed'] for v in group),
                converged=sum(v['result']['converged'] for v in full),
                maximum_prediction_horizontal_rms_m=max((v['checked']['prediction']['horizontal_rms_m'] for v in full),default=None),
                maximum_prediction_height_rms_m=max((v['checked']['prediction']['vertical_rms_m'] for v in full),default=None),
                maximum_prediction_spatial_error_m=max((v['checked']['prediction']['maximum_3d_m'] for v in full),default=None)))
        passed=sum(v['result']['passed'] for v in rows)
        return dict(verified=True,total=24,returned=len(rows),passed=passed,qualified=len(rows)==passed==24,families=families,rows=rows,
            charged=charged,construction_totals={k:sum((v['construction'] or {}).get(k,0) for v in rows) for k in limits},
            construction_accounting_complete=all(v['construction'] is not None for v in rows),elapsed_s=study.summary['elapsed_s'],
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            audit_environment=audit_environment,native_calls_during_audit=0,original_reads=0,protected_reads=0,observed_starts=0,
            raw_array_hashes_audited_without_regeneration=True,raw_arrays_retained=False,
            confidence_calibrated=False,scientific_decision='abstain')
    finally:study.close()


def render(report):
    lines=['# Predicting the later climb after learning calibration','',
        f"**{report['passed']}/{report['total']} generated fits pass all frozen checks.** "
        +('The tested training/forecast procedure qualifies.' if report['qualified'] else 'The complete procedure does not qualify.'),'',
        'These are twenty-minute generated northern climbing/turning tracks, not aircraft recordings.',
        'Earlier 800 receiver positions determine initialization, working weights, calibration and the gravity anchor.',
        'Later 400 positions score the continuous forecast after it is saved. True initial state and calibration',
        'are not supplied. Both starts, both removal cases and both working error policies remain in the result.','',
        '| Generating candidate | Passed | Converged | Largest later horizontal RMS | Largest later height RMS | Largest later spatial error |',
        '|---|---:|---:|---:|---:|---:|']
    labels=dict(sphere_rotating='Globe + field',sphere_still='Globe, zero field',flat_still='Tested disc')
    for row in report['families']:
        number=lambda k:'Unavailable' if row[k] is None else f"{row[k]:.6g} m"
        lines.append('| '+' | '.join([labels[row['model']],f"{row['passed']}/8",str(row['converged']),
            number('maximum_prediction_horizontal_rms_m'),number('maximum_prediction_height_rms_m'),number('maximum_prediction_spatial_error_m')])+' |')
    lines+=['','Each section requires horizontal and height RMS ≤0.1 m and maximum spatial error ≤0.5 m, plus',
        'numerical convergence and all declared nuisance columns. No failures are replaced by better starts.',
        'These examples have no added random measurement noise. Their error sizes are software results,',
        'not instrument specifications, calibrated uncertainty or evidence selecting an Earth model.','',
        f"The run charges {report['charged']['native_calls']:,} native calls in {report['elapsed_s']/3600:.2f} hours.",
        'The saved-only audit checks every earlier/later boundary, training-derived gravity anchor,',
        'input-hash consistency across starts and policies, physical errors, calibration columns and charges.',
        'Deterministic generated rate arrays are represented by frozen source/environment/recipe and hashes,',
        'rather than repeated large array archives. The audit checks their saved bindings without regenerating',
        'those arrays; exact raw regeneration is a separate reproducibility operation. Original measurements',
        'are not involved or discarded.','',
        'This northern climbing geometry limits the qualification. Seven ESA confirmation groups remain',
        'protected. A revised observed comparison needs its own finite freeze and unchanged accuracy checks.','',
        '[Frozen plan](PLAN.md) · [Known-correction gravity controls](../esa-gravity-controls/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md)']
    if not report['construction_accounting_complete']:lines+=['','Some failed cases lack a sealed construction journal; construction totals are incomplete.']
    return '\n'.join(lines)+'\n'


def publish(root,prefix='data/esa-height-training-controls-20261023',output='docs/esa-height-training-controls'):
    from pathlib import Path
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic,digest,encoded,safe_path
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('height-training publication already sealed')
    report=inspect(root,prefix);package(data,public,render(report),plan='docs/esa-height-training-controls/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    for name,raw in [('verified-report.json',encoded(report)),('reporter.py',Path(__file__).read_bytes())]:
        name='artifacts/publication/'+name;atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,native_calls=0,original_reads=0)
