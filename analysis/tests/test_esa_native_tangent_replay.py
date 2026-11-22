# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_native_tangent_replay import checked_jacobian


def test_replay_preserves_complete_derivative_with_exact_reference():
    design = np.arange(12., dtype=float).reshape(6, 2)
    saved = dict(coordinates=[[.1, .2, 500.], [.2, .3, 500.]],
                 training_coordinate_difference=[[0., 0., .01]],
                 active_parameters=['bias', 'gain'], training_epochs=1,
                 prediction_epochs=1, prediction_receiver_positions_used=False,
                 continuous_propagation_without_gps_reset=True)
    prediction = dict(saved, jacobian=design)
    np.testing.assert_array_equal(checked_jacobian(prediction, saved), design)


@pytest.mark.parametrize('changed,value', [
    ('coordinates', [[.1, .2, 500.], [.2, .3, 501.]]),
    ('training_coordinate_difference', [[0., 0., .02]]),
    ('active_parameters', ['gain', 'bias']),
    ('prediction_receiver_positions_used', True),
    ('jacobian', np.zeros((6, 1))),
    ('jacobian', np.full((6, 2), np.inf)),
])
def test_replay_rejects_changed_reference_or_incomplete_derivatives(changed, value):
    saved = dict(coordinates=[[.1, .2, 500.], [.2, .3, 500.]],
                 training_coordinate_difference=[[0., 0., .01]],
                 active_parameters=['bias', 'gain'], training_epochs=1,
                 prediction_epochs=1, prediction_receiver_positions_used=False,
                 continuous_propagation_without_gps_reset=True)
    prediction = dict(saved, jacobian=np.ones((6, 2)))
    with pytest.raises(ValueError):
        checked_jacobian(dict(prediction, **{changed: value}), saved)
