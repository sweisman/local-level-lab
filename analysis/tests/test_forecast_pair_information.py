# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from scipy.stats import norm

from lll.state_space_covariance import LinearInnovations


def fixture():
    n = 14
    operator = LinearInnovations((dict(transition=[[1.]], process_loading=[[0.]],
        observation=[[1.]], white_loading=[[1.]]) for _ in range(n)),
        epoch_count=n, state_dimension=1, observation_dimension=1,
        initial_loading=[[0.]], maximum_bytes=8000, design_is_fixed=True,
        error_distribution='gaussian')
    return operator, np.arange(n, dtype=float)


def test_equal_covariance_power_and_variance_budget_match_normal_reference():
    from lll.forecast_pair_information import ideal_comparison

    r = ideal_comparison(16., alpha=.01, target_power=.8)
    assert r['ideal_power'] == pytest.approx(norm.cdf(4. - norm.isf(.01)))
    limit = r['largest_variance_multiplier_at_target_power']
    assert ideal_comparison(16. / limit, alpha=.01, target_power=.8)['ideal_power'] == pytest.approx(.8)
    assert ideal_comparison(0., alpha=.01, target_power=.8)['ideal_power'] == pytest.approx(.01)


def test_smooth_nuisance_removes_all_contrast_for_two_cubic_paths():
    from lll.forecast_pair_information import compare_paths

    operator, t = fixture()
    y = (1 + t[4:]**3)[:, None]
    result = compare_paths(operator, t, y, np.zeros_like(y), training_epochs=4)
    assert result['full']['ideal_power'] == pytest.approx(1.)
    assert result['after_cubic']['ideal_power'] == pytest.approx(.01)
    assert result['after_cubic']['squared_distance'] == pytest.approx(0., abs=1e-20)


def test_only_orthogonal_shape_contrast_survives_smooth_nuisance():
    from lll.forecast_pair_information import compare_paths

    operator, t = fixture()
    x = np.vander(t[4:] / t[-1], N=4, increasing=True)
    alternative = (-1.) ** np.arange(len(x))
    expected = alternative - x @ np.linalg.lstsq(x, alternative, rcond=None)[0]
    first, second = (alternative + x @ [10, 2, 3, 4])[:, None], np.zeros((len(x), 1))
    result = compare_paths(operator, t, first, second, training_epochs=4)
    assert result['after_cubic']['squared_distance'] == pytest.approx(expected @ expected)
    assert result == compare_paths(operator, t, second, first, training_epochs=4)
