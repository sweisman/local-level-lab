# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite known-calibration benchmark using shared construction and lifecycle."""
import json
from pathlib import Path

SCOPE='generated known-calibration conditional noise benchmark; no fitting or original/protected reads'


def recipe():
    return dict(version='known-calibration-noise-benchmark-v1',durations_s=[120.,1200.],
        laws=['increment','point'],workers=2,threads=1,maximum_wall_s=7200.,maximum_operator_bytes=64*1024**2,
        accuracy_limits=dict(horizontal_rms_m=10.,vertical_rms_m=30.),optimizer_starts=0,random_draws=0)


def limits(payload):
    duration=payload.get('duration_s');law=payload.get('law')
    if set(payload)!=set(('law','duration_s')) or law not in recipe()['laws'] or duration not in recipe()['durations_s']:
        raise ValueError('one fixed benchmark setting required')
    n=round(duration*300);m=119 if duration==120 else 1200
    return dict(native_calls=n+m,packet_visits=n+m,bound_calls=0,bound_steps=0),dict(
        generated_samples=n+1+m,constructed_intervals=n,summary_epochs=m-2*m//3)


def tasks():
    return [dict(identity=f'{law}-{int(duration)}',input_key='recipe',native_kind='tangent',
        payload=dict(law=law,duration_s=duration),limits=limits(dict(law=law,duration_s=duration))[0])
        for duration in recipe()['durations_s'] for law in recipe()['laws']]


def kernel(context):
    from lll.ilvis0_noise_step import load
    from lll.studies.journal import Journal
    from lll.studies.artifacts import digest
    from lll.airquantumgrav_inventory import environment
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels'
    journal=Journal(directory/'builds.sqlite',freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={'worker':dict(builds=1)})
    if not journal.verify()['starts']:journal.start('worker')
    hashes=context.manifest['sources']
    native,metadata=load(directory,expected_source_sha256=hashes['analysis/lll/ilvis0_tangent.cpp'],
        expected_bridge_sha256=hashes['analysis/lll/ilvis0_noise_bridge.cpp'],
        expected_wide_loader_sha256=hashes['analysis/lll/ilvis0_wide_tangent.py'],
        reserve_build=lambda:journal.reserve('worker','builds'))
    if metadata['compiler']!=environment()['compilers']['c++']:raise ValueError('compiler differs from frozen environment')
    journal.verify();context.save('compilation.json',metadata)
    context.save_bytes('worker-build-journal.sqlite',journal.path.read_bytes())
    return native


def evaluate(task,context):
    from lll.studies.artifacts import digest
    from lll.studies.journal import Journal
    from lll.ilvis0_control_shards import _check_continue
    from lll.generated_noise_benchmark import material,build_operator
    from lll.prediction_error_benchmark import summarize
    from lll.airquantumgrav_inventory import environment
    import numpy as np
    expected={v['identity']:v for v in tasks()}
    if ({k:v for k,v in task.items() if k not in ('index','shard')}!=expected.get(task['identity'])
            or context.manifest['scope']!=SCOPE
            or json.loads(context.input_path('recipe').read_bytes())!=recipe()
            or json.loads(context.input_path('qualification-environment').read_bytes())!=environment()):
        raise ValueError('unchanged benchmark identity, recipe and scope required')
    work,construction=limits(task['payload']);identity=task['identity'];budget=None
    journal=Journal(context.directory/'construction.sqlite',freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={identity:construction});journal.start(identity)
    def reserve_construction(**counts):
        _check_continue(context.root,context.manifest)
        for name,value in counts.items():journal.reserve(identity,name,value)
    try:
        native=kernel(context)
        with context.prepay_native(native_calls=work['native_calls'],packet_visits=work['packet_visits']) as budget:
            payload=task['payload'];queries=119 if payload['duration_s']==120 else 1200
            data=material(duration_s=payload['duration_s'],queries=queries,query_start_s=.5,query_step_s=1.,
                reserve=reserve_construction)
            def reserve_native(**counts):
                if set(counts)!=set(('native_calls','packet_steps')) or counts['native_calls']!=1 or counts['packet_steps']!=1:
                    raise ValueError('one complete charged native step required')
                budget.reserve(native_calls=1,packet_visits=1)
            operator,mean,descriptor=build_operator(data,law=payload['law'],kernel=native,
                reserve=reserve_native,maximum_bytes=recipe()['maximum_operator_bytes'])
            cut=data['training_epochs'];reserve_construction(summary_epochs=queries-cut)
            summary=summarize(operator,training_epochs=cut,nominal_position_scales=data['nominal_metric'][cut:],
                accuracy_limits=recipe()['accuracy_limits'])
            error=(mean-data['nominal_receiver'])*data['nominal_metric']
            context.save('error-operator.json',descriptor)
            context.save('benchmark.json',summary)
            context.save('nominal-context.json',dict(times_s=data['times'].tolist(),
                receiver_coordinates=data['nominal_receiver'].tolist(),integrated_coordinates=mean.tolist(),
                nominal_metric=data['nominal_metric'].tolist(),mean_nominal_errors_neu_m=error.tolist(),
                oracle_nominal_future_geometry_used=True,initial_state_is_known=True,calibration_is_known=True))
        journal.verify()
        if any(journal.count(identity,key)!=value for key,value in construction.items()):
            raise ValueError('benchmark construction or summary work differs from its frozen allowance')
        return dict(passed=True,**task['payload'],queries=queries,training_epochs=cut,prediction_epochs=queries-cut,
            native_calls_attempted=budget.snapshot()['attempted']['native_calls'],
            sqrt_expected_horizontal_squared_rms_m=summary['sqrt_expected_horizontal_squared_rms_m'],
            sqrt_expected_vertical_squared_rms_m=summary['sqrt_expected_vertical_squared_rms_m'],
            mean_nominal_maximum_3d_error_m=float(np.max(np.linalg.norm(error,axis=1))),
            known_calibration_benchmark=True,oracle_nominal_future_geometry_used=True,
            descriptive_second_moment_exceeds_screen=summary['descriptive_second_moment_exceeds_screen'],
            prediction_qualified=False,confidence_calibrated=False,optimizer_starts=0,random_draws=0,
            original_reads=0,protected_reads=0,scientific_decision='abstain')
    finally:
        if budget is not None:context.save('native-prepayment.json',budget.snapshot())
        context.note_file(journal.path)


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/noise_benchmark_study.py','analysis/tests/test_noise_benchmark_study.py',
        'analysis/tests/test_generated_noise_benchmark.py','analysis/tests/test_prediction_error_benchmark.py',
        'analysis/lll/studies/qualification.py','docs/noisy-prediction-benchmark/EXECUTION_PLAN.md',
        'analysis/lll/ilvis0_tangent.cpp','analysis/lll/ilvis0_noise_bridge.cpp','analysis/lll/ilvis0_wide_tangent.py'])


