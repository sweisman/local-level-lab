# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separately charged no-refit continuation of the observed prediction pilot."""

from pathlib import Path


IDENTITY = 'prediction-observed-development-continuation-v1-20261113'
SMOKE_ID = IDENTITY + '-smoke-v3'
SCOPE = ('one saved-point ESA development receiver bound and withheld score; '
         'no optimizer or protected confirmation recording')
SMOKE_SCOPE = 'one saved-point generated receiver bound and exact sealed-control score'
SOURCE_INPUTS = ('interval', 'training', 'layout', 'frozen-hashes', 'context',
                 'recipe', 'numerical_environment', 'scoring')
SAVED_ARTIFACTS = (
    'input-binding.json',
    'increment/fit.json', 'increment/forecast.json',
    'increment/receiver-error-diagnostic.json',
    'increment/simultaneous-bounded-physical.json',
    'increment/simultaneous-bounded-receiver.json',
    'point/fit.json', 'point/forecast.json',
    'point/training-error-operator.json',
    'point/simultaneous-bounded-physical.json')
SCIENCE_SEEDS = (
    'analysis/lll/prediction_observed_material.py',
    'analysis/lll/airquantumgrav_error_policy.py',
    'analysis/lll/airquantumgrav_noisy_inputs.py',
    'analysis/lll/ilvis0_native_error_training.py',
    'analysis/lll/ilvis0_forecast.py',
    'analysis/lll/bounded_simultaneous_forecast_wrapper.py',
    'analysis/lll/prediction_training_law_comparison.py',
    'analysis/lll/prediction_observed_scoring.py')


def _key(name):
    return 'saved-'+name.replace('/', '-').removesuffix('.json')


def task(*, smoke):
    from .prediction_observed_development_study import tasks
    source = tasks()[0]
    return dict(identity='generated-no-refit' if smoke else 'esa-187-no-refit',
                input_key='interval', native_kind='tangent',
                payload=dict(source['payload']),
                limits=dict(native_calls=10_000 if smoke else 2_500_000,
                            packet_visits=1_000_000 if smoke else 10_000_000_000,
                            bound_calls=0, bound_steps=0))


def qualification_sources(root):
    from .studies.dependencies import source_closure
    return source_closure(root, [
        'analysis/lll/prediction_observed_continuation_study.py',
        'analysis/lll/prediction_observed_continuation.py',
        'analysis/lll/prediction_observed_continuation_smoke.py',
        'analysis/tests/test_prediction_observed_continuation.py',
        'analysis/tests/test_prediction_observed_continuation_study.py',
        'docs/prediction-observed-development/CONTINUATION_PLAN.md'])


def required_tests():
    return ('test_continuation_has_one_fixed_no_refit_task_and_finite_allowance',
            'test_continuation_requires_staged_scoring_and_source_bound_artifacts',
            'test_native_continuation_requires_original_training_split_before_native_work',
            'test_native_continuation_reuses_saved_point_without_a_fitter',
            'test_saved_law_assembly_rejects_missing_bound_before_withheld_read',
            'test_qualified_law_assembly_opens_withheld_only_after_two_unions')


def recovery_sources(root):
    from .studies import task_resume
    from .studies.task_resume_sourcefix import SOURCE, TEST
    return list(dict.fromkeys((*task_resume.qualification_sources(root), SOURCE, TEST)))


def recovery_required_tests():
    from .studies import task_resume
    from .studies.task_resume_sourcefix import TEST_NAME
    return tuple(dict.fromkeys((*task_resume.REQUIRED_TESTS, TEST_NAME)))


def request_qualification(root, *, recovery=False):
    from .airquantumgrav_inventory import environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    root = Path(root).resolve()
    base = 'docs/prediction-observed-development/qualification/'
    return request(root,
                   sources=recovery_sources(root) if recovery
                           else qualification_sources(root),
                   environment=runtime_environment() if recovery
                               else environment(),
                   output=base+('continuation-recovery-request.json' if recovery
                                else 'continuation-v2-request.json'),
                   report=base+('continuation-recovery-tests.xml' if recovery
                                else 'continuation-v2-tests.xml'))


def definition(root, *, smoke, inputs):
    return dict(id=SMOKE_ID if smoke else IDENTITY,
                scope=SMOKE_SCOPE if smoke else SCOPE,
                adapter='analysis/lll/prediction_observed_continuation_study.py',
                sources=qualification_sources(root), inputs=dict(inputs),
                tasks=[task(smoke=smoke)], workers=1, threads=1,
                maximum_wall_s=600. if smoke else 14_400.)


