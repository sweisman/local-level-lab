"""Score bounded generated targets only after they have been sealed."""
import numpy as np
import pytest


def test_marginal_score_uses_all_axes_and_wraps_longitude():
    from lll.bounded_nonlinear_case import _score
    bounds = dict(lower=[0., 3.13, -1.], upper=[2., 3.15, 1.])
    observed = np.array([[9., 9., 9.], [1., -3.14, 0.]])
    result = _score(bounds, observed, 1)
    assert result['marginal_covered'] == [1, 1, 1]
    assert result['marginal_total'] == 3
    assert result['scientific_decision'] == 'abstain'


def test_marginal_score_rejects_missing_future_epoch():
    from lll.bounded_nonlinear_case import _score
    with pytest.raises(ValueError, match='complete matched'):
        _score(dict(lower=[0., 0., 0.], upper=[1., 1., 1.]),
               np.zeros((3, 3)), 1)
