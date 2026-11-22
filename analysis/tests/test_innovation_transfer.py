# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.innovation_transfer import diagnose, estimates, score


def test_covariance_estimated_from_earlier_errors_is_frozen_for_later_errors():
    earlier = np.array([[1., 0., 2.], [0., 3., 1.], [2., 1., 0.], [0., 0., 2.]])
    weights = estimates(earlier)
    np.testing.assert_allclose(weights['full'], earlier.T@earlier/len(earlier))
    assert score(earlier, weights['full']) == pytest.approx(1.)
    assert score(3*earlier, weights['full']) == pytest.approx(9.)
    assert score(3*earlier, weights['per_channel']) == pytest.approx(9.)


def test_fixed_block_and_peak_accounting_preserve_signed_bias():
    values = np.column_stack(([1.,2.,3.,4.], [-2.,-2.,-2.,-2.], [1.,0.,0.,3.]))
    result = diagnose(values, blocks=2, peaks=1)
    np.testing.assert_allclose(result['block_energy_shares'],
        [[5/30, .5, .1], [25/30, .5, .9]])
    np.testing.assert_allclose(result['largest_epoch_energy_share'], [16/30, .25, .9])
    np.testing.assert_allclose(result['mean_fraction_of_energy'], [25/30, 1., .4])
    assert result['lag_one_centered'][1] is None
