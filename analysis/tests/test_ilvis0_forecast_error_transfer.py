# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def test_elapsed_time_drift_transfers_to_new_cut_without_later_errors():
    from lll.ilvis0_forecast_error_transfer import predict_error

    times = np.array([1., 2., 3.])
    offset, slope = np.array([2., -1., 7.]), np.array([1.,2.,-3.])
    result, fit = predict_error(times, offset+times[:,None]*slope, [1.,3.,4.])
    np.testing.assert_allclose(result, offset+np.array([1.,3.,4.])[:,None]*slope)
    np.testing.assert_allclose(fit['rate_mps'], slope)


def test_fallback_choice_uses_cost_but_preserves_failed_status():
    from lll.ilvis0_forecast_error_transfer import choose_start

    a = dict(training_cost=1., start=0, passed=False)
    b = dict(training_cost=2., start=1, passed=True)
    assert choose_start([a,b]) is b
    b['passed'] = False
    assert choose_start([b,a]) is a
    assert not a['passed']


def test_invalid_elapsed_time_cannot_define_a_transfer():
    from lll.ilvis0_forecast_error_transfer import predict_error

    with pytest.raises(ValueError, match='elapsed'):
        predict_error([1.,1.,2.], np.zeros((3,3)), [1.,2.])


def test_height_only_correction_leaves_north_and_east_unchanged():
    from lll.ilvis0_forecast_error_transfer import predict_error

    change, _ = predict_error([1.,2.], [[2.,3.,4.],[3.,4.,5.]], [1.,2.,3.], height_only=True)
    np.testing.assert_array_equal(change, [[0.,0.,4.],[0.,0.,5.],[0.,0.,6.]])
