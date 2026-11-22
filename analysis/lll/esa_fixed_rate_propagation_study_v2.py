# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separately frozen matching-kernel ESA fixed-rate sensitivity study."""
import json
from pathlib import Path


ID = 'esa-fixed-rate-propagation-v2-20261114'
SMOKE_ID = ID+'-generated-smoke'
SCOPE = ('original-wide-kernel fixed saved-point ESA development rate sensitivity; '
         'no refit, original recording or protected group read')
SMOKE_SCOPE = 'matching-kernel three-task generated baseline qualification'


def tasks(*, smoke):
    from .esa_fixed_rate_propagation_study import tasks as original
    return original(smoke=smoke)


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/esa_fixed_rate_propagation_study_v2.py',
        'analysis/lll/esa_fixed_rate_protocol.py',
        'analysis/lll/esa_fixed_rate_propagation.py',
        'analysis/lll/esa_fixed_rate_inputs.py',
        'analysis/lll/esa_rate_hypothesis_audit.py',
        'analysis/lll/esa_fixed_rate_propagation_study.py',
        'analysis/lll/ilvis0_wide_tangent.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/tests/test_esa_fixed_rate_wide.py',
        'analysis/tests/test_esa_fixed_rate_propagation_study_v2.py',
        'analysis/tests/test_esa_fixed_rate_inputs.py',
        'analysis/tests/test_esa_rate_hypothesis_audit.py',
        'analysis/lll/studies/task_resume.py',
        'analysis/tests/test_task_resume.py',
        'docs/prediction-observed-development/RATE_PROPAGATION_V2_PLAN.md'])


def required_tests():
    return ('test_wide_kernel_reproduces_sealed_generated_baseline',
            'test_v2_preserves_three_finite_tasks_and_uses_new_identity',
            'test_v2_preparation_requires_source_qualification',
            'test_three_hypotheses_keep_time_support_and_saved_baseline',
            'test_changed_saved_increment_prevents_alternative_construction',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_source_input_environment_mutation_blocks',
            'test_recovery_caps_and_completed_failure')


def request_qualification(root):
    from .airquantumgrav_inventory import environment
    from .studies.qualification import request
    root = Path(root).resolve()
    return request(root, sources=sources(root), environment=environment(),
                   output='docs/prediction-observed-development/qualification/rate-propagation-v2-request.json',
                   report='docs/prediction-observed-development/qualification/rate-propagation-v2-tests.xml')


def prepare(root, *, smoke, qualification=None):
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    from .esa_fixed_rate_protocol import stage_parent
    from .ilvis0_control_shards import verify_completion
    from .studies.artifacts import atomic, encoded, safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition

    root = Path(root).resolve()
    identity = SMOKE_ID if smoke else ID
    base = safe_path(root, 'data/'+identity+'-inputs')
    if base.exists() or safe_path(root, 'data/'+identity).exists():
        raise ValueError('fresh matching-kernel study identity required')
    env = environment()
    if env['numerical_environment'] != numerical_environment(workers=1, threads=1):
        raise ValueError('guarded one-thread environment required')
    extra = {}
    if not smoke:
        if qualification is None:
            raise ValueError('source-bound qualification required before observed preparation')
        request, report = checked(root, qualification,
                                  sources=sources(root), environment=env,
                                  required_tests=required_tests(),
                                  minimum_tests=len(required_tests()))
        smoke_result = verify_completion(root/'data'/SMOKE_ID)
        if (smoke_result['state'] != 'complete' or
                smoke_result['completed'] != 3 or
                smoke_result['passed'] is not True):
            raise ValueError('matching-kernel generated smoke required')
        previous = ClosedStudy(root, 'data/esa-fixed-rate-propagation-v1-20261114')
        try:
            if (previous.completion['state'] != 'terminal' or
                    previous.completion['manifest_sha256'] !=
                    '2162c1ed5fb8f8b39eb5e8ce93dabe15cf369746b2c4e81680ec5e44bfca4dce' or
                    previous.completion['summary_sha256'] !=
                    'd57aeff8f6111b96fac79d3c1f222bad2be244795b05e00ff02e2ca6c03d3c01'):
                raise ValueError('preserved terminal first attempt required')
        finally:
            previous.close()
        extra = dict(qualification_request=request, qualification_report=report)
    copied = stage_parent(root, smoke=smoke)
    materials = dict(copied, qualification_environment=encoded(env), **extra)
    base.mkdir(parents=True)
    inputs = {}
    for number, (key, raw) in enumerate(materials.items()):
        path = base/f'input-{number:03d}'
        atomic(path, raw)
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=identity, scope=SMOKE_SCOPE if smoke else SCOPE,
                      adapter='analysis/lll/esa_fixed_rate_propagation_study_v2.py',
                      sources=sources(root), inputs=inputs, tasks=tasks(smoke=smoke),
                      workers=1, threads=1, maximum_wall_s=600. if smoke else 2700.)
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+identity, total=3,
                allocation=manifest['allocation'])


