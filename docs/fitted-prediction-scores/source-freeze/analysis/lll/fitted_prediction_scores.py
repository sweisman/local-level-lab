# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved fitted-prediction scoring, retaining failures and training-only choice."""
import json
from collections import defaultdict
from lll.studies.artifacts import digest,encoded,atomic,safe_path

PARENT='docs/structured-noisy-training'
SCOPE='saved generated fitted-prediction scores; no fitting, new truth, original/protected reads or noise draws'
NAMES=('forecast.json','forecast-error-diagnostic.json','scoring-observations.json','conditional-scores.json')
REFERENCES=('analysis/lll/airquantumgrav_training_report.py','analysis/lll/airquantumgrav_truth.py',
    'analysis/lll/airquantumgrav_geographic_report.py')


def recipe():
    return dict(version='saved-fitted-prediction-scores-v1',maximum_saved_fits=24,maximum_future_epochs=40,
        maximum_bundle_bytes=32*1024**2,maximum_wall_s=300.)


def tasks():
    return [dict(identity='saved-fitted-prediction-scores',input_key='bundle',payload={},native_kind='value',
        limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0))]


def collect(root):
    from lll.structured_noisy_diagnostics import collect as calibration
    from lll.structured_noisy_publication import inspect
    from lll.studies.closed import ClosedStudy
    base=calibration(root)
    if encoded(inspect(root,PARENT))!=encoded(base['parent_report']):raise ValueError('parent audit differs from its sealed report')
    study=ClosedStudy(root,PARENT)
    try:
        bundle=dict(calibration=base,predictions={identity:{name:study.artifact(identity,name) for name in NAMES}
            for identity in study.tasks},references={name:study.read('source-freeze/'+name,
                study.manifest['sources'][name],raw=True).decode() for name in REFERENCES})
    finally:study.close()
    if len(encoded(bundle))>recipe()['maximum_bundle_bytes']:raise ValueError('saved bundle exceeds its allowance')
    calculate(bundle)
    return bundle


def select_primaries(rows):
    from lll.ilvis0_forecast_publication import primary
    groups=defaultdict(list)
    for row in rows:groups[(row['law'],row['model'],row['profile'])].append(row)
    result=[]
    for (law,model,profile),values in sorted(groups.items()):
        if len(values)!=2 or {v['start'] for v in values}!={0,1}:raise ValueError('both declared starts required')
        chosen=primary([dict(v,passed=v['converged']) for v in values])
        result.append(dict(law=law,model=model,profile=profile,selected_identity=None if chosen is None else chosen['identity'],
            selected_start=None if chosen is None else chosen['start'],available=chosen is not None,
            selection='qualified training cost, then declared start order'))
    return result


