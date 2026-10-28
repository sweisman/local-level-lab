# SPDX-License-Identifier: AGPL-3.0-or-later
"""New cohorts and qualified mean provider; shared campaign/scoring machinery."""
import json
from pathlib import Path

from lll import prediction_calibration_study as original
from lll.coordinate_optimizer_study import ARITHMETIC

SCOPE='fresh compensated generated prediction calibration and validation; no original/protected inputs'
EXCLUDED_SEEDS=tuple(sorted(set(original.EXCLUDED_SEEDS)|set(original.recipe('calibration')['seeds'])|
    set(original.recipe('validation')['seeds'])))
REQUIRED_SOURCES=original.REQUIRED_SOURCES|frozenset(ARITHMETIC)|{'analysis/lll/compensated_prediction_release.py'}
PLAN='docs/COMPENSATED_CALIBRATION_PLAN.md'
PARENT='docs/compensated-optimizer-qualification'


def recipe(role):
    r=original.recipe(role);first=281474977010656 if role=='calibration' else 281474977110656
    return dict(r,version='compensated-prediction-release-v1',seeds=list(range(first,first+len(r['seeds']))),
        excluded_seeds=list(EXCLUDED_SEEDS),workers=4)


def case_recipe(seed):
    if type(seed) is not int or not any(seed in recipe(role)['seeds'] for role in ('calibration','validation')):
        raise ValueError('one fresh preassigned release seed required')
    return dict(original._configured(seed),workers=4)


def tasks(role,population_sha256):
    return original.family_tasks(role,population_sha256,policy=recipe(role),case_provider=case_recipe)


def population(sources,environment):
    from lll.studies.artifacts import digest,encoded
    if not REQUIRED_SOURCES<=set(sources):raise ValueError('qualified compensated scientific sources required')
    p=original.population(sources,environment);d=p['descriptor'];d['recipe']['workers']=4
    d.update(version='compensated-prediction-population-v1',mean_arithmetic='compensated-coordinate-tangent-v1')
    return dict(sha256=digest(encoded(d)),descriptor=d)


def native_bindings(study):
    from lll.structured_noisy_publication import native_bindings as base
    from lll.ilvis0_coordinate_precision import derive
    from lll.studies.artifacts import digest
    result=base(study);name='analysis/lll/ilvis0_tangent.cpp';sha=study.manifest['sources'][name]
    result['wide_sha256']=digest(derive(study.read('source-freeze/'+name,sha,raw=True),expected_sha256=sha))
    return result


def policy():
    from types import SimpleNamespace
    return SimpleNamespace(recipe=recipe,tasks=tasks,case_recipe=case_recipe,population=population,
        EXCLUDED_SEEDS=EXCLUDED_SEEDS,SCOPE=SCOPE,native_bindings=native_bindings,
        qualification_sources=qualification_sources,plan=PLAN)


def verify_optimizer_gate(report,binding,current,environment):
    if (report.get('complete')!=48 or report.get('selected')!=48 or report.get('failures')
            or report.get('candidate_qualified') is not True or len(report.get('rows',[]))!=48
            or not all(r['passed'] for r in report['rows']) or len(report.get('pairs',[]))!=24
            or not all(p['passed'] for p in report['pairs']) or report.get('original_binding_replays')!=4
            or report.get('original_binding_replays_exact') is not True or binding.get('environment')!=environment
            or not binding.get('sources') or any(current.get(k)!=v for k,v in binding['sources'].items())):
        raise ValueError('complete unchanged optimizer qualification required')


def evaluate(task,context):
    from lll.airquantumgrav_inventory import environment
    from lll.coordinate_optimizer_study import kernels
    verify_optimizer_gate(json.loads(context.input_path('optimizer-gate').read_bytes()),
        json.loads(context.input_path('optimizer-binding').read_bytes()),context.manifest['sources'],environment())
    return original.evaluate(task,context,protocol=policy(),kernel_provider=kernels)


def qualification_sources(root):
    from lll.studies.closed import ClosedStudy
    from lll.studies.dependencies import source_closure
    s=ClosedStudy(root,PARENT)
    try:parents=set(s.manifest['sources'])
    finally:s.close()
    own=['analysis/lll/compensated_prediction_release.py','analysis/tests/test_compensated_prediction_release.py',
        'analysis/tests/test_prediction_calibration_study.py','analysis/tests/test_prediction_calibration_report.py',
        'analysis/tests/test_prediction_family_state.py','analysis/tests/test_structured_noisy_publication.py',PLAN]
    return sorted(parents|set(source_closure(root,own)))


def optimizer_report(root):
    from lll.coordinate_optimizer_report import inspect
    return inspect(root,PARENT)


