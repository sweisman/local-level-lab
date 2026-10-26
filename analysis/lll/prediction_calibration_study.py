# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed generated population and separate prediction-calibration cohorts.

Preparation/execution must qualify before these definitions can launch work.
No population descriptor alone authorizes fitting or establishes coverage.
"""
import json
from pathlib import Path
import re

SCOPE='generated prediction calibration and independent validation; no original or protected inputs'
REQUIRED_SOURCES=frozenset(('analysis/lll/prediction_calibration_study.py',
    'analysis/lll/structured_noisy_training.py','analysis/lll/airquantumgrav_noisy_inputs.py',
    'analysis/lll/airquantumgrav_observation_truth.py','analysis/lll/ilvis0_tangent.cpp',
    'analysis/lll/prediction_scores.py','analysis/lll/prediction_calibration.py'))
EXCLUDED_SEEDS=(26062413,*range(26102500,26102516),26102600,26102601,26102602,26102610,26102611)
NATIVE_QUALIFICATION='data/ilvis0-source-point-development/independent-noisy-native-20261025-request.json'
AUDIT_QUALIFICATION='data/ilvis0-source-point-development/independent-noisy-report-20261025-request.json'


def recipe(role):
    if role=='calibration':first,count,hours,coverage,failures=281474976810656,299,120,.99,None
    elif role=='validation':first,count,hours,coverage,failures=281474976910656,181,72,.95,4
    else:raise ValueError('separate calibration or validation phase required')
    return dict(version='prediction-calibration-phase-v1',role=role,seeds=list(range(first,first+count)),
        excluded_seeds=list(EXCLUDED_SEEDS),coverage=coverage,confidence=.95,allowed_failures=failures,
        workers=2,threads=1,maximum_wall_s=hours*3600,maximum_evaluations=200,retries=0,
        order_statistic_rank=count if role=='calibration' else None)


def _configured(seed):
    from lll.structured_noisy_training import recipe as base
    from lll.airquantumgrav_noisy_inputs import noise_settings,rate_point_noise_settings
    return dict(base(),workers=2,noise_by_law=dict(increment=noise_settings(seed=seed),
        point=rate_point_noise_settings(seed=seed)))


def case_recipe(seed):
    if type(seed) is not int or not any(seed in recipe(role)['seeds'] for role in ('calibration','validation')):
        raise ValueError('one preassigned calibration/validation seed required')
    return _configured(seed)


def _population_hash(value):
    if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{64}',value):
        raise ValueError('frozen population SHA-256 required')


def tasks(role,population_sha256):
    from lll.structured_noisy_training import tasks as cases
    _population_hash(population_sha256)
    return [dict(identity=f"{role}-seed-{seed}-{v['identity']}",input_key='recipe',native_kind='tangent',
        payload=dict(draw_seed=seed,role=role,population_sha256=population_sha256,case=v['payload']),limits=v['limits'])
        for seed in recipe(role)['seeds'] for v in cases(case_recipe(seed))]


def population(sources,environment):
    """Bind an explicitly verified source map and environment to one population."""
    from lll.studies.artifacts import digest,encoded
    if not isinstance(sources,dict) or not REQUIRED_SOURCES<=set(sources) or not isinstance(environment,dict) or not environment:
        raise ValueError('complete scientific source hashes and explicit environment required')
    for value in sources.values():_population_hash(value)
    r=_configured(0)
    r['noise_by_law']={law:{k:v for k,v in settings.items() if k!='seed'} for law,settings in r['noise_by_law'].items()}
    descriptor=dict(version='prediction-score-population-v1',recipe=r,sources=dict(sorted(sources.items())),
        environment=environment,truth_calibration='fixed +/- fixtures in airquantumgrav_observation_truth._parameters',
        scope='fixed generated calibration fixtures; no uniform parameter-domain or aircraft coverage')
    return dict(sha256=digest(encoded(descriptor)),descriptor=descriptor)


def _context(task,context):
    from lll.airquantumgrav_inventory import environment
    from lll.studies.source_binding import verify
    r=json.loads(context.input_path().read_bytes());role=r.get('role')
    if r!=recipe(role) or context.manifest['scope']!=SCOPE:raise ValueError('unchanged finite phase required')
    env=json.loads(context.input_path('qualification-environment').read_bytes())
    pop=json.loads(context.input_path('population').read_bytes());declared=pop['descriptor']['sources']
    if (env!=environment() or context.manifest['sources']!=declared
            or pop!=population(declared,env)):
        raise ValueError('common frozen scientific sources, population and environment required')
    expected={v['identity']:v for v in tasks(role,pop['sha256'])}
    normalized={v['identity']:{k:x for k,x in v.items() if k not in ('index','shard')} for v in context.manifest['tasks']}
    if (normalized!=expected or {k:v for k,v in task.items() if k not in ('index','shard')}!=expected.get(task['identity'])):
        raise ValueError('exact finite phase task matrix required')
    verify(context.root/'source-freeze',declared=declared,manifest=context.manifest['sources'])
    handoff=None
    if role=='validation':
        from lll.prediction_calibration_report import check_handoff
        handoff=json.loads(context.input_path('calibration-handoff').read_bytes())
        check_handoff(handoff,population_sha256=pop['sha256'])
    return r,pop,handoff


def evaluate(task,context):
    from lll.structured_noisy_study import run_case
    from lll.independent_noisy_study import score_saved_case
    from lll.prediction_family_state import record,check
    r,pop,handoff=_context(task,context);p=task['payload'];seed=p['draw_seed']
    context.save('draw-identity.json',dict(seed=seed,role=r['role'],case=p['case'],population_sha256=pop['sha256'],
        calibration_draw=r['role']=='calibration',validation_draw=r['role']=='validation',confidence_calibrated=False))
    threshold=None if handoff is None else handoff['calibration']['threshold']
    try:
        result=run_case(task,context,r=case_recipe(seed),payload=p['case'])
        score=score_saved_case(context,seed=seed);context.save('prediction-score.json',score)
        result=dict(result,draw_seed=seed,role=r['role'],population_sha256=pop['sha256'],
            maximum_standardized_error=score['maximum_standardized_error'],confidence_calibrated=False)
        record(context,task,result);check(context,task,policy=r,threshold=threshold)
        return result
    except Exception:
        if not (context.directory/'family-outcome.json').exists():
            record(context,task,{});check(context,task,policy=r,threshold=threshold)
        raise


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    from lll.studies.source_binding import ENGINE_FILES
    from lll.studies.artifacts import safe_path
    references=[json.loads(safe_path(root,name).read_bytes()) for name in (NATIVE_QUALIFICATION,AUDIT_QUALIFICATION)]
    names=['analysis/lll/prediction_calibration_study.py','analysis/tests/test_prediction_calibration_study.py',
        'analysis/lll/prediction_family_state.py','analysis/tests/test_prediction_family_state.py',
        'analysis/lll/prediction_calibration_report.py','analysis/tests/test_prediction_calibration_report.py',
        'analysis/lll/prediction_calibration.py','analysis/tests/test_prediction_calibration.py',
        'docs/prediction-score-qualification/EXECUTION_PLAN.md','analysis/lll/studies/qualification.py']
    shared=[str(p.relative_to(root)) for p in (Path(root)/'analysis/lll/studies').glob('*.py')]
    parents=set().union(*(set(value['sources']) for value in references))
    return sorted(set(source_closure(root,names))|parents|set(shared)|set(ENGINE_FILES))


def prepare(root,*,role,qualification,native_qualification,calibration=None,identity=None):
    if qualification is None or native_qualification is None:raise ValueError('phase and existing native qualifications required')
    from lll.studies.artifacts import atomic,encoded,digest,safe_path
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    from lll.airquantumgrav_inventory import environment
    from lll.compute_budget import environment as threads
    root=Path(root).resolve();r=recipe(role);env=environment();identity=identity or 'prediction-'+role+'-20261025'
    if not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',identity):raise ValueError('safe fresh phase identity required')
    if env['numerical_environment']!=threads(workers=1,threads=1):raise ValueError('one-thread worker environment required')
    if native_qualification!=NATIVE_QUALIFICATION:raise ValueError('explicit previously qualified native reference required')
    source=qualification_sources(root)
    own,own_tests=checked(root,qualification,sources=source,environment=env,minimum_tests=62,
        required_tests=['test_calibration_adapter_metadata_loads_in_real_frozen_namespace',
            'test_calibration_worker_rejects_changed_frozen_source_before_work',
            'test_validation_worker_requires_handoff_before_work',
            'test_futility_stops_cooperatively_after_both_starts_fail',
            'test_validation_futility_stops_at_fifth_distinct_family_not_four',
            'test_handoff_rejects_unexecuted_calibration_draws',
            'test_validation_target_can_be_distinct_from_conservative_calibration'])
    parent=json.loads(safe_path(root,native_qualification).read_bytes())
    required=[f'test_independent_short_native_protocol_and_score[True-{p}-{m}-{law}-independent-noisy-v1]'
        for p in (False,True) for m in (0,1,2) for law in ('increment','point')]
    native,native_tests=checked(root,native_qualification,sources=sorted(parent['sources']),environment=env,
        minimum_tests=42,required_tests=required)
    from lll.studies.closed import ClosedStudy
    reference=json.loads(safe_path(root,AUDIT_QUALIFICATION).read_bytes())
    prior=ClosedStudy(root,'docs/independent-noisy-training-pilot')
    try:audit_env=dict(env,closed_pilot_manifest_sha256=prior.completion['manifest_sha256'])
    finally:prior.close()
    audit,audit_tests=checked(root,AUDIT_QUALIFICATION,sources=sorted(reference['sources']),environment=audit_env,
        minimum_tests=17,required_tests=['test_previous_numeric_replay_after_shared_audit_extraction_is_unchanged',
            'test_closed_pilot_numeric_replay_preserves_all_seeds_and_returned_outcomes'])
    pop=population({name:digest((root/name).read_bytes()) for name in source},env);handoff=None
    if role=='validation':
        from lll.prediction_calibration_report import calibration_handoff,check_handoff
        if calibration is None:raise ValueError('closed calibration reference required before validation preparation')
        handoff=calibration_handoff(root,calibration);check_handoff(handoff,population_sha256=pop['sha256'])
    directory=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if directory.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh separate phase required')
    values={'recipe':encoded(r),'population':encoded(pop),'validation-policy':encoded(recipe('validation')),
        'qualification-environment':encoded(env),'qualification-request':own,'qualification-report':own_tests,
        'native-qualification-request':native,'native-qualification-report':native_tests,
        'audit-qualification-request':audit,'audit-qualification-report':audit_tests}
    if handoff is not None:values['calibration-handoff']=encoded(handoff)
    directory.mkdir(parents=True);inputs={}
    for i,(key,raw) in enumerate(values.items()):
        path=directory/f'input-{i:03d}';atomic(path,raw);inputs[key]=str(path.relative_to(root))
    definition=dict(id=identity,scope=SCOPE,adapter='analysis/lll/prediction_calibration_study.py',sources=source,
        inputs=inputs,tasks=tasks(role,pop['sha256']),workers=r['workers'],threads=r['threads'],maximum_wall_s=r['maximum_wall_s'])
    atomic(directory/'definition.json',encoded(definition));m=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+identity,population_sha256=pop['sha256'],allocation=m['allocation'],limits=m['limits'])