def calculate(bundle):
    from lll.structured_noisy_diagnostics import calculate as calibration
    from lll.studies.closed import load_python_reference
    from lll.prediction_scores import coordinate_score
    try:
        base=bundle['calibration'];diagnosis=calibration(base);manifest=json.loads(base['manifest'])
        receipt=base['receipt']['artifacts'];parent_rows={r['identity']:r for r in base['parent_report']['rows']}
        expected={v['identity']:v for v in manifest['tasks']}
        if (set(bundle['predictions'])!=set(expected) or len(expected)!=24
                or base['recipe']['queries']!=119 or base['recipe']['duration_s']!=120.):
            raise ValueError('complete declared parent cohort required')
        references=[]
        for name in REFERENCES:
            raw=bundle['references'][name].encode();sha=manifest['sources'][name]
            references.append(load_python_reference(raw,name='lll._fitted_score_reference_'+sha[:16],sha256=sha))
        physical,truth,statistics=references;constants={key:getattr(truth,key) for key in ('A','E2','DISC_RADIUS')}
        rows=[];cut=79
        for identity,task in expected.items():
            records=bundle['predictions'][identity];fit=base['fits'][identity]['fit'];spec=task['payload']
            if set(records)!=set(NAMES):raise ValueError('complete saved prediction artifacts required')
            for name,value in records.items():
                if digest(encoded(value))!=receipt['artifacts/'+identity+'/'+name]:raise ValueError('saved prediction artifact differs')
            forecast=records['forecast.json'];diag=records['forecast-error-diagnostic.json'];fixed=diag['fixed_parameters']
            answer=records['scoring-observations.json'];conditional=records['conditional-scores.json']
            if (forecast['normalized_parameters']!=fit['normalized_parameters'] or forecast['active_parameters']!=fit['active_parameters']
                    or forecast['training_epochs']!=cut or forecast['prediction_epochs']!=40
                    or forecast['prediction_receiver_positions_used'] or diag['later_observations_used']
                    or diag['prediction_target']!='physical_position' or diag['raw_coordinates']!=forecast['coordinates']
                    or fixed['conditioning_epochs']!=cut or fixed['forecast_epochs']!=40
                    or fixed['later_observations_used'] or fixed['parameter_uncertainty_included']
                    or len(fixed['mean'])!=40 or len(fixed['covariance'])!=40 or len(answer['coordinates'])!=119
                    or conditional['parameter_uncertainty_included'] or conditional['confidence_calibrated']):
                raise ValueError('chronological split, fitted point or physical prediction target differs')
            errors=physical.saved_position_errors(forecast['coordinates'][:cut]+fixed['mean'],answer,
                model=spec['model'],constants=constants)
            if any(abs(a-b)>1e-7 for actual,saved in zip(errors,conditional['errors_neu_m'],strict=True)
                    for a,b in zip(actual,saved,strict=True)):raise ValueError('saved conditional physical errors differ')
            measured=statistics.error_metrics(errors[cut:])
            statistics._same_metrics(measured,conditional['prediction'])
            score=coordinate_score(fixed['mean'],answer['coordinates'][cut:],fixed['covariance'],maximum_epochs=40)
            rows.append(dict(identity=identity,**spec,converged=fit['converged'],training_cost=fit['residual_sum_squares'],
                original_numerical_pass=parent_rows[identity]['converged'],score=score,
                conditional_prediction=conditional['prediction'],linear_calibration_status=diag['linear_calibration']['status']))
        primaries=select_primaries(rows)
        return dict(verified=True,version=recipe()['version'],parent=PARENT,total=24,
            manifest_sha256=diagnosis['manifest_sha256'],summary_sha256=diagnosis['summary_sha256'],
            numerically_converged=sum(r['converged'] for r in rows),rows=rows,primaries=primaries,
            available_primaries=sum(r['available'] for r in primaries),shared_seed=diagnosis['shared_seed'],independent_noise_seeds=1,
            quantile_available=False,labels_changed=False,confidence_calibrated=False,scientific_decision='abstain',
            native_calls=0,optimizer_starts=0,noise_draws=0,original_reads=0,protected_reads=0)
    except (KeyError,TypeError,json.JSONDecodeError) as exc:raise ValueError('complete hash-bound saved fitted-score inputs required') from exc


