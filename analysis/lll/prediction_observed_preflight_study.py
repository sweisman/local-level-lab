# SPDX-License-Identifier: AGPL-3.0-or-later
"""Four source-bound no-fit error-operator checks on ESA development recording 187."""

from pathlib import Path


IDENTITY = 'prediction-observed-law-preflight-v2-20261113'
SMOKE_ID = IDENTITY + '-smoke'
QUALIFICATION_BASE = 'docs/prediction-observed-law-preflight/qualification-v2/'
SCOPE = ('four no-fit fixed-law operator constructions on prepared ESA '
         'development recording 187; no scoring or protected inputs')
SMOKE_SCOPE = 'one generated short frozen-worker no-fit operator check'
SMOKE_GROUP = 'generated-worker-smoke'
PARENT = 'docs/esa-development-pilot-preparation'
PARENT_TASK = 'prepare-earliest-187-v2'
GROUP_ID = 'esa-99f1530c3eda4318'
NATIVE_PACKETS = 360028
RECEIVER_EPOCHS = 1200
TRAINING_EPOCHS = 800
TRAINING_PREFIX = 239867
TASK_NATIVE_LIMIT = NATIVE_PACKETS + RECEIVER_EPOCHS + TRAINING_PREFIX + TRAINING_EPOCHS
SMOKE_PACKETS = 400
SMOKE_EPOCHS = 9
SMOKE_TRAINING = 6
SMOKE_PREFIX = 222
SMOKE_NATIVE_LIMIT = SMOKE_PACKETS + SMOKE_EPOCHS + SMOKE_TRAINING + SMOKE_PREFIX


def recipe():
    from .airquantumgrav_noisy_inputs import noise_settings, rate_point_noise_settings
    from .airquantumgrav_observed_height import recipe as base
    return dict(base(), version='prediction-observed-law-preflight-v1',
                model='sphere_rotating', profile=False,
                policy_id='reported-short-v1', clock='header_elapsed',
                input_laws=['increment', 'point'],
                noise_by_law=dict(increment=noise_settings(seed=97),
                                  point=rate_point_noise_settings(seed=97)),
                covariance_anchor_policy='normalized-midpoint-v1',
                receiver_transform_policy='last-training-transform-v1',
                maximum_covariance_bytes=64*1024**2,
                maximum_wall_s=14400.)


def tasks(r=None):
    r = recipe() if r is None else r
    if (r != recipe() or TASK_NATIVE_LIMIT != 601895 or
            r['workers'] != 4 or r['threads'] != 1):
        raise ValueError('unchanged finite four-task preflight required')
    limit = dict(native_calls=TASK_NATIVE_LIMIT,
                 packet_visits=TASK_NATIVE_LIMIT,
                 bound_calls=0, bound_steps=0)
    return [dict(identity=f'{law}-{target}', input_key='interval',
                 native_kind='tangent',
                 payload=dict(law=law, target=target), limits=limit)
            for law in r['input_laws']
            for target in ('physical_position', 'receiver_measurement')]


def smoke_recipe():
    return dict(recipe(), version='prediction-observed-law-preflight-smoke-v1',
                duration_s=2., rate_hz=200, queries=9,
                query_start_s=.1, query_step_s=.2,
                maximum_evaluations=8, maximum_wall_s=600.)


def smoke_task():
    return dict(identity='smoke-point-receiver_measurement',
                input_key='interval', native_kind='tangent',
                payload=dict(law='point', target='receiver_measurement'),
                limits=dict(native_calls=SMOKE_NATIVE_LIMIT,
                            packet_visits=SMOKE_NATIVE_LIMIT,
                            bound_calls=0, bound_steps=0))


def qualification_sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/prediction_observed_preflight_study.py',
        'analysis/lll/prediction_observed_material.py',
        'analysis/lll/prediction_observed_native.py',
        'analysis/lll/prediction_observed_preflight.py',
        'analysis/lll/airquantumgrav_noisy_inputs.py',
        'analysis/lll/prediction_paired_law_study.py',
        'analysis/lll/structured_noisy_study.py',
        'analysis/lll/ilvis0_noise_step.py',
        'analysis/lll/ilvis0_wide_tangent.py',
        'analysis/lll/ilvis0_noise_bridge.cpp',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/tests/test_prediction_observed_material.py',
        'analysis/tests/test_prediction_observed_native.py',
        'analysis/tests/test_prediction_observed_preflight.py',
        'analysis/tests/test_prediction_observed_preflight_study.py',
        'docs/prediction-observed-law-preflight/PLAN.md'])


