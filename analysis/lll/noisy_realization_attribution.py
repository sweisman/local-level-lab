# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bind a generated oracle forecast to saved historical sensor streams."""

import re
import math

_CHANNELS = ('theta', 'dv', 'dt', 'times')
_SHA256 = re.compile(r'[0-9a-f]{64}\Z')
SCOPE = 'generated same-realization oracle diagnostic; no original or protected reads'


def recipe():
    from lll.airquantumgrav_noisy_inputs import noise_settings
    from lll.airquantumgrav_truth import MODELS

    return dict(version='noisy-realization-attribution-v1',
                parent='docs/esa-noisy-prediction',
                models=list(MODELS), profiles=[False, True],
                policies=['reported-short-v1', 'reported-persistent-v1'],
                starts=[0, 1], latitude_deg=55., duration_s=1200., rate_hz=300,
                queries=1200, noise=noise_settings(),
                workers=2, threads=1, maximum_wall_s=7200.,
                recovery=dict(version='lll-task-resume-v1',
                              max_attempts_per_task=3,
                              max_technical_interruptions=12,
                              continuation_wall_s=86400,
                              minimum_free_bytes=10*1024**3),
                optimizer_starts=0, protected_reads=0, original_reads=0)


def construction_limits():
    from lll.airquantumgrav_noisy_inputs import construction_limits as parent_limits
    design = recipe()
    limits = parent_limits(design)
    # The oracle also constructs a true time-zero state and all receiver
    # positions for later scoring. Neither is part of the parent's input build.
    limits['generated_samples'] += 1 + design['queries']
    return limits


def known_point(parameters, limits, active, *, removal):
    """Normalize known generating corrections in the predictor's active order."""
    if (not isinstance(parameters, dict) or not isinstance(limits, dict)
            or not active or len(set(active)) != len(active)
            or not isinstance(removal, (int, float))
            or not math.isfinite(removal) or not 0 <= removal <= 1):
        raise ValueError('complete known correction and removal required')
    point = []
    for name in active:
        if name == 'earth_removal':
            value = 2 * removal - 1
        else:
            parameter = parameters.get(name)
            limit = limits.get(name)
            if (not isinstance(parameter, (int, float))
                    or not isinstance(limit, (int, float))
                    or not math.isfinite(parameter) or not math.isfinite(limit)
                    or limit <= 0):
                raise ValueError('complete known correction and bounds required')
            value = parameter / limit
        if not math.isfinite(value) or abs(value) > 1:
            raise ValueError('known correction must remain inside declared bounds')
        point.append(value)
    return point


def oracle_value_forecast(material, known, *, model, profile, limits,
                          kernel, reserve):
    """Propagate one known-calibration IMU stream without receiver fitting."""
    if (model not in recipe()['models'] or type(profile) is not bool
            or not callable(kernel) or not callable(reserve)):
        raise ValueError('declared model, processing case and native reservation required')
    import numpy as np
    from lll.airquantumgrav_observation_controls import value_prediction
    from lll.ilvis0_estimator import Bounds
    from lll.ilvis0_exploratory import ConditionalProblem

    times = np.asarray(material['times'], dtype=float)
    if times.ndim != 1 or len(times) < 2:
        raise ValueError('two supported receiver query placeholders required')
    problem = ConditionalProblem(
        material['theta'], material['dv'], material['dt'],
        times[:2], np.zeros((2, 3)), np.eye(6), known['initial'],
        Bounds(limits), kernel=kernel, fit_earth_removal=profile,
        clock_hypothesis='header_elapsed',
        processing_hypothesis='unsubtracted_increment_hypothesis',
        maximum_interval_s=1.5 / 300.,
        gravity_mps2=known['gravity_mps2'], disc_radius_m=6371000.)
    point = known_point(known['parameters'], limits, problem.bounds.active,
                        removal=.35 if profile else 0.)
    problem.bounds.decode(point)
    return value_prediction(problem, point, model, times, reserve=reserve)


