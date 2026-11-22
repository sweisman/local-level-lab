# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def test_peak_errors_can_fail_even_when_both_rms_limits_pass():
    from lll.esa_absolute_accuracy import describe

    errors = [[0., 0., 0.]] * 119 + [[51., 0., -151.]]
    actual = describe(range(1, 121), errors)

    assert actual['score']['maximum_horizontal_m'] == 51.
    assert actual['score']['maximum_absolute_up_m'] == 151.
    assert actual['limits']['checks'] == dict(horizontal_rms_m=True, vertical_rms_m=True,
        maximum_horizontal_m=False, maximum_absolute_up_m=False)
    assert actual['limits']['passed'] is False
    assert actual['limits']['calibrated_goodness_of_fit'] is False
    with pytest.raises(ValueError, match='120'):
        describe(range(1, 120), errors[:-1])
