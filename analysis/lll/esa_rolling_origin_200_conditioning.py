# SPDX-License-Identifier: AGPL-3.0-or-later
"""Condition sealed ESA 200/120 fits using only their earlier receiver rows."""

import json
from pathlib import Path

from .esa_rolling_origin_200_study import ID as FIT_ID


ID = 'esa-rolling-origin-200-conditioning-v1-20261116'
SCOPE = 'condition sealed 200/120 forecasts on the first 200 receiver reports only'
INPUT_KEYS = ('interval', 'training', 'forecast_times', 'recipe',
              'saved-input-binding', 'parent_identity', 'fit_identity',
              'qualification_environment', 'qualification_request',
              'qualification_report', 'increment-fit', 'increment-forecast',
              'increment-error-operator', 'increment-training-observations',
              'point-fit', 'point-forecast', 'point-error-operator',
              'point-training-observations')
REQUEST = ('docs/prediction-observed-development/qualification/'
           'rolling-origin-200-conditioning-request.json')
REPORT = ('docs/prediction-observed-development/qualification/'
          'rolling-origin-200-conditioning-tests.xml')
RECOVERY_POLICY = ('docs/prediction-observed-development/qualification/'
                   'rolling-origin-200-conditioning-recovery-policy.json')
LAWS = ('increment', 'point')


def tasks(laws=LAWS):
    if not set(laws) <= set(LAWS):
        raise ValueError('declared error laws required')
    return [dict(identity=law, input_key='interval', native_kind='tangent',
                 payload=dict(law=law, model='sphere_rotating', optimize=False,
                              training_epochs=200, forecast_epochs=120),
                 limits=dict(native_calls=450000, packet_visits=1000000000,
                             bound_calls=0, bound_steps=0)) for law in laws]


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/esa_rolling_origin_200_conditioning.py',
        'analysis/lll/esa_temporal_conditioning_worker.py',
        'analysis/lll/esa_conditional_forecast_v2_study.py',
        'analysis/lll/esa_conditional_forecast_v3_study.py',
        'analysis/lll/esa_rolling_origin_200_study.py',
        'analysis/tests/test_esa_rolling_origin_200_conditioning.py',
        'analysis/tests/test_esa_conditional_forecast_v2_study.py',
        'analysis/tests/test_esa_conditional_forecast_v3_study.py',
        'analysis/tests/test_original_recovery_policy.py',
        'analysis/tests/test_task_resume.py',
        'docs/prediction-observed-development/'
        'ROLLING_ORIGIN_200_CONDITIONING_PLAN.md'])


def required_tests():
    return ('test_200_conditioning_tasks_and_input_boundary',
            'test_200_conditioning_requires_closed_fit_and_qualification',
            'test_200_conditioning_rejects_changed_task_before_reading_input',
            'test_single_pass_conditions_only_on_saved_early_residuals',
            'test_full_operator_prefix_replays_separate_early_operator',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_recovery_policy_seals_interrupted_charge_before_continuation',
            'test_source_input_environment_mutation_blocks')


def _guarded_environment():
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    value = environment()
    if value['numerical_environment'] != numerical_environment(workers=2,
                                                                threads=1):
        raise ValueError('guarded two-worker conditioning environment required')
    return value


def request_qualification(root):
    from .studies.qualification import request
    root = Path(root).resolve()
    return request(root, sources=sources(root),
                   environment=_guarded_environment(),
                   output=REQUEST, report=REPORT)


def prepare(root, *, qualification=None):
    if qualification is None:
        raise ValueError('source-bound qualification required before staging')
    from .studies.artifacts import atomic, encoded, safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition

    root = Path(root).resolve()
    base = safe_path(root, 'data/'+ID+'-inputs')
    if base.exists() or safe_path(root, 'data/'+ID).exists():
        raise ValueError('fresh finite conditioning identity required')
    env = _guarded_environment()
    request, report = checked(
        root, qualification, sources=sources(root), environment=env,
        required_tests=required_tests(), minimum_tests=len(required_tests()))
    parent = ClosedStudy(root, 'data/'+FIT_ID)
    try:
        if (parent.completion['state'] not in ('complete', 'terminal') or
                parent.summary['completed'] != 2 or
                set(parent.tasks) != set(LAWS)):
            raise ValueError('both sealed 200/120 fit outcomes required')
        binding = parent.input('saved-input-binding')
        identity = parent.input('parent_identity')
        if (binding['source_id'] != 'esa-99f1530c3eda4318' or
                identity['protected_reads'] != 0 or
                identity['original_reads'] != 0):
            raise ValueError('unchanged saved development input required')
        passed = []
        staged = {name: parent.input(name, raw=True) for name in INPUT_KEYS[:6]}
        staged['fit_identity'] = encoded(dict(
            prefix='data/'+FIT_ID,
            manifest_sha256=parent.completion['manifest_sha256'],
            summary_sha256=parent.completion['summary_sha256']))
        for law in LAWS:
            outcome = parent.envelope(law)['result']
            if outcome.get('passed') is True:
                if (outcome.get('later_receiver_positions_used') is not False or
                        outcome.get('law') != law):
                    raise ValueError('sealed fit observation boundary differs')
                passed.append(law)
                for artifact, key in (
                    ('fit.json', 'fit'), ('forecast.json', 'forecast'),
                    ('training-error-operator.json', 'error-operator'),
                    ('training-observations.json', 'training-observations')):
                    staged[f'{law}-{key}'] = parent.artifact(law, artifact,
                                                              raw=True)
        if not passed:
            return dict(state='no_passing_fit', total=0,
                        scientific_decision='abstain')
        staged.update(qualification_environment=encoded(env),
                      qualification_request=request,
                      qualification_report=report)
        expected = set(INPUT_KEYS[:10]) | {
            f'{law}-{key}' for law in passed for key in (
                'fit', 'forecast', 'error-operator', 'training-observations')}
        if set(staged) != expected:
            raise ValueError('unexpected conditioning input or scoring position')
        base.mkdir(parents=True)
        inputs = {}
        for index, name in enumerate(sorted(staged)):
            path = base/f'input-{index:03d}'
            atomic(path, staged[name])
            inputs[name] = path.relative_to(root).as_posix()
        definition = dict(id=ID, scope=SCOPE,
            adapter='analysis/lll/esa_rolling_origin_200_conditioning.py',
            sources=sources(root), inputs=inputs, tasks=tasks(passed),
            workers=2, threads=1, maximum_wall_s=7200.)
        atomic(base/'definition.json', encoded(definition))
        manifest = Definition.from_dict(definition, root).prepare(root)
        return dict(path='data/'+ID, total=len(passed), laws=passed,
                    allocation=manifest['allocation'],
                    later_receiver_positions_staged=False)
    finally:
        parent.close()


def evaluate(task, context):
    declared = {key: value for key, value in task.items()
                if key not in ('index', 'shard')}
    expected = set(INPUT_KEYS[:10]) | {
        f"{row['identity']}-{key}"
        for row in context.manifest.get('tasks', [])
        for key in ('fit', 'forecast', 'error-operator', 'training-observations')}
    if (context.manifest.get('scope') != SCOPE or
            declared not in tasks() or
            set(context.manifest.get('inputs', {})) != expected):
        raise ValueError('unchanged earlier-only conditioning task required')
    from .esa_temporal_conditioning_worker import evaluate_conditioning
    return evaluate_conditioning(
        task, context, fit_id=FIT_ID, training_epochs=200,
        total_epochs=320, packet_count=95868)


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