def evaluate(task, context):
    from .airquantumgrav_inventory import environment
    from .esa_fixed_rate_protocol import material, run_one, PARENT, SMOKE_PARENT
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_wide_tangent import load

    smoke = context.manifest.get('scope') == SMOKE_SCOPE
    declared = {key: value for key, value in task.items()
                if key not in ('index', 'shard')}
    if (context.manifest.get('scope') not in (SCOPE, SMOKE_SCOPE) or
            declared != {row['identity']: row for row in tasks(smoke=smoke)}.get(
                task['identity'])):
        raise ValueError('unchanged matching-kernel task required')
    read = lambda key: json.loads(context.input_path(key).read_bytes())
    parent = read('parent_identity')
    binding = read('saved-input-binding')
    if (parent['parent_prefix'] != (SMOKE_PARENT if smoke else PARENT) or
            parent['source_id'] != ('generated-worker-smoke' if smoke else
                                    'esa-99f1530c3eda4318') or
            parent['original_reads'] != 0 or parent['protected_reads'] != 0 or
            parent['refits'] != 0 or binding['source_id'] != parent['source_id'] or
            read('qualification_environment') != environment()):
        raise ValueError('source-bound parent and numerical environment required')
    bound = material(context.input_path('interval').read_bytes(),
                     context.input_path('training').read_bytes(),
                     binding=binding, fit=read('saved-increment-fit'),
                     saved=read('saved-increment-forecast'),
                     recipe=read('recipe'), smoke=smoke)
    folder = context.root/'shards'/f'{context.shard:03d}'/'kernels'
    kernel, compilation = load(
        folder, gravity_anchor_height_m=bound['training_gps'][0, 2],
        expected_source_sha256=context.manifest['sources'][
            'analysis/lll/ilvis0_tangent.cpp'])
    if (compilation['original_source_sha256'] != context.manifest['sources'][
            'analysis/lll/ilvis0_tangent.cpp'] or
            compilation['internal_mantissa_bits'] < 64):
        raise ValueError('original extended-precision native source required')
    context.save('compilation.json', compilation)
    budget = None
    try:
        with context.prepay_native(**{
                key: task['limits'][key] for key in ('native_calls', 'packet_visits')}) as budget:
            _check_continue(context.root, context.manifest)
            trajectory = run_one(bound, task['identity'],
                                 tangent_kernel=kernel, reserve=budget.reserve)
        context.save('trajectory.json', trajectory)
        passed = (trajectory['baseline_reproduced']
                  if task['identity'] == 'linear_points' else True)
        return dict(passed=passed, method=task['identity'], refits=0,
                    original_reads=0, protected_reads=0,
                    scientific_decision='abstain')
    finally:
        if budget is not None:
            context.save('native-prepayment.json', budget.snapshot())


def launch(root, *, smoke):
    from .ilvis0_control_shards import launch as run
    root = Path(root).resolve()
    return run(root/'data'/(SMOKE_ID if smoke else ID), reserved_threads=0)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare-smoke', 'run-smoke',
                                           'prepare', 'run'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if args.action == 'request': result = request_qualification(root)
    elif args.action == 'prepare-smoke': result = prepare(root, smoke=True)
    elif args.action == 'run-smoke': result = launch(root, smoke=True)
    elif args.action == 'prepare':
        result = prepare(root, smoke=False,
                         qualification='docs/prediction-observed-development/qualification/rate-propagation-v2-request.json')
    else: result = launch(root, smoke=False)
    print(result)
    return result


if __name__ == '__main__':
    main()
