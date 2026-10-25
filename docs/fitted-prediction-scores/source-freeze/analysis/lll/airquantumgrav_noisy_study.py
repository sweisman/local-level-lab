# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated noisy fitting study using shared libraries and lifecycle."""
from lll.airquantumgrav_inventory import environment
from lll.airquantumgrav_height_training import tasks

SCOPE='generated noisy training/forecast robustness; no original/protected reads or observed starts'


def recipe():
    from lll.airquantumgrav_wide_training_controls import recipe as base
    from lll.airquantumgrav_noisy_inputs import noise_settings
    from lll.ilvis0_prediction_observed import recipe as observed
    result=dict(base(),version='esa-noisy-prediction-v1',noise=noise_settings(),
        accuracy_limits=observed()['accuracy_limits'])
    result.pop('accuracy')
    return result


def construction_limits(r):
    from lll.airquantumgrav_noisy_inputs import construction_limits as before_scoring
    result=before_scoring(r);result['generated_samples']+=r['queries'];return result


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    from lll.ilvis0_wide_training import SOURCES
    return source_closure(root,['analysis/lll/airquantumgrav_noisy_study.py',
        'analysis/lll/airquantumgrav_noisy_report.py','analysis/lll/generated_prediction.py',
        'analysis/tests/test_measurement_noise.py','analysis/tests/test_airquantumgrav_noisy_inputs.py',
        'analysis/tests/test_generated_prediction.py','analysis/tests/test_airquantumgrav_noisy_prediction.py',
        'analysis/tests/test_airquantumgrav_noisy_study.py','analysis/lll/ilvis0_native.c','analysis/lll/ilvis0_tangent.cpp',
        *['analysis/lll/'+name for name in SOURCES],'docs/esa-noisy-prediction/PLAN.md'])


def required_tests():
    return ['test_component_streams_are_reproducible_independent_and_do_not_touch_global_rng',
        'test_white_increment_units_and_nonuniform_intervals_match_independent_draws',
        'test_ou_integration_keeps_state_increment_correlation_and_stationary_variance',
        'test_ou_path_can_continue_without_redrawing_bias_or_resetting_noise_origin',
        'test_receiver_draws_reproduce_independent_cross_axis_and_time_covariance',
        'test_later_noise_and_query_extension_cannot_change_earlier_noisy_material',
        'test_noisy_study_defines_fresh_finite_24_case_scope_without_observed_inputs',
        'test_noisy_study_requires_qualification_before_creating_inputs',
        'test_noisy_study_requires_guarded_thread_environment_before_parent_or_inputs',
        'test_noisy_report_rejects_open_study_before_numerical_imports',
        'test_noisy_report_render_distinguishes_generated_robustness_from_archive_confidence',
        'test_generated_prediction_rejects_a_provider_that_does_not_save_forecast_before_scoring']+[
        f'test_noisy_native_pipeline_keeps_future_truth_out_of_fit_and_counts_every_call[{policy}-{profile}]'
        for policy in recipe()['policies'] for profile in (False,True)]


