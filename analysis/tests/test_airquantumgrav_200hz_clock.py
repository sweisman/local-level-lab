# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generated 200 Hz clock support, separate from the original ESA controls."""
import numpy as np
import pytest
from test_airquantumgrav_prediction import kernels


def short_recipe():
    from lll.airquantumgrav_training_controls import recipe
    return dict(recipe(), rate_hz=200, duration_s=2., queries=9,
                query_start_s=.1, query_step_s=.2, maximum_evaluations=8)


def test_generated_200hz_increments_have_exact_nominal_period_and_charges():
    from lll.airquantumgrav_training_controls import generated_training
    charges = []
    material = generated_training(
        dict(model='sphere_rotating', latitude_deg=55., profile=False, start=0),
        short_recipe(), reserve=lambda **work: charges.append(work),
        height_profile='climb', gravity_model='inverse_square_height')
    assert material['theta'].shape == material['dv'].shape == (400, 3)
    assert np.array_equal(material['dt'], np.full(400, .005))
    assert sum(work.get('constructed_intervals', 0) for work in charges) == 400
    assert sum(work.get('generated_samples', 0) for work in charges) == 407


def test_generated_prediction_forwards_declared_clock_before_truth():
    from lll.airquantumgrav_noisy_inputs import construct, noise_settings
    from lll.generated_prediction import calculate
    spec = dict(model='sphere_rotating', latitude_deg=55., profile=False,
                start=0, policy_id='reported-short-v1')
    r = dict(short_recipe(), noise=noise_settings(), clock='nominal_200Hz')
    material = construct(spec, r, reserve=lambda **work: None)
    seen = []

    def fit(**kwargs):
        seen.append(kwargs.get('clock'))
        raise RuntimeError('clock dispatch reached before later truth')

    def forbidden_truth(times):
        raise AssertionError('later truth opened')

    with pytest.raises(RuntimeError, match='clock dispatch'):
        calculate(spec, r, material=material, train_and_forecast=fit,
                  kernel_factory=lambda anchor: (None, None, {}),
                  reserve=lambda **work: None,
                  reserve_construction=lambda **work: None,
                  save=lambda name, value: None, truth=forbidden_truth,
                  check_continue=lambda: None)
    assert seen == ['nominal_200Hz']


@pytest.mark.parametrize('clock', ['header_elapsed', 'nominal_200Hz'])
def test_real_native_training_receives_declared_200hz_clock(clock, kernels,
                                                             monkeypatch):
    from lll import ilvis0_training_forecast as engine
    from lll.airquantumgrav_prediction import train_and_forecast
    from lll.airquantumgrav_training_controls import generated_training
    from lll.airquantumgrav_weighted_controls import fixture_rows

    r = short_recipe()
    material = generated_training(
        dict(model='sphere_rotating', latitude_deg=55., profile=False, start=0),
        r, reserve=lambda **work: None, height_profile='climb',
        gravity_model='inverse_square_height')
    rows = fixture_rows(material['training_gps'],
                        material['times'][:material['training_epochs']])
    seen = []
    original = engine.training_problem

    def tracked(*args, **kwargs):
        seen.append(kwargs['clock'])
        return original(*args, **kwargs)

    monkeypatch.setattr(engine, 'training_problem', tracked)
    saved = {}
    result = train_and_forecast(
        theta=material['theta'], dv=material['dv'], dt=material['dt'],
        times=material['times'], training_rows=rows, time_origin_s=0.,
        model='sphere_rotating', profile=False, policy_id='reported-short-v1',
        start=0, limits=r['limits'], maximum_evaluations=8,
        maximum_interval_s=.0075, kernel=kernels[0],
        tangent_kernel=kernels[1], reserve=lambda **work: None,
        save=lambda name, value: saved.__setitem__(name, value),
        check_continue=lambda: None, clock=clock)
    assert seen == [clock]
    assert saved['forecast.json']['prediction_receiver_positions_used'] is False
    assert result['fit']['evaluations'] <= 8


def test_generated_packet_jitter_changes_forecast_without_changing_measurements(kernels):
    from lll.airquantumgrav_clock_disturbance import apply_header_timestamp_jitter
    from lll.airquantumgrav_noisy_inputs import construct, noise_settings
    from lll.airquantumgrav_prediction import train_and_forecast
    from lll.airquantumgrav_training_controls import _spec
    from lll.airquantumgrav_observation_truth import receiver_samples
    from lll.generated_prediction import calculate

    spec = dict(model='sphere_rotating', latitude_deg=55., profile=False,
                start=0, policy_id='reported-short-v1')
    r = dict(short_recipe(), noise=noise_settings())
    nominal = construct(spec, r, reserve=lambda **work: None)
    header = apply_header_timestamp_jitter(nominal, amplitude_s=.0004,
                                           cycles=19)
    arguments, sign = _spec({key: value for key, value in spec.items()
                             if key != 'policy_id'})

    def truth(times):
        return receiver_samples(times=times, sign=sign, **arguments,
                                height_profile='climb',
                                gravity_model='inverse_square_height')

    outputs = []
    for material, clock in ((nominal, 'nominal_200Hz'),
                            (header, 'header_elapsed')):
        saved = {}
        calculate(spec, dict(r, clock=clock), material=material,
                  train_and_forecast=train_and_forecast,
                  kernel_factory=lambda anchor: (*kernels, {'anchor': anchor}),
                  reserve=lambda **work: None,
                  reserve_construction=lambda **work: None,
                  save=lambda name, value: saved.__setitem__(name, value),
                  truth=truth, check_continue=lambda: None)
        outputs.append(saved)
    a, b = outputs
    assert a['training-receiver.json'] == b['training-receiver.json']
    assert a['input-binding.json']['full_array_sha256']['theta'] == b['input-binding.json']['full_array_sha256']['theta']
    assert a['input-binding.json']['full_array_sha256']['dv'] == b['input-binding.json']['full_array_sha256']['dv']
    assert a['input-binding.json']['full_array_sha256']['dt'] != b['input-binding.json']['full_array_sha256']['dt']
    assert a['forecast.json']['coordinates'] != b['forecast.json']['coordinates']
