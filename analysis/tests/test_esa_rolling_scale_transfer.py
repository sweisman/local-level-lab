# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def test_positive_earlier_scale_and_exact_transfer_ratio():
    from lll.esa_rolling_scale_transfer import transfer

    result = transfer(9.0, 18.0, coordinates=360)
    assert result['earlier_variance_multiplier'] == pytest.approx(0.025)
    assert result['later_variance_multiplier'] == pytest.approx(0.05)
    assert result['later_to_earlier_variance_ratio'] == 2.0
    assert result['later_rms_after_earlier_scaling'] == pytest.approx(np.sqrt(2.0))


@pytest.mark.parametrize('earlier,later,count', [(0., 1., 360), (1., -1., 360),
                                                 (np.inf, 1., 360), (1., 1., 0)])
def test_invalid_scale_does_not_receive_a_reference(earlier, later, count):
    from lll.esa_rolling_scale_transfer import transfer

    with pytest.raises(ValueError):
        transfer(earlier, later, coordinates=count)
