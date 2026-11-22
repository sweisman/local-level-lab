# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def test_full_overlap_preserves_every_model_pair():
    from lll.forecast_direction_transfer import retention

    donors = np.array([[[1., 0., 0.], [0., 1., 0.]],
                       [[2., 0., 0.], [0., 3., 0.]]])
    target = np.array([[0., 0., 0.], [1., 1., 0.], [-1., 1., 0.]])
    result = retention(donors, target)
    assert result['worst_case_information_fraction'] == pytest.approx(1.)
    assert result['pair_information_fractions'] == pytest.approx([1., 1., 1.])


def test_one_good_pair_does_not_hide_a_missing_direction():
    from lll.forecast_direction_transfer import retention

    donors = np.array([[[1., 0., 0.], [0., 1., 0.]]])
    target = np.array([[0., 0., 0.], [1., 0., 0.], [0., 0., 1.]])
    result = retention(donors, target)
    assert result['pair_information_fractions'] == pytest.approx([1., 0., .5])
    assert result['worst_case_information_fraction'] == pytest.approx(0.)


def test_template_cancellation_leaves_no_artificial_test_direction():
    from lll.forecast_direction_transfer import retention

    donor = np.eye(3)[:2]
    result = retention(np.array([donor, -donor]), np.eye(3))
    assert result['donor_rank'] == 0
    assert result['pair_information_fractions'] == [0., 0., 0.]


def test_donor_selection_uses_no_target_seed_or_route_from_wrong_side():
    from lll.forecast_direction_transfer import donors_for

    cases = [dict(identity=name, seed=i, latitude_deg=latitude)
             for i, (name, latitude) in enumerate((('a', 55), ('b', 55), ('c', -55), ('d', -55)))]
    assert [row['identity'] for row in donors_for(cases, cases[0], same_route=True)] == ['b']
    assert [row['identity'] for row in donors_for(cases, cases[0], same_route=False)] == ['c', 'd']
    cases[2]['seed'] = cases[0]['seed']
    with pytest.raises(ValueError, match='disjoint'):
        donors_for(cases, cases[0], same_route=False)