def render(report):
    if report.get('verified') is not True:raise ValueError('verified fitted-score report required')
    by_id={r['identity']:r for r in report['rows']}
    lines=['# Do noise-only allowances describe fitted predictions?','',
        f"**{report['numerically_converged']}/{report['total']} fits passed their original numerical checks.**",'',
        'These generated cases use one shared noise seed. They are not independent replications.',
        'The score divides each later coordinate error by its conditional noise standard deviation',
        'and takes the largest absolute value over the complete later block. Calibration',
        'was estimated, but that noise allowance treats its estimate as known.','',
        'A large score is not a detection or a confidence level. Uncertainty is not calibrated.',
        'The current data cannot estimate a calibration quantile. All failed fits retain their labels.','',
        '| Input format / model / processing | Training-selected start | Maximum error/noise score | Later horizontal RMS | Later height RMS |',
        '|---|---:|---:|---:|---:|']
    for group in report['primaries']:
        label=f"{group['law']} / {group['model']} / {int(group['profile'])}"
        if group['available']:
            r=by_id[group['selected_identity']];p=r['conditional_prediction']
            values=f"{r['start']} | {r['score']['maximum_standardized_error']:.3f} | {p['horizontal_rms_m']:.3f} m | {p['vertical_rms_m']:.3f} m"
        else:values='Unavailable | Unavailable | Unavailable | Unavailable'
        lines.append(f'| {label} | {values} |')
    failures=[r['identity'] for r in report['rows'] if not r['converged']]
    lines+=['','Numerically unfinished starts: '+', '.join(failures)+'.','',
        'Primary starts use qualified training cost and declared start order, never later errors.',
        'Fresh, independent full-pipeline draws are needed before score calibration and validation.',
        'No model labels, physical accuracy screens, aircraft fits or confirmation reservations change.','',
        '[Parent study](../structured-noisy-training/README.md) · [Frozen scoring plan](PLAN.md) ·',
        '[Next analyses](../NEXT_STEPS.md).']
    return '\n'.join(lines)+'\n'


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/fitted_prediction_scores.py','analysis/tests/test_fitted_prediction_scores.py',
        'analysis/lll/prediction_scores.py','analysis/tests/test_prediction_scores.py',
        'docs/prediction-score-qualification/PLAN.md','analysis/lll/studies/qualification.py'])


def prepare(root,*,qualification,identity='saved-fitted-prediction-scores-20261025'):
    if qualification is None:raise ValueError('source-bound saved-score qualification required')
    from pathlib import Path
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    from lll.airquantumgrav_inventory import environment
    from lll.compute_budget import environment as threads
    root=Path(root).resolve();safe_path(root,'data/'+identity);env=environment()
    if env['numerical_environment']!=threads(workers=1,threads=1):raise ValueError('one-thread environment required')
    source=qualification_sources(root)
    request,report=checked(root,qualification,sources=source,environment=env,minimum_tests=25,
        required_tests=['test_prediction_score_uses_entire_block_and_every_coordinate',
            'test_coordinate_score_wraps_longitude_and_preserves_radian_height_covariance_units',
            'test_fitted_primary_ignores_later_score_and_uses_start_order_for_cost_tie',
            'test_fitted_scores_retain_24_starts_four_failures_and_one_shared_seed',
            'test_fitted_score_evaluator_uses_frozen_loader_and_no_native_budget'])
    base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh finite saved-score scope required')
    material=dict(bundle=encoded(collect(root)),recipe=encoded(recipe()),qualification_request=request,
        qualification_report=report,qualification_environment=encoded(env))
    base.mkdir(parents=True);inputs={}
    for index,(key,raw) in enumerate(material.items()):
        path=base/f'input-{index:03d}';atomic(path,raw);inputs[key]=str(path.relative_to(root))
    definition=dict(id=identity,scope=SCOPE,adapter='analysis/lll/fitted_prediction_scores.py',sources=source,
        inputs=inputs,tasks=tasks(),workers=1,threads=1,maximum_wall_s=recipe()['maximum_wall_s'])
    atomic(base/'definition.json',encoded(definition));m=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+identity,allocation=m['allocation'],limits=m['limits'])


def evaluate(task,context):
    if (task['identity']!=tasks()[0]['identity'] or task['payload'] or context.manifest['scope']!=SCOPE
            or json.loads(context.input_path('recipe').read_bytes())!=recipe()):raise ValueError('frozen saved-score scope differs')
    raw=context.input_path('bundle').read_bytes()
    if len(raw)>recipe()['maximum_bundle_bytes']:raise ValueError('saved bundle exceeds allowance')
    report=calculate(json.loads(raw));context.save('scores.json',report)
    return dict(passed=True,native_calls=0,optimizer_starts=0,noise_draws=0,original_reads=0,protected_reads=0,
        saved_starts=24,numerical_passes=report['numerically_converged'],available_primaries=report['available_primaries'],
        confidence_calibrated=False,scientific_decision='abstain')
