"""A fixed-law family must retain every candidate forecast interval."""

import pytest


def _member(lower, upper, *, binding='a' * 64, target='receiver_measurement',
            coverage=.95):
    return {
        'binding_sha256': binding,
        'prediction_target': target,
        'interval': {
            'scope': 'affine_known_gaussian_box',
            'lower': lower,
            'upper': upper,
            'marginal_coverage_lower_bound': coverage,
            'simultaneous_coverage_established': False,
            'true_calibration_inside_box_assumed': True,
            'error_covariance_known_assumed': True,
            'nonlinear_aircraft_coverage_established': False,
            'scientific_decision': 'abstain',
        },
    }


def test_union_covers_each_fixed_law_without_selecting_one():
    from lll.prediction_law_family import union_marginal_intervals
    result = union_marginal_intervals({
        'white': _member([-1., 4.], [2., 6.]),
        'persistent': _member([-3., 5.], [1., 9.]),
    }, minimum_marginal_coverage=.95)
    assert result['lower'] == [-3., 4.]
    assert result['upper'] == [2., 9.]
    assert result['candidate_laws'] == ['persistent', 'white']
    assert result['selected_law'] is None
    assert result['coverage_calibrated'] is False
    assert result['scientific_decision'] == 'abstain'


@pytest.mark.parametrize('change', [
    {'binding_sha256': 'b' * 64},
    {'prediction_target': 'physical_position'},
    {'interval': _member([-1.], [2.])['interval']},
])
def test_rejects_mixed_targets_or_epoch_support(change):
    from lll.prediction_law_family import union_marginal_intervals
    other = _member([-2., 3.], [4., 7.])
    other.update(change)
    with pytest.raises(ValueError):
        union_marginal_intervals({'a': _member([-1., 4.], [2., 6.]),
                                  'b': other}, minimum_marginal_coverage=.95)


def test_rejects_undercovered_or_unqualified_law():
    from lll.prediction_law_family import union_marginal_intervals
    for bad in (_member([-2.], [2.], coverage=.90),
                _member([-2.], [2.])):
        if bad['interval']['marginal_coverage_lower_bound'] == .95:
            bad['interval']['error_covariance_known_assumed'] = False
        with pytest.raises(ValueError):
            union_marginal_intervals({'a': _member([-1.], [1.]), 'b': bad},
                                      minimum_marginal_coverage=.95)


def test_rejects_nonfinite_and_reversed_intervals():
    from lll.prediction_law_family import union_marginal_intervals
    for lower, upper in (([float('nan')], [1.]), ([2.], [1.])):
        with pytest.raises(ValueError):
            union_marginal_intervals({'a': _member([-1.], [1.]),
                                      'b': _member(lower, upper)},
                                      minimum_marginal_coverage=.95)


def test_family_retains_wider_real_affine_prediction():
    from lll.bounded_linear_prediction import envelope
    from lll.prediction_law_family import union_marginal_intervals
    def fixed_law(sigma):
        interval = envelope([[1.], [1.]], [0., 0.], [[1.]], [0.], [sigma],
                            [-1.], [1.], calibration_alpha=.025,
                            future_alpha=.025, rank_rtol=1e-10)
        return dict(binding_sha256='a' * 64,
                    prediction_target='receiver_measurement', interval=interval)
    narrow = fixed_law(.1)
    broad = fixed_law(1.)
    result = union_marginal_intervals({'narrow': narrow, 'broad': broad},
                                      minimum_marginal_coverage=.95)
    assert result['lower'][0] == broad['interval']['lower'][0]
    assert result['upper'][0] == broad['interval']['upper'][0]
