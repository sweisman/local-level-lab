# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent dense check of a profiled score on joint IMU/receiver error."""
import math

import numpy as np
import pytest

from lll.ilvis0_error_model import covariance
from lll.prediction_error_law import score_profiled_training_laws
from lll.receiver_noise_states import ReceiverAugmentation
from test_receiver_noise_states import example, operator


def test_profiled_score_matches_dense_joint_error_contrasts():
    times, spec, transforms, steps, initial = example()
    baseline = operator(steps, initial, 2, len(times))
    native_root = baseline.unwhiten(np.eye(3*len(times)))
    dense = native_root@native_root.T + covariance(times, spec, transforms)
    for i, step in enumerate(steps):
        sl = slice(3*i, 3*i+3)
        dense[sl, sl] -= step['white_loading']@step['white_loading'].T
    augmented = ReceiverAugmentation(
        iter(steps), times=times, spec=spec, transforms=transforms,
        state_dimension=2, initial_loading=initial, maximum_epochs=16)
    joint = operator(augmented.steps(), augmented.initial_loading,
                     augmented.state_dimension, len(times))
    cutoff = 5
    n = 3*cutoff
    observed = np.sin(np.arange(n)/7.)
    design = np.column_stack((np.ones(n), np.arange(n)/n))
    u, _, _ = np.linalg.svd(design, full_matrices=True)
    contrast = u[:, 2:]
    projected = contrast.T@dense[:n, :n]@contrast
    projected_observed = contrast.T@observed
    expected = .5*(projected_observed@np.linalg.solve(projected, projected_observed)
                   + np.linalg.slogdet(projected)[1]
                   + (n-2)*math.log(2*math.pi))
    result = score_profiled_training_laws(
        {'joint': joint}, observed, design, training_epochs=cutoff,
        rank_rtol=1e-10, parameter_scales=np.ones(2))
    assert result['training_mean_rank'] == 2
    assert result['laws'][0]['restricted_negative_log_likelihood'] == pytest.approx(
        expected, rel=2e-10, abs=2e-10)
    assert result['later_observations_used'] is False
    assert result['error_law_calibrated'] is False
