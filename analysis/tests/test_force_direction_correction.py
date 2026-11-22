# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from lll.force_accel_calibration import normalize_with_tangent
from lll.force_direction_alignment import fit_unit_rotation, unit_vectors
from lll.force_direction_correction import correct_direction_fit
from lll.gyro_force_tangent import corrected_transport


@pytest.mark.parametrize('active', [False, True])
def test_exact_bounded_correction_recovers_generated_direction_optimum(active):
    rng = np.random.default_rng(565)
    theta = rng.normal(scale=.06, size=(25, 3))
    force = rng.normal(size=theta.shape) + [0., 0., 10.]
    dt = rng.uniform(.1, .2, len(theta))
    limits = np.array([[.1]*3, [.02]*3, [.002]*3, [.01]*3])
    truth = rng.uniform(-.3, .3, 12)
    if active:
        truth[1] = 1.
    ab, ag, gb, gg = truth.reshape(4, 3)*limits
    q = Rotation.identity()
    known = []
    for raw, f, interval in zip(theta, force, dt, strict=True):
        vector = (raw-interval*gb)/(1.+gg)
        known.append((q*Rotation.from_rotvec(vector/2.)).apply((f-ab)/(1.+ag)))
        q *= Rotation.from_rotvec(vector)
    reference = unit_vectors(Rotation.from_rotvec([.1, -.4, .2]).apply(known))

    def evaluate(point):
        mapped, jac = corrected_transport(theta, force, dt, point, limits)
        u, d = normalize_with_tangent(mapped, jac)
        _, rotation = fit_unit_rotation(reference, u)
        aligned = reference @ rotation.T
        return u-aligned, d, aligned

    start = np.clip(truth-.04, -1., 1.)
    result = correct_direction_fit(evaluate, start, maximum_calls=6)
    assert result['converged'] and result['training_evaluations'] <= 6
    assert result['exact_training_loss'] < 1e-12
    assert all(abs(x) <= 1. for x in result['normalized_calibration'])
    losses = [row['loss'] for row in result['step_history'] if row['accepted']]
    assert all(b < a for a, b in zip(losses, losses[1:]))


def test_budget_exhaustion_preserves_nonpass_and_first_point():
    def evaluate(point):
        aligned = np.eye(3)
        residual = aligned*point[0]
        return residual, aligned[:, :, None], aligned

    result = correct_direction_fit(evaluate, [.1], maximum_calls=1)
    assert result['normalized_calibration'] == [.1]
    assert not result['converged'] and result['training_evaluations'] == 1
