# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite two-law forecast on the prepared ESA development recording."""

from pathlib import Path


IDENTITY = 'prediction-observed-development-stage1-20261113'
SMOKE_ID = IDENTITY + '-smoke'
SCOPE = ('one fixed-candidate two-law ESA development forecast; later receiver '
         'rows score only after both forecast interval unions are saved')
SMOKE_SCOPE = 'one short generated source-bound two-law forecast and receiver score'
PREFLIGHT = 'data/prediction-observed-law-preflight-v2-20261113'
PREFLIGHT_SMOKE = PREFLIGHT + '-smoke'
PARENT = 'docs/esa-development-pilot-preparation'
PARENT_TASK = 'prepare-earliest-187-v2'
GROUP_ID = 'esa-99f1530c3eda4318'
SMOKE_GROUP = 'generated-worker-smoke'
SOURCE_INPUTS = ('interval', 'training', 'layout', 'frozen-hashes',
                 'context', 'source-validation')
FULL_NATIVE_LIMIT = 3_000_000
FULL_VISIT_LIMIT = 80_000_000_000
SMOKE_NATIVE_LIMIT = 10_000
SMOKE_VISIT_LIMIT = 1_000_000


def recipe():
    from .prediction_observed_preflight_study import recipe as base
    from .prediction_simultaneous_study_v3 import recipe as generated
    reference = generated()
    return dict(base(), version='prediction-observed-development-stage1-v1',
                workers=1, threads=1, maximum_wall_s=28800.,
                maximum_evaluations=200,
                calibration_alpha=reference['calibration_alpha'],
                simultaneous_alpha=reference['simultaneous_alpha'],
                bound_margin=reference['bound_margin'],
                rank_rtol=reference['rank_rtol'],
                estimability_rtol=reference['estimability_rtol'],
                estimability_atol=reference['estimability_atol'],
                receiver_transform_policy=reference['receiver_transform_policy'])


def smoke_recipe():
    return dict(recipe(), version='prediction-observed-development-smoke-v1',
                duration_s=2., rate_hz=200, queries=9, query_start_s=.1,
                query_step_s=.2, maximum_evaluations=8,
                maximum_wall_s=600.)


def tasks():
    return [dict(identity='sphere_rotating-0-reported-short-v1-0',
                 input_key='interval', native_kind='tangent',
                 payload=dict(model='sphere_rotating', profile=False,
                              policy_id='reported-short-v1', start=0),
                 limits=dict(native_calls=FULL_NATIVE_LIMIT,
                             packet_visits=FULL_VISIT_LIMIT,
                             bound_calls=0, bound_steps=0))]


def smoke_task():
    return dict(tasks()[0], identity='generated-smoke',
                limits=dict(native_calls=SMOKE_NATIVE_LIMIT,
                            packet_visits=SMOKE_VISIT_LIMIT,
                            bound_calls=0, bound_steps=0))


def qualification_sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/prediction_observed_development_study.py',
        'analysis/lll/prediction_observed_native.py',
        'analysis/lll/prediction_observed_scoring.py',
        'analysis/lll/prediction_observed_material.py',
        'analysis/lll/structured_noisy_study.py',
        'analysis/lll/ilvis0_noise_bridge.cpp',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/tests/test_prediction_observed_development_study.py',
        'analysis/tests/test_prediction_observed_scoring.py',
        'analysis/tests/test_prediction_observed_native.py',
        'docs/prediction-observed-development/PLAN.md'])


