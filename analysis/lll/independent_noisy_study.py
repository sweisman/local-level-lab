# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fresh-draw generated diagnostic, using the existing shared case runner."""
import json
from pathlib import Path

SCOPE='fresh generated full-pipeline diagnostic; no confidence calibration or original/protected inputs'
SCORE_INPUTS=('input-binding.json','fit.json','forecast.json','forecast-error-diagnostic.json','scoring-observations.json')


def recipe():
    return dict(version='independent-noisy-training-pilot-v1',seeds=[26102610,26102611],qualification_seed=26102602,
        role='method_diagnostic_pilot',workers=2,threads=1,maximum_wall_s=14400.,maximum_evaluations=200,
        source_policy='existing declared noise laws with fresh seeds; unchanged physical bounds and accuracy screens')


def case_recipe(seed):
    from lll.structured_noisy_training import recipe as base
    from lll.airquantumgrav_noisy_inputs import noise_settings,rate_point_noise_settings
    r=recipe()
    if type(seed) is not int or seed not in [r['qualification_seed'],*r['seeds']]:raise ValueError('one predeclared diagnostic seed required')
    return dict(base(),noise_by_law=dict(increment=noise_settings(seed=seed),point=rate_point_noise_settings(seed=seed)),
        workers=r['workers'],threads=r['threads'],maximum_wall_s=r['maximum_wall_s'])


def tasks():
    from lll.structured_noisy_training import tasks as cases
    return [dict(identity=f"seed-{seed}-{case['identity']}",input_key='recipe',native_kind='tangent',
        payload=dict(draw_seed=seed,role=recipe()['role'],case=case['payload']),limits=case['limits'])
        for seed in recipe()['seeds'] for case in cases(case_recipe(seed))]


def score_records(saved,*,seed):
    from lll.prediction_scores import coordinate_score
    try:
        binding=saved['input-binding.json'];fit=saved['fit.json'];forecast=saved['forecast.json']
        diag=saved['forecast-error-diagnostic.json'];fixed=diag['fixed_parameters'];cut=forecast['training_epochs']
        answer=saved['scoring-observations.json'];count=forecast['prediction_epochs'];error=diag['error_operator']
        if (binding['noise']['settings']['seed']!=seed or binding['training_epochs']!=cut
                or fit['normalized_parameters']!=forecast['normalized_parameters']
                or fit['active_parameters']!=forecast['active_parameters'] or len(fit['active_parameters']) not in (26,27)
                or forecast['prediction_receiver_positions_used'] or diag['later_observations_used']
                or diag['prediction_target']!='physical_position' or diag['raw_coordinates']!=forecast['coordinates']
                or error['later_receiver_fields_used'] or error['weights_depend_on_fitted_residuals']
                or fixed['conditioning_epochs']!=cut or fixed['forecast_epochs']!=count
                or fixed['later_observations_used'] or fixed['parameter_uncertainty_included']
                or type(count) is not int or not 1<=count<=40 or len(fixed['mean'])!=count
                or len(fixed['covariance'])!=count or len(answer['coordinates'])!=cut+count):
            raise ValueError('saved seed, fitted point, chronological split or physical target differs')
        return coordinate_score(fixed['mean'],answer['coordinates'][cut:],fixed['covariance'],maximum_epochs=40)
    except (KeyError,TypeError) as exc:raise ValueError('complete saved score bindings required') from exc


def score_saved_case(context,*,seed):
    return score_records({name:json.loads((context.directory/name).read_bytes()) for name in SCORE_INPUTS},seed=seed)


