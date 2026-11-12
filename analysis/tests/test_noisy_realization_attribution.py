# SPDX-License-Identifier: AGPL-3.0-or-later
"""The oracle comparison must bind to exactly six historical sensor streams."""
import copy
from array import array
from hashlib import sha256

import pytest


MODELS = ('sphere_rotating', 'sphere_still', 'flat_still')
POLICIES = ('reported-short-v1', 'reported-persistent-v1')


def cases():
    rows = []
    for model_index, model in enumerate(MODELS):
        for profile in (False, True):
            mark = format(1 + 2 * model_index + int(profile), 'x')
            hashes = {name: mark * 64 for name in ('theta', 'dv', 'dt', 'times')}
            for policy in POLICIES:
                for start in (0, 1):
                    rows.append(dict(identity=f'{model}-{int(profile)}-{policy}-{start}',
                                     model=model, latitude_deg=55., profile=profile,
                                     policy_id=policy,
                                     start=start, hashes=dict(hashes)))
    return rows


def test_six_stream_bindings_require_all_matched_starts_and_policies():
    from lll.noisy_realization_attribution import bound_streams

    rows = cases()
    bindings = bound_streams(rows, models=MODELS, policies=POLICIES)
    assert len(bindings) == 6
    assert all(len(item['parent_identities']) == 4 for item in bindings)
    assert bindings[0]['hashes']['theta'] == '1' * 64
    damaged = copy.deepcopy(rows)
    damaged[1]['hashes']['theta'] = 'f' * 64
    with pytest.raises(ValueError, match='same saved sensor stream'):
        bound_streams(damaged, models=MODELS, policies=POLICIES)
    with pytest.raises(ValueError, match='exact historical case matrix'):
        bound_streams(rows[:-1], models=MODELS, policies=POLICIES)
    with pytest.raises(ValueError, match='exact historical case matrix'):
        bound_streams(rows[:-1] + [rows[0]], models=MODELS,
                      policies=POLICIES)
    damaged = copy.deepcopy(rows)
    damaged[0]['latitude_deg'] = -55.
    with pytest.raises(ValueError, match='latitude'):
        bound_streams(damaged, models=MODELS, policies=POLICIES)


def test_oracle_task_matrix_has_finite_six_forecast_allowance():
    from lll.noisy_realization_attribution import bound_streams, recipe, tasks

    bindings = bound_streams(cases(), models=MODELS, policies=POLICIES)
    design = recipe()
    work = tasks(bindings)
    assert design['workers'] == 2 and design['threads'] == 1
    assert design['maximum_wall_s'] == 7200.
    assert design['recovery'] == dict(
        version='lll-task-resume-v1', max_attempts_per_task=3,
        max_technical_interruptions=12, continuation_wall_s=86400,
        minimum_free_bytes=10*1024**3)
    assert len(work) == 6
    assert len({row['identity'] for row in work}) == 6
    assert all(row['limits']['native_calls'] == 1 for row in work)
    assert all(row['payload']['latitude_deg'] == 55. for row in work)
    assert all(row['limits']['packet_visits'] == 360000 * 1200 for row in work)
    assert all(row['limits']['bound_calls'] == 0 for row in work)
    assert sum(row['limits']['native_calls'] for row in work) == 6


def test_oracle_construction_allowance_covers_exact_parent_draws():
    from lll.noisy_realization_attribution import construction_limits

    assert construction_limits() == dict(
        constructed_intervals=360000, generated_samples=362002,
        noise_normal_variates=6484812)


def test_oracle_evaluator_rejects_changed_recipe_before_construction(tmp_path):
    import json
    from lll.noisy_realization_attribution import evaluate

    recipe_path = tmp_path / 'recipe.json'
    recipe_path.write_text(json.dumps({'version': 'changed'}))

    class Context:
        def input_path(self, key='recipe'):
            assert key == 'recipe'
            return recipe_path

    with pytest.raises(ValueError, match='unchanged oracle recipe'):
        evaluate(dict(identity='changed'), Context())


