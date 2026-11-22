# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np
import pytest

from lll.esa_girafe_force_error_law import fit_laws, score_window


def test_window_level_error_increases_uncertainty_of_a_later_window_mean():
    fluctuation = np.array([0.02, -0.04, 0.01, 0.01])
    training = np.array([-2.0, -1.0, 1.0, 2.0])[:, None]+fluctuation
    laws = fit_laws(training)
    assert laws['iid']['mean'] == laws['correlated']['mean'] == pytest.approx(0.)
    assert laws['correlated']['window_variance'] > 3.
    later = np.full(4, 2.)
    iid = score_window(later, laws['iid'])
    correlated = score_window(later, laws['correlated'])
    assert iid['mean_supported'] is False
    assert correlated['mean_supported'] is True
    assert correlated['log_score_per_support'] < iid['log_score_per_support']


def test_constant_training_cannot_supply_an_error_law():
    with pytest.raises(ValueError, match='positive'):
        fit_laws(np.full((4, 16), 1.))


def test_independent_forecast_includes_finite_training_mean_uncertainty():
    training = np.arange(24, dtype=float).reshape(4, 6)
    law = fit_laws(training)['iid']
    variance = np.var(training, ddof=1)
    expected = variance*np.eye(6)+variance/training.size
    np.testing.assert_allclose(law['covariance'], expected)
