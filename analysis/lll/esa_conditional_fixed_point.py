# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reusable fixed-parameter, earlier-only conditional forecast checks."""


def check_nominal_replay(generated, saved, fit, *, training_epochs, times):
    """Require the new native path to reproduce the sealed uncorrected path."""
    import numpy as np

    if (type(training_epochs) is not int or training_epochs < 2 or
            fit.get('converged') is not True or
            generated.get('training_epochs') != training_epochs or
            generated.get('prediction_receiver_positions_used') is not False or
            generated.get('continuous_propagation_without_gps_reset') is not True or
            generated.get('training_residual_subtraction') !=
                'native-before-binary64-cast' or
            saved.get('training_epochs') != training_epochs or
            saved.get('prediction_receiver_positions_used') is not False or
            generated.get('active_parameters') != fit.get('active_parameters') or
            saved.get('active_parameters') != fit.get('active_parameters') or
            generated.get('normalized_parameters') !=
                fit.get('normalized_parameters') or
            generated.get('prediction_epochs') != saved.get('prediction_epochs')):
        raise ValueError('saved fit and nominal replay metadata differ')
    a, b = np.asarray(generated.get('coordinates')), np.asarray(saved.get('coordinates'))
    if a.shape != b.shape or not np.array_equal(a, b):
        raise ValueError('saved nominal route differs from native replay')
    if not np.array_equal(np.asarray(times), np.asarray(saved.get('times_s'))):
        raise ValueError('saved nominal forecast time grid differs')
    difference = np.asarray(generated.get('training_coordinate_difference'))
    if (difference.shape != (training_epochs, 3) or
            not np.all(np.isfinite(difference))):
        raise ValueError('complete native-before-cast early residual required')
    return True


def nominal_replay_receipt(generated, *, training_epochs):
    """Serialize only hashes of the matched native route and early residual."""
    import hashlib
    import numpy as np

    coordinates = np.asarray(generated['coordinates'], dtype='<f8')
    difference = np.asarray(
        generated['training_coordinate_difference'], dtype='<f8')
    if (coordinates.ndim != 2 or coordinates.shape[1] != 3 or
            difference.shape != (training_epochs, 3) or
            not np.all(np.isfinite(coordinates)) or
            not np.all(np.isfinite(difference))):
        raise ValueError('complete finite replay arrays required')
    return dict(version='esa-nominal-replay-receipt-v1',
        forecast_epochs=int(len(coordinates)),
        training_epochs=training_epochs,
        coordinates_sha256=hashlib.sha256(coordinates.tobytes()).hexdigest(),
        early_difference_sha256=hashlib.sha256(difference.tobytes()).hexdigest(),
        exact_saved_coordinates=True, later_receiver_values_used=False)


def condition_saved_point(operator, generated, *, training_epochs,
                          expected_cost, expected_logdet):
    """Replay the weighted training cost, then predict without later reports."""
    from .esa_conditional_forecast_v2_study import fixed_receiver_mean
    from .esa_conditional_forecast_v3_study import replay_training_prefix

    prefix = replay_training_prefix(
        operator, generated, training_epochs=training_epochs,
        expected_cost=expected_cost, expected_logdet=expected_logdet)
    fixed = fixed_receiver_mean(
        operator, generated, training_epochs=training_epochs)
    return dict(prefix=prefix, fixed=fixed)
