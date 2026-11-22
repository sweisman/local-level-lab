# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
from scipy.sparse import csr_matrix

from lll.ilvis0_error_model import Spec, covariance


def test_covariance_action_matches_dense_error_law():
    from lll.ilvis0_structured_force_projection import covariance_action

    times = np.array([0., .9, 2.1, 4.])
    law = Spec(np.eye(3), ((1.8, np.eye(3)*2),), np.eye(3)*3,
               np.eye(3)*4, times[0], times[-1]-times[0])
    load = np.zeros((4, 3))
    load[[1, 3], :] = [[1, -2, 3], [.2, 2.5, -3.5]]
    actual = covariance_action(times, law, load[:, :, None]).ravel()
    np.testing.assert_allclose(actual, covariance(times, law) @ load.ravel(), atol=1e-12)


def test_one_error_vector_meets_multiple_force_constraints():
    from lll.ilvis0_shared_force_witness import project_witness

    times = np.array([0., 1.])
    law = Spec(np.eye(3))
    weights = csr_matrix([[1., 0., 0., 0., 0., 0.], [0., -2., 0., 0., 0., 0.]])
    result = project_witness(times, law, weights, [-.4, .6], [1., 2.], maximum_steps=3)
    np.testing.assert_allclose(result['error_m'], [0., -.3, 0., 0., 0., 0.])
    assert result['remaining'] == 0 and result['steps'] == 1
    assert result['covariance_norm'] == .3


def test_incompatible_constraints_end_without_a_witness():
    from lll.ilvis0_shared_force_witness import project_witness

    weights = csr_matrix([[1., 0., 0.], [-1., 0., 0.]])
    result = project_witness([0.], Spec(np.eye(3)), weights, [1., 1.], [1., 1.], maximum_steps=5)
    assert result['steps'] == 5 and result['remaining'] == 1
