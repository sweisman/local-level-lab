"""Channel comparisons keep the full-noise outcome as a separate case."""


def test_channel_comparison_reports_ratios_without_adding_errors():
    from lll.esa_oracle_channel_report import compare_channels

    result=compare_channels(gyro=dict(horizontal_rms_m=9.),
        accel=dict(horizontal_rms_m=3.),full=dict(horizontal_rms_m=8.))
    assert result['gyro_to_accel_horizontal_rms_ratio']==3.
    assert result['full_to_gyro_horizontal_rms_ratio']==8/9
    assert result['dominant_single_channel_horizontal']=='gyro'
