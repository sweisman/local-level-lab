"""Known parameters are passed through every native calibration coordinate."""

import numpy as np
import pytest


def test_sealed_oracle_case_uses_original_measured_stream_and_only_early_receiver(
        tmp_path, monkeypatch):
    from pathlib import Path
    import sys
    from lll.esa_fit_adjusted_control_report import _study
    from lll.esa_oracle_control import load_case
    from lll.studies.closed import load_python_reference
    from public_fixtures import isolate_frozen_source_reads

    root = Path(__file__).resolve().parents[2]
    study, _ = _study(root)
    try:
        isolate_frozen_source_reads(study, tmp_path, monkeypatch)
        for module_name in ('airquantumgrav_truth', 'airquantumgrav_observation_truth'):
            name = 'analysis/lll/' + module_name + '.py'
            sha = study.manifest['sources'][name]
            module = load_python_reference(study.read('source-freeze/' + name, sha, raw=True),
                name='lll._sealed_oracle_' + module_name + '_' + sha, sha256=sha)
            monkeypatch.setitem(sys.modules, 'lll.' + module_name, module)
    finally:
        study.close()

    case = load_case(root, 'increment')
    assert case['theta'].shape == (270000, 3)
    assert case['dv'].shape == (270000, 3)
    assert case['dt'].shape == (270000,)
    assert case['times'].shape == (900,)
    assert case['earlier_coordinates'].shape == (2, 3)
    assert case['training_epochs'] == 600
    assert case['known_state']['corrections_supplied_not_fitted'] is True
    assert case['parent_manifest_sha256']
    assert case['parent_input_sha256']


def test_sealed_oracle_case_rejects_an_unlisted_law():
    from pathlib import Path
    from lll.esa_oracle_control import load_case

    with pytest.raises(ValueError, match='declared generated law'):
        load_case(Path('.'), 'unknown')


def test_oracle_problem_requires_true_state_and_complete_prefix():
    from lll.esa_oracle_control import oracle_problem

    theta = np.zeros((400, 3))
    dv = np.zeros((400, 3))
    dt = np.full(400, .005)
    times = np.array([.1, .3, .5])
    with pytest.raises(ValueError, match='known state'):
        oracle_problem(theta, dv, dt, times, np.zeros((2, 3)),
            {}, {'time_offset':.01}, lambda *args:0, rate_hz=200)


def test_clean_known_calibration_forecasts_short_generated_trajectory(tmp_path):
    import hashlib
    from lll.airquantumgrav_training_controls import generated_training
    from lll.airquantumgrav_observation_truth import receiver_samples, start
    from lll.airquantumgrav_truth import truth
    from lll.esa_fit_adjusted_control_study import preflight_recipe
    from lll.esa_fit_adjusted_forecast_report import position_errors_neu
    from lll.esa_oracle_control import oracle_problem
    from lll.ilvis0_forecast import native_forecast
    from lll.ilvis0_wide_tangent import load

    recipe = preflight_recipe()
    spec = dict(model='sphere_rotating',latitude_deg=55.,profile=False,start=0)
    clean = generated_training(spec, recipe, reserve=lambda **work:None,
        height_profile='climb', gravity_model='inverse_square_height')
    arguments = dict(model='sphere_rotating', latitude_deg=55.,
        pattern='fast', removal=0., height_profile='climb',
        gravity_model='inverse_square_height')
    initial = start(truth(times=np.array([0.]), **arguments),
        model='sphere_rotating',sign=1)
    source = __import__('pathlib').Path('analysis/lll/ilvis0_tangent.cpp')
    tangent, _ = load(tmp_path,
        expected_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        gravity_anchor_height_m=float(clean['training_gps'][0, 2]))
    problem, point = oracle_problem(clean['theta'], clean['dv'], clean['dt'],
        clean['times'], clean['training_gps'][:2], initial,
        recipe['limits'], tangent, rate_hz=200)
    forecast = native_forecast(problem, point, 'sphere_rotating',
        theta=clean['theta'],dv=clean['dv'],dt=clean['dt'],
        times=clean['times'],maximum_interval_s=1.5/200,
        reserve=lambda **work:None)
    answer = receiver_samples(times=clean['times'],sign=1,**arguments)
    errors = position_errors_neu(forecast['coordinates'], answer['coordinates'])
    assert np.max(np.linalg.norm(errors, axis=1)) < .01
