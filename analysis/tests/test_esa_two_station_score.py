import math

import pytest

from lll.esa_two_station_score import minimum_station_error


def test_unconstrained_station_error_is_half_the_ground_disagreement():
    result = minimum_station_error([0., 2.], [0., 6.], [1., 0.])
    assert result['common'] == pytest.approx([0., 4.])
    assert result['maximum_rms'] == pytest.approx(math.sqrt(2.))


def test_score_constraint_has_an_interior_minimax_witness():
    result = minimum_station_error([0., 0.], [2., 4.], [1., 0.], target=0.)
    assert result['common'] == pytest.approx([0., 2.5])
    assert result['station_rms'] == pytest.approx([2.5/math.sqrt(2.)]*2)


def test_larger_vertical_error_can_put_optimum_at_an_endpoint():
    result = minimum_station_error([0., 0.], [4., 1.], [1., 0.], target=0.)
    assert result['common'] == pytest.approx([0., 1.])
    assert result['maximum_rms'] == pytest.approx(math.sqrt(8.))
