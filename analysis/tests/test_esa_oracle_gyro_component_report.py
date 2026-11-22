"""Saved gyro-component scores do not assume additivity."""


def test_gyro_component_comparison_keeps_combined_error_separate():
    from lll.esa_oracle_gyro_component_report import compare_components

    report = compare_components(dict(horizontal_rms_m=4.),
        dict(horizontal_rms_m=9.), dict(horizontal_rms_m=7.))
    assert report['larger_single_component'] == 'bias'
    assert report['white_to_bias_horizontal_rms_ratio'] == 4/9
    assert report['combined_gyro_horizontal_rms_m'] == 7.
    assert report['additive_error_assumption_made'] is False


def test_horizontal_error_alignment_uses_signed_matched_vectors():
    from lll.esa_oracle_gyro_component_report import horizontal_alignment

    assert horizontal_alignment([[1., 2., 5.], [2., 4., 6.]],
                                [[-1., -2., 8.], [-2., -4., 9.]]) == -1.
