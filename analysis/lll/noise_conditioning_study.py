# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite, recoverable same-operator receiver-conditioning comparison."""

import json
import re
from pathlib import Path


SCOPE = 'generated same-operator conditioning comparison; no aircraft or protected reads'


def recipe():
    return dict(version='noise-conditioning-comparison-v1',
                model='sphere_rotating', removal=0., latitude_deg=55.,
                duration_s=1200., rate_hz=300, queries=1200,
                training_epochs=800, law='increment',
                maximum_operator_bytes=64 * 1024**2,
                workers=1, threads=1, maximum_wall_s=3600.,
                recovery=dict(version='lll-task-resume-v1',
                              max_attempts_per_task=3,
                              max_technical_interruptions=3,
                              continuation_wall_s=3600,
                              minimum_free_bytes=10 * 1024**3),
                optimizer_starts=0, random_draws=0,
                original_reads=0, protected_reads=0)


def tasks():
    return [dict(identity='increment-1200-conditioning', input_key='recipe',
                 native_kind='tangent',
                 payload=dict(law='increment', duration_s=1200.),
                 limits=dict(native_calls=361200, packet_visits=361200,
                             bound_calls=0, bound_steps=0))]


def construction_limits():
    return dict(generated_samples=361201,
                constructed_intervals=360000, summary_epochs=400)


def kernel(context):
    from lll.noise_benchmark_study import kernel as benchmark_kernel
    return benchmark_kernel(context)


def evaluate(task, context):
    from lll.airquantumgrav_inventory import environment

    declared = {key: value for key, value in task.items()
                if key not in ('index', 'shard')}
    if (declared != tasks()[0] or context.manifest['scope'] != SCOPE
            or json.loads(context.input_path('recipe').read_bytes()) != recipe()
            or json.loads(context.input_path(
                'qualification-environment').read_bytes()) != environment()):
        raise ValueError('unchanged qualified conditioning task required')

    from lll.generated_noise_benchmark import material, build_operator
    from lll.noise_conditioning_comparison import compare
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.artifacts import digest
    from lll.studies.journal import Journal

    identity = task['identity']
    journal = Journal(context.directory / 'construction.sqlite',
                      freeze=digest((context.root / 'manifest.json').read_bytes()),
                      limits={identity: construction_limits()})
    journal.start(identity)
    budget = None
    try:
        native = kernel(context)
        with context.prepay_native(native_calls=361200,
                                   packet_visits=361200) as budget:
            def reserve_construction(**counts):
                _check_continue(context.root, context.manifest)
                for name, count in counts.items():
                    journal.reserve(identity, name, count)

            data = material(duration_s=1200., queries=1200,
                            query_start_s=.5, query_step_s=1.,
                            reserve=reserve_construction)
            if data['training_epochs'] != 800:
                raise ValueError('unchanged 800-epoch conditioning boundary required')

            def reserve_native(**counts):
                if (set(counts) != {'native_calls', 'packet_steps'}
                        or counts['native_calls'] != 1
                        or counts['packet_steps'] != 1):
                    raise ValueError('one charged native step required')
                budget.reserve(native_calls=1, packet_visits=1)

            operator, _, descriptor = build_operator(
                data, law='increment', kernel=native, reserve=reserve_native,
                maximum_bytes=recipe()['maximum_operator_bytes'])
            reserve_construction(summary_epochs=400)
            comparison = compare(
                operator, training_epochs=800,
                physical_scales=data['nominal_metric'][800:])
            context.save('error-operator.json', descriptor)
            context.save('variance-comparison.json', comparison)
        journal.verify()
        if any(journal.count(identity, name) != limit
               for name, limit in construction_limits().items()):
            raise ValueError('construction work differs from frozen allowance')
        return dict(passed=True, training_epochs=800, later_epochs=400,
                    unconditional_horizontal_rms_scale_m=comparison[
                        'unconditional']['horizontal_rms_scale_m'],
                    conditioned_horizontal_rms_scale_m=comparison[
                        'conditioned']['horizontal_rms_scale_m'],
                    unconditional_height_rms_scale_m=comparison[
                        'unconditional']['height_rms_scale_m'],
                    conditioned_height_rms_scale_m=comparison[
                        'conditioned']['height_rms_scale_m'],
                    native_calls_attempted=budget.snapshot()[
                        'attempted']['native_calls'],
                    original_reads=0, protected_reads=0,
                    optimizer_starts=0, random_draws=0,
                    prediction_qualified=False,
                    confidence_calibrated=False,
                    scientific_decision='abstain')
    finally:
        if budget is not None:
            context.save('native-prepayment.json', budget.snapshot())
        context.note_file(journal.path)


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root, [
        'analysis/lll/noise_conditioning_study.py',
        'analysis/lll/noise_conditioning_comparison.py',
        'analysis/lll/noise_benchmark_study.py',
        'analysis/lll/generated_noise_benchmark.py',
        'analysis/lll/state_space_covariance.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',
        'analysis/lll/ilvis0_wide_tangent.py',
        'analysis/tests/test_noise_conditioning_study.py',
        'analysis/tests/test_noise_conditioning_comparison.py',
        'analysis/tests/test_generated_noise_benchmark.py',
        'analysis/tests/test_prediction_error_benchmark.py',
        'docs/noisy-realization-attribution/conditioning-comparison/PLAN.md'])