def required_tests():
    return [
        'test_observed_development_has_one_finite_two_law_task',
        'test_observed_development_requires_gates_before_archive_reads',
        'test_observed_development_source_freeze_includes_scoring_and_plan',
        'test_observed_development_smoke_uses_finite_generated_input',
        'test_observed_development_rejects_changed_scope_before_input_read',
        'test_observed_score_uses_receiver_only_and_never_physical_truth',
        'test_observed_score_rejects_changed_training_prefix',
        'test_observed_score_abstains_when_interval_unsupported',
        'test_observed_native_opens_later_receiver_only_after_both_unions']


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
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    root = Path(root).resolve()
    directory = 'docs/prediction-observed-development/qualification/'
    return request(root,
                   sources=recovery_sources(root) if recovery
                           else qualification_sources(root),
                   environment=runtime_environment() if recovery
                               else environment(),
                   output=directory+('recovery-request.json' if recovery
                                     else 'request.json'),
                   report=directory+('recovery-tests.xml' if recovery
                                     else 'tests.xml'))


def definition(root, *, smoke, inputs):
    return dict(id=SMOKE_ID if smoke else IDENTITY,
                scope=SMOKE_SCOPE if smoke else SCOPE,
                adapter='analysis/lll/prediction_observed_development_study.py',
                sources=qualification_sources(root), inputs=dict(inputs),
                tasks=[smoke_task()] if smoke else tasks(),
                workers=1, threads=1,
                maximum_wall_s=600. if smoke else 28800.)


def smoke_definition(root, *, inputs):
    return definition(root, smoke=True, inputs=inputs)


def prepare(root, *, qualification, recovery_qualification):
    if qualification is None or recovery_qualification is None:
        raise ValueError('source and recovery qualification required before archive reads')
    return _prepare(root, smoke=False, qualification=qualification,
                    recovery_qualification=recovery_qualification)


def prepare_smoke(root):
    return _prepare(root, smoke=True)


def evaluate(task, context):
    scope = context.manifest.get('scope')
    smoke = scope == SMOKE_SCOPE
    expected = smoke_task() if smoke else tasks()[0]
    if (scope not in (SCOPE, SMOKE_SCOPE) or
            {key: value for key, value in task.items()
             if key not in ('index', 'shard')} != expected):
        raise ValueError('unchanged frozen observed-development task required')
    return _evaluate(task, context, smoke=smoke)


