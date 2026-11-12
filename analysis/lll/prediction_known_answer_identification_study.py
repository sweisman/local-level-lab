# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite, source-bound known-answer error-law identification trial."""
from dataclasses import replace


IDENTITY = 'prediction-known-answer-identification-20261111'
SCOPE = ('generated linearized IMU and receiver error only; earlier-only '
         'law selection, later receiver coverage diagnostic; no aircraft data')


def recipe():
    return dict(version='prediction-known-answer-identification-v1',
                truths=['reference', 'persistent'], cadence_s=[1., 10.],
                seeds_per_task=100, training_epochs=30, withheld_epochs=10,
                speed_mps=200., compatible_delta_nll=2.,
                material_sigma_ratio=1.25, material_mean_spread=1.,
                nominal_interval_coverage=.95,
                rank_rtol=1e-8, workers=1, threads=1,
                maximum_wall_s=900., original_reads=0,
                protected_reads=0, aircraft_fits=0,
                calls_per_task=101, steps_per_task=406)


def tasks():
    return [dict(identity=f'{truth}-{int(cadence)}s', input_key='recipe',
                 payload=dict(truth=truth, cadence_s=cadence,
                              seed_start=10000*truth_index+1000*cadence_index,
                              seed_count=100),
                 limits=dict(native_calls=0, packet_visits=0,
                             bound_calls=101, bound_steps=406))
            for truth_index, truth in enumerate(recipe()['truths'])
            for cadence_index, cadence in enumerate(recipe()['cadence_s'])]


def candidates():
    from lll.prediction_error_known_answer import Law
    base = Law()
    return dict(reference=base,
                persistent=replace(base, receiver_ar_m=1.5,
                                   receiver_ar_tau_s=100.),
                gyro_bias=replace(base, gyro_bias_rad_s=5e-6))


def assess_history(history, truth_id, cadence_s, laws, *, operators=None):
    """Choose from the earlier prefix; use later residuals only to score."""
    import numpy as np
    from lll.calibrated_linear_prediction import predict
    from lll.prediction_error_identification import classify_training_laws
    from lll.prediction_error_known_answer import operator
    r = recipe()
    if truth_id not in r['truths'] or cadence_s not in r['cadence_s'] or set(laws) != set(candidates()):
        raise ValueError('exact declared truth and candidate laws required')
    times = cadence_s*np.arange(1., 41.)
    residual = np.asarray(history['residual_m'], dtype=float)
    if (residual.shape != (40,) or not np.all(np.isfinite(residual)) or
            not np.array_equal(history['times_s'], times)):
        raise ValueError('exact complete known-answer history required')
    if operators is None:
        operators = {name:operator(law, times, speed_mps=r['speed_mps'])
                     for name, law in laws.items()}
    design = np.ones((40, 1))
    train = residual[:30].copy()
    options = dict(training_epochs=30, parameter_scales=np.ones(1),
                   prediction_scales=np.ones(10), rank_rtol=1e-10,
                   estimability_rtol=1e-10, estimability_atol=1e-12,
                   maximum_parameters=1)
    classification = classify_training_laws(
        operators, design, train, **options,
        compatible_delta_nll=r['compatible_delta_nll'],
        material_sigma_ratio=r['material_sigma_ratio'],
        material_mean_spread=r['material_mean_spread'])
    selected = (classification['compatible_laws'][0]
                if classification['status'] == 'provisional_minimum' else None)

    def score(law_id):
        forecast = predict(operators[law_id], design, train, **options)
        if forecast['status'] != 'estimable':
            raise ValueError('known-answer constant-mean forecast must be estimable')
        sigma = np.sqrt(forecast['covariance'][:, 0, 0])
        standardized = (residual[30:]-forecast['mean'][:, 0])/sigma
        return int(np.count_nonzero(np.abs(standardized) <= 1.959963984540054)), float(
            np.mean(2*1.959963984540054*sigma))

    oracle_covered, oracle_width = score(truth_id)
    if selected is None:
        selected_covered = selected_width = None
    elif selected == truth_id:
        selected_covered, selected_width = oracle_covered, oracle_width
    else:
        selected_covered, selected_width = score(selected)
    return dict(classification=classification, selected_law=selected,
                oracle_covered_epochs=oracle_covered,
                oracle_mean_width_m=oracle_width,
                selected_covered_epochs=selected_covered,
                selected_mean_width_m=selected_width,
                scientific_detection=False)


