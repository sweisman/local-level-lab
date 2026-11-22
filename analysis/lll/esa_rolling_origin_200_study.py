# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite two-law ESA 200/120 temporal-transfer development fit."""

import json
from pathlib import Path


ID = 'esa-rolling-origin-200-development-v1-20261116'
SCOPE = ('two ESA development fits on receiver reports 0-199; predict '
         'reports 200-319 without their positions')
FIT_INPUT_KEYS = ('interval', 'training', 'forecast_times', 'recipe',
                  'saved-input-binding', 'parent_identity',
                  'qualification_environment', 'qualification_request',
                  'qualification_report')
REQUEST = ('docs/prediction-observed-development/qualification/'
           'rolling-origin-200-request.json')
REPORT = ('docs/prediction-observed-development/qualification/'
          'rolling-origin-200-tests.xml')
RECOVERY_POLICY = ('docs/prediction-observed-development/qualification/'
                   'rolling-origin-200-recovery-policy.json')


def tasks():
    return [dict(identity=law, input_key='interval', native_kind='tangent',
                 payload=dict(law=law, model='sphere_rotating', start=0),
                 limits=dict(native_calls=700000, packet_visits=45000000000,
                             bound_calls=0, bound_steps=0))
            for law in ('increment', 'point')]


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/esa_rolling_origin_200.py',
        'analysis/lll/esa_rolling_origin_200_study.py',
        'analysis/lll/esa_temporal_refit.py',
        'analysis/lll/esa_training_split.py',
        'analysis/lll/esa_fixed_rate_protocol.py',
        'analysis/lll/airquantumgrav_prediction.py',
        'analysis/lll/ilvis0_native_error_training.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',
        'analysis/lll/studies/task_resume.py',
        'analysis/tests/test_esa_rolling_origin_200.py',
        'analysis/tests/test_esa_rolling_origin_200_study.py',
        'analysis/tests/test_original_recovery_policy.py',
        'analysis/tests/test_task_resume.py',
        'docs/prediction-observed-development/ROLLING_ORIGIN_200_PLAN.md'])


def required_tests():
    return ('test_200_120_fit_material_excludes_all_scoring_values',
            'test_200_study_tasks_and_inputs_are_fixed',
            'test_200_study_requires_qualification_before_staging',
            'test_200_study_rejects_changed_task_before_any_input_read',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_recovery_policy_seals_interrupted_charge_before_continuation',
            'test_source_input_environment_mutation_blocks')


def request_qualification(root):
    from .airquantumgrav_inventory import environment
    from .studies.qualification import request
    root = Path(root).resolve()
    return request(root, sources=sources(root), environment=environment(),
                   output=REQUEST, report=REPORT)


def prepare(root, *, qualification=None):
    if qualification is None:
        raise ValueError('source-bound qualification required before staging')
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    from .esa_fixed_rate_protocol import stage_parent
    from .esa_rolling_origin_200 import build_material
    from .studies.artifacts import atomic, encoded, digest, safe_path
    from .studies.qualification import checked
    from .studies.runtime import Definition

    root = Path(root).resolve()
    base = safe_path(root, 'data/'+ID+'-inputs')
    if base.exists() or safe_path(root, 'data/'+ID).exists():
        raise ValueError('fresh finite temporal-transfer identity required')
    env = environment()
    if env['numerical_environment'] != numerical_environment(workers=2,
                                                                threads=1):
        raise ValueError('guarded two-worker allocation required')
    request, report = checked(
        root, qualification, sources=sources(root), environment=env,
        required_tests=required_tests(), minimum_tests=len(required_tests()))
    source = stage_parent(root, smoke=False)
    material = build_material(source)
    split = material.split
    fit = split.fit_material()
    preflight = json.loads((root/'docs/prediction-observed-development/'
        'ROLLING_ORIGIN_200_PREFLIGHT.json').read_bytes())
    if (preflight['fit_input_sha256'] !=
            {name: digest(value) for name, value in fit.items()} or
            preflight['staged_imu_packets'] != 95868 or
            split.packet_count != 95868 or
            preflight['scoring_positions_staged_with_fit'] is not False):
        raise ValueError('saved 200/120 input preflight differs')
    staged = dict(fit, recipe=source['recipe'],
                  **{'saved-input-binding': source['saved-input-binding'],
                     'parent_identity': source['parent_identity'],
                     'qualification_environment': encoded(env),
                     'qualification_request': request,
                     'qualification_report': report})
    if set(staged) != set(FIT_INPUT_KEYS):
        raise ValueError('unexpected fit input or scoring position')
    base.mkdir(parents=True)
    inputs = {}
    for number, name in enumerate(FIT_INPUT_KEYS):
        path = base/f'input-{number:03d}'
        atomic(path, staged[name])
        inputs[name] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE,
                      adapter='analysis/lll/esa_rolling_origin_200_study.py',
                      sources=sources(root), inputs=inputs, tasks=tasks(),
                      workers=2, threads=1, maximum_wall_s=7200.)
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, total=2,
                allocation=manifest['allocation'],
                withheld_receiver_positions_staged=False)


def evaluate(task, context):
    declared = {key: value for key, value in task.items()
                if key not in ('index', 'shard')}
    if (context.manifest.get('scope') != SCOPE or
            declared != {row['identity']: row for row in tasks()}.get(
                task['identity']) or
            set(context.manifest.get('inputs', {})) != set(FIT_INPUT_KEYS)):
        raise ValueError('unchanged finite temporal-transfer task required')
    from .esa_temporal_refit import evaluate_temporal_fit
    return evaluate_temporal_fit(
        task, context, training_epochs=200, total_epochs=320,
        packet_count=95868, source_id='esa-99f1530c3eda4318')


def launch(root):
    from .studies.original_recovery_policy import resume
    return resume(Path(root).resolve(), RECOVERY_POLICY)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'run'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    result = (request_qualification(root) if args.action == 'request' else
              prepare(root, qualification=REQUEST) if args.action == 'prepare'
              else launch(root))
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