def _prepare(root, *, smoke, qualification=None, recovery_qualification=None):
    import gzip
    import json
    import shutil
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as thread_environment
    from .ilvis0_control_shards import runtime_environment, verify_completion
    from .studies.artifacts import atomic, digest, encoded, safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition

    root = Path(root).resolve()
    env = environment()
    if env['numerical_environment'] != thread_environment(workers=1, threads=1):
        raise ValueError('guarded one-thread observed-development environment required')
    identity = SMOKE_ID if smoke else IDENTITY
    base = safe_path(root, 'data/'+identity+'-inputs')
    if base.exists() or safe_path(root, 'data/'+identity).exists():
        raise ValueError('fresh observed-development allowance required')
    qualifications = {}
    if not smoke:
        request, report = checked(
            root, qualification, sources=qualification_sources(root),
            environment=env, required_tests=required_tests(),
            minimum_tests=len(required_tests()))
        recovery_request, recovery_report = checked(
            root, recovery_qualification, sources=recovery_sources(root),
            environment=runtime_environment(),
            required_tests=recovery_required_tests(),
            minimum_tests=len(recovery_required_tests()))
        check = verify_completion(root/'data'/SMOKE_ID)
        if (check['state'] != 'complete' or check['completed'] != 1 or
                check['passed'] is not True):
            raise ValueError('verified source-bound short worker required')
        smoke_manifest = json.loads((root/'data'/SMOKE_ID/'manifest.json').read_bytes())
        if (smoke_manifest['scope'] != SMOKE_SCOPE or
                any(smoke_manifest['sources'].get(name) != digest((root/name).read_bytes())
                    for name in qualification_sources(root))):
            raise ValueError('worker smoke source differs from qualified source')
        if shutil.disk_usage(root).free < 35*1024**3:
            raise ValueError('35 GiB free disk required before observed preparation')
        qualifications = dict(**{'qualification-request': request,
                                  'qualification-report': report,
                                  'recovery-request': recovery_request,
                                  'recovery-report': recovery_report})

    preflight = ClosedStudy(root, PREFLIGHT_SMOKE if smoke else PREFLIGHT)
    try:
        if (preflight.completion['state'] != 'complete' or
                preflight.summary['passed'] is not True):
            raise ValueError('verified completed input preflight required')
        raw = {name: preflight.input(name, raw=True) for name in SOURCE_INPUTS
               if name in preflight.manifest['inputs']}
        if set(raw) != set(SOURCE_INPUTS) - ({'source-validation'} if smoke else set()):
            raise ValueError('complete frozen preflight inputs required')
        binding = dict(preflight_manifest_sha256=preflight.completion['manifest_sha256'],
                       preflight_summary_sha256=preflight.completion['summary_sha256'],
                       preflight_inputs_sha256={key: digest(value)
                                                for key, value in raw.items()})
    finally:
        preflight.close()
    context = json.loads(raw['context'])
    if context.get('group_id') != (SMOKE_GROUP if smoke else GROUP_ID):
        raise ValueError('changed or protected observed group')
    layout = json.loads(raw['layout'])
    training = json.loads(gzip.decompress(raw['training']))
    if smoke:
        origin = layout['time_origin_gps_sow_s']
        later = [dict(training[-1], time_s=origin + time_s)
                 for time_s in layout['times_s'][len(training):]]
        scoring = gzip.compress(encoded(training + later), mtime=0)
    else:
        parent = ClosedStudy(root, PARENT)
        try:
            if (parent.completion['state'] != 'complete' or
                    parent.summary['passed'] is not True):
                raise ValueError('verified completed ESA preparation required')
            scoring = parent.artifact(PARENT_TASK, 'scoring-receiver.json.gz', raw=True)
            binding.update(parent_manifest_sha256=parent.completion['manifest_sha256'],
                           parent_summary_sha256=parent.completion['summary_sha256'])
        finally:
            parent.close()
    binding['scoring_sha256'] = digest(scoring)
    materials = dict(raw, scoring=scoring, recipe=encoded(smoke_recipe() if smoke else recipe()),
                     numerical_environment=encoded(env),
                     **{'source-parent-binding': encoded(binding)}, **qualifications)
    base.mkdir(parents=True)
    inputs = {}
    for index, (name, value) in enumerate(materials.items()):
        path = base/f'input-{index:03d}'
        atomic(path, value)
        inputs[name] = path.relative_to(root).as_posix()
    frozen = definition(root, smoke=smoke, inputs=inputs)
    atomic(base/'definition.json', encoded(frozen))
    manifest = Definition.from_dict(frozen, root).prepare(root)
    return dict(path='data/'+identity, tasks=1, allocation=manifest['allocation'])