def test_oracle_evaluator_checks_parent_from_repository_root(tmp_path, monkeypatch):
    import json
    from lll import noisy_realization_attribution as module

    bindings = module.bound_streams(cases(), models=MODELS, policies=POLICIES)
    proof = {'bindings': bindings}
    values = {
        'recipe': module.recipe(),
        'parent-proof': proof,
        'qualification-environment': module.environment(),
    }
    study = tmp_path / 'data' / 'oracle-study'
    study.mkdir(parents=True)
    paths = {}
    for key, value in values.items():
        path = study / f'{key}.json'
        path.write_text(json.dumps(value))
        paths[key] = path

    class Context:
        root = study
        manifest = {'scope': module.SCOPE}

        def input_path(self, key):
            return paths[key]

    seen = []

    def stop_after_parent_check(root):
        seen.append(root)
        raise RuntimeError('parent-location probe')

    monkeypatch.setattr(module, 'collect_parent_bindings', stop_after_parent_check)
    with pytest.raises(RuntimeError, match='parent-location probe'):
        module.evaluate(module.tasks(bindings)[0], Context())
    assert seen == [tmp_path]


def test_saved_oracle_comparison_preserves_four_original_failure_labels():
    from lll.noisy_realization_attribution import bound_streams, comparison_rows

    bindings = bound_streams(cases(), models=MODELS, policies=POLICIES)
    parent = {}
    oracle = {}
    for binding in bindings:
        model, profile = binding['model'], binding['profile']
        identity = f'{model}-{int(profile)}'
        oracle[identity] = dict(model=model, profile=profile, passed=True,
                                technical_passed=True, accuracy_all_sections=True,
                                parent_identities=binding['parent_identities'],
                                prediction=dict(horizontal_rms_m=1.,
                                                vertical_rms_m=2.),
                                scientific_decision='abstain')
        for index, parent_identity in enumerate(binding['parent_identities']):
            parent[parent_identity] = dict(model=model, profile=profile,
                                           converged=True, passed=False,
                                           accuracy_all_sections=False,
                                           prediction=dict(horizontal_rms_m=10. + index,
                                                           vertical_rms_m=20. + index))
    result = comparison_rows(bindings, parent, oracle)
    assert len(result) == 6
    assert all(len(row['original_fits']) == 4 for row in result)
    assert result[0]['oracle_prediction']['horizontal_rms_m'] == 1.
    assert result[0]['original_fits'][0]['prediction']['horizontal_rms_m'] == 10.
    damaged = copy.deepcopy(parent)
    damaged[bindings[0]['parent_identities'][0]]['passed'] = True
    with pytest.raises(ValueError, match='historical failure label'):
        comparison_rows(bindings, damaged, oracle)


def test_known_correction_coordinates_include_exact_removal_fraction():
    from lll.noisy_realization_attribution import known_point

    parameters = dict(gyro_bias_x=.2, time_offset=-.001)
    limits = dict(gyro_bias_x=.5, time_offset=.01)
    active = ('gyro_bias_x', 'time_offset', 'earth_removal')
    assert known_point(parameters, limits, active, removal=.35) == pytest.approx([
        .4, -.1, -.3])
    with pytest.raises(ValueError, match='inside declared bounds'):
        known_point(dict(parameters, gyro_bias_x=.6), limits, active,
                    removal=.35)
    with pytest.raises(ValueError, match='complete known correction'):
        known_point({}, limits, active, removal=.35)


def test_regenerated_sensor_bytes_must_match_all_four_parent_hashes():
    from lll.noisy_realization_attribution import verify_regenerated_stream

    measured = {key: array('d', values) for key, values in dict(
        theta=[1., -2., 3.], dv=[4., 5., -6.], dt=[.005],
        times=[0., .005]).items()}
    hashes = {key: sha256(value.tobytes()).hexdigest()
              for key, value in measured.items()}
    verify_regenerated_stream(measured, hashes)
    measured['dv'][1] = 5.25
    with pytest.raises(ValueError, match='parent sensor hash'):
        verify_regenerated_stream(measured, hashes)
    measured['dv'][1] = 5.
    with pytest.raises(ValueError, match='four complete'):
        verify_regenerated_stream(measured, dict(hashes, extra='0' * 64))
    measured['dv'] = array('f', [4., 5., -6.])
    with pytest.raises(ValueError, match='float64'):
        verify_regenerated_stream(measured, hashes)