def evaluate(task, context):
    """One charged finite task; retain all seed outcomes, including abstentions."""
    import json
    import numpy as np
    from lll.prediction_error_identification import local_information
    from lll.prediction_error_known_answer import generate, operator
    if (context.manifest.get('scope') != SCOPE or
            {key:value for key,value in task.items() if key not in ('index', 'shard')}
            not in tasks() or json.loads(context.input_path('recipe').read_bytes()) != recipe()):
        raise ValueError('unchanged bounded known-answer task and recipe required')
    declaration = task['payload']
    truth_id, cadence = declaration['truth'], declaration['cadence_s']
    times = cadence*np.arange(1., 41.)
    laws = candidates()
    operators = {name:operator(law, times, speed_mps=200.)
                 for name,law in laws.items()}
    context.charge(bound_calls=1, bound_steps=6)
    information = local_information(
        laws[truth_id], times, speed_mps=200., training_epochs=30,
        training_design=np.ones((30, 1)),
        fields=('receiver_white_m', 'receiver_ar_m', 'gyro_bias_rad_s'),
        rank_rtol=recipe()['rank_rtol'])
    rows = []
    for seed in range(declaration['seed_start'],
                      declaration['seed_start']+declaration['seed_count']):
        context.charge(bound_calls=1, bound_steps=4)
        history = generate(seed, laws[truth_id], times, speed_mps=200.)
        result = assess_history(history, truth_id, cadence, laws,
                                operators=operators)
        rows.append(dict(seed=seed, **result))
    context.save('histories.json', rows)
    context.save('training-information.json', information)
    statuses = {name:sum(row['classification']['status'] == name for row in rows)
                for name in ('provisional_minimum', 'equivalent_forecast', 'abstain')}
    return dict(passed=True, scientific_detection=False,
                scientific_status='development_diagnostic',
                truth=truth_id, cadence_s=cadence,
                histories=len(rows), status_counts=statuses,
                truth_selected=sum(row['selected_law'] == truth_id for row in rows),
                wrong_selected=sum(row['selected_law'] not in (None, truth_id)
                                   for row in rows),
                oracle_covered_epochs=sum(row['oracle_covered_epochs'] for row in rows),
                selected_covered_epochs=sum(row['selected_covered_epochs'] or 0
                                            for row in rows),
                selected_histories=sum(row['selected_law'] is not None for row in rows),
                information_rank=information['rank'],
                original_reads=0, protected_reads=0, aircraft_fits=0)


def qualification_sources(root):
    from pathlib import Path
    from lll.studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/prediction_known_answer_identification_study.py',
        'analysis/lll/prediction_error_identification.py',
        'analysis/lll/prediction_error_known_answer.py',
        'analysis/tests/test_prediction_known_answer_identification_study.py',
        'analysis/tests/test_prediction_error_identification.py',
        'analysis/tests/test_prediction_error_known_answer.py',
        'analysis/tests/test_prediction_error_law.py',
        'docs/prediction-known-answer-identification/PLAN.md'])


def required_tests():
    return [
        'test_white_receiver_scale_has_exact_information_after_fitting_constant_mean',
        'test_two_distinct_receiver_error_shapes_have_two_local_directions',
        'test_training_compatible_laws_with_different_forecast_scales_abstain',
        'test_independent_generator_matches_declared_joint_covariance',
        'test_correct_fixed_law_covers_withheld_receiver_residuals_with_fitted_mean',
        'test_frozen_trial_has_four_disjoint_bounded_tasks',
        'test_withheld_values_cannot_change_law_selection',
        'test_one_task_charges_every_history_and_preserves_every_result',
        'test_worker_adapter_loads_directly_from_frozen_file',
        'test_preparation_requires_source_bound_tests_and_exact_plan']


def prepare(root, *, qualification, recovery_qualification):
    from pathlib import Path
    from lll.ilvis0_control_shards import runtime_environment
    from lll.studies.artifacts import atomic, encoded
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    from lll.studies.task_resume import (qualification_sources as recovery_sources,
                                         REQUIRED_TESTS as recovery_tests)
    if qualification is None or recovery_qualification is None:
        raise ValueError('source-bound software and recovery qualification required')
    root = Path(root).resolve()
    base = root/'data'/(IDENTITY+'-inputs')
    if base.exists() or (root/'data'/IDENTITY).exists():
        raise ValueError('fresh finite known-answer identity required')
    environment = runtime_environment()
    source_request, source_report = checked(
        root, qualification, sources=qualification_sources(root),
        environment=environment, required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    recovery_request, recovery_report = checked(
        root, recovery_qualification, sources=recovery_sources(root),
        environment=environment, required_tests=recovery_tests,
        minimum_tests=len(recovery_tests))
    material = dict(recipe=encoded(recipe()),
                    qualification_request=source_request,
                    qualification_report=source_report,
                    recovery_request=recovery_request,
                    recovery_report=recovery_report,
                    numerical_environment=encoded(environment))
    base.mkdir(parents=True)
    inputs = {}
    for name, blob in material.items():
        path = base/name
        atomic(path, blob)
        inputs[name] = path.relative_to(root).as_posix()
    definition = dict(id=IDENTITY, scope=SCOPE,
                      adapter='analysis/lll/prediction_known_answer_identification_study.py',
                      sources=qualification_sources(root), inputs=inputs,
                      tasks=tasks(), workers=1, threads=1,
                      maximum_wall_s=recipe()['maximum_wall_s'])
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+IDENTITY, total=4,
                allocation=manifest['allocation'], limits=manifest['limits'])
