# SPDX-License-Identifier: AGPL-3.0-or-later
"""One frozen receiver-only weighting fit on the ESA development interval."""
import json
from pathlib import Path


ID = 'esa-weighting-control-development-v1-20261114'
PARENT = 'data/esa-rate-refit-development-v2-20261114'
SCOPE = 'one ESA development receiver-only wide fit; later receiver values withheld'
INPUT_KEYS = ('interval', 'training', 'recipe', 'saved-input-binding',
              'saved-increment-fit', 'saved-increment-forecast',
              'parent-identity', 'qualification-environment',
              'qualification-request', 'qualification-report')


def accepted_input_keys(candidate=None):
    keys = INPUT_KEYS if candidate is None else tuple(candidate)
    if set(keys) != set(INPUT_KEYS) or len(keys) != len(INPUT_KEYS):
        raise ValueError('exact training-only input set required')
    return keys


def technical_gate(*, converged, forecast_complete):
    return converged is True and forecast_complete is True


def tasks():
    return [dict(identity='linear-points-receiver-only', input_key='interval',
                 native_kind='tangent',
                 payload=dict(model='sphere_rotating', profile=False,
                              policy_id='reported-short-v1', start=0,
                              method='linear_points'),
                 limits=dict(native_calls=201, packet_visits=45_000_000_000,
                             bound_calls=0, bound_steps=0))]


def sources(root):
    from .studies.dependencies import source_closure
    from .esa_rate_refit_study_v2 import sources as parent_sources
    return source_closure(Path(root).resolve(), parent_sources(root) + [
        'analysis/lll/esa_weighting_control_study.py',
        'analysis/lll/ilvis0_wide_training.py',
        'analysis/lll/airquantumgrav_height_training.py',
        'analysis/tests/test_esa_weighting_control_study.py',
        'docs/prediction-observed-development/WEIGHTING_CONTROL_PLAN.md'])


def required_tests():
    return ('test_weighting_control_has_one_fixed_receiver_only_task',
            'test_weighting_control_rejects_scoring_as_worker_input',
            'test_weighting_control_needs_source_bound_qualification',
            'test_weighting_control_preserves_failed_accuracy_as_abstention',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_source_input_environment_mutation_blocks')


def request_qualification(root):
    from .airquantumgrav_inventory import environment
    from .studies.qualification import request
    root = Path(root).resolve()
    return request(root, sources=sources(root), environment=environment(),
                   output='docs/prediction-observed-development/qualification/weighting-control-request.json',
                   report='docs/prediction-observed-development/qualification/weighting-control-tests.xml')


def prepare(root, *, qualification=None):
    if qualification is None:
        raise ValueError('source-bound qualification required before observed preparation')
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    from .studies.artifacts import atomic, encoded, safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition

    root = Path(root).resolve()
    base = safe_path(root, 'data/'+ID+'-inputs')
    if base.exists() or safe_path(root, 'data/'+ID).exists():
        raise ValueError('fresh finite weighting-control identity required')
    env = environment()
    if env['numerical_environment'] != numerical_environment(workers=1, threads=1):
        raise ValueError('guarded one-thread allocation required')
    request, report = checked(root, qualification, sources=sources(root),
                              environment=env, required_tests=required_tests(),
                              minimum_tests=len(required_tests()))
    parent = ClosedStudy(root, PARENT)
    try:
        if (parent.completion['state'] != 'complete' or
                parent.completion['manifest_sha256'] !=
                'fabb0ef004ce452a7a0b0a14ac71c307b350d3b9b4d25ca8bc8545598f75c2ba' or
                parent.completion['summary_sha256'] !=
                '47f01b56eda5710d0698f26a4727b12945abfcaa8f8fe3be50ff5a8df0fc03a7' or
                parent.summary['completed'] != 6 or
                parent.input('saved-input-binding')['source_id'] != 'esa-99f1530c3eda4318'):
            raise ValueError('exact completed development comparator required')
        staged = {key: parent.input(key, raw=True) for key in INPUT_KEYS[:6]}
        parent_identity = encoded(dict(prefix=PARENT,
            manifest_sha256=parent.completion['manifest_sha256'],
            summary_sha256=parent.completion['summary_sha256'],
            comparator='linear_points-increment'))
    finally:
        parent.close()
    staged.update({'parent-identity': parent_identity,
                   'qualification-environment': encoded(env),
                   'qualification-request': request,
                   'qualification-report': report})
    accepted_input_keys(staged)
    base.mkdir(parents=True)
    inputs = {}
    for number, key in enumerate(INPUT_KEYS):
        path = base/f'input-{number:03d}'
        atomic(path, staged[key])
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE,
                      adapter='analysis/lll/esa_weighting_control_study.py',
                      sources=sources(root), inputs=inputs, tasks=tasks(),
                      workers=1, threads=1, maximum_wall_s=14_400.)
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, total=1, allocation=manifest['allocation'])


