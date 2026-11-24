import pytest

from lll.esa_apron_nkar import matched_residuals, pooled_statistics


def test_matched_ranges_use_identical_satellites_and_remove_common_offsets():
    air = {1: 5., 2: 7., 3: 16.}
    ground = {1: -8., 2: -4., 4: -23.}
    row = matched_residuals(air, ground, minimum=2)
    assert row['satellites'] == [1, 2]
    stats = pooled_statistics([row])
    assert stats['aircraft_rms_m'] == pytest.approx(1.)
    assert stats['ground_rms_m'] == pytest.approx(2.)
    assert stats['difference_rms_m'] == pytest.approx(1.)
    assert stats['correlation'] == pytest.approx(1.)
    assert matched_residuals(air, ground, minimum=3) is None