def required_tests():
    return [
        'test_observed_material_binds_complete_imu_and_earlier_receiver_only',
        'test_observed_material_rejects_changed_imu_split_or_training_rows',
        'test_observed_material_rejects_scoring_fields_at_its_input_boundary',
        'test_observed_native_opens_later_receiver_only_after_both_unions',
        'test_observed_preflight_constructs_target_without_later_receiver[physical_position]',
        'test_observed_preflight_constructs_target_without_later_receiver[receiver_measurement]',
        'test_observed_preflight_rejects_changed_law_before_work',
        'test_observed_preflight_has_four_finite_target_law_tasks',
        'test_observed_preflight_requires_qualification_before_archive_reads',
        'test_observed_preflight_source_freeze_includes_adapter_and_plan',
        'test_observed_preflight_definition_has_no_scoring_artifact',
        'test_observed_preflight_rejects_changed_task_before_input_read',
        'test_observed_preflight_smoke_is_short_finite_and_has_no_scoring',
        'test_observed_preflight_launch_checks_disk_before_worker_start',
        'test_observed_preflight_cli_passes_relative_qualification_paths',
        'test_observed_preflight_parent_hashes_map_source_validation_name']


def recovery_sources(root):
    from .studies import task_resume
    from .studies.task_resume_sourcefix import SOURCE, TEST
    return list(dict.fromkeys((*task_resume.qualification_sources(root),
                               SOURCE, TEST)))


def recovery_required_tests():
    from .studies import task_resume
    from .studies.task_resume_sourcefix import TEST_NAME
    return tuple(dict.fromkeys((*task_resume.REQUIRED_TESTS, TEST_NAME)))


def request_qualification(root, *, recovery=False):
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as thread_environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    root = Path(root).resolve()
    env = environment()
    if not recovery and env['numerical_environment'] != thread_environment(
            workers=4, threads=1):
        raise ValueError('guarded four-thread source qualification request required')
    base = QUALIFICATION_BASE
    return request(root,
                   sources=recovery_sources(root) if recovery
                           else qualification_sources(root),
                   environment=runtime_environment() if recovery else env,
                   output=base+('recovery-request.json' if recovery
                                else 'request.json'),
                   report=base+('recovery-tests.xml' if recovery
                                else 'tests.xml'))


def definition(root, *, inputs):
    if 'scoring' in inputs:
        raise ValueError('withheld scoring artifact cannot enter preflight')
    return dict(id=IDENTITY, scope=SCOPE,
                adapter='analysis/lll/prediction_observed_preflight_study.py',
                sources=qualification_sources(root), inputs=dict(inputs),
                tasks=tasks(), workers=4, threads=1,
                maximum_wall_s=14400.)


def smoke_definition(root, *, inputs):
    if 'scoring' in inputs:
        raise ValueError('smoke has no withheld scoring artifact')
    return dict(id=SMOKE_ID, scope=SMOKE_SCOPE,
                adapter='analysis/lll/prediction_observed_preflight_study.py',
                sources=qualification_sources(root), inputs=dict(inputs),
                tasks=[smoke_task()], workers=1, threads=1,
                maximum_wall_s=600.)


def parent_hashes_match(manifest_inputs, bound_hashes):
    names = ('interval', 'training', 'context', 'source-validation')
    return all(manifest_inputs.get(name, {}).get('sha256') ==
               bound_hashes.get(name.replace('-', '_'))
               for name in names)