def prepare(root, *, smoke, qualification=None, recovery_qualification=None):
    """Freeze verified parent bytes without opening withheld receiver values."""
    import json
    import shutil
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as thread_environment
    from .ilvis0_control_shards import runtime_environment, verify_completion
    from .prediction_observed_development_study import (
        IDENTITY as PARENT_ID, SMOKE_ID as PARENT_SMOKE_ID,
        tasks as parent_tasks, smoke_task)
    from .studies.artifacts import atomic, digest, encoded, safe_path
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.qualification import checked
    from .studies.runtime import Definition

    root = Path(root).resolve()
    study_id = SMOKE_ID if smoke else IDENTITY
    base = safe_path(root, 'data/'+study_id+'-inputs')
    if ((base/'definition.json').exists() or
            safe_path(root, 'data/'+study_id).exists()):
        raise ValueError('fresh separately charged continuation required')
    env = environment()
    if env['numerical_environment'] != thread_environment(workers=1, threads=1):
        raise ValueError('guarded one-thread continuation environment required')
    receipt_path = root/'docs/prediction-observed-development/continuation-smoke-equivalence.json'
    receipt = json.loads(receipt_path.read_bytes())
    if (receipt.get('passed') is not True or
            receipt.get('exact_receiver_bound') is not True or
            receipt.get('exact_law_unions') is not True or
            receipt.get('exact_withheld_score') is not True or
            receipt.get('refits') != 0 or
            receipt.get('continuation_sha256') != digest(
                (root/'analysis/lll/prediction_observed_continuation.py').read_bytes()) or
            receipt.get('checker_sha256') != digest(
                (root/'analysis/lll/prediction_observed_continuation_smoke.py').read_bytes())):
        raise ValueError('current exact no-refit generated control required')
    qualifications = {}
    if not smoke:
        if qualification is None or recovery_qualification is None:
            raise ValueError('source and interruption-recovery qualification required')
        q, report = checked(root, qualification,
                            sources=qualification_sources(root),
                            environment=env,
                            required_tests=required_tests(),
                            minimum_tests=len(required_tests()))
        rq, rreport = checked(root, recovery_qualification,
                              sources=recovery_sources(root),
                              environment=runtime_environment(),
                              required_tests=recovery_required_tests(),
                              minimum_tests=len(recovery_required_tests()))
        qualifications = dict(qualification_request=q,
                              qualification_report=report,
                              recovery_request=rq,
                              recovery_report=rreport)
        if shutil.disk_usage(root).free < 20*1024**3:
            raise ValueError('20 GiB free disk required before observed continuation')
        check = verify_completion(root/'data'/SMOKE_ID)
        if (check['state'] != 'complete' or check['completed'] != 1 or
                check['passed'] is not True):
            raise ValueError('verified continuation study smoke required')

    parent_id = PARENT_SMOKE_ID if smoke else PARENT_ID
    parent_task = smoke_task() if smoke else parent_tasks()[0]
    parent = ClosedStudy(root, 'data/'+parent_id)
    try:
        parent.envelope(parent_task['identity'])
        if (parent.completion['state'] != ('complete' if smoke else 'terminal') or
                parent.summary['total'] != 1 or
                parent.summary['completed'] != 1 or
                parent.manifest['tasks'][0]['identity'] != parent_task['identity'] or
                parent.input('numerical_environment') != env):
            raise ValueError('original sealed parent and numerical environment required')
        if not smoke and parent.rows[parent_task['identity']]['passed'] is not False:
            raise ValueError('terminal parent failure must remain unchanged')
        science = source_closure(root, SCIENCE_SEEDS)
        for name in science:
            expected = parent.manifest['sources'].get(name)
            if expected is not None and digest((root/name).read_bytes()) != expected:
                raise ValueError('original scientific dependency changed: '+name)
        inputs = {}
        parent_inputs = {}
        for name in SOURCE_INPUTS:
            record = parent.manifest['inputs'][name]
            path = safe_path(root, record['source'])
            if digest(path.read_bytes()) != record['sha256']:
                raise ValueError('original input changed: '+name)
            inputs[name] = record['source']
            parent_inputs[name] = record['sha256']
        saved_bytes = {
            name: parent.artifact(parent_task['identity'], name, raw=True)
            for name in SAVED_ARTIFACTS}
        artifact_hashes = {name: digest(raw) for name, raw in saved_bytes.items()}
        expected = {}
        if smoke:
            for name in ('point/simultaneous-bounded-receiver.json',
                         'point/receiver-error-diagnostic.json',
                         'training-law-comparison.json',
                         'union-simultaneous-bounded-physical.json',
                         'union-simultaneous-bounded-receiver.json',
                         'withheld-receiver-score.json'):
                expected[name] = parent.artifact(parent_task['identity'], name)
        parent_binding = dict(parent_id=parent_id,
                              parent_task=parent_task['identity'],
                              parent_manifest_sha256=parent.completion['manifest_sha256'],
                              parent_summary_sha256=parent.completion['summary_sha256'],
                              parent_inputs_sha256=parent_inputs,
                              saved_artifacts_sha256={_key(name): value
                                                       for name, value in artifact_hashes.items()},
                              source_id=('generated-worker-smoke' if smoke
                                         else 'esa-99f1530c3eda4318'),
                              original_reads=0, protected_reads=0,
                              scientific_decision='abstain')
    finally:
        parent.close()
    base.mkdir(parents=True, exist_ok=True)

    def write_or_verify(path, raw):
        if path.exists():
            if path.read_bytes() != raw:
                raise ValueError('partial preparation input differs from verified evidence')
        else:
            atomic(path, raw)

    for index, (name, raw) in enumerate(saved_bytes.items()):
        path = base/f'input-{index:03d}'
        write_or_verify(path, raw)
        inputs[_key(name)] = path.relative_to(root).as_posix()
    for name, value in [('parent-binding', parent_binding),
                        ('smoke-reference', expected)]:
        if name == 'smoke-reference' and not smoke:
            continue
        path = base/f'input-{len(inputs):03d}'
        write_or_verify(path, encoded(value))
        inputs[name] = path.relative_to(root).as_posix()
    for name, raw in qualifications.items():
        path = base/f'input-{len(inputs):03d}'
        write_or_verify(path, raw)
        inputs[name] = path.relative_to(root).as_posix()
    frozen = definition(root, smoke=smoke, inputs=inputs)
    atomic(base/'definition.json', encoded(frozen))
    manifest = Definition.from_dict(frozen, root).prepare(root)
    return dict(path='data/'+study_id, tasks=1,
                allocation=manifest['allocation'])


