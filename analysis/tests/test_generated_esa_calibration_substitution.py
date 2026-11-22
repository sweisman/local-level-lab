"""Fixed known-sensor substitution without refitting other parameters."""

import numpy as np
import pytest


def test_four_candidates_change_only_the_declared_blocks():
    from lll.generated_esa_calibration_substitution import candidates

    names = ['gyro_bias_x', 'gyro_gain_x', 'accel_bias_x', 'accel_gain_x',
             'gravity_delta', 'time_offset', 'position_x']
    fit = np.array([.1, -.2, .3, -.4, .5, -.6, .7])
    limits = {name: 2. for name in names}
    truth = {name: 1. for name in names[:-1]}
    result = candidates(fit, names, limits, truth)
    assert result['labels'] == ('baseline', 'sensor', 'gravity_clock', 'all14')
    np.testing.assert_allclose(result['points'][0], fit)
    np.testing.assert_allclose(result['points'][1],
                               [.5, .5, .5, .5, .5, -.6, .7])
    np.testing.assert_allclose(result['points'][2],
                               [.1, -.2, .3, -.4, .5, .5, .7])
    np.testing.assert_allclose(result['points'][3],
                               [.5, .5, .5, .5, .5, .5, .7])


def test_rejects_missing_truth_and_out_of_box_substitution():
    from lll.generated_esa_calibration_substitution import candidates

    with pytest.raises(ValueError):
        candidates([0.], ['gyro_bias_x'], {'gyro_bias_x': 1.}, {})
    with pytest.raises(ValueError):
        candidates([0.], ['gyro_bias_x'], {'gyro_bias_x': 1.},
                   {'gyro_bias_x': 2.})