def evaluate(task,context):
    from lll.airquantumgrav_inventory import environment
    from lll.structured_noisy_study import run_case
    expected={t['identity']:t for t in tasks()}
    if ({k:v for k,v in task.items() if k not in ('index','shard')}!=expected.get(task['identity'])
            or context.manifest['scope']!=SCOPE or json.loads(context.input_path().read_bytes())!=recipe()
            or json.loads(context.input_path('qualification-environment').read_bytes())!=environment()):
        raise ValueError('unchanged pilot identity, seed role, scope and environment required')
    p=task['payload'];seed=p['draw_seed']
    context.save('draw-identity.json',dict(seed=seed,role=p['role'],case=p['case'],
        calibration_draw=False,validation_draw=False,confidence_calibrated=False))
    result=run_case(task,context,r=case_recipe(seed),payload=p['case'])
    score=score_saved_case(context,seed=seed);context.save('prediction-score.json',score)
    return dict(result,draw_seed=seed,role=p['role'],maximum_standardized_error=score['maximum_standardized_error'],
        confidence_calibrated=False)


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/independent_noisy_study.py','analysis/tests/test_independent_noisy_study.py',
        'analysis/lll/structured_noisy_study.py','analysis/tests/test_structured_noisy_study.py',
        'analysis/lll/prediction_scores.py','analysis/tests/test_prediction_scores.py',
        'analysis/lll/studies/qualification.py','docs/prediction-score-qualification/PIPELINE_PILOT.md'])


def prepare(root,*,qualification,native_qualification,identity='independent-noisy-training-pilot-20261025'):
    if qualification is None or native_qualification is None:raise ValueError('lifecycle and native-composition qualifications required')
    import re
    if not isinstance(identity,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',identity):raise ValueError('safe fresh pilot identity required')
    from lll.studies.artifacts import atomic,encoded,safe_path
    from lll.studies.qualification import checked
    from lll.airquantumgrav_inventory import environment
    from lll.compute_budget import environment as threads
    from lll.studies.runtime import Definition
    root=Path(root).resolve();env=environment()
    if env['numerical_environment']!=threads(workers=1,threads=1):raise ValueError('one-thread worker environment required')
    source=qualification_sources(root)
    own,own_report=checked(root,qualification,sources=source,environment=env,minimum_tests=33,
        required_tests=['test_independent_pilot_has_exact_fresh_seeds_matrix_and_finite_allowance',
            'test_independent_pilot_retains_failed_fits_and_calls_shared_runner',
            'test_independent_adapter_executes_through_frozen_loader',
            'test_shared_case_runner_rejects_expanded_work_before_construction'])
    parent=json.loads(safe_path(root,native_qualification).read_bytes())
    critical={'analysis/tests/test_independent_noisy_protocol.py','analysis/lll/independent_noisy_study.py',
        'analysis/lll/airquantumgrav_noisy_inputs.py','analysis/lll/structured_noisy_study.py','analysis/lll/prediction_scores.py'}
    if not critical<=set(parent['sources']):raise ValueError('complete native-composition source bindings required')
    required=[f'test_independent_short_native_protocol_and_score[True-{p}-{m}-{law}-independent-noisy-v1]'
        for p in (False,True) for m in (0,1,2) for law in ('increment','point')]
    native,native_report=checked(root,native_qualification,sources=sorted(parent['sources']),environment=env,
        minimum_tests=42,required_tests=required+['test_original_seed_is_bitwise_compatible_with_frozen_generator[increment]',
            'test_original_seed_is_bitwise_compatible_with_frozen_generator[point]'])
    directory=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if directory.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh finite diagnostic required')
    directory.mkdir(parents=True);inputs={}
    for i,(key,raw) in enumerate(dict(recipe=encoded(recipe()),**{'qualification-environment':encoded(env),
            'qualification-request':own,'qualification-report':own_report,
            'native-qualification-request':native,'native-qualification-report':native_report}).items()):
        path=directory/f'input-{i:03d}';atomic(path,raw);inputs[key]=str(path.relative_to(root))
    r=recipe();value=dict(id=identity,scope=SCOPE,adapter='analysis/lll/independent_noisy_study.py',
        sources=sorted(set(source)|set(parent['sources'])),inputs=inputs,tasks=tasks(),workers=r['workers'],threads=r['threads'],
        maximum_wall_s=r['maximum_wall_s'])
    atomic(directory/'definition.json',encoded(value));m=Definition.from_dict(value,root).prepare(root)
    return dict(path='data/'+identity,allocation=m['allocation'],limits=m['limits'])
