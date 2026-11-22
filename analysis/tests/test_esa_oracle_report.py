"""Oracle and fitted forecast scores must be compared on the same units."""


def test_compare_scores_keeps_absolute_error_and_direction():
    from lll.esa_oracle_report import compare_scores

    result = compare_scores(dict(horizontal_rms_m=60.,vertical_rms_m=8.),
                            dict(horizontal_rms_m=50.,vertical_rms_m=2.))
    assert result['oracle_minus_fitted_horizontal_rms_m'] == 10.
    assert result['oracle_minus_fitted_vertical_rms_m'] == 6.
    assert result['oracle_to_fitted_horizontal_rms_ratio'] == 1.2
    assert result['oracle_better_horizontal'] is False