def prepare(root,*,qualification,identity='esa-noisy-prediction-20261024'):
    if qualification is None:raise ValueError('source-bound noisy prediction qualification required')
    import re
    from pathlib import Path
    from lll.compute_budget import environment as threads
    from lll.studies.artifacts import atomic,digest,encoded,safe_path
    from lll.studies.qualification import checked
    from lll.studies.closed import ClosedStudy
    from lll.studies.runtime import Definition
    from lll.ilvis0_wide_training import SOURCES,bind
    r=recipe();env=environment()
    if env['numerical_environment']!=threads(workers=4,threads=1):raise ValueError('declared thread environment required')
    root=Path(root).resolve()
    if not isinstance(identity,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',identity):raise ValueError('safe fresh identity required')
    base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh noisy study scope required')
    sources=qualification_sources(root);request,tests=checked(root,qualification,sources=sources,
        environment=env,required_tests=required_tests(),minimum_tests=41)
    parent=ClosedStudy(root,'docs/esa-wide-training-controls')
    try:
        receipt=parent.read('evidence-receipt.json');key='artifacts/publication/verified-report.json'
        report=parent.read(key,receipt['artifacts'][key])
        if not report['verified'] or not report['qualified'] or report['passed']!=24:
            raise ValueError('all 24 noiseless wider controls must qualify first')
        for name in set(sources)&parent.manifest['sources'].keys():
            if digest((root/name).read_bytes())!=parent.manifest['sources'][name]:
                raise ValueError('qualified shared dependency changed: '+name)
        proof=dict(manifest_sha256=parent.completion['manifest_sha256'],summary_sha256=parent.completion['summary_sha256'],
            report_sha256=receipt['artifacts'][key])
    finally:parent.close()
    _,_,protocol=bind(expected_sources={n:digest((root/'analysis/lll'/n).read_bytes()) for n in SOURCES})
    materials={'recipe':encoded(r),'qualification-environment':encoded(env),'qualification-request':request,
        'qualification-report':tests,'qualified-parent':encoded(proof),'protocol-binding':encoded(protocol)}
    base.mkdir(parents=True);inputs={}
    for i,(key,raw) in enumerate(materials.items()):
        path=base/f'input-{i:03d}';atomic(path,raw);inputs[key]=str(path.relative_to(root))
    value=dict(id=identity,scope=SCOPE,adapter='analysis/lll/airquantumgrav_noisy_study.py',sources=sources,inputs=inputs,
        tasks=tasks(),workers=4,threads=1,maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json',encoded(value));manifest=Definition.from_dict(value,root).prepare(root)
    return dict(path='data/'+identity,allocation=manifest['allocation'],limits=manifest['limits'])


def evaluate(task,context):
    import json
    from lll.airquantumgrav_noisy_inputs import construct
    from lll.generated_prediction import calculate
    from lll.airquantumgrav_training_controls import _spec
    from lll.airquantumgrav_observation_truth import receiver_samples
    from lll.ilvis0_wide_training import SOURCES,bind
    from lll.ilvis0_wide_tangent import load
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.artifacts import digest
    from lll.studies.journal import Journal
    read=lambda key:json.loads(context.input_path(key).read_bytes());r=recipe()
    if (read('recipe')!=r or read('qualification-environment')!=environment() or context.manifest['scope']!=SCOPE
            or {t['identity']:t for t in tasks()}.get(task['identity'])
                !={k:v for k,v in task.items() if k not in ('index','shard')}):
        raise ValueError('unchanged qualified noisy scope required')
    run,_,protocol=bind(expected_sources={n:context.manifest['sources']['analysis/lll/'+n] for n in SOURCES})
    if protocol!=read('protocol-binding'):raise ValueError('qualified fitting protocol differs')
    context.save('protocol-binding.json',protocol);limits=construction_limits(r)
    journal=Journal(context.directory/'construction.sqlite',freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={task['identity']:limits});journal.start(task['identity'])
    try:
        def check():_check_continue(context.root,context.manifest)
        def reserve(**work):
            check()
            for key,value in work.items():journal.reserve(task['identity'],key,value)
        material=construct(task['payload'],r,reserve=reserve)
        directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';env=environment()
        def factory(anchor):
            value,vm=load_kernel(directory,gravity_anchor_height_m=anchor)
            tangent,tm=load(directory,gravity_anchor_height_m=anchor,
                expected_source_sha256=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp'])
            if vm['source_sha256']!=context.manifest['sources']['analysis/lll/ilvis0_native.c'] or vm['compiler']!=env['compilers']['cc'] or tm['compiler']!=env['compilers']['c++']:
                raise ValueError('frozen source and compilers required')
            return value,tangent,dict(value=vm,tangent=dict(tm,gravity_model='inverse-square-height-v1'))
        arguments,sign=_spec({k:v for k,v in task['payload'].items() if k!='policy_id'})
        def truth(times):
            return receiver_samples(times=times,sign=sign,**arguments,height_profile='climb',gravity_model='inverse_square_height')
        result=calculate(task['payload'],r,material=material,train_and_forecast=run,kernel_factory=factory,
            reserve=context.charge,reserve_construction=reserve,save=context.save,truth=truth,check_continue=check)
        journal.verify()
        if any(journal.count(task['identity'],key)!=value for key,value in limits.items()):raise ValueError('construction charges differ')
        return dict(result,constructed_intervals=limits['constructed_intervals'],generated_samples=limits['generated_samples'],
            noise_normal_variates=limits['noise_normal_variates'])
    finally:context.note_file(journal.path)