def prepare_smoke(root):
    import gzip
    import io
    import numpy as np
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_noisy_inputs import construct
    from .compute_budget import environment as thread_environment
    from .prediction_observed_material import bind
    from .prediction_paired_law_study import recipe as generator_recipe
    from .studies.artifacts import atomic, digest, encoded, safe_path
    from .studies.runtime import Definition

    root = Path(root).resolve()
    env = environment()
    if env['numerical_environment'] != thread_environment(workers=1, threads=1):
        raise ValueError('guarded one-thread smoke environment required')
    base = safe_path(root, 'data/'+SMOKE_ID+'-inputs')
    if base.exists() or safe_path(root, 'data/'+SMOKE_ID).exists():
        raise ValueError('fresh short smoke allowance required')
    r = smoke_recipe()
    generation = dict(generator_recipe(), duration_s=2., rate_hz=200,
                      queries=9, query_start_s=.1, query_step_s=.2,
                      maximum_evaluations=8)
    spec = dict(model='sphere_rotating', latitude_deg=55., profile=False,
                start=0, policy_id='reported-short-v1')
    generated = construct(spec, dict(generation,
                          noise=generation['noise_by_law']['increment'],
                          sensor_case='interior'), reserve=lambda **work: None)
    arrays = {name: generated[name] for name in ('theta', 'dv', 'dt')}
    origin = 100.
    training = [dict(row, time_s=row['time_s']+origin)
                for row in generated['training_rows']]
    times = np.array([float(t+origin)-origin for t in generated['times']])
    prefix = int(np.searchsorted(np.cumsum(arrays['dt']),
                                 times[SMOKE_TRAINING-1]+r['limits']['time_offset'],
                                 side='left'))+1
    layout = dict(times_s=times.tolist(), training_epochs=SMOKE_TRAINING,
                  prediction_epochs=SMOKE_EPOCHS-SMOKE_TRAINING,
                  training_prefix_packets=prefix,
                  time_origin_gps_sow_s=origin)
    hashes = {name: digest(np.asarray(value, dtype='<f8').tobytes())
              for name, value in arrays.items()}
    hashes.update(layout=digest(encoded(layout)),
                  training_rows=digest(encoded(training)))
    material = bind(arrays=arrays, layout=layout, training_rows=training,
                    frozen_hashes=hashes, source_id=SMOKE_GROUP,
                    maximum_interval_s=r['maximum_interval_s'],
                    time_offset_bound_s=r['limits']['time_offset'])
    if (len(material['dt']) != SMOKE_PACKETS or
            len(material['times']) != SMOKE_EPOCHS or
            material['binding']['training_prefix_packets'] != SMOKE_PREFIX):
        raise ValueError('generated smoke size differs from finite allowance')
    buffer = io.BytesIO()
    np.savez(buffer, **arrays)
    materials = dict(interval=buffer.getvalue(),
                     training=gzip.compress(encoded(training), mtime=0),
                     layout=encoded(layout), **{'frozen-hashes': encoded(hashes),
                     'context': encoded(dict(group_id=SMOKE_GROUP)),
                     'recipe': encoded(r),
                     'numerical_environment': encoded(env)})
    base.mkdir(parents=True)
    inputs = {}
    for index, (name, value) in enumerate(materials.items()):
        path = base/f'input-{index:03d}'
        atomic(path, value)
        inputs[name] = path.relative_to(root).as_posix()
    frozen = smoke_definition(root, inputs=inputs)
    atomic(base/'definition.json', encoded(frozen))
    manifest = Definition.from_dict(frozen, root).prepare(root)
    return dict(path='data/'+SMOKE_ID, tasks=1,
                allocation=manifest['allocation'])


