# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from scipy.stats import chi2, ncx2


def test_more_external_modes_recover_a_weak_target_contrast():
    from lll.wide_direction_preflight import evaluate_spaces

    donors = np.array([[1., 0., 0., 0.]] * 3 + [[0., 1., 0., 0.], [0., 0., 1., 0.]])
    target = np.array([[0., 0., 0., 0.], [3., 0., 0., 0.], [0., 4., 0., 0.]])
    result = evaluate_spaces(donors, target, widths=(1, 3), alpha=.01)
    assert result['1']['pairs'][1]['retained_squared_distance'] == pytest.approx(0.)
    assert result['3']['pairs'][1]['retained_squared_distance'] == pytest.approx(16.)
    assert result['3']['pairs'][1]['ideal_power'] == pytest.approx(
        ncx2.sf(chi2.isf(.01, 3), 3, 16.))
    assert result['1']['pairs'][1]['ideal_power'] == pytest.approx(.01)
    assert result['1']['pairs'][0]['ideal_power'] > result['3']['pairs'][0]['ideal_power']


def test_width_above_donor_rank_never_adds_arbitrary_axes():
    from lll.wide_direction_preflight import evaluate_spaces

    first, second = np.eye(4)[:2]
    donors = np.array([first, first, 2 * first])
    result = evaluate_spaces(donors, np.array([first, second, 2 * second]),
                             widths=(1, 4), alpha=.01)
    assert result['4'] == result['1']
    assert result['4']['actual_rank'] == 1


def test_missing_information_can_abstain_with_zero_donor_span():
    from lll.wide_direction_preflight import evaluate_spaces

    result = evaluate_spaces(np.zeros((3, 4)), np.eye(4)[:3], widths=(2,), alpha=.01)
    assert result['2']['actual_rank'] == 0
    assert all(pair['ideal_power'] is None for pair in result['2']['pairs'])
