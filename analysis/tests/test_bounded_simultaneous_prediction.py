"""A whole-forecast affine control must retain multiplicity and law ambiguity."""
import math

import numpy as np
import pytest


def bound(earlier, *, sigma=1.):
    from lll.bounded_simultaneous_prediction import envelope
    return envelope([[1.], [1.], [1.]], earlier,
                    [[1.]] * 6, [0.] * 6, [sigma] * 6,
                    [-1.], [1.], calibration_alpha=.025,
                    simultaneous_alpha=.05, rank_rtol=1e-10)


def test_whole_forecast_allowance_widens_each_marginal_interval():
    from lll.bounded_linear_prediction import envelope as marginal
    whole = bound([0., 0., 0.])
    single = marginal([[1.], [1.], [1.]], [0., 0., 0.],
                      [[1.]] * 6, [0.] * 6, [1.] * 6,
                      [-1.], [1.], calibration_alpha=.025,
                      future_alpha=.025, rank_rtol=1e-10)
    assert all(a < b for a, b in zip(whole['lower'], single['lower']))
    assert all(a > b for a, b in zip(whole['upper'], single['upper']))
    assert whole['coordinate_count'] == 6
    assert whole['affine_conditional_simultaneous_lower_bound'] == .95
    assert whole['affine_conditional_simultaneous_bound_derived']
    assert not whole['simultaneous_coverage_established']
    assert not whole['observed_aircraft_coverage_established']


def test_correlated_future_draws_respect_known_law_whole_forecast_control():
    rng = np.random.default_rng(914)
    covered = 0
    for _ in range(250):
        earlier = .4+rng.normal(size=3)
        future = .4 + .7*rng.normal() + math.sqrt(.51)*rng.normal(size=6)
        result = bound(earlier)
        covered += bool(np.all((np.asarray(result['lower']) <= future) &
                               (future <= np.asarray(result['upper']))))
    assert covered >= 238


def test_law_union_keeps_widest_interval_without_selecting_a_law():
    from lll.prediction_simultaneous_law_family import union_simultaneous_intervals
    narrow = bound([0., 0., 0.])
    wide = bound([0., 0., 0.], sigma=2.)
    inputs = {law:dict(binding_sha256='a'*64,
                       prediction_target='physical_position',
                       operator_configuration=key*64,
                       interval=dict(value, prediction_target='physical_position',
                                     forecast_support_sha256='d'*64,
                                     error_operator_configuration=key*64,
                                     later_observations_used=False))
              for law, key, value in (('increment', 'b', narrow),
                                      ('point', 'c', wide))}
    result = union_simultaneous_intervals(
        inputs, minimum_simultaneous_coverage=.95)
    assert result['lower'] == wide['lower']
    assert result['upper'] == wide['upper']
    assert result['candidate_laws'] == ['increment', 'point']
    assert result['selected_law'] is None
    assert result['affine_conditional_simultaneous_lower_bound'] == .95
    assert not result['coverage_calibrated']
    assert result['scientific_decision'] == 'abstain'


def test_mismatched_law_binding_or_unrepresentable_tail_is_rejected():
    from lll.prediction_simultaneous_law_family import union_simultaneous_intervals
    value = bound([0., 0., 0.])
    with pytest.raises(ValueError, match='representable Gaussian tail'):
        from lll.bounded_simultaneous_prediction import envelope
        envelope([[1.]], [0.], [[1.]] * 6, [0.] * 6, [1.] * 6,
                 [-1.], [1.], calibration_alpha=.025,
                 simultaneous_alpha=math.nextafter(.025, 1.),
                 rank_rtol=1e-10)
    inputs = {law:dict(binding_sha256=key*64,
                       prediction_target='physical_position',
                       operator_configuration='c'*64,
                       interval=dict(value, prediction_target='physical_position',
                                     forecast_support_sha256='d'*64,
                                     error_operator_configuration='c'*64,
                                     later_observations_used=False))
              for law, key in (('increment', 'a'), ('point', 'b'))}
    with pytest.raises(ValueError, match='share target and forecast support'):
        union_simultaneous_intervals(inputs,
                                     minimum_simultaneous_coverage=.95)


def test_law_union_rejects_interval_from_another_error_operator():
    from lll.prediction_simultaneous_law_family import union_simultaneous_intervals
    value = bound([0., 0., 0.])
    inputs = {law:dict(binding_sha256='a'*64,
                       prediction_target='receiver_measurement',
                       operator_configuration=key*64,
                       interval=dict(value, prediction_target='receiver_measurement',
                                     forecast_support_sha256='d'*64,
                                     error_operator_configuration='b'*64,
                                     later_observations_used=False))
              for law, key in (('increment', 'b'), ('point', 'c'))}
    with pytest.raises(ValueError, match='error operator'):
        union_simultaneous_intervals(inputs,
                                     minimum_simultaneous_coverage=.95)


def test_law_union_rejects_different_future_time_grids():
    from lll.prediction_simultaneous_law_family import union_simultaneous_intervals
    value = bound([0., 0., 0.])
    inputs = {law:dict(binding_sha256='a'*64,
                       prediction_target='physical_position',
                       operator_configuration='c'*64,
                       interval=dict(value, prediction_target='physical_position',
                                     forecast_support_sha256=key*64,
                                     error_operator_configuration='c'*64,
                                     later_observations_used=False))
              for law, key in (('increment', 'd'), ('point', 'e'))}
    with pytest.raises(ValueError, match='forecast support'):
        union_simultaneous_intervals(inputs,
                                     minimum_simultaneous_coverage=.95)
