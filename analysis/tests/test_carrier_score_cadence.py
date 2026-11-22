# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.carrier_score_cadence import project_cadence


def test_projection_matches_dense_ground_observation_operator():
    support = [[1, 2, 3], [1, 2, 4], [1, 3, 4], [1, 3, 4]]
    dual = np.arange(1., 13.)**2
    intervals = [(0, 2), (3, 4)]
    result = project_cadence(support, dual, intervals, available=[1, 2, 3, 4])
    observation = np.array([[1, -1, 0, 1, -1, 0, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, -1, 0],
                            [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, -1]])
    expected = np.linalg.pinv(observation)@observation@dual
    assert result['projected_weights'] == pytest.approx(expected)
    assert result['observable_norm_fraction'] == pytest.approx(np.linalg.norm(expected)/np.linalg.norm(dual))
    assert result['intervals'][0]['satellites'] == [1, 2]
    assert result['projected_norm']**2 + result['unobserved_norm']**2 == pytest.approx(dual@dual)


def test_projected_score_uses_centered_satellite_totals_without_interpolation():
    dual = [1., -1., 2., -2.]
    result = project_cadence([[1, 2], [1, 2]], dual, [(0, 2)], available=[1, 2])
    interval, = result['intervals']
    total = np.array([.2, -.1])
    assert np.dot(interval['aggregate_weights'], total) == pytest.approx(.45)
    assert np.sum(interval['aggregate_weights']) == pytest.approx(0.)
    with pytest.raises(ValueError, match='nonoverlapping'):
        project_cadence([[1, 2], [1, 2]], dual, [(0, 2), (1, 2)])
