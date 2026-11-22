# SPDX-License-Identifier: AGPL-3.0-or-later
import math

import numpy as np
from scipy.integrate import quad

from lll.esa_changing_drift_transfer import POLICY, operator
from lll.esa_drift_correction_audit import decompose


def test_innovations_and_driver_split_match_an_independent_dense_covariance():
    times = np.array([0., .47, 1.41, 2.66, 3.49, 5.3])
    cut = 4
    earlier, later = times[:cut], times[cut:]
    loading = np.repeat(np.array([[[.05, 0., 0.], [.01, .04, 0.], [.01, -.01, .03]]]), len(times), axis=0)
    loading *= np.linspace(.8, 1.2, len(times))[:, None, None]
    residual = np.random.default_rng(608).normal(0., .07, size=(cut, 3))
    spec = {'inertial_acceleration': (1, 'acceleration_psd'), 'inertial_jerk': (2, 'jerk_psd'),
            'inertial_snap': (3, 'snap_psd'), 'receiver_walk': (0, 'receiver_random_walk_psd')}
    blocks = {name: POLICY[key]*np.kron(np.array([
        [quad(lambda u: ((a-u)*(b-u))**order/math.factorial(order)**2, 0., min(a, b))[0]
         for b in earlier] for a in times]), np.eye(3)) for name, (order, key) in spec.items()}
    blocks['receiver_offset'] = np.tile(np.eye(3)*POLICY['initial_receiver_offset_std_m']**2,
                                        (len(times), cut))
    white = np.zeros((3*len(times), 3*cut))
    for i, matrix in enumerate(loading[:cut]):
        block = slice(3*i, 3*i+3)
        white[block, block] = matrix @ matrix.T
    blocks['receiver_white'] = white
    total = sum(blocks.values())
    precision_residual = np.linalg.solve(total[:3*cut], residual.ravel())
    actual = decompose(operator(times, loading), earlier, later, loading[:cut], residual)
    for name, block in blocks.items():
        contribution = block @ precision_residual
        np.testing.assert_allclose(actual['energies'][name], precision_residual @ contribution[:3*cut], atol=1e-11)
        np.testing.assert_allclose(actual['future_means'][name].ravel(), contribution[3*cut:], atol=1e-11)
    np.testing.assert_allclose(actual['innovations'].ravel() @ actual['innovations'].ravel(),
                               residual.ravel() @ precision_residual, atol=1e-10)