def bound_streams(rows, *, models, policies, latitude_deg=55.):
    """Require the complete 24-case matrix and four identical streams per pair.

    This checks saved hashes only. It does not regenerate inputs, fit a model or
    imply four independent noise realizations within one model/profile pair.
    """
    models = tuple(models)
    policies = tuple(policies)
    if (len(models) != 3 or len(set(models)) != 3
            or len(policies) != 2 or len(set(policies)) != 2
            or len(rows) != 24):
        raise ValueError('exact historical case matrix required')
    by_case = {}
    identities = set()
    for row in rows:
        case = (row['model'], row['profile'], row['policy_id'], row['start'])
        hashes = row['hashes']
        if (row['model'] not in models or type(row['profile']) is not bool
                or row.get('latitude_deg') != latitude_deg
                or row['policy_id'] not in policies or type(row['start']) is not int
                or row['start'] not in (0, 1) or case in by_case
                or not isinstance(row['identity'], str)
                or row['identity'] in identities):
            raise ValueError('exact historical case matrix and latitude required')
        if (not isinstance(hashes, dict) or set(hashes) != set(_CHANNELS)
                or any(not isinstance(value, str) or not _SHA256.fullmatch(value)
                       for value in hashes.values())):
            raise ValueError('four complete SHA-256 sensor-array bindings required')
        by_case[case] = row
        identities.add(row['identity'])
    if len(by_case) != 24:
        raise ValueError('exact historical case matrix required')
    result = []
    for model in models:
        for profile in (False, True):
            matched = [by_case[model, profile, policy, start]
                       for policy in policies for start in (0, 1)]
            hashes = matched[0]['hashes']
            if any(row['hashes'] != hashes for row in matched[1:]):
                raise ValueError('four fits must use the same saved sensor stream')
            result.append(dict(model=model, latitude_deg=latitude_deg,
                               profile=profile, hashes=dict(hashes),
                               parent_identities=[row['identity'] for row in matched]))
    return result


def verify_regenerated_stream(material, hashes):
    """Require exact little-endian float64 bytes for all saved IMU/time arrays."""
    import sys
    from lll.studies.artifacts import digest

    if (sys.byteorder != 'little' or not isinstance(hashes, dict)
            or set(hashes) != set(_CHANNELS)
            or any(not isinstance(value, str) or not _SHA256.fullmatch(value)
                   for value in hashes.values())):
        raise ValueError('four complete parent sensor hashes required')
    for key in _CHANNELS:
        try:
            view = memoryview(material[key])
        except (KeyError, TypeError) as error:
            raise ValueError('four complete float64 sensor arrays required') from error
        if (not view.c_contiguous or view.itemsize != 8
                or view.format not in ('d', '<d', '=d', '@d')):
            raise ValueError('contiguous little-endian float64 sensor arrays required')
        if digest(view.cast('B')) != hashes[key]:
            raise ValueError('regenerated stream differs from parent sensor hash')
    return dict(hashes)


def score_saved_oracle(*, forecast, later_truth, score, save):
    """Persist the value-only forecast before generating any later truth."""
    prediction = forecast()
    save('forecast.json', prediction)
    answer = later_truth()
    result = score(prediction, answer)
    save('scores.json', result)
    return result


def calculate_oracle(task, proof, *, construct, initial, forecast,
                     later_truth, score, reserve_construction, save):
    """Bind one realized stream and score only after its forecast is sealed."""
    if (not isinstance(proof, dict)
            or not isinstance(proof.get('parent_recipe'), dict)
            or not isinstance(proof.get('bindings'), list)
            or any(not isinstance(proof.get(key), str)
                   or not _SHA256.fullmatch(proof[key])
                   for key in ('parent_manifest_sha256',
                               'parent_summary_sha256'))):
        raise ValueError('closed parent recipe and stream proof required')
    canonical = {row['identity']: row for row in tasks(proof['bindings'])}
    declared = {key: value for key, value in task.items()
                if key not in ('index', 'shard')}
    if canonical.get(task.get('identity')) != declared:
        raise ValueError('unchanged six-task oracle scope required')
    payload = task['payload']
    design = recipe()
    spec = dict(model=payload['model'], latitude_deg=payload['latitude_deg'],
                profile=payload['profile'], policy_id=design['policies'][0],
                start=design['starts'][0])
    material = construct(spec, proof['parent_recipe'],
                         reserve=reserve_construction)
    hashes = verify_regenerated_stream(material, payload['hashes'])
    save('input-binding.json', dict(
        parent_manifest_sha256=proof['parent_manifest_sha256'],
        parent_summary_sha256=proof['parent_summary_sha256'],
        parent_identities=payload['parent_identities'],
        full_array_sha256=hashes, original_reads=0, protected_reads=0))
    known = initial()

    def checked_truth():
        verify_regenerated_stream(material, hashes)
        return later_truth()

    return score_saved_oracle(
        forecast=lambda: forecast(material, known),
        later_truth=checked_truth, score=score, save=save)


