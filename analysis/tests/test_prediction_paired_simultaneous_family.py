# SPDX-License-Identifier: AGPL-3.0-or-later
"""The two-law whole-period union uses only matched earlier measurements."""
import pytest

from lll.prediction_paired_simultaneous_family import run
from test_prediction_training_law_comparison import candidate


def _interval(target, law, *, support='f'*64):
    configuration = ('1' if law == 'point' else '0')*64
    return dict(scope='affine_known_gaussian_box_bonferroni',
                lower=[-2.]*9, upper=[2.]*9,
                coordinate_count=9, training_epochs=6,
                prediction_epochs=3, prediction_target=target,
                forecast_support_sha256=support,
                error_operator_configuration=configuration,
                affine_conditional_simultaneous_lower_bound=.975,
                affine_conditional_simultaneous_bound_derived=True,
                simultaneous_coverage_established=False,
                true_calibration_inside_box_assumed=True,
                error_covariance_known_assumed=True,
                observed_aircraft_coverage_established=False,
                nonlinear_aircraft_coverage_established=False,
                later_observations_used=False,
                scientific_decision='abstain')


def _callbacks(*, mismatched_support=False, wrong_target=False,
               failed=False):
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
        for target, suffix in (('physical_position', 'physical'),
                               ('receiver_measurement', 'receiver')):
            value = _interval(target, law,
                              support='e'*64 if mismatched_support and
                              law == 'point' and suffix == 'physical'
                              else 'f'*64)
            save_candidate('simultaneous-bounded-'+suffix+'.json', value)
        record = candidate(10., 1., converged=not (failed and law == 'point'))
        for target, key in (('physical_position', 'physical_diagnostic'),
                            ('receiver_measurement', 'diagnostic')):
            descriptor = dict(error_operator=dict(
                prediction_target=('receiver_measurement' if wrong_target and
                                   law == 'point' and key == 'physical_diagnostic'
                                   else target),
                operator_configuration=('1' if law == 'point' else '0')*64))
            if key == 'diagnostic':
                record[key].update(descriptor)
            else:
                record[key] = descriptor
        return record

    def truth():
        events.append('truth')
        assert 'union-simultaneous-bounded-physical.json' in saved
        assert 'union-simultaneous-bounded-receiver.json' in saved
        return {'opened': True}

    return fit, save, truth, saved, events


def test_two_target_union_is_saved_before_truth_without_law_selection():
    fit, save, truth, saved, events = _callbacks()
    result = run(('increment', 'point'), fit_candidate=fit,
                 save=save, withheld_truth=truth)
    assert result['simultaneous_law_family']['physical_position']['scope'] == \
        'union_of_supplied_affine_simultaneous_laws'
    assert result['simultaneous_law_family']['receiver_measurement']['selected_law'] is None
    assert events.index('union-simultaneous-bounded-receiver.json') < events.index('truth')


@pytest.mark.parametrize('change,pattern', [
    ({'mismatched_support': True}, 'forecast support'),
    ({'wrong_target': True}, 'error operator'),
])
def test_changed_support_or_target_blocks_truth(change, pattern):
    fit, save, truth, saved, events = _callbacks(**change)
    with pytest.raises(ValueError, match=pattern):
        run(('increment', 'point'), fit_candidate=fit,
            save=save, withheld_truth=truth)
    assert 'truth' not in events


def test_failed_candidate_abstains_before_truth():
    fit, save, truth, saved, events = _callbacks(failed=True)
    result = run(('increment', 'point'), fit_candidate=fit,
                 save=save, withheld_truth=truth)
    assert result['comparison']['status'] == 'numerically_unqualified'
    assert saved['union-simultaneous-bounded-physical.json']['supported'] is False
    assert events.index('union-simultaneous-bounded-receiver.json') < events.index('truth')


def test_missing_error_operator_rejected_before_truth():
    fit, save, truth, saved, events = _callbacks()

    def missing(law, save_candidate):
        record = fit(law, save_candidate)
        if law == 'point':
            record['physical_diagnostic'] = {}
        return record

    with pytest.raises(ValueError, match='error operator'):
        run(('increment', 'point'), fit_candidate=missing,
            save=save, withheld_truth=truth)
    assert 'truth' not in events
