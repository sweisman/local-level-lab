# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll.esa_changing_drift_transfer import POLICY, operator
from lll.esa_no_snap_ablation import no_snap_operator


def test_only_the_integrated_changing_jerk_variance_is_removed():
    times = np.array([0., .37, 1.24, 2.5, 6., 15., 20.])
    weights = np.broadcast_to(np.eye(3)*.03, (len(times), 3, 3))
    original = operator(times, weights).conditional_marginals()
    changed = no_snap_operator(times, weights).conditional_marginals()
    # The squared position kernel of the removed driver is t^6 / 36.
    expected = POLICY['snap_psd']*times**7/(7*36)
    np.testing.assert_allclose(original['covariance']-changed['covariance'],
                               expected[:, None, None]*np.eye(3), atol=1e-12)
    np.testing.assert_array_equal(original['mean'], changed['mean'])