def collect_parent_bindings(root):
    """Read only sealed parent inputs and require its exact historical matrix."""
    from lll.studies.closed import ClosedStudy

    design = recipe()
    parent = ClosedStudy(root, design['parent'])
    try:
        historical = parent.input('recipe')
        expected = dict(models=design['models'], profiles=design['profiles'],
                        policies=design['policies'], starts=2,
                        duration_s=design['duration_s'], rate_hz=design['rate_hz'],
                        queries=design['queries'], noise=design['noise'],
                        version='esa-noisy-prediction-v1', pattern='fast',
                        method='linear_points', height_profile='climb',
                        gravity_model='inverse_square_height',
                        query_start_s=.5, query_step_s=1., retries=0)
        if (parent.completion['state'] not in ('complete', 'terminal')
                or any(historical.get(key) != value
                       for key, value in expected.items())
                or len(parent.tasks) != 24 or len(parent.rows) != 24
                or set(parent.tasks) != set(parent.rows)):
            raise ValueError('exact closed historical noisy study required')
        receipt = parent.read('evidence-receipt.json')
        report_name = 'artifacts/publication/verified-report.json'
        report = parent.read(report_name, receipt['artifacts'][report_name])
        if (report.get('verified') is not True
                or any(report.get(key) != value for key, value in
                       (('total', 24), ('complete', 24),
                        ('numerically_converged', 24), ('accurate', 0)))
                or report.get('manifest_sha256') != parent.completion['manifest_sha256']
                or report.get('summary_sha256') != parent.completion['summary_sha256']):
            raise ValueError('verified historical 24-fit failure report required')
        rows = []
        for identity, task in parent.tasks.items():
            outcome = parent.envelope(identity)['result']
            if (outcome.get('converged') is not True
                    or outcome.get('accuracy_all_sections') is not False
                    or outcome.get('passed') is not False):
                raise ValueError('original numerical and accuracy labels differ')
            spec = task['payload']
            binding = parent.artifact(identity, 'input-binding.json')
            rows.append(dict(identity=identity,
                             **{key: spec[key] for key in
                                ('model', 'latitude_deg', 'profile', 'policy_id', 'start')},
                             hashes=binding['full_array_sha256']))
        bindings = bound_streams(rows, models=design['models'],
                                 policies=design['policies'],
                                 latitude_deg=design['latitude_deg'])
        return dict(parent_manifest_sha256=parent.completion['manifest_sha256'],
                    parent_summary_sha256=parent.completion['summary_sha256'],
                    parent_recipe=historical,
                    bindings=bindings)
    finally:
        parent.close()


def comparison_rows(bindings, parent_results, oracle_results):
    """Compare six sealed oracle scores with all 24 unchanged fitted failures."""
    if (not isinstance(bindings, list) or len(bindings) != 6
            or not isinstance(parent_results, dict)
            or not isinstance(oracle_results, dict)):
        raise ValueError('six oracle streams and 24 historical fits required')
    expected_oracle = {item['identity'] for item in tasks(bindings)}
    expected_parent = {identity for item in bindings
                       for identity in item['parent_identities']}
    if (len(expected_oracle) != 6 or len(expected_parent) != 24
            or set(oracle_results) != expected_oracle
            or set(parent_results) != expected_parent):
        raise ValueError('complete unchanged oracle and parent identity matrix required')

    def measures(row):
        try:
            result = {key: row['prediction'][key] for key in
                      ('horizontal_rms_m', 'vertical_rms_m')}
        except (KeyError, TypeError) as error:
            raise ValueError('complete saved prediction metrics required') from error
        if any(not isinstance(value, (int, float)) or
               not math.isfinite(value) or value < 0
               for value in result.values()):
            raise ValueError('finite nonnegative prediction metrics required')
        return result

    rows = []
    for item in bindings:
        model, profile = item['model'], item['profile']
        identity = f'{model}-{int(profile)}'
        oracle = oracle_results[identity]
        if (oracle.get('model') != model or oracle.get('profile') is not profile
                or oracle.get('parent_identities') != item['parent_identities']
                or oracle.get('technical_passed') is not True
                or oracle.get('passed') is not True
                or oracle.get('scientific_decision') != 'abstain'):
            raise ValueError('complete technical oracle result required')
        fitted = []
        for parent_identity in item['parent_identities']:
            old = parent_results[parent_identity]
            if (old.get('model') != model or old.get('profile') is not profile
                    or old.get('converged') is not True
                    or old.get('accuracy_all_sections') is not False
                    or old.get('passed') is not False):
                raise ValueError('historical failure label changed')
            fitted.append(dict(identity=parent_identity,
                               prediction=measures(old), passed=False))
        rows.append(dict(model=model, profile=profile,
                         oracle_identity=identity,
                         oracle_prediction=measures(oracle),
                         oracle_accuracy_all_sections=
                             oracle.get('accuracy_all_sections'),
                         original_fits=fitted))
    return rows


