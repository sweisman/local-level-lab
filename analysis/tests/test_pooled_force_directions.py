# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from lll.pooled_force_directions import pooled_alignment, pooled_tangent, source_scores


def test_duplicate_identical_velocity_paths_do_not_increase_mean_loss_weight():
    target = np.eye(3)
    measured = Rotation.from_rotvec([.05, .1, .23]).apply(target)
    measured[2] = Rotation.from_rotvec([.02, 0., 0.]).apply(measured[2])
    rotation, once, _ = pooled_alignment(target[None, ...], measured)
    duplicate, twice, _ = pooled_alignment(np.stack([target, target]), measured)
    np.testing.assert_allclose(rotation, duplicate, atol=1e-14)
    assert np.mean(once**2) == pytest.approx(np.mean(twice**2), abs=1e-15)
    _, derivative, _ = pooled_tangent(np.stack([target, target]), measured, np.zeros((3, 3, 12)))
    assert derivative.shape == (6, 3, 12)


def test_later_and_omitted_directions_do_not_choose_shared_training_alignment():
    target = np.vstack((np.eye(3), [1., 0., 0.]))
    measured = Rotation.from_rotvec([.05, .1, .23]).apply(target)
    alpha = target.copy()
    beta = target.copy()
    beta[3] *= -1.
    third = target.copy()
    third[:3] *= -1.
    earlier_loss, per_source = source_scores({'a': alpha, 'b': beta, 'c': third}, measured,
                                               included=['a', 'b'], training=3)
    assert earlier_loss < 1e-20 and per_source['a']['later_rms_deg'] < 1e-12
    assert per_source['b']['later_rms_deg'] == pytest.approx(180.)
    assert per_source['c']['earlier_mean_squared_chord'] > 3.9