def evaluate(task_record, context):
    """Spend only the new allowance on the missing point receiver bound."""
    import gzip
    import json
    import numpy as np
    from .airquantumgrav_inventory import environment
    from .ilvis0_control_shards import _check_continue
    from .prediction_observed_continuation import (
        assemble_saved_laws, rebuild_native_point_bound)
    from .prediction_observed_development_study import recipe, smoke_recipe
    from .prediction_observed_material import bind
    from .prediction_observed_scoring import score_recording
    from .structured_noisy_study import _kernels
    from .studies.artifacts import reports_equal

    smoke = context.manifest.get('scope') == SMOKE_SCOPE
    expected = task(smoke=smoke)
    if (context.manifest.get('scope') not in (SCOPE, SMOKE_SCOPE) or
            {name: value for name, value in task_record.items()
             if name not in ('index', 'shard')} != expected):
        raise ValueError('unchanged fixed no-refit continuation task required')
    read = lambda name: json.loads(context.input_path(name).read_bytes())
    r = read('recipe')
    env = environment()
    parent = read('parent-binding')
    if (r != (smoke_recipe() if smoke else recipe()) or
            read('numerical_environment') != env or
            parent['source_id'] != ('generated-worker-smoke' if smoke
                                    else 'esa-99f1530c3eda4318') or
            parent['original_reads'] != 0 or parent['protected_reads'] != 0 or
            parent['scientific_decision'] != 'abstain' or
            any(context.manifest['inputs'][name]['sha256'] != sha
                for name, sha in parent['parent_inputs_sha256'].items()) or
            any(context.manifest['inputs'][name]['sha256'] != sha
                for name, sha in parent['saved_artifacts_sha256'].items())):
        raise ValueError('changed frozen parent evidence or environment')
    if read('context').get('group_id') != parent['source_id']:
        raise ValueError('changed or protected observed group')
    with np.load(context.input_path('interval'), allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in ('theta', 'dv', 'dt')}
    training = json.loads(gzip.decompress(
        context.input_path('training').read_bytes()))
    material = bind(
        arrays=arrays, layout=read('layout'), training_rows=training,
        frozen_hashes=read('frozen-hashes'), source_id=parent['source_id'],
        maximum_interval_s=r['maximum_interval_s'],
        time_offset_bound_s=r['limits']['time_offset'])
    actual = (len(material['dt']), len(material['times']),
              material['training_epochs'],
              material['binding']['training_prefix_packets'])
    if actual != ((400, 9, 6, 222) if smoke
                  else (360028, 1200, 800, 239867)):
        raise ValueError('continuation source split differs from frozen parent')
    saved = {name: read(_key(name)) for name in SAVED_ARTIFACTS}
    binding = saved['input-binding.json']
    noise_kernel, kernel_factory = _kernels(context, env)
    kernel, tangent, compilation = kernel_factory(
        material['training_rows'][0]['height_m'])
    context.save('compilation.json', compilation)
    written = set()
    point_bound = {}

    def save(name, value):
        if name in written:
            raise ValueError('duplicate continuation artifact')
        context.save(name, value)
        written.add(name)

    def save_point(name, value):
        if name != 'simultaneous-bounded-receiver.json':
            raise ValueError('only missing point receiver bound may be recalculated')
        point_bound[name] = value
        save('point/'+name, value)

    check = lambda: _check_continue(context.root, context.manifest)
    budget = None
    try:
        with context.prepay_native(
                native_calls=task_record['limits']['native_calls'],
                packet_visits=task_record['limits']['packet_visits']) as budget:
            point_diagnostic = rebuild_native_point_bound(
                binding, saved['point/fit.json'],
                saved['point/forecast.json'],
                saved['point/simultaneous-bounded-physical.json'],
                spec=task_record['payload'], recipe=r, material=material,
                kernel=kernel, tangent_kernel=tangent,
                noise_kernel=noise_kernel, reserve=budget.reserve,
                save=save_point, check_continue=check,
                training_operator=saved['point/training-error-operator.json'])
        point_diagnostic = json.loads(json.dumps(
            point_diagnostic, default=lambda value: value.tolist(),
            allow_nan=False))
        save('point/receiver-error-diagnostic.json', point_diagnostic)
        fits = {law: saved[law+'/fit.json'] for law in ('increment', 'point')}
        forecasts = {law: saved[law+'/forecast.json'] for law in ('increment', 'point')}
        physical = {law: saved[law+'/simultaneous-bounded-physical.json']
                    for law in ('increment', 'point')}
        receiver = dict(increment=saved[
            'increment/simultaneous-bounded-receiver.json'],
            point=point_bound['simultaneous-bounded-receiver.json'])
        diagnostics = dict(increment=saved[
            'increment/receiver-error-diagnostic.json'],
            point=point_diagnostic)

        def open_scoring():
            if not {'union-simultaneous-bounded-physical.json',
                    'union-simultaneous-bounded-receiver.json'} <= written:
                raise ValueError('both unions must precede withheld receiver read')
            return json.loads(gzip.decompress(
                context.input_path('scoring').read_bytes()))

        result = assemble_saved_laws(
            binding, fits=fits, forecasts=forecasts,
            physical_bounds=physical, receiver_bounds=receiver,
            receiver_diagnostics=diagnostics,
            minimum_simultaneous_coverage=1-r['simultaneous_alpha'],
            save=save, open_scoring=open_scoring)
        score = score_recording(
            result, training_rows=material['training_rows'],
            times=material['times'], time_origin_s=material['time_origin_s'],
            save=save)
        if smoke:
            reference = read('smoke-reference')
            checks = {
                'point/simultaneous-bounded-receiver.json': receiver['point'],
                'point/receiver-error-diagnostic.json': point_diagnostic,
                'training-law-comparison.json': result['comparison'],
                'union-simultaneous-bounded-physical.json':
                    result['simultaneous_law_family']['physical_position'],
                'union-simultaneous-bounded-receiver.json':
                    result['simultaneous_law_family']['receiver_measurement'],
                'withheld-receiver-score.json': score}
            if set(reference) != set(checks) or any(
                    not reports_equal(reference[name], value)
                    for name, value in checks.items()):
                raise ValueError('continuation differs from sealed generated control')
        summary = dict(passed=True, group_id=parent['source_id'],
                       training_epochs=material['training_epochs'],
                       prediction_epochs=len(material['times'])-
                                         material['training_epochs'],
                       original_reads=0, protected_reads=0, refits=0,
                       receiver_interval_supported=result[
                           'simultaneous_law_family']['receiver_measurement'][
                               'supported'],
                       receiver_interval_score=score['receiver_interval_score'],
                       confidence_calibrated=False,
                       scientific_decision='abstain')
        save('technical-summary.json', summary)
        return summary
    finally:
        if budget is not None:
            context.save('native-prepayment.json', budget.snapshot())


def launch(root, *, smoke):
    from .ilvis0_control_shards import launch as run_study
    root = Path(root).resolve()
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
        result = prepare(root, smoke=True)
    elif args.action == 'run-smoke':
        result = launch(root, smoke=True)
    elif args.action == 'prepare':
        result = prepare(root, smoke=False,
                         qualification=base+'continuation-v2-request.json',
                         recovery_qualification=
                             base+'continuation-recovery-request.json')
    else:
        result = launch(root, smoke=False)
    print(result)
    return result


if __name__ == '__main__':
    main()