def prepare(root,*,role,qualification,calibration=None,definition=None):
    if qualification is None:raise ValueError('source-bound fresh release qualification required')
    from lll.studies.artifacts import atomic,encoded,digest
    from lll.studies.closed import ClosedStudy
    from lll.studies.runtime import Definition
    from lll.studies.qualification import checked
    from lll.airquantumgrav_inventory import environment
    from lll.prediction_calibration_report import calibration_handoff,check_handoff
    import sys
    release=sys.modules[__name__] if definition is None else definition
    protocol=release.policy()
    root=Path(root).resolve();r=release.recipe(role)
    identity=release.identity(role) if definition is not None else 'prediction-'+role+'-compensated-20261026'
    if role=='validation' and calibration is None:raise ValueError('closed fresh calibration handoff required')
    directory=root/'data/ilvis0-source-point-development'/f'{identity}-inputs'
    if directory.exists() or (root/'data'/identity).exists():raise ValueError('fresh separate finite phase required')
    names=release.qualification_sources(root);env=environment();current={n:digest((root/n).read_bytes()) for n in names}
    gate=release.optimizer_report(root);parent=ClosedStudy(root,release.PARENT)
    try:
        old=parent.manifest['sources'];before=parent.input('qualification-environment')
        completion=parent.completion
    finally:parent.close()
    allowed={'analysis/lll/prediction_calibration_study.py','analysis/lll/prediction_calibration_report.py',
        'analysis/lll/structured_noisy_publication.py','analysis/tests/test_structured_noisy_publication.py',
        'analysis/lll/coordinate_optimizer_report.py','analysis/tests/test_coordinate_optimizer_report.py'}
    allowed=set(getattr(release,'allowed_parent_updates',allowed))
    updates={k:dict(original_sha256=v,current_sha256=current.get(k)) for k,v in old.items() if current.get(k)!=v}
    if not set(updates)<=allowed:raise ValueError('qualified parent scientific source changed')
    binding=dict(environment=before,sources={k:v for k,v in old.items() if k not in allowed},completion=completion)
    release.verify_optimizer_gate(gate,binding,current,env)
    required=['test_compensated_population_binds_mean_provider_without_changing_noise_or_physics',
        'test_compensated_handoff_requires_its_own_cohort_and_validation_policy',
        'test_compensated_validation_requires_calibration_before_preparation',
        'test_compensated_frozen_worker_uses_shared_executor_and_qualified_provider',
        'test_compensated_partial_report_uses_new_cohort_and_cannot_supply_handoff',
        'test_compensated_publication_uses_its_qualified_sources_plan_and_protocol',
        'test_original_calibration_defaults_match_frozen_reference_exactly',
        'test_modern_tangent_cache_entries_use_metadata_paths',
        'test_calibration_worker_retains_failed_fit_using_shared_case_runner',
        'test_calibration_worker_preserves_exception_without_retry',
        'test_handoff_rejects_unexecuted_calibration_draws',
        'test_futility_stops_cooperatively_after_both_starts_fail',
        'test_validation_futility_stops_at_fifth_distinct_family_not_four']
    required += [f'test_compensated_short_protocol[{int(p)}-{m}-{law}]'
        for p in (False,True) for m in (0,1,2) for law in ('increment','point')]
    required=getattr(release,'required_tests',required)
    request,tests=checked(root,qualification,sources=names,environment=env,minimum_tests=60,required_tests=required)
    pop=release.population(current,env);handoff=None
    if role=='validation':
        if calibration is None:raise ValueError('closed fresh calibration handoff required')
        handoff=calibration_handoff(root,calibration,protocol=protocol)
        check_handoff(handoff,population_sha256=pop['sha256'],protocol=protocol)
    values=dict(recipe=encoded(r),population=encoded(pop),**{'validation-policy':encoded(release.recipe('validation')),
        'qualification-environment':encoded(env),'qualification-request':request,'qualification-report':tests,
        'optimizer-gate':encoded(gate),'optimizer-binding':encoded(binding),'parent-source-updates':encoded(updates)})
    if handoff is not None:values['calibration-handoff']=encoded(handoff)
    directory.mkdir(parents=True);inputs={}
    for i,(key,raw) in enumerate(values.items()):
        path=directory/f'input-{i:03d}';atomic(path,raw);inputs[key]=str(path.relative_to(root))
    definition=dict(id=identity,scope=release.SCOPE,adapter=release.ADAPTER if definition is not None else 'analysis/lll/compensated_prediction_release.py',sources=names,
        inputs=inputs,tasks=release.tasks(role,pop['sha256']),workers=r['workers'],threads=r['threads'],maximum_wall_s=r['maximum_wall_s'])
    atomic(directory/'definition.json',encoded(definition));m=Definition.from_dict(definition,root).prepare(root)
    if m['sources']!=current:raise ValueError('prepared execution sources differ from the qualified population')
    return dict(path='data/'+identity,population_sha256=pop['sha256'],allocation=m['allocation'],limits=m['limits'])