def prepare(root,*,qualification,parent_qualification,identity='known-calibration-noise-benchmark-20261025'):
    if qualification is None or parent_qualification is None:raise ValueError('both passing qualifications required')
    import re
    if not isinstance(identity,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',identity):
        raise ValueError('safe fresh benchmark identity required')
    from lll.studies.artifacts import atomic,encoded,safe_path
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    from lll.airquantumgrav_inventory import environment
    from lll.compute_budget import environment as threads
    root=Path(root).resolve();env=environment()
    if env['numerical_environment']!=threads(workers=1,threads=1):raise ValueError('declared per-worker environment required')
    sources=qualification_sources(root)
    own,own_report=checked(root,qualification,sources=sources,environment=env,minimum_tests=14,
        required_tests=['test_noise_benchmark_matrix_and_allowances_are_finite_and_observation_free',
            'test_noise_benchmark_keeps_full_prepayment_after_construction_failure',
            'test_noise_benchmark_adapter_executes_through_frozen_loader'])
    parent=json.loads(safe_path(root,parent_qualification).read_bytes())
    critical={'analysis/lll/generated_noise_benchmark.py','analysis/lll/prediction_error_benchmark.py',
        'analysis/tests/test_native_prediction_benchmark.py','analysis/lll/ilvis0_noise_step.py'}
    if not critical<=set(parent['sources']):raise ValueError('native construction source bindings missing')
    parent_raw,parent_report=checked(root,parent_qualification,sources=sorted(parent['sources']),environment=env,
        minimum_tests=27,required_tests=['test_native_known_calibration_noise_benchmark[True-False-0-increment-training_kernels0]',
            'test_native_known_calibration_noise_benchmark[True-False-0-point-training_kernels0]'])
    base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh finite benchmark required')
    values={'recipe':encoded(recipe()),'qualification-request':own,'qualification-report':own_report,
        'qualification-environment':encoded(env),'native-parent-request':parent_raw,'native-parent-report':parent_report}
    base.mkdir(parents=True);inputs={}
    for i,(key,raw) in enumerate(values.items()):
        path=base/f'input-{i:03d}';atomic(path,raw);inputs[key]=str(path.relative_to(root))
    value=dict(id=identity,scope=SCOPE,adapter='analysis/lll/noise_benchmark_study.py',
        sources=sorted(set(sources)|set(parent['sources'])),inputs=inputs,tasks=tasks(),
        workers=recipe()['workers'],threads=recipe()['threads'],maximum_wall_s=recipe()['maximum_wall_s'])
    atomic(base/'definition.json',encoded(value));manifest=Definition.from_dict(value,root).prepare(root)
    return dict(path='data/'+identity,allocation=manifest['allocation'],limits=manifest['limits'])