def tasks(bindings):
    """Reserve six known-calibration value forecasts and no fitting work."""
    design = recipe()
    expected = {(model, profile) for model in design['models']
                for profile in design['profiles']}
    if len(bindings) != 6 or {(v['model'], v['profile']) for v in bindings} != expected:
        raise ValueError('six distinct bound sensor streams required')
    visits = int(design['duration_s'] * design['rate_hz']) * design['queries']
    result = []
    for model in design['models']:
        for profile in design['profiles']:
            binding = next(v for v in bindings
                           if v['model'] == model and v['profile'] is profile)
            hashes = binding['hashes']
            if (binding.get('latitude_deg') != design['latitude_deg']
                    or set(hashes) != set(_CHANNELS)
                    or any(not isinstance(value, str) or not _SHA256.fullmatch(value)
                           for value in hashes.values())
                    or len(binding['parent_identities']) != 4):
                raise ValueError('complete parent stream binding required')
            result.append(dict(identity=f'{model}-{int(profile)}',
                               input_key='recipe', native_kind='value',
                               payload=dict(model=model,
                                            latitude_deg=design['latitude_deg'],
                                            profile=profile,
                                            hashes=dict(hashes),
                                            parent_identities=list(binding['parent_identities'])),
                               limits=dict(native_calls=1, packet_visits=visits,
                                           bound_calls=0, bound_steps=0)))
    return result


def qualification_sources(root):
    from lll.studies.dependencies import source_closure

    return source_closure(root, [
        'analysis/lll/noisy_realization_attribution.py',
        'analysis/lll/airquantumgrav_noisy_inputs.py',
        'analysis/lll/airquantumgrav_truth.py',
        'analysis/lll/airquantumgrav_observation_truth.py',
        'analysis/lll/airquantumgrav_observation_controls.py',
        'analysis/lll/airquantumgrav_scoring.py',
        'analysis/lll/ilvis0_shape.py',
        'analysis/lll/ilvis0_estimator.py',
        'analysis/lll/ilvis0_exploratory.py',
        'analysis/lll/ilvis0_native.c',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/tests/test_noisy_realization_attribution.py',
        'docs/noisy-realization-attribution/PLAN.md'])


def environment():
    from lll.airquantumgrav_inventory import environment as base
    return base()


def required_tests():
    return [
        'test_six_stream_bindings_require_all_matched_starts_and_policies',
        'test_oracle_task_matrix_has_finite_six_forecast_allowance',
        'test_oracle_construction_allowance_covers_exact_parent_draws',
        'test_known_correction_coordinates_include_exact_removal_fraction',
        'test_regenerated_sensor_bytes_must_match_all_four_parent_hashes',
        'test_oracle_forecast_is_saved_before_later_truth_is_opened',
        'test_oracle_orchestration_binds_input_before_forecast_and_truth',
        'test_oracle_orchestration_rejects_mutated_stream_before_truth',
        'test_oracle_orchestration_rejects_incomplete_parent_before_construction',
        'test_oracle_binding_reads_closed_parent_and_rejects_changed_stream',
        'test_oracle_preparation_requires_qualification_before_writing',
        'test_oracle_preparation_binds_parent_streams_and_finite_tasks',
        'test_oracle_evaluator_rejects_changed_recipe_before_construction',
        'test_oracle_evaluator_checks_parent_from_repository_root',
        'test_saved_oracle_comparison_preserves_four_original_failure_labels',
        'test_oracle_value_forecast_reproduces_known_correction_truth']