def evaluate(task, context):
    import gzip
    from .airquantumgrav_inventory import environment
    from .esa_fixed_rate_protocol import material
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_wide_training import SOURCES as WIDE_SOURCES, bind
    from .structured_noisy_study import _kernels

    declared = {k: v for k, v in task.items() if k not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE or declared != tasks()[0] or
            set(context.manifest['inputs']) != set(INPUT_KEYS) or
            json.loads(context.input_path('qualification-environment').read_bytes()) != environment()):
        raise ValueError('unchanged receiver-only task, inputs and environment required')
    read = lambda key: json.loads(context.input_path(key).read_bytes())
    parent = read('parent-identity')
    binding = read('saved-input-binding')
    recipe = read('recipe')
    if (parent['prefix'] != PARENT or parent['manifest_sha256'] !=
            'fabb0ef004ce452a7a0b0a14ac71c307b350d3b9b4d25ca8bc8545598f75c2ba' or
            binding['source_id'] != 'esa-99f1530c3eda4318' or
            binding['later_receiver_positions_read'] is not False or
            recipe['clock'] != 'header_elapsed' or
            recipe['limits']['gyro_gain_z'] != .01):
        raise ValueError('original development interval and model required')
    bound = material(context.input_path('interval').read_bytes(),
                     context.input_path('training').read_bytes(),
                     binding=binding, fit=read('saved-increment-fit'),
                     saved=read('saved-increment-forecast'),
                     recipe=recipe, smoke=False)
    arrays = bound['alternatives']['linear_points']
    rows = json.loads(gzip.decompress(context.input_path('training').read_bytes()))
    _, kernel_factory = _kernels(context, environment())
    kernel, tangent, compilation = kernel_factory(rows[0]['height_m'])
    if compilation['tangent']['original_source_sha256'] != context.manifest[
            'sources']['analysis/lll/ilvis0_tangent.cpp']:
        raise ValueError('original wide tangent source required')
    context.save('compilation.json', compilation)
    wide, _, protocol = bind(expected_sources={name: context.manifest[
        'sources']['analysis/lll/'+name] for name in WIDE_SOURCES})
    context.save('protocol-binding.json', protocol)
    with context.prepay_native(native_calls=task['limits']['native_calls'],
                               packet_visits=task['limits']['packet_visits']) as budget:
        _check_continue(context.root, context.manifest)
        result = wide(theta=arrays['theta'], dv=arrays['dv'], dt=arrays['dt'],
            times=bound['forecast_times'], training_rows=rows,
            time_origin_s=binding['time_origin_s'],
            model='sphere_rotating', profile=False,
            policy_id='reported-short-v1', start=0,
            limits=recipe['limits'], maximum_evaluations=200,
            maximum_interval_s=recipe['maximum_interval_s'],
            kernel=kernel, tangent_kernel=tangent, reserve=budget.reserve,
            save=context.save,
            check_continue=lambda: _check_continue(context.root, context.manifest),
            clock='header_elapsed')
    fit, forecast = result['fit'], result['forecast']
    complete = (forecast['prediction_receiver_positions_used'] is False and
                forecast['prediction_epochs'] == 400 and
                forecast['training_epochs'] == 800 and
                len(forecast['coordinates']) == 1200)
    passed = technical_gate(converged=fit['converged'], forecast_complete=complete)
    context.save('technical-summary.json', dict(
        passed=passed, numerical_converged=fit['converged'],
        forecast_complete=complete, evaluations=fit['evaluations'],
        physical_accuracy_scored=False, later_receiver_positions_used=False,
        original_reads=0, protected_reads=0, scientific_decision='abstain'))
    return dict(passed=passed, numerical_converged=fit['converged'],
                forecast_complete=complete, original_reads=0,
                protected_reads=0, scientific_decision='abstain')


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'run'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if args.action == 'request':
        result = request_qualification(root)
    elif args.action == 'prepare':
        result = prepare(root, qualification=
            'docs/prediction-observed-development/qualification/weighting-control-request.json')
    else:
        from .ilvis0_control_shards import launch
        result = launch(root/'data'/ID, reserved_threads=0)
    print(result)
    return result


if __name__ == '__main__':
    main()