def test_oracle_forecast_is_saved_before_later_truth_is_opened():
    from lll.noisy_realization_attribution import score_saved_oracle

    saved = {}
    prediction = dict(times_s=[.5, 1.5], coordinates=[[1., 2., 3.],
                                                       [4., 5., 6.]])

    def later_truth():
        assert saved['forecast.json'] == prediction
        return [[1., 2., 3.], [4., 5., 6.]]

    result = score_saved_oracle(
        forecast=lambda: prediction, later_truth=later_truth,
        score=lambda forecast, truth: dict(epochs=len(truth),
                                           exact=forecast['coordinates'] == truth),
        save=lambda name, value: saved.setdefault(name, value))
    assert result == dict(epochs=2, exact=True)
    assert saved['scores.json'] == result
    saved.clear()

    def refused_save(name, value):
        raise OSError('forecast could not be saved')

    with pytest.raises(OSError, match='forecast could not be saved'):
        score_saved_oracle(forecast=lambda: prediction,
                           later_truth=lambda: pytest.fail('later truth opened'),
                           score=lambda forecast, truth: None, save=refused_save)


def test_oracle_orchestration_binds_input_before_forecast_and_truth():
    from lll.noisy_realization_attribution import (
        bound_streams, calculate_oracle, tasks)

    measured = {key: array('d', values) for key, values in dict(
        theta=[1., 2., 3.], dv=[4., 5., 6.], dt=[.005],
        times=[.5, 1.5]).items()}
    hashes = {key: sha256(value.tobytes()).hexdigest()
              for key, value in measured.items()}
    bindings = bound_streams(cases(), models=MODELS, policies=POLICIES)
    bindings[0]['hashes'] = hashes
    proof = dict(parent_recipe={'version': 'historical'}, bindings=bindings,
                 parent_manifest_sha256='a' * 64,
                 parent_summary_sha256='b' * 64)
    task = tasks(bindings)[0]
    saved = {}
    calls = []

    def construct(spec, historical, *, reserve):
        assert historical == proof['parent_recipe']
        assert spec == dict(model=MODELS[0], latitude_deg=55., profile=False,
                            policy_id=POLICIES[0], start=0)
        calls.append('construct')
        return measured

    def initial():
        assert saved['input-binding.json']['parent_manifest_sha256'] == 'a' * 64
        calls.append('initial')
        return {'known': 'start'}

    def forecast(material, known):
        assert material is measured and known == {'known': 'start'}
        calls.append('forecast')
        return dict(times_s=[.5, 1.5], coordinates=[[1., 2., 3.],
                                                    [4., 5., 6.]])

    def later_truth():
        assert 'forecast.json' in saved
        calls.append('truth')
        return [[1., 2., 3.], [4., 5., 6.]]

    result = calculate_oracle(
        task, proof, construct=construct, initial=initial,
        forecast=forecast, later_truth=later_truth,
        score=lambda prediction, truth: dict(exact=prediction['coordinates'] == truth),
        reserve_construction=lambda **work: None,
        save=lambda name, value: saved.setdefault(name, value))
    assert result == {'exact': True}
    assert calls == ['construct', 'initial', 'forecast', 'truth']


def test_oracle_orchestration_rejects_mutated_stream_before_truth():
    from lll.noisy_realization_attribution import (
        bound_streams, calculate_oracle, tasks)

    measured = {key: array('d', values) for key, values in dict(
        theta=[1., 2., 3.], dv=[4., 5., 6.], dt=[.005],
        times=[.5, 1.5]).items()}
    bindings = bound_streams(cases(), models=MODELS, policies=POLICIES)
    bindings[0]['hashes'] = {key: sha256(value.tobytes()).hexdigest()
                             for key, value in measured.items()}
    proof = dict(parent_recipe={}, bindings=bindings,
                 parent_manifest_sha256='a' * 64,
                 parent_summary_sha256='b' * 64)

    def mutating_forecast(material, known):
        material['dv'][0] += 1.
        return {'coordinates': []}

    with pytest.raises(ValueError, match='parent sensor hash'):
        calculate_oracle(
            tasks(bindings)[0], proof,
            construct=lambda spec, historical, reserve: measured,
            initial=lambda: {}, forecast=mutating_forecast,
            later_truth=lambda: pytest.fail('later truth opened'),
            score=lambda prediction, truth: None,
            reserve_construction=lambda **work: None,
            save=lambda name, value: None)


def test_oracle_orchestration_rejects_incomplete_parent_before_construction():
    from lll.noisy_realization_attribution import (
        bound_streams, calculate_oracle, tasks)

    bindings = bound_streams(cases(), models=MODELS, policies=POLICIES)
    with pytest.raises(ValueError, match='closed parent recipe and stream proof'):
        calculate_oracle(
            tasks(bindings)[0],
            dict(parent_recipe={}, bindings=bindings,
                 parent_manifest_sha256='a' * 64),
            construct=lambda *args, **kwargs: pytest.fail('construction began'),
            initial=lambda: None, forecast=lambda material, known: None,
            later_truth=lambda: None, score=lambda prediction, truth: None,
            reserve_construction=lambda **work: None,
            save=lambda name, value: None)


