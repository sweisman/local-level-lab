# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest

from lll.esa_direction_receiver_derivative import angle_scores


def test_direction_scores_distinguish_smaller_error_and_keep_the_pair_margin():
    row = angle_scores([1.0]*28, {'globe': [1.0]*28, 'disc': [3.0]*28})
    assert row['rms_deg'] == {'globe': 0., 'disc': 2.}
    assert row['disc_minus_globe_deg'] == pytest.approx(2.)
    assert row['minimum_change_to_tie_rms_deg'] == pytest.approx(1.)
    row = angle_scores([2.0]*28, {'globe': [1.0]*28, 'disc': [3.0]*28})
    assert row['disc_minus_globe_deg'] == 0.
    assert row['minimum_change_to_tie_rms_deg'] == 0.


def test_direction_scores_reject_mismatched_support():
    with pytest.raises(ValueError):
        angle_scores([1.0]*28, {'globe': [1.0]*28, 'disc': [3.0]*27})
