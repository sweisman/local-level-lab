# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reproduce one generated stream and replay its four noise components."""

import json
import re
from pathlib import Path


SCOPE = 'same-realization generated IMU component attribution; no aircraft or protected reads'


def recipe():
    from lll.airquantumgrav_noisy_inputs import noise_settings
    from lll.noise_component_decomposition import variants

    return dict(version='noise-component-attribution-v1',
                parent='data/noisy-realization-attribution-20261111-v2',
                model='sphere_rotating', profile=False, latitude_deg=55.,
                duration_s=1200., rate_hz=300, queries=1200,
                training_epochs=800, noise=noise_settings(),
                variants=list(variants()),
                workers=2, threads=1, maximum_wall_s=7200.,
                recovery=dict(version='lll-task-resume-v1',
                              max_attempts_per_task=3,
                              max_technical_interruptions=20,
                              continuation_wall_s=7200,
                              minimum_free_bytes=10 * 1024**3),
                optimizer_starts=0, original_reads=0, protected_reads=0)


def tasks():
    from lll.noise_component_decomposition import variants

    return [dict(identity='component-' + variant, input_key='recipe',
                 native_kind='value', payload=dict(variant=variant),
                 limits=dict(native_calls=1, packet_visits=432000000,
                             bound_calls=0, bound_steps=0))
            for variant in variants()]


def construction_limits():
    return dict(constructed_intervals=360000,
                generated_samples=362002,
                noise_normal_variates=6480012)


def parent_proof(root):
    """Bind the selected stream to both closed generated parent studies."""
    from lll.noisy_realization_attribution import collect_parent_bindings
    from lll.studies.artifacts import digest, encoded
    from lll.studies.closed import ClosedStudy

    design = recipe()
    source = collect_parent_bindings(root)
    matched = [row for row in source['bindings']
               if row['model'] == design['model']
               and row['profile'] is design['profile']]
    if len(matched) != 1 or matched[0]['latitude_deg'] != 55.:
        raise ValueError('one exact selected generated parent stream required')
    oracle = ClosedStudy(root, design['parent'])
    try:
        identity = 'sphere_rotating-0'
        if (oracle.completion['state'] != 'complete'
                or len(oracle.tasks) != 6 or len(oracle.rows) != 6
                or oracle.input('parent-proof') != source
                or oracle.envelope(identity)['result'].get('technical_passed') is not True):
            raise ValueError('closed corrected oracle and matching parent required')
        forecast = oracle.artifact(identity, 'forecast.json')
        scores = oracle.artifact(identity, 'scores.json')
        if (len(forecast.get('times_s', [])) != 1200
                or len(forecast.get('coordinates', [])) != 1200
                or scores.get('training_epochs') != 800):
            raise ValueError('complete original full-noise oracle evidence required')
        return dict(version='noise-component-parent-binding-v1',
                    parent_manifest_sha256=source['parent_manifest_sha256'],
                    parent_summary_sha256=source['parent_summary_sha256'],
                    parent_recipe=source['parent_recipe'],
                    selected_binding=matched[0],
                    oracle_study=design['parent'],
                    oracle_manifest_sha256=oracle.completion['manifest_sha256'],
                    oracle_summary_sha256=oracle.completion['summary_sha256'],
                    oracle_full_forecast_sha256=digest(encoded(forecast)),
                    oracle_full_scores_sha256=digest(encoded(scores)))
    finally:
        oracle.close()


def build_material(proof, *, reserve):
    """Regenerate once per task; demand exact original full-stream hashes."""
    import numpy as np
    from lll.airquantumgrav_noisy_inputs import noise_settings
    from lll.airquantumgrav_training_controls import generated_training
    from lll.measurement_noise import perturb_imu
    from lll.noise_component_decomposition import compose
    from lll.noisy_realization_attribution import verify_regenerated_stream

    design = recipe()
    if (proof.get('version') != 'noise-component-parent-binding-v1'
            or proof.get('selected_binding', {}).get('model') != design['model']
            or proof['selected_binding'].get('profile') is not False
            or proof['selected_binding'].get('latitude_deg') != 55.
            or proof.get('parent_recipe', {}).get('noise') != design['noise']):
        raise ValueError('unchanged selected generated parent proof required')
    historical = proof['parent_recipe']
    spec = dict(model=design['model'], latitude_deg=55.,
                profile=False, start=0)
    clean = generated_training(spec, historical, reserve=reserve,
                               height_profile='climb',
                               gravity_model='inverse_square_height')
    if clean['training_epochs'] != 800 or len(clean['dt']) != 360000:
        raise ValueError('unchanged 800/400 and 300 Hz input support required')
    settings = noise_settings()
    isotropic = lambda std: np.eye(3) * std * std
    reserve(noise_normal_variates=6480012)
    noisy = perturb_imu(
        clean['theta'], clean['dv'], clean['dt'],
        seed=settings['seed'], maximum_steps=360000,
        gyro_white_psd=isotropic(settings['gyro_white_rads_per_sqrt_s']),
        accel_white_psd=isotropic(settings['accel_white_mps_per_sqrt_s']),
        gyro_bias_covariance=isotropic(settings['gyro_bias_stationary_rads']),
        accel_bias_covariance=isotropic(settings['accel_bias_stationary_mps2']),
        gyro_bias_tau_s=settings['gyro_bias_tau_s'],
        accel_bias_tau_s=settings['accel_bias_tau_s'])
    full = compose(clean, noisy, 'full')
    verify_regenerated_stream(full, proof['selected_binding']['hashes'])
    return clean, noisy


