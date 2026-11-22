import pytest

from lll.esa_dispatch_accuracy import METHODS, choose_starts, score_path, verify_release
from lll.studies.artifacts import encoded


def test_primary_choice_uses_training_cost_and_breaks_exact_ties_by_start():
    candidates = {start: {method: cost for method, cost in zip(METHODS, costs, strict=True)}
                  for start, costs in enumerate(((2., 3.), (2., 1.)))}
    assert choose_starts(candidates) == dict(zip(METHODS, (0, 1), strict=True))


def test_primary_choice_rejects_missing_or_nonfinite_alternates():
    with pytest.raises(ValueError):
        choose_starts({0: dict.fromkeys(METHODS, 1.)})
    with pytest.raises(ValueError):
        choose_starts({0: dict.fromkeys(METHODS, 1.), 1: dict.fromkeys(METHODS, float('nan'))})


def test_scoring_requires_unchanged_release():
    release = {'primary': ['a'], 'source': 'forecast'}
    verify_release(release, encoded(release))
    with pytest.raises(ValueError, match='release'):
        verify_release(release, encoded(dict(release, primary=['b'])))


def test_accuracy_scores_all_later_epochs_and_retains_vertical_failure():
    times = list(range(400))
    actual = [[.7, -.4, 500.]] * 400
    predicted = actual[:-1] + [[.7, -.4, 700.]]
    scores = score_path(times, predicted, actual)
    assert scores['120']['limits']['passed']
    assert scores['240']['limits']['passed']
    assert not scores['400']['limits']['passed']
    assert scores['400']['score']['maximum_absolute_up_m'] == 200.
    with pytest.raises(ValueError):
        score_path(times[:-1], predicted[:-1], actual[:-1])