def recovery_sources(root):
    from lll.studies.task_resume import qualification_sources
    return qualification_sources(root)


def recovery_tests():
    from lll.studies.task_resume import REQUIRED_TESTS
    return REQUIRED_TESTS


def recovery_environment():
    from lll.ilvis0_control_shards import runtime_environment
    return runtime_environment()


def prepare(root, *, qualification=None, recovery_qualification=None,
            identity='noisy-realization-attribution-20261110'):
    """Freeze six parent-bound oracle tasks after source-bound qualification."""
    if qualification is None:
        raise ValueError('source-bound qualification required')
    if recovery_qualification is None:
        raise ValueError('source-bound recovery qualification required')
    from pathlib import Path
    from lll.compute_budget import environment as thread_environment
    from lll.studies.artifacts import atomic, encoded, safe_path
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition

    if not isinstance(identity, str) or not re.fullmatch(
            r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}', identity):
        raise ValueError('safe fresh oracle identity required')
    root = Path(root).resolve()
    base = safe_path(root, 'data/ilvis0-source-point-development/' + identity + '-inputs')
    if base.exists() or safe_path(root, 'data/' + identity).exists():
        raise ValueError('fresh oracle study required')
    design = recipe()
    env = environment()
    if env.get('numerical_environment') != thread_environment(
            workers=design['workers'], threads=design['threads']):
        raise ValueError('declared thread environment required')
    sources = qualification_sources(root)
    request, report = checked(root, qualification, sources=sources,
                              environment=env, required_tests=required_tests(),
                              minimum_tests=len(required_tests()))
    recovery_request, recovery_report = checked(
        root, recovery_qualification, sources=recovery_sources(root),
        environment=recovery_environment(), required_tests=recovery_tests(),
        minimum_tests=len(recovery_tests()))
    proof = collect_parent_bindings(root)
    work = tasks(proof['bindings'])
    materials = dict(recipe=encoded(design),
                     **{'qualification-request': request,
                        'qualification-report': report,
                        'qualification-environment': encoded(env),
                        'recovery-qualification-request': recovery_request,
                        'recovery-qualification-report': recovery_report,
                        'parent-proof': encoded(proof)})
    base.mkdir(parents=True)
    inputs = {}
    for index, (key, raw) in enumerate(materials.items()):
        path = base / f'input-{index:03d}'
        atomic(path, raw)
        inputs[key] = str(path.relative_to(root))
    definition = dict(id=identity,
                      scope=SCOPE,
                      adapter='analysis/lll/noisy_realization_attribution.py',
                      sources=sources, inputs=inputs, tasks=work,
                      workers=design['workers'], threads=design['threads'],
                      maximum_wall_s=design['maximum_wall_s'])
    atomic(base / 'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/' + identity, identities=len(work),
                allocation=manifest['allocation'], limits=manifest['limits'])


