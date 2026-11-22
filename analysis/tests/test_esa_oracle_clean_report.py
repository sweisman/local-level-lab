"""A clean forecast comparison preserves the raw error scale."""


def test_clean_to_noisy_ratios_compare_matching_axes():
    from lll.esa_oracle_clean_report import clean_to_noisy_ratios

    assert clean_to_noisy_ratios(
        dict(horizontal_rms_m=.1,vertical_rms_m=.2),
        dict(horizontal_rms_m=10.,vertical_rms_m=4.)) == dict(
            horizontal=100.,vertical=20.)
