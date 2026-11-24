# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path

import pytest

from lll.esa_nkar_error_budget import evidence, split_score


def test_split_requires_an_orthogonal_projection():
    result = split_score([1., -1., 2., -2.], [1., -1., 0., 0.], [1., 3., 2., 5.])
    assert result['full_aircraft_score'] == pytest.approx(-8.)
    assert result['covered_aircraft_score'] == pytest.approx(-2.)
    assert result['uncovered_aircraft_score'] == pytest.approx(-6.)
    with pytest.raises(ValueError, match='orthogonal'):
        split_score([1., -1., 2., -2.], [.5, -.5, 0., 0.], [1., 3., 2., 5.])


def test_ground_coverage_does_not_supply_an_aircraft_error_cap():
    data = evidence(Path(__file__).resolve().parents[2])
    assert data['matched_intervals'] == 120
    assert data['current']['status'] == 'abstain'
    assert data['current']['missing'] == ['acceleration_rms_mps2', 'anchor_axis_m',
                                         'invisible_range_rms_m', 'visible_range_rms_m']
    assert data['coefficients']['invisible_range_rms_m'] == pytest.approx(.473901, abs=1e-6)
    assert data['illustration']['geometric_remainder_score'] > 0.
    assert 0.0009 < data['illustration']['max_covered_rms_m'] < 0.0010