def evaluate(task, context):
    """Run one bound sensor stream with generating corrections, without a fit."""
    import json
    from pathlib import Path

    read = lambda key: json.loads(context.input_path(key).read_bytes())
    if read('recipe') != recipe():
        raise ValueError('unchanged oracle recipe required')
    proof = read('parent-proof')
    declared = {key: value for key, value in task.items()
                if key not in ('index', 'shard')}
    canonical = {row['identity']: row for row in tasks(proof['bindings'])}
    study_root = Path(context.root).resolve()
    if study_root.parent.name != 'data':
        raise ValueError('oracle study must be a direct data/ child')
    project_root = study_root.parents[1]
    if (canonical.get(task['identity']) != declared
            or context.manifest['scope'] != SCOPE
            or read('qualification-environment') != environment()
            or collect_parent_bindings(project_root) != proof):
        raise ValueError('unchanged qualified oracle task and parent required')

    import numpy as np
    from lll.airquantumgrav_noisy_inputs import construct
    from lll.airquantumgrav_truth import truth
    from lll.airquantumgrav_observation_truth import start, receiver_samples
    from lll.airquantumgrav_geographic_controls import position_errors
    from lll.airquantumgrav_scoring import sections
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.artifacts import digest
    from lll.studies.journal import Journal

    limits = construction_limits()
    journal = Journal(context.directory / 'construction.sqlite',
                      freeze=digest((context.root / 'manifest.json').read_bytes()),
                      limits={task['identity']: limits})
    journal.start(task['identity'])
    try:
        def check():
            _check_continue(context.root, context.manifest)

        def reserve_construction(**work):
            check()
            for key, value in work.items():
                journal.reserve(task['identity'], key, value)

        directory = (context.root / 'shards' / f'{context.shard:03d}' /
                     'kernels')
        kernel, metadata = load_kernel(directory,
                                       gravity_anchor_height_m=1500.)
        if (metadata['source_sha256'] != context.manifest['sources'][
                'analysis/lll/ilvis0_native.c']
                or metadata['compiler'] != environment()['compilers']['cc']):
            raise ValueError('frozen oracle native source and compiler required')
        context.save('compilation.json', metadata)

        payload = task['payload']
        historical = proof['parent_recipe']
        model = payload['model']
        profile = payload['profile']
        removal = .35 if profile else 0.
        sign = -1 if profile else 1
        arguments = dict(model=model, latitude_deg=payload['latitude_deg'],
                         pattern=historical['pattern'], removal=removal,
                         height_profile=historical['height_profile'],
                         gravity_model=historical['gravity_model'])
        material = None

        def bound_construct(spec, parent_recipe, *, reserve):
            nonlocal material
            material = construct(spec, parent_recipe, reserve=reserve)
            return material

        def initial():
            reserve_construction(generated_samples=1)
            origin = truth(times=np.array([0.]), **arguments)
            known = start(origin, model=model, sign=sign)
            context.save('known-corrections.json', dict(
                initial={key: value.tolist() if hasattr(value, 'tolist')
                         else value for key, value in known['initial'].items()},
                parameters=known['parameters'],
                gravity_mps2=known['gravity_mps2'],
                removal=removal,
                known_corrections_supplied_not_estimated=True))
            return known

        def forecast(measured, known):
            predicted = oracle_value_forecast(
                measured, known, model=model, profile=profile,
                limits=historical['limits'], kernel=kernel,
                reserve=context.charge)
            return dict(times_s=measured['times'].tolist(),
                        coordinates=predicted.tolist(),
                        known_corrections_supplied_not_estimated=True,
                        prediction_receiver_positions_used=False,
                        continuous_propagation_without_gps_reset=True)

        def later_truth():
            reserve_construction(generated_samples=len(material['times']))
            answer = receiver_samples(times=material['times'], sign=sign,
                                      **arguments)
            context.save('scoring-observations.json',
                         {key: value.tolist() for key, value in answer.items()})
            return answer

        def score(prediction, answer):
            times = np.asarray(prediction['times_s'], dtype=float)
            if not np.array_equal(times, material['times']):
                raise ValueError('oracle forecast query times changed')
            errors = position_errors(prediction['coordinates'], answer,
                                     model=model)
            cut = material['training_epochs']
            if cut != 800 or len(errors) != 1200:
                raise ValueError('unchanged 800/400 scoring split required')
            return dict(times_s=times.tolist(), errors_neu_m=errors.tolist(),
                        **sections(errors, cut), training_epochs=cut,
                        prediction_epochs=len(errors)-cut,
                        score_reference='generated noiseless physical truth',
                        later_receiver_noise_added=False)

        result = calculate_oracle(
            task, proof, construct=bound_construct, initial=initial,
            forecast=forecast, later_truth=later_truth, score=score,
            reserve_construction=reserve_construction, save=context.save)
        journal.verify()
        if any(journal.count(task['identity'], key) != value
               for key, value in limits.items()):
            raise ValueError('oracle construction charges differ')
        accuracy = all(result[name]['accuracy']['passed']
                       for name in ('training', 'prediction'))
        return dict(passed=True, technical_passed=True,
                    accuracy_all_sections=accuracy,
                    training=result['training'], prediction=result['prediction'],
                    training_epochs=result['training_epochs'],
                    prediction_epochs=result['prediction_epochs'], model=model,
                    latitude_deg=payload['latitude_deg'], profile=profile,
                    parent_identities=payload['parent_identities'],
                    native_calls=1, constructed_intervals=limits['constructed_intervals'],
                    generated_samples=limits['generated_samples'],
                    noise_normal_variates=limits['noise_normal_variates'],
                    original_reads=0, protected_reads=0,
                    oracle_not_real_flight_estimator=True,
                    confidence_calibrated=False, scientific_decision='abstain')
    finally:
        context.note_file(journal.path)