def kernel(context):
    from lll.airquantumgrav_inventory import environment
    from lll.ilvis0_exploratory import load_kernel

    directory = (context.root / 'shards' / f'{context.shard:03d}' /
                 'kernels')
    native, metadata = load_kernel(directory, gravity_anchor_height_m=1500.)
    if (metadata['source_sha256'] != context.manifest['sources'][
            'analysis/lll/ilvis0_native.c']
            or metadata['compiler'] != environment()['compilers']['cc']):
        raise ValueError('frozen native source and compiler required')
    context.save('compilation.json', metadata)
    return native


def evaluate(task, context):
    from lll.airquantumgrav_inventory import environment

    declared = {key: value for key, value in task.items()
                if key not in ('index', 'shard')}
    if (declared not in tasks() or context.manifest['scope'] != SCOPE
            or json.loads(context.input_path('recipe').read_bytes()) != recipe()
            or json.loads(context.input_path(
                'qualification-environment').read_bytes()) != environment()):
        raise ValueError('unchanged qualified component task required')
    proof = json.loads(context.input_path('parent-proof').read_bytes())

    import numpy as np
    from lll.airquantumgrav_truth import truth
    from lll.airquantumgrav_observation_truth import start, receiver_samples
    from lll.airquantumgrav_geographic_controls import position_errors
    from lll.airquantumgrav_scoring import sections
    from lll.noise_component_decomposition import compose
    from lll.noisy_realization_attribution import (oracle_value_forecast,
                                                    score_saved_oracle)
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.artifacts import digest, encoded
    from lll.studies.journal import Journal

    identity = task['identity']
    journal = Journal(context.directory / 'construction.sqlite',
                      freeze=digest((context.root / 'manifest.json').read_bytes()),
                      limits={identity: construction_limits()})
    journal.start(identity)
    budget = None
    try:
        native = kernel(context)
        with context.prepay_native(native_calls=1,
                                   packet_visits=432000000) as budget:
            def reserve_construction(**counts):
                _check_continue(context.root, context.manifest)
                for name, count in counts.items():
                    journal.reserve(identity, name, count)

            clean, noisy = build_material(proof, reserve=reserve_construction)
            variant = task['payload']['variant']
            selected = compose(clean, noisy, variant)
            context.save('stream-binding.json', dict(
                variant=variant,
                selected_sha256={key: digest(np.asarray(
                    selected[key], dtype='<f8').tobytes())
                    for key in ('theta', 'dv', 'dt', 'times')},
                full_parent_sha256=proof['selected_binding']['hashes'],
                component_sha256={channel: {kind: digest(np.asarray(
                    noisy['noise'][channel][kind + '_increments'],
                    dtype='<f8').tobytes()) for kind in ('white', 'bias')}
                    for channel in ('gyro', 'accel')},
                same_realization_across_variants=True))

            arguments = dict(model='sphere_rotating', latitude_deg=55.,
                             pattern='fast', removal=0.,
                             height_profile='climb',
                             gravity_model='inverse_square_height')
            reserve_construction(generated_samples=1)
            origin = truth(times=np.array([0.]), **arguments)
            known = start(origin, model='sphere_rotating', sign=1)
            context.save('known-corrections.json', dict(
                initial={key: value.tolist() if hasattr(value, 'tolist')
                         else value for key, value in known['initial'].items()},
                parameters=known['parameters'],
                gravity_mps2=known['gravity_mps2'],
                known_corrections_supplied_not_estimated=True))

            def reserve_native(**counts):
                if counts != dict(native_calls=1, packet_visits=432000000):
                    raise ValueError('one complete charged value forecast required')
                budget.reserve(**counts)

            def forecast():
                predicted = oracle_value_forecast(
                    selected, known, model='sphere_rotating', profile=False,
                    limits=proof['parent_recipe']['limits'],
                    kernel=native, reserve=reserve_native)
                value = dict(times_s=selected['times'].tolist(),
                             coordinates=predicted.tolist(),
                             known_corrections_supplied_not_estimated=True,
                             prediction_receiver_positions_used=False,
                             continuous_propagation_without_gps_reset=True)
                if (variant == 'full'
                        and digest(encoded(value)) !=
                        proof['oracle_full_forecast_sha256']):
                    raise ValueError('complete-noise forecast differs from sealed oracle')
                return value

            def later_truth():
                reserve_construction(generated_samples=1200)
                answer = receiver_samples(times=selected['times'], sign=1,
                                          **arguments)
                context.save('scoring-observations.json',
                             {key: value.tolist() for key, value in answer.items()})
                return answer

            def score(prediction, answer):
                errors = position_errors(prediction['coordinates'], answer,
                                         model='sphere_rotating')
                if len(errors) != 1200:
                    raise ValueError('complete 1200-epoch scoring support required')
                return dict(times_s=selected['times'].tolist(),
                            errors_neu_m=errors.tolist(),
                            **sections(errors, 800),
                            training_epochs=800, prediction_epochs=400,
                            score_reference='generated noiseless physical truth',
                            later_receiver_noise_added=False)

            scores = score_saved_oracle(forecast=forecast,
                                       later_truth=later_truth,
                                       score=score, save=context.save)
            if (variant == 'full'
                    and digest(encoded(scores)) !=
                    proof['oracle_full_scores_sha256']):
                raise ValueError('complete-noise scores differ from sealed oracle')
        journal.verify()
        if any(journal.count(identity, name) != limit
               for name, limit in construction_limits().items()):
            raise ValueError('component construction charges differ')
        return dict(passed=True, technical_passed=True,
                    variant=variant, model='sphere_rotating',
                    training_epochs=800, prediction_epochs=400,
                    prediction=scores['prediction'],
                    native_calls_attempted=budget.snapshot()[
                        'attempted']['native_calls'],
                    original_reads=0, protected_reads=0,
                    optimizer_starts=0,
                    confidence_calibrated=False,
                    scientific_decision='abstain')
    finally:
        if budget is not None:
            context.save('native-prepayment.json', budget.snapshot())
        context.note_file(journal.path)


