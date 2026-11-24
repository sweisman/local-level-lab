import pytest

from lll.esa_carrier_error_requirements import bracket_limit, checked_upper


def test_upper_accounts_for_caps_and_geometric_error_on_each_range_part():
    caps = dict(anchor_axis_m=1., acceleration_rms_mps2=.01,
                visible_range_rms_m=.002, invisible_range_rms_m=.003)
    coefficients = dict(anchor_axis_m=.1, acceleration_rms_mps2=20.,
                        visible_range_rms_m=100., invisible_range_rms_m=50.)
    assert checked_upper(coefficients, caps, .001, .02) == pytest.approx(.82)


def test_limit_returns_verified_side_of_crossing_and_reports_ceiling():
    limit = bracket_limit(0., 5., lambda x: 2*x, score_limit=1.)
    assert limit['value'] < .5
    assert limit['value'] == pytest.approx(.5, abs=2e-9)
    assert not limit['at_search_ceiling']
    ceiling = bracket_limit(0., 2., lambda x: .1*x, score_limit=1.)
    assert ceiling == dict(value=2., at_search_ceiling=True)
    assert bracket_limit(0., 2., lambda x: 1.+x, score_limit=1.) is None