def _evaluate(task, context, *, smoke):
    import gzip
    import json
    import numpy as np
    from .airquantumgrav_inventory import environment
    from .ilvis0_control_shards import _check_continue
    from .prediction_observed_material import bind
    from .prediction_observed_native import calculate
    from .prediction_observed_scoring import score_recording
    from .structured_noisy_study import _kernels
    from .studies.artifacts import digest

    read = lambda name: json.loads(context.input_path(name).read_bytes())
    r = smoke_recipe() if smoke else recipe()
    env = environment()
    binding = read('source-parent-binding')
    source_hashes = binding.get('preflight_inputs_sha256')
    if (read('recipe') != r or read('numerical_environment') != env or
            not isinstance(source_hashes, dict) or
            set(source_hashes) != set(SOURCE_INPUTS) -
            ({'source-validation'} if smoke else set()) or
            any(context.manifest['inputs'][name]['sha256'] != sha
                for name, sha in source_hashes.items()) or
            context.manifest['inputs']['scoring']['sha256'] !=
            binding.get('scoring_sha256')):
        raise ValueError('changed frozen observed-development source or environment')
    source_id = SMOKE_GROUP if smoke else GROUP_ID
    if read('context').get('group_id') != source_id:
        raise ValueError('changed observed development group')
    with np.load(context.input_path('interval'), allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in ('theta', 'dv', 'dt')}
    training = json.loads(gzip.decompress(context.input_path('training').read_bytes()))
    material = bind(arrays=arrays, layout=read('layout'),
                    training_rows=training, frozen_hashes=read('frozen-hashes'),
                    source_id=source_id,
                    maximum_interval_s=r['maximum_interval_s'],
                    time_offset_bound_s=r['limits']['time_offset'])
    expected = ((400, 9, 6, 222) if smoke else (360028, 1200, 800, 239867))
    actual = (len(material['dt']), len(material['times']),
              material['training_epochs'],
              material['binding']['training_prefix_packets'])
    if actual != expected:
        raise ValueError('observed-development interval differs from frozen plan')
    context.save('material-binding.json', material['binding'])
    noise_kernel, kernel_factory = _kernels(context, env)
    saved = set()

    def save(name, value):
        context.save(name, value)
        saved.add(name)

    def open_scoring():
        if not {'union-simultaneous-bounded-physical.json',
                'union-simultaneous-bounded-receiver.json'} <= saved:
            raise ValueError('both target unions must precede withheld receiver read')
        return json.loads(gzip.decompress(context.input_path('scoring').read_bytes()))

    check = lambda: _check_continue(context.root, context.manifest)
    budget = None
    try:
        with context.prepay_native(native_calls=task['limits']['native_calls'],
                                   packet_visits=task['limits']['packet_visits']) as budget:
            result = calculate(task['payload'], r, material,
                               noise_kernel=noise_kernel,
                               kernel_factory=kernel_factory,
                               reserve=budget.reserve, save=save,
                               open_scoring=open_scoring,
                               check_continue=check)
        score = score_recording(result, training_rows=material['training_rows'],
                                times=material['times'],
                                time_origin_s=material['time_origin_s'], save=save)
        if (result.get('scientific_decision') not in (None, 'abstain') or
                score['scientific_decision'] != 'abstain'):
            raise ValueError('development worker must abstain from science decision')
        candidates = result['candidates']
        summary = dict(passed=True, group_id=source_id,
                       laws={name: dict(converged=bool(value['fit']['converged']),
                                        evaluations=value['fit']['evaluations'])
                             for name, value in candidates.items()},
                       training_epochs=material['training_epochs'],
                       prediction_epochs=len(material['times'])-material['training_epochs'],
                       receiver_interval_supported=result['simultaneous_law_family'][
                           'receiver_measurement']['supported'],
                       receiver_interval_score=score['receiver_interval_score'],
                       physical_position_truth_available=False,
                       original_reads=0, protected_reads=0,
                       confidence_calibrated=False, scientific_decision='abstain')
        save('technical-summary.json', summary)
        return summary
    finally:
        if budget is not None:
            context.save('native-prepayment.json', budget.snapshot())


def launch(root, *, smoke=False):
    import shutil
    from .ilvis0_control_shards import launch as run_study
    root = Path(root).resolve()
    if not smoke and shutil.disk_usage(root).free < 35*1024**3:
        raise ValueError('35 GiB free disk required before observed worker launch')
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
    base = 'docs/prediction-observed-development/qualification/'
    if args.action == 'request':
        result = request_qualification(root)
    elif args.action == 'recovery-request':
        result = request_qualification(root, recovery=True)
    elif args.action == 'prepare-smoke':
        result = prepare_smoke(root)
    elif args.action == 'run-smoke':
        result = launch(root, smoke=True)
    elif args.action == 'prepare':
        result = prepare(root, qualification=base+'request.json',
                         recovery_qualification=base+'recovery-request.json')
    else:
        result = launch(root)
    print(result)
    return result


if __name__ == '__main__':
    main()