def prepare(root, *, qualification, recovery_qualification):
    if qualification is None or recovery_qualification is None:
        raise ValueError('source-bound software and recovery qualification required')
    import gzip
    import io
    import json
    import numpy as np
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as thread_environment
    from .prediction_observed_material import bind
    from .studies.artifacts import atomic, digest, encoded, safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .ilvis0_control_shards import runtime_environment, verify_completion

    root = Path(root).resolve()
    env = environment()
    if env['numerical_environment'] != thread_environment(workers=4, threads=1):
        raise ValueError('guarded four-thread preflight environment required')
    request, report = checked(
        root, qualification, sources=qualification_sources(root),
        environment=env, required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    recovery_tests = recovery_required_tests()
    recovery_request, recovery_report = checked(
        root, recovery_qualification, sources=recovery_sources(root),
        environment=runtime_environment(), required_tests=recovery_tests,
        minimum_tests=len(recovery_tests))
    smoke = verify_completion(root/'data'/SMOKE_ID)
    if smoke['state'] != 'complete' or smoke['completed'] != 1 or smoke['passed'] is not True:
        raise ValueError('verified short frozen-worker smoke required')
    smoke_manifest = json.loads((root/'data'/SMOKE_ID/'manifest.json').read_bytes())
    if (smoke_manifest['scope'] != SMOKE_SCOPE or
            any(smoke_manifest['sources'].get(name) != digest((root/name).read_bytes())
                for name in qualification_sources(root))):
        raise ValueError('short worker source differs from qualified source')
    base = safe_path(root, 'data/'+IDENTITY+'-inputs')
    if base.exists() or safe_path(root, 'data/'+IDENTITY).exists():
        raise ValueError('fresh preflight allowance required')
    parent = ClosedStudy(root, PARENT)
    try:
        if parent.completion['state'] != 'complete' or parent.summary['passed'] is not True:
            raise ValueError('verified completed ESA development preparation required')
        raw = dict(
            interval=parent.artifact(PARENT_TASK, 'interval.npz', raw=True),
            training=parent.artifact(PARENT_TASK, 'training-receiver.json.gz', raw=True),
            query=parent.artifact(PARENT_TASK, 'query-layout.json', raw=True),
            context=parent.input('context', raw=True),
            source_validation=parent.artifact(PARENT_TASK,
                                              'source-validation.json', raw=True))
        parent_binding = dict(manifest_sha256=parent.completion['manifest_sha256'],
                              summary_sha256=parent.completion['summary_sha256'],
                              input_sha256={name: digest(value)
                                            for name, value in raw.items()},
                              source_task=PARENT_TASK)
    finally:
        parent.close()
    context = json.loads(raw['context'])
    if context.get('group_id') != GROUP_ID:
        raise ValueError('protected or changed ESA group')
    with np.load(io.BytesIO(raw['interval']), allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in ('theta', 'dv', 'dt')}
    query = json.loads(raw['query'])
    training = json.loads(gzip.decompress(raw['training']))
    r = recipe()
    prefix = int(np.searchsorted(np.cumsum(arrays['dt']),
                                 query['times_s'][TRAINING_EPOCHS-1]
                                 + r['limits']['time_offset'],
                                 side='left')) + 1
    layout = dict(query, training_prefix_packets=prefix)
    hashes = {name: digest(np.asarray(value, dtype='<f8').tobytes())
              for name, value in arrays.items()}
    hashes.update(layout=digest(encoded(layout)),
                  training_rows=digest(encoded(training)))
    material = bind(arrays=arrays, layout=layout, training_rows=training,
                    frozen_hashes=hashes, source_id=GROUP_ID,
                    maximum_interval_s=r['maximum_interval_s'],
                    time_offset_bound_s=r['limits']['time_offset'])
    if (len(material['dt']) != NATIVE_PACKETS or
            len(material['times']) != RECEIVER_EPOCHS or
            material['training_epochs'] != TRAINING_EPOCHS or
            prefix != TRAINING_PREFIX):
        raise ValueError('ESA development interval differs from frozen plan')
    materials = dict(interval=raw['interval'], training=raw['training'],
                     layout=encoded(layout),
                     **{'frozen-hashes': encoded(hashes),
                        'context': raw['context'],
                        'source-validation': raw['source_validation'],
                        'recipe': encoded(r),
                        'numerical_environment': encoded(env),
                        'parent-binding': encoded(parent_binding),
                        'qualification-request': request,
                        'qualification-report': report,
                        'recovery-request': recovery_request,
                        'recovery-report': recovery_report})
    base.mkdir(parents=True)
    inputs = {}
    for index, (name, value) in enumerate(materials.items()):
        path = base/f'input-{index:03d}'
        atomic(path, value)
        inputs[name] = path.relative_to(root).as_posix()
    frozen = definition(root, inputs=inputs)
    atomic(base/'definition.json', encoded(frozen))
    manifest = Definition.from_dict(frozen, root).prepare(root)
    return dict(path='data/'+IDENTITY, tasks=len(tasks()),
                allocation=manifest['allocation'])


def evaluate(task, context):
    scope = context.manifest.get('scope')
    smoke = scope == SMOKE_SCOPE
    expected = {smoke_task()['identity']: smoke_task()} if smoke else {
        row['identity']: row for row in tasks()}
    if (scope not in (SCOPE, SMOKE_SCOPE) or
            {key: value for key, value in task.items()
             if key not in ('index', 'shard')} != expected.get(task.get('identity'))):
        raise ValueError('unchanged frozen preflight task and scope required')
    import gzip
    import json
    import numpy as np
    from .airquantumgrav_inventory import environment
    from .ilvis0_control_shards import _check_continue
    from .prediction_observed_material import bind
    from .prediction_observed_preflight import construct_operator
    from .structured_noisy_study import _kernels

    read = lambda name: json.loads(context.input_path(name).read_bytes())
    r = smoke_recipe() if smoke else recipe()
    env = environment()
    if (read('recipe') != r or read('numerical_environment') != env or
            'scoring' in context.manifest['inputs']):
        raise ValueError('changed source-bound preflight inputs or environment')
    if not smoke:
        parent = read('parent-binding')
        if parent.get('source_task') != PARENT_TASK:
            raise ValueError('changed prepared ESA parent identity')
        if not parent_hashes_match(context.manifest['inputs'],
                                   parent['input_sha256']):
            raise ValueError('prepared ESA source input hash changed')
    source_id = SMOKE_GROUP if smoke else GROUP_ID
    if read('context').get('group_id') != source_id:
        raise ValueError('changed preflight source group')
    with np.load(context.input_path('interval'), allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in ('theta', 'dv', 'dt')}
    training = json.loads(gzip.decompress(context.input_path('training').read_bytes()))
    material = bind(arrays=arrays, layout=read('layout'),
                    training_rows=training, frozen_hashes=read('frozen-hashes'),
                    source_id=source_id,
                    maximum_interval_s=r['maximum_interval_s'],
                    time_offset_bound_s=r['limits']['time_offset'])
    counts = ((SMOKE_PACKETS, SMOKE_EPOCHS, SMOKE_TRAINING, SMOKE_PREFIX)
              if smoke else
              (NATIVE_PACKETS, RECEIVER_EPOCHS, TRAINING_EPOCHS, TRAINING_PREFIX))
    if (len(material['dt']) != counts[0] or
            len(material['times']) != counts[1] or
            material['training_epochs'] != counts[2] or
            material['binding']['training_prefix_packets'] != counts[3]):
        raise ValueError('prepared real-size interval differs from frozen plan')
    context.save('material-binding.json', material['binding'])
    noise_kernel, kernel_factory = _kernels(context, env)
    kernel, tangent, compilation = kernel_factory(training[0]['height_m'])
    context.save('compilation.json', compilation)
    check = lambda: _check_continue(context.root, context.manifest)
    budget = None
    try:
        with context.prepay_native(
                native_calls=task['limits']['native_calls'],
                packet_visits=task['limits']['packet_visits']) as budget:
            result = construct_operator(
                material, recipe=r,
                spec=dict(model=r['model'], profile=r['profile'],
                          policy_id=r['policy_id']),
                law=task['payload']['law'], target=task['payload']['target'],
                kernel=kernel, tangent_kernel=tangent,
                noise_kernel=noise_kernel, reserve=budget.reserve,
                check_continue=check)
        if (result['native_calls'] != budget.snapshot()['attempted']['native_calls']
                or result['native_calls'] > task['limits']['native_calls']
                or result['operator_storage_bytes'] > r['maximum_covariance_bytes']
                or result['scientific_decision'] != 'abstain'):
            raise ValueError('native charges, storage or decision differ from freeze')
        context.save('operator-summary.json', result)
        return dict(result, passed=True, original_reads=0, protected_reads=0,
                    observed_fits=0, scored_epochs=0)
    finally:
        if budget is not None:
            context.save('native-prepayment.json', budget.snapshot())


def launch(root, *, smoke=False):
    import shutil
    from .ilvis0_control_shards import launch as run_study
    root = Path(root).resolve()
    if not smoke and shutil.disk_usage(root).free < 35*1024**3:
        raise ValueError('35 GiB free space required before full-size worker launch')
    return run_study(root/'data'/(SMOKE_ID if smoke else IDENTITY),
                     reserved_threads=0)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'recovery-request',
                                           'prepare-smoke', 'run-smoke',
                                           'prepare', 'run'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if args.action == 'request':
        result = request_qualification(root)
    elif args.action == 'recovery-request':
        result = request_qualification(root, recovery=True)
    elif args.action == 'prepare-smoke':
        result = prepare_smoke(root)
    elif args.action == 'run-smoke':
        result = launch(root, smoke=True)
    elif args.action == 'run':
        result = launch(root)
    else:
        base = QUALIFICATION_BASE
        result = prepare(root, qualification=base+'request.json',
                         recovery_qualification=base+'recovery-request.json')
    print(result)
    return result


if __name__ == '__main__':
    main()
