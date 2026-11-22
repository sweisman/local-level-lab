"""Guards for the fixed-parameter ESA conditional forecast study."""
import numpy as np
import pytest


def test_conditional_study_has_one_early_only_fixed_task():
    from lll.esa_conditional_forecast_study import INPUT_KEYS, accepted_input_keys, tasks

    assert 'scoring' not in INPUT_KEYS
    assert 'weighted-fit' in INPUT_KEYS
    assert 'weighted-forecast' in INPUT_KEYS
    assert 'weighted-error-operator' in INPUT_KEYS
    assert len(tasks()) == 1
    assert tasks()[0]['payload']['optimize'] is False
    assert tasks()[0]['payload']['target'] == 'receiver_measurement'
    assert tasks()[0]['limits']['native_calls'] == 600_000
    assert tasks()[0]['limits']['packet_visits'] == 6_000_000_000
    assert accepted_input_keys(INPUT_KEYS) == INPUT_KEYS
    with pytest.raises(ValueError,match='exact'):
        accepted_input_keys((*INPUT_KEYS,'scoring'))


def test_conditional_study_requires_source_qualification(tmp_path):
    from lll.esa_conditional_forecast_study import prepare

    with pytest.raises(ValueError,match='qualification'):
        prepare(tmp_path)


def test_conditional_qualification_rejects_unguarded_numerical_environment():
    from lll.esa_conditional_forecast_study import require_guarded_environment

    with pytest.raises(ValueError,match='guarded'):
        require_guarded_environment({'numerical_environment':
                                     {'OPENBLAS_NUM_THREADS': None}})


def test_conditional_study_requires_exact_saved_nominal_forecast():
    from lll.esa_conditional_forecast_study import check_saved_forecast

    generated = dict(coordinates=np.array([[.1,.2,3.],[.3,.4,5.]]),
                     normalized_parameters=np.array([.25]),
                     active_parameters=['x'],
                     training_coordinate_difference=np.array([[.01,.02,.03]]),
                     training_residual_subtraction='native-before-binary64-cast',
                     frozen_error_model='sphere_rotating',
                     error_training_configuration='abc',
                     training_epochs=1,prediction_epochs=1,
                     prediction_receiver_positions_used=False,
                     continuous_propagation_without_gps_reset=True)
    saved = dict(coordinates=[[.1,.2,3.],[.3,.4,5.]],
                 normalized_parameters=[.25], active_parameters=['x'],
                 training_coordinate_difference=[[.01,.02,.03]],
                 training_residual_subtraction='native-before-binary64-cast',
                 frozen_error_model='sphere_rotating',
                 error_training_configuration='abc',
                 training_epochs=1,prediction_epochs=1,
                 prediction_receiver_positions_used=False)
    assert check_saved_forecast(generated,saved,training_epochs=1)
    changed=dict(saved,coordinates=[[.1,.2,3.],[.3,.4,6.]])
    with pytest.raises(ValueError,match='saved nominal'):
        check_saved_forecast(generated,changed,training_epochs=1)
    changed=dict(saved,prediction_receiver_positions_used=True)
    with pytest.raises(ValueError,match='saved nominal'):
        check_saved_forecast(generated,changed,training_epochs=1)
