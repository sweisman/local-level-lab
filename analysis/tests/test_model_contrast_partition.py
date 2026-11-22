# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def distances(means):
    return np.sum((means[:, None] - means[None, :]) ** 2, axis=2)


def test_sealed_scores_recover_contrast_and_remaining_error():
    from lll.model_contrast_partition import partition

    means = np.array([[0., 0., 0., 0.], [2., 0., 0., 0.], [1., 3., 0., 0.]])
    point = np.array([1.5, .5, 4., -3.])
    errors = np.sum((means - point) ** 2, axis=1)
    r = partition(distances(means), errors, coordinates=4)
    assert r['contrast_rank'] == 2
    assert r['orthogonal_squared_error'] == pytest.approx(25.)
    assert r['contrast_squared_errors'] == pytest.approx(errors - 25.)
    reverse = partition(distances(means[::-1]), errors[::-1], coordinates=4)
    assert reverse['orthogonal_squared_error'] == pytest.approx(25.)


def test_collinear_mean_paths_supply_one_coordinate():
    from lll.model_contrast_partition import partition

    means = np.array([[0., 0., 0.], [1., 0., 0.], [3., 0., 0.]])
    r = partition(distances(means), [2., 1., 5.], coordinates=3)
    assert r['contrast_rank'] == 1
    assert r['orthogonal_squared_error'] == pytest.approx(1.)
    assert r['contrast_squared_errors'] == pytest.approx([1., 0., 4.])


def test_identical_predictions_give_no_discriminating_component():
    from lll.model_contrast_partition import partition

    r = partition(np.zeros((3, 3)), [3., 3., 3.], coordinates=5)
    assert r['contrast_rank'] == 0
    assert r['orthogonal_squared_error'] == 3.


@pytest.mark.parametrize('matrix,energies', [
    ([[0, 1, 1], [1, 0, 20], [1, 20, 0]], [1, 1, 1]),
    ([[0, 1, 4], [1, 0, 1], [4, 1, 0]], [1, 300, 1]),
    ([[0, 1, 1], [1, 0, 2], [1, 2, 0]], [1, 25, 25]),
])
def test_incompatible_scores_or_path_distances_cannot_be_partitioned(matrix, energies):
    from lll.model_contrast_partition import partition

    with pytest.raises(ValueError):
        partition(matrix, energies, coordinates=5)
