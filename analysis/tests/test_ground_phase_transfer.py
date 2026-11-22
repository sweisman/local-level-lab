# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.ground_phase_transfer import compare_transfer


def test_ground_phase_transfer_uses_only_earlier_pairs_to_estimate_gain():
    ground = [[1., -1.], [2., -2.], [1., -1.], [1., -1.]]
    aircraft = [[.5, -.5], [1., -1.], [3., -3.], [10., -10.]]
    result = compare_transfer(aircraft, ground, training=[0, 1], withheld=[2])
    assert result['trained_gain'] == pytest.approx(.5)
    assert result['training']['earlier_gain_rms_m'] == pytest.approx(0.)
    assert result['withheld']['no_ground_rms_m'] == pytest.approx(3.)
    assert result['withheld']['unit_ground_rms_m'] == pytest.approx(2.)
    assert result['withheld']['earlier_gain_rms_m'] == pytest.approx(2.5)


def test_ground_phase_transfer_rejects_overlapping_or_unordered_groups():
    rows = [[10., -10.]]*3
    with pytest.raises(ValueError, match='chronological'):
        compare_transfer(rows, rows, training=[0, 1], withheld=[1, 2])
