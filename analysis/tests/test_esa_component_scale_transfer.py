# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_component_scale_transfer import evaluate_fold, fit_cases, make_case


def synthetic_case(index, scale):
    identity = np.eye(6)
    y = np.repeat(np.sqrt(scale), 2)
    roots = dict(native=identity*.25, persistent=identity[:, :4], maneuver=identity[:, 4:])
    return make_case(index, roots, y)


def test_estimate_separate_scales_and_score_all_candidates():
    cases = [synthetic_case(i, [.4, .4, 2.0]) for i in range(8)]
    cases[1] = make_case(1,
        dict(native=np.eye(6)*.25, persistent=np.eye(6)[:, 2:4], maneuver=np.eye(6)[:, 4:]),
        np.repeat(np.sqrt([.1, .4, 2.0]), 2))
    fit = fit_cases(cases, maximum=100)
    assert fit['separate']['status'] in ('bound', 'interior')
    target = synthetic_case(9, [.4, .4, 2.0])
    fold = evaluate_fold(cases, [target], maximum=100)
    record = fold['target'][0]['scores']
    assert record['separate']['negative_log_score'] < record['fixed']['negative_log_score']
    assert record['separate']['negative_log_score'] < record['common']['negative_log_score']


def test_held_out_errors_cannot_change_the_fitted_covariance():
    train = [synthetic_case(i, [1., 1., 1.]) for i in range(4)]
    target = synthetic_case(5, [1., 1., 1.])
    shifted = synthetic_case(5, [10., 10., 10.])
    first = evaluate_fold(train, [target], maximum=100)
    second = evaluate_fold(train, [shifted], maximum=100)
    assert first['fit'] == second['fit']
    assert first['target'] != second['target']
    assert first['fit']['separate']['status'] == 'unidentifiable'
    assert 'separate' not in first['target'][0]['scores']


def test_refuse_to_fit_a_scoring_window():
    shared = synthetic_case(9, [1., 1., 1.])
    with pytest.raises(ValueError, match='disjoint'):
        evaluate_fold([shared], [shared], maximum=100)
