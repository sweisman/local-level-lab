import numpy as np
import pytest

from lll import esa_bounded_drift_support


@pytest.mark.parametrize(('target', 'remaining'), [(2., .5625), (-2., .25)])
def test_box_certificate_resolves_asymmetric_known_answer(target, remaining):
    result = esa_bounded_drift_support.bounded_match(
        [[1.]], [target], [-1.], [.5], max_iterations=100, maximum_gap=1e-5)
    assert result['verified']
    assert result['remaining_fraction'] == pytest.approx(remaining)
    assert result['lower_fraction'] == pytest.approx(remaining, abs=1e-9)
    assert result['at_bound'] == [0]


def test_fixed_column_does_not_hide_signal():
    result = esa_bounded_drift_support.bounded_match(
        np.eye(2), [1., 1.], [-2., 0.], [2., 0.], max_iterations=100, maximum_gap=1e-5)
    assert result['verified']
    assert result['remaining_fraction'] == pytest.approx(.5)
    assert result['step'] == pytest.approx([1., 0.])
    assert result['at_bound'] == []
