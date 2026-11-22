"""Cross-costs diagnose two saved points without claiming a global optimum."""

from lll.esa_error_law_cross_score_report import classify_cross_score


def test_cross_score_classifies_weighted_preference_for_saved_point():
    costs = {'weighted':{'receiver_only':20.,'weighted':13.}}
    assert classify_cross_score(costs) == 'weighted_prefers_own_saved_point'


def test_cross_score_flags_saved_better_point_for_optimizer_review():
    costs = {'weighted':{'receiver_only':10.,'weighted':13.}}
    assert classify_cross_score(costs) == 'weighted_saved_point_not_best_of_two'


def test_cross_score_preserves_tie_as_unresolved():
    costs = {'weighted':{'receiver_only':13.,'weighted':13.+1e-7}}
    assert classify_cross_score(costs) == 'saved_points_tied_under_weighted_cost'
