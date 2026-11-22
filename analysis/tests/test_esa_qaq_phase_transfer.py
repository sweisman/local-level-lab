# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.esa_qaq_phase_transfer import transfer


def test_qaq_transfer_fits_earlier_rows_only_with_variable_satellite_counts():
    early = [(100, [2., -2.], [4., -4.]), (101, [1., -2., 1.], [2., -4., 2.])]
    later = [(103, [4., -4., 0.], [2., -2., 0.])]
    result = transfer(early, later)
    assert result['trained_gain'] == pytest.approx(.5)
    assert result['training']['earlier_gain_rms_m'] == pytest.approx(0.)
    assert result['withheld']['earlier_gain_rms_m'] == pytest.approx((18./3.)**.5)
    assert result['withheld']['unit_ground_rms_m'] < result['withheld']['earlier_gain_rms_m']
    assert result['training']['values'] == 5 and result['withheld']['values'] == 3


def test_qaq_transfer_refuses_a_later_interval_that_uses_a_training_epoch():
    with pytest.raises(ValueError, match='disjoint'):
        transfer([(100, [1., -1.], [1., -1.])], [(101, [1., -1.], [1., -1.])])
