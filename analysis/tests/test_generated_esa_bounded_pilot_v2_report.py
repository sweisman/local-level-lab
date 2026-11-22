"""Bound-aware pilot reporting keeps technical and physical outcomes apart."""

import pytest


def test_interval_coverage_counts_each_axis_and_whole_path():
    from lll.generated_esa_bounded_pilot_v2_report import interval_coverage

    bounds = dict(lower=[-1.] * 6, upper=[1.] * 6)
    truth = [[0., 0., 0.], [0., 2., 0.]]
    result = interval_coverage(bounds, truth)
    assert result['covered_by_axis'] == {'latitude': 2, 'longitude': 1,
                                         'height': 2}
    assert result['all_coordinates_covered'] is False
    assert result['epochs'] == 2


def test_incomplete_or_reversed_interval_is_rejected():
    from lll.generated_esa_bounded_pilot_v2_report import interval_coverage

    with pytest.raises(ValueError):
        interval_coverage(dict(lower=[0.] * 6, upper=[1.] * 5),
                          [[0., 0., 0.], [0., 0., 0.]])
    with pytest.raises(ValueError):
        interval_coverage(dict(lower=[1.] * 6, upper=[0.] * 6),
                          [[0., 0., 0.], [0., 0., 0.]])


def test_interval_span_reports_physical_scale():
    from lll.generated_esa_bounded_pilot_v2_report import interval_span

    result = interval_span(dict(lower=[0., 0., 0.],
                                upper=[1e-6, 2e-6, 10.]),
                           [[0., 0., 0.]])
    assert result['median_neu_span_m'][0] == pytest.approx(6.335, rel=.01)
    assert result['median_neu_span_m'][1] == pytest.approx(12.756, rel=.01)
    assert result['median_neu_span_m'][2] == 10.