def test_oracle_value_forecast_reproduces_known_correction_truth(tmp_path):
    from lll.noisy_realization_attribution import oracle_value_forecast
    import numpy as np
    from lll.airquantumgrav_noisy_study import recipe as parent_recipe
    from lll.airquantumgrav_truth import truth
    from lll.airquantumgrav_observation_truth import observe, start, receiver_samples
    from lll.airquantumgrav_geographic_controls import construct, position_errors
    from lll.ilvis0_exploratory import load_kernel

    rate_times = np.arange(1201) / 300.
    queries = np.array([.5, 1.5, 2.5, 3.5])
    kernel, _ = load_kernel(tmp_path, gravity_anchor_height_m=1500.)
    for model in MODELS:
        for profile in (False, True):
            removal = .35 if profile else 0.
            sign = -1 if profile else 1
            arguments = dict(model=model, latitude_deg=55., pattern='fast',
                             removal=removal, height_profile='climb',
                             gravity_model='inverse_square_height')
            geometric = truth(model, rate_times, latitude_deg=55.,
                              pattern='fast', removal=removal,
                              height_profile='climb',
                              gravity_model='inverse_square_height')
            raw = observe(geometric, sign=sign)
            raw['times'] = rate_times
            increments = construct(raw, method='linear_points', rate_hz=300,
                                   reserve=lambda **work: None)
            initial = start(truth(model, np.array([0.]), latitude_deg=55.,
                                  pattern='fast', removal=removal,
                                  height_profile='climb',
                                  gravity_model='inverse_square_height'),
                            model=model, sign=sign)
            material = dict(**increments, times=queries)
            charges = []
            prediction = oracle_value_forecast(
                material, initial, model=model, profile=profile,
                limits=parent_recipe()['limits'], kernel=kernel,
                reserve=lambda **work: charges.append(work))
            answer = receiver_samples(times=queries, sign=sign, **arguments)
            error = position_errors(prediction, answer, model=model)
            assert np.max(np.linalg.norm(error, axis=1)) < 1.
            assert charges == [dict(native_calls=1,
                                    packet_visits=1200 * len(queries))]


def test_oracle_binding_reads_closed_parent_and_rejects_changed_stream(monkeypatch):
    from lll.noisy_realization_attribution import collect_parent_bindings, recipe
    from lll.studies import closed

    rows = cases()
    design = recipe()
    parent_recipe = dict(models=design['models'], profiles=design['profiles'],
                         policies=design['policies'], starts=2,
                         duration_s=design['duration_s'], rate_hz=design['rate_hz'],
                         queries=design['queries'], noise=design['noise'],
                         version='esa-noisy-prediction-v1', pattern='fast',
                         method='linear_points', height_profile='climb',
                         gravity_model='inverse_square_height',
                         query_start_s=.5, query_step_s=1., retries=0)
    state = {'closed': 0, 'rows': rows}

    class Parent:
        def __init__(self, root, path):
            assert path == design['parent']
            self.tasks = {row['identity']: dict(payload=row) for row in state['rows']}
            self.rows = {row['identity']: {} for row in state['rows']}
            self.completion = dict(state='complete', manifest_sha256='a' * 64,
                                   summary_sha256='b' * 64)

        def input(self, name):
            assert name == 'recipe'
            return parent_recipe

        def artifact(self, identity, name):
            assert name == 'input-binding.json'
            row = next(row for row in state['rows'] if row['identity'] == identity)
            return dict(full_array_sha256=row['hashes'])

        def read(self, name, expected=None):
            if name == 'evidence-receipt.json':
                return dict(artifacts={'artifacts/publication/verified-report.json':
                                       'c' * 64})
            assert name == 'artifacts/publication/verified-report.json'
            assert expected == 'c' * 64
            return dict(verified=True, total=24, complete=24,
                        numerically_converged=24, accurate=0,
                        manifest_sha256='a' * 64, summary_sha256='b' * 64)

        def envelope(self, identity):
            return dict(result=dict(converged=state.get('converged', True),
                                    accuracy_all_sections=False, passed=False))

        def close(self):
            state['closed'] += 1

    monkeypatch.setattr(closed, 'ClosedStudy', Parent)
    result = collect_parent_bindings('/repository')
    assert len(result['bindings']) == 6
    assert result['parent_recipe'] == parent_recipe
    assert result['parent_manifest_sha256'] == 'a' * 64
    assert state['closed'] == 1
    parent_recipe['gravity_model'] = 'constant'
    with pytest.raises(ValueError, match='exact closed historical noisy study'):
        collect_parent_bindings('/repository')
    assert state['closed'] == 2
    parent_recipe['gravity_model'] = 'inverse_square_height'
    state['rows'] = copy.deepcopy(rows)
    state['rows'][3]['hashes']['dt'] = 'f' * 64
    with pytest.raises(ValueError, match='same saved sensor stream'):
        collect_parent_bindings('/repository')
    assert state['closed'] == 3
    state['rows'] = rows
    state['converged'] = False
    with pytest.raises(ValueError, match='original numerical and accuracy labels'):
        collect_parent_bindings('/repository')
    assert state['closed'] == 4