def required_tests():
    return [
        'test_conditioning_study_has_one_finite_observation_free_task',
        'test_conditioning_study_requires_qualifications_before_writing',
        'test_conditioning_study_rejects_changed_task_before_work',
        'test_conditioning_study_preserves_prepaid_work_after_failure',
        'test_same_operator_scales_match_dense_unconditional_and_conditional']


def prepare(root, *, qualification=None, recovery_qualification=None,
            identity='noise-conditioning-comparison-20261111'):
    if qualification is None or recovery_qualification is None:
        raise ValueError('source-bound qualification and recovery required')
    from lll.airquantumgrav_inventory import environment
    from lll.compute_budget import environment as thread_environment
    from lll.studies.artifacts import atomic, encoded, safe_path
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    from lll.studies.task_resume import (qualification_sources as recovery_sources,
                                         REQUIRED_TESTS as recovery_tests)
    from lll.ilvis0_control_shards import runtime_environment

    if not isinstance(identity, str) or not re.fullmatch(
            r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}', identity):
        raise ValueError('safe fresh study identity required')
    root = Path(root).resolve()
    base = safe_path(root, 'data/ilvis0-source-point-development/' +
                     identity + '-inputs')
    if base.exists() or safe_path(root, 'data/' + identity).exists():
        raise ValueError('fresh finite conditioning study required')
    design = recipe()
    env = environment()
    if env['numerical_environment'] != thread_environment(
            workers=1, threads=1):
        raise ValueError('declared thread environment required')
    sources = qualification_sources(root)
    request, report = checked(root, qualification, sources=sources,
                              environment=env, required_tests=required_tests(),
                              minimum_tests=8)
    recovery_request, recovery_report = checked(
        root, recovery_qualification, sources=recovery_sources(root),
        environment=runtime_environment(),
        required_tests=recovery_tests,
        minimum_tests=len(recovery_tests))
    values = dict(recipe=encoded(design),
                  **{'qualification-request': request,
                     'qualification-report': report,
                     'qualification-environment': encoded(env),
                     'recovery-qualification-request': recovery_request,
                     'recovery-qualification-report': recovery_report})
    base.mkdir(parents=True)
    inputs = {}
    for index, (key, raw) in enumerate(values.items()):
        path = base / f'input-{index:03d}'
        atomic(path, raw)
        inputs[key] = str(path.relative_to(root))
    definition = dict(id=identity, scope=SCOPE,
                      adapter='analysis/lll/noise_conditioning_study.py',
                      sources=sources, inputs=inputs, tasks=tasks(),
                      workers=1, threads=1,
                      maximum_wall_s=design['maximum_wall_s'])
    atomic(base / 'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/' + identity, allocation=manifest['allocation'],
                limits=manifest['limits'])
