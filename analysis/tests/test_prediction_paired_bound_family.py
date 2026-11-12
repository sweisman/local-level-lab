# SPDX-License-Identifier: AGPL-3.0-or-later
"""Matched uncertainty alternatives must be saved before withheld truth."""
import pytest

from lll.prediction_paired_bound_family import run
from test_prediction_training_law_comparison import candidate


def bounded(target, low, high):
    return dict(scope='affine_known_gaussian_box',
                lower=[low]*9, upper=[high]*9,
                marginal_coverage_lower_bound=.95,
                simultaneous_coverage_established=False,
                true_calibration_inside_box_assumed=True,
                error_covariance_known_assumed=True,
                nonlinear_aircraft_coverage_established=False,
                prediction_target=target, training_epochs=6,
                prediction_epochs=3,
                coordinate_chart='local_unwrapped_geodetic',
                later_observations_used=False,
                scientific_decision='abstain')


def callbacks(*, mismatch=False, failed=False):
    saved = {}
    events = []

    def save(name, value):
        saved[name] = value
        events.append(name)

    def fit(law, save_candidate):
        for name in ('fit.json', 'forecast.json',
                     'forecast-error-diagnostic.json',
                     'receiver-error-diagnostic.json'):
            save_candidate(name, {'law': law})
        for target, artifact in (
                ('physical_position', 'bounded-physical.json'),
                ('receiver_measurement', 'bounded-receiver.json')):
            low, high = (-2., 2.) if law == 'point' else (-1., 1.)
            value = bounded(target, low, high)
            value['error_operator_configuration'] = ('1' if law == 'point' else '0') * 64
            save_candidate(artifact, value)
        record = candidate(10., 1., converged=not (failed and law == 'point'))
        record['diagnostic']['error_operator'] = dict(
            prediction_target='receiver_measurement',
            operator_configuration=('1' if law == 'point' else '0') * 64)
        record['physical_diagnostic'] = dict(error_operator=dict(
            prediction_target='physical_position',
            operator_configuration=('1' if law == 'point' else '0') * 64))
        if mismatch and law == 'point':
            record['binding']['training_receiver_sha256'] = 'c'*64
        return record

    def truth():
        events.append('truth')
        assert 'union-bounded-physical.json' in saved
        assert 'union-bounded-receiver.json' in saved
        return {'later': 'opened'}

    return fit, save, truth, saved, events


def test_saves_both_law_unions_before_truth_without_selecting_a_law():
    fit, save, truth, saved, events = callbacks()
    result = run(('increment', 'point'), fit_candidate=fit,
                 save=save, withheld_truth=truth)
    assert result['bounded_law_family']['physical_position']['lower'] == [-2.]*9
    assert result['bounded_law_family']['physical_position']['upper'] == [2.]*9
    assert result['bounded_law_family']['receiver_measurement']['selected_law'] is None
    assert not result['bounded_law_family']['receiver_measurement']['coverage_calibrated']
    assert events.index('union-bounded-receiver.json') < events.index('truth')


def test_failed_candidate_saves_abstention_before_truth():
    fit, save, truth, saved, events = callbacks(failed=True)
    result = run(('increment', 'point'), fit_candidate=fit,
                 save=save, withheld_truth=truth)
    assert result['comparison']['status'] == 'numerically_unqualified'
    assert not saved['union-bounded-physical.json']['supported']
    assert len(saved['union-bounded-physical.json']['binding_sha256']) == 64
    assert events.index('union-bounded-physical.json') < events.index('truth')


def test_active_fit_bound_keeps_full_box_interval_family():
    fit, save, truth, saved, events = callbacks()

    def at_bound(law, save_candidate):
        record = fit(law, save_candidate)
        if law == 'point':
            record['fit']['active_bounds'] = ['attitude_x']
        return record

    result = run(('increment', 'point'), fit_candidate=at_bound,
                 save=save, withheld_truth=truth)
    assert result['comparison']['status'] == 'active_bounds_unsupported'
    assert result['bounded_law_family']['physical_position']['lower'] == [-2.]*9
    assert events.index('union-bounded-physical.json') < events.index('truth')


def test_mismatched_training_prefix_blocks_truth():
    fit, save, truth, saved, events = callbacks(mismatch=True)
    with pytest.raises(ValueError, match='same measured training prefix'):
        run(('increment', 'point'), fit_candidate=fit,
            save=save, withheld_truth=truth)
    assert 'truth' not in events


def test_missing_bounded_target_blocks_truth():
    fit, save, truth, saved, events = callbacks()

    def incomplete(law, save_candidate):
        def without_receiver(name, value):
            if name != 'bounded-receiver.json':
                save_candidate(name, value)
        return fit(law, without_receiver)

    with pytest.raises(ValueError, match='bounded target'):
        run(('increment', 'point'), fit_candidate=incomplete,
            save=save, withheld_truth=truth)
    assert 'truth' not in events


def test_mismatched_interval_epoch_or_invalid_target_blocks_truth():
    fit, save, truth, saved, events = callbacks()

    def wrong_epoch(law, save_candidate):
        def alter(name, value):
            if name == 'bounded-physical.json' and law == 'point':
                value = dict(value, training_epochs=7)
            save_candidate(name, value)
        return fit(law, alter)

    with pytest.raises(ValueError, match='bounded target'):
        run(('increment', 'point'), fit_candidate=wrong_epoch,
            save=save, withheld_truth=truth)
    assert 'truth' not in events
    with pytest.raises(ValueError, match='finite marginal target'):
        run(('increment', 'point'), fit_candidate=fit, save=save,
            withheld_truth=truth, minimum_marginal_coverage=float('nan'))


def test_interval_must_match_its_own_law_and_target_operator():
    fit, save, truth, saved, events = callbacks()

    def switched_operator(law, save_candidate):
        def alter(name, value):
            if name == 'bounded-physical.json' and law == 'point':
                value = dict(value, error_operator_configuration='0' * 64)
            save_candidate(name, value)
        return fit(law, alter)

    with pytest.raises(ValueError, match='error operator'):
        run(('increment', 'point'), fit_candidate=switched_operator,
            save=save, withheld_truth=truth)
    assert 'truth' not in events


def test_interval_must_match_reported_target_operator():
    fit, save, truth, saved, events = callbacks()

    def wrong_target(law, save_candidate):
        record = fit(law, save_candidate)
        if law == 'point':
            record['physical_diagnostic']['error_operator']['prediction_target'] = 'receiver_measurement'
        return record

    with pytest.raises(ValueError, match='error operator'):
        run(('increment', 'point'), fit_candidate=wrong_target,
            save=save, withheld_truth=truth)
    assert 'truth' not in events