def test_oracle_preparation_requires_qualification_before_writing(tmp_path):
    from lll.noisy_realization_attribution import prepare

    with pytest.raises(ValueError, match='source-bound qualification'):
        prepare(tmp_path, qualification=None)
    with pytest.raises(ValueError, match='recovery qualification'):
        prepare(tmp_path, qualification='unopened-request.json',
                recovery_qualification=None)
    assert not tuple(tmp_path.iterdir())


def test_oracle_preparation_binds_parent_streams_and_finite_tasks(tmp_path, monkeypatch):
    import json
    from lll import noisy_realization_attribution as module
    from lll.compute_budget import environment as thread_environment
    from lll.studies import runtime
    from lll.studies.qualification import request

    source = 'analysis/lll/noisy_realization_attribution.py'
    source_path = tmp_path / source
    source_path.parent.mkdir(parents=True)
    source_path.write_text('frozen test adapter')
    env = dict(numerical_environment=thread_environment(workers=2, threads=1))
    monkeypatch.setattr(module, 'qualification_sources', lambda root: [source],
                        raising=False)
    monkeypatch.setattr(module, 'environment', lambda: env, raising=False)
    monkeypatch.setattr(module, 'required_tests', lambda: ['stream_qualified'],
                        raising=False)
    monkeypatch.setattr(module, 'recovery_sources', lambda root: [source],
                        raising=False)
    monkeypatch.setattr(module, 'recovery_tests', lambda: ['reboot_qualified'],
                        raising=False)
    monkeypatch.setattr(module, 'recovery_environment', lambda: env,
                        raising=False)
    bound = module.bound_streams(cases(), models=MODELS, policies=POLICIES)
    proof = dict(parent_manifest_sha256='a' * 64,
                 parent_summary_sha256='b' * 64, bindings=bound)
    monkeypatch.setattr(module, 'collect_parent_bindings', lambda root: proof)
    monkeypatch.setattr(runtime.Definition, 'prepare',
                        lambda self, root: dict(limits={}, allocation={}))
    request(tmp_path, sources=[source], environment=env,
            output='qualification.json', report='qualification.xml')
    (tmp_path / 'qualification.xml').write_text(
        '<testsuite tests="1"><testcase name="stream_qualified"/></testsuite>')
    request(tmp_path, sources=[source], environment=env,
            output='recovery.json', report='recovery.xml')
    (tmp_path / 'recovery.xml').write_text(
        '<testsuite tests="1"><testcase name="reboot_qualified"/></testsuite>')

    result = module.prepare(tmp_path, qualification='qualification.json',
                            recovery_qualification='recovery.json')
    assert result['identities'] == 6
    definition = json.loads(next((tmp_path / 'data').glob('*/*-inputs/definition.json')).read_text())
    assert len(definition['tasks']) == 6
    assert sum(task['limits']['native_calls'] for task in definition['tasks']) == 6
    assert definition['workers'] == 2 and definition['threads'] == 1
    proof_path = tmp_path / definition['inputs']['parent-proof']
    assert json.loads(proof_path.read_text()) == proof
    assert 'recovery-qualification-request' in definition['inputs']
    assert 'recovery-qualification-report' in definition['inputs']
    assert json.loads((tmp_path / definition['inputs']['recipe']).read_text())[
        'recovery']['max_attempts_per_task'] == 3
