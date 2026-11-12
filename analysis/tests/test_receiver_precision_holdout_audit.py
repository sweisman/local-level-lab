# SPDX-License-Identifier: AGPL-3.0-or-later
"""Straight-trend diagnostic uses only later rows and reports its limits."""

import pytest


def test_linear_trend_exact_line_and_earlier_rows_ignored():
    from lll.receiver_precision_holdout_audit import linear_trend

    rows = [dict(role='training', time_s=0., north_error_m=1e6,
                 east_error_m=-1e6, height_error_m=0.)]
    rows.extend(dict(role='prediction', time_s=float(index),
                     north_error_m=2. + .5 * index,
                     east_error_m=-3. - .25 * index,
                     height_error_m=7.) for index in range(1, 6))
    result = linear_trend(rows)
    assert result['north']['slope_m_per_min'] == pytest.approx(30.)
    assert result['east']['slope_m_per_min'] == pytest.approx(-15.)
    assert result['north']['centered_variance_explained'] == pytest.approx(1.)
    assert result['east']['centered_variance_explained'] == pytest.approx(1.)
    assert result['height']['centered_variance_explained'] is None
    assert result['north']['prediction_epochs'] == 5


def test_linear_trend_rejects_disordered_or_missing_later_support():
    from lll.receiver_precision_holdout_audit import linear_trend

    rows = [dict(role='prediction', time_s=float(index),
                 north_error_m=float(index), east_error_m=0.,
                 height_error_m=0.) for index in range(3)]
    with pytest.raises(ValueError, match='ordered finite'):
        linear_trend([rows[1], rows[0], rows[2]])
    with pytest.raises(ValueError, match='at least three'):
        linear_trend(rows[:2])
