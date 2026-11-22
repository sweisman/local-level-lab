# SPDX-License-Identifier: AGPL-3.0-or-later
"""Resource accounting checks for the saved ESA trial history."""

import pytest


def fit_fixture():
    return dict(evaluations=6, evaluation_trace=[dict(evaluation=i, fresh=i in (5, 6))
                                                for i in range(1, 7)], step_history=[
        dict(evaluation=2, accepted=False), dict(evaluation=2, accepted=True),
        dict(evaluation=3, accepted=False), dict(evaluation=3, accepted=False),
        dict(evaluation=4, accepted=True)])


def test_cache_hits_count_once_and_later_acceptance_preserves_the_derivative():
    from lll.esa_dispatch_trial_work import trial_work

    result = trial_work(fit_fixture())
    assert result == dict(tangent_calls=6, value_only_calls=3, avoided_tangent_calls=1,
                          planned_tangent_calls=5, break_even_ratio=1./3.)


@pytest.mark.parametrize('problem', ['fresh_proposal', 'wrong_index', 'missing_trace'])
def test_rejects_invalid_proposal_identity_or_incomplete_trace(problem):
    from lll.esa_dispatch_trial_work import trial_work

    fit = fit_fixture()
    if problem == 'fresh_proposal':
        fit['step_history'][0]['evaluation'] = 5
    elif problem == 'wrong_index':
        fit['step_history'][0]['evaluation'] = 7
    else:
        fit['evaluation_trace'].pop()
    with pytest.raises(ValueError):
        trial_work(fit)


def test_no_proposals_have_no_break_even_cost():
    from lll.esa_dispatch_trial_work import trial_work

    fit = fit_fixture()
    fit['step_history'] = []
    result = trial_work(fit)
    assert result['planned_tangent_calls'] == result['tangent_calls']
    assert result['break_even_ratio'] is None