def qualification_sources(root):
    from lll.studies.dependencies import source_closure

    return source_closure(root, [
        'analysis/lll/noise_component_study.py',
        'analysis/lll/noise_component_decomposition.py',
        'analysis/lll/noisy_realization_attribution.py',
        'analysis/lll/airquantumgrav_noisy_inputs.py',
        'analysis/lll/airquantumgrav_training_controls.py',
        'analysis/lll/measurement_noise.py',
        'analysis/lll/ilvis0_native.c',
        'analysis/tests/test_noise_component_study.py',
        'analysis/tests/test_noise_component_decomposition.py',
        'analysis/tests/test_noisy_realization_attribution.py',
        'docs/noisy-realization-attribution/component-decomposition/PLAN.md'])


def required_tests():
    return ['test_component_study_has_ten_finite_reboot_safe_tasks',
            'test_component_study_requires_qualifications_before_writing',
            'test_component_study_rejects_changed_task_before_construction',
            'test_component_study_preserves_prepayment_if_construction_stops',
            'test_component_study_executes_through_frozen_adapter',
            'test_component_variants_have_exact_ten_fixed_identities',
            'test_component_streams_preserve_source_arrays_and_full_realization',
            'test_component_stream_rejects_missing_or_changed_realization',
            'test_oracle_value_forecast_reproduces_known_correction_truth']


def prepare(root, *, qualification=None, recovery_qualification=None,
            identity='noise-component-decomposition-20261111'):
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
        raise ValueError('safe fresh attribution identity required')
    root = Path(root).resolve()
    base = safe_path(root, 'data/ilvis0-source-point-development/' +
                     identity + '-inputs')
    if base.exists() or safe_path(root, 'data/' + identity).exists():
        raise ValueError('fresh finite attribution study required')
    design = recipe()
    env = environment()
    if env['numerical_environment'] != thread_environment(
            workers=2, threads=1):
        raise ValueError('declared two-worker environment required')
    sources = qualification_sources(root)
    request, report = checked(root, qualification, sources=sources,
                              environment=env, required_tests=required_tests(),
                              minimum_tests=len(required_tests()))
    recovery_request, recovery_report = checked(
        root, recovery_qualification, sources=recovery_sources(root),
        environment=runtime_environment(),
        required_tests=recovery_tests,
        minimum_tests=len(recovery_tests))
    proof = parent_proof(root)
    values = dict(recipe=encoded(design),
                  **{'qualification-request': request,
                     'qualification-report': report,
                     'qualification-environment': encoded(env),
                     'recovery-qualification-request': recovery_request,
                     'recovery-qualification-report': recovery_report,
                     'parent-proof': encoded(proof)})
    base.mkdir(parents=True)
    inputs = {}
    for index, (key, raw) in enumerate(values.items()):
        path = base / f'input-{index:03d}'
        atomic(path, raw)
        inputs[key] = str(path.relative_to(root))
    definition = dict(id=identity, scope=SCOPE,
                      adapter='analysis/lll/noise_component_study.py',
                      sources=sources, inputs=inputs, tasks=tasks(),
                      workers=2, threads=1,
                      maximum_wall_s=design['maximum_wall_s'])
    atomic(base / 'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/' + identity, allocation=manifest['allocation'],
                limits=manifest['limits'])
