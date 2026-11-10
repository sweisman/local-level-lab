"""Saved-result gate for a matched wide/selective training comparison."""
import pytest

from lll.ilvis0_hybrid_fit_check import compare


def case():
    result = dict(model='sphere_rotating', latitude_deg=55., profile=False,
                  policy_id='reported-short-v1', start=0, passed=True,
                  converged=True, all_columns_retained=True,
                  training_cost=0.2)
    binding = dict(full_array_sha256={'theta': 'a' * 64},
                   training_receiver_sha256='b' * 64)
    errors = [[0., 0., 0.], [0.1, 0., 0.]]
    return result, binding, errors


def test_matched_fits_pass_at_frozen_centimetre_threshold():
    result, binding, errors = case()
    candidate = [row.copy() for row in errors]
    candidate[1][0] += 0.009
    report = compare(result, result, binding, binding, errors, candidate)
    assert report['passed']
    assert report['maximum_prediction_difference_m'] == pytest.approx(0.009)
    assert report['training_cost_difference'] == 0.


def test_fits_reject_changed_inputs_and_silent_missing_epochs():
    result, binding, errors = case()
    with pytest.raises(ValueError, match='same frozen inputs'):
        compare(result, result, binding, dict(binding, training_receiver_sha256='c' * 64), errors, errors)
    with pytest.raises(ValueError, match='matched finite forecast'):
        compare(result, result, binding, binding, errors, errors[:1])


def test_fits_reject_nonfinite_cost_and_forecast():
    result, binding, errors = case()
    with pytest.raises(ValueError, match='finite nonnegative cost'):
        compare(dict(result, training_cost=float('nan')), result, binding, binding, errors, errors)
    with pytest.raises(ValueError, match='matched finite forecast'):
        compare(result, result, binding, binding, errors, [[float('nan'), 0., 0.], errors[1]])


def test_fits_fail_when_prediction_differs_or_one_fit_is_inadequate():
    result, binding, errors = case()
    farther = [row.copy() for row in errors]
    farther[0][2] = 0.011
    assert not compare(result, result, binding, binding, errors, farther)['passed']
    assert not compare(result, dict(result, passed=False), binding, binding, errors, errors)['passed']


def test_fits_reject_mismatched_cases():
    result, binding, errors = case()
    with pytest.raises(ValueError, match='same declared case'):
        compare(result, dict(result, profile=True), binding, binding, errors, errors)


def test_fits_reject_different_withheld_truth():
    result, binding, errors = case()
    with pytest.raises(ValueError, match='same withheld truth'):
        compare(result, result, binding, binding, errors, errors,
                reference_scoring_sha256='a' * 64,
                candidate_scoring_sha256='b' * 64)
