"""Saved-only publication checks for the ESA development continuation."""

from types import SimpleNamespace

import pytest

from lll.prediction_observed_continuation_report import summarize


def _closed(*, supported=False, score=None, refits=0):
    identity = 'generated-no-refit'
    reason = None if supported else 'candidate_fit_unqualified'
    artifacts = {
        'technical-summary.json': dict(
            passed=True, group_id='generated-worker-smoke',
            training_epochs=6, prediction_epochs=3, original_reads=0,
            protected_reads=0, refits=refits,
            receiver_interval_supported=supported,
            receiver_interval_score=score, confidence_calibrated=False,
            scientific_decision='abstain'),
        'training-law-comparison.json': dict(
            status='qualified' if supported else 'numerically_unqualified'),
        'union-simultaneous-bounded-physical.json': dict(
            supported=supported, prediction_target='physical_position',
            reason=reason),
        'union-simultaneous-bounded-receiver.json': dict(
            supported=supported, prediction_target='receiver_measurement',
            reason=reason),
        'withheld-receiver-score.json': dict(
            training_epochs=6, prediction_epochs=3,
            receiver_interval_score=score, interval_reason=reason,
            physical_position_truth_available=False,
            physical_position_interval_scored=False,
            receiver_values_used_for_training=False,
            confidence_calibrated=False, scientific_decision='abstain'),
        'point/simultaneous-bounded-receiver.json': dict(
            prediction_target='receiver_measurement',
            training_epochs=6, prediction_epochs=3,
            later_observations_used=False),
        'point/receiver-error-diagnostic.json': dict(
            prediction_target='receiver_measurement',
            later_observations_used=False),
    }
    return SimpleNamespace(
        completion=dict(state='complete', manifest_sha256='a'*64,
                        summary_sha256='b'*64),
        summary=dict(total=1, completed=1, results=[dict(
            identity=identity, passed=True, status='complete')]),
        artifact=lambda selected, name: artifacts[name],
        envelope=lambda selected: dict(identity=selected),
    )


def test_saved_report_keeps_unsupported_interval_as_abstention():
    report = summarize(_closed(), identity='generated-no-refit',
                       group_id='generated-worker-smoke',
                       training_epochs=6, prediction_epochs=3)
    assert report['receiver_interval_supported'] is False
    assert report['receiver_interval_score'] is None
    assert report['interval_reason'] == 'candidate_fit_unqualified'
    assert report['scientific_decision'] == 'abstain'


def test_saved_report_accepts_scored_interval_without_claiming_calibration():
    score = dict(all_inside=True, outside_count=0)
    report = summarize(_closed(supported=True, score=score),
                       identity='generated-no-refit',
                       group_id='generated-worker-smoke',
                       training_epochs=6, prediction_epochs=3)
    assert report['receiver_interval_score'] == score
    assert report['confidence_calibrated'] is False


def test_saved_report_rejects_refit_or_unsealed_study():
    with pytest.raises(ValueError, match='refit'):
        summarize(_closed(refits=1), identity='generated-no-refit',
                  group_id='generated-worker-smoke',
                  training_epochs=6, prediction_epochs=3)
    unfinished = _closed()
    unfinished.completion['state'] = 'running'
    with pytest.raises(ValueError, match='closed'):
        summarize(unfinished, identity='generated-no-refit',
                  group_id='generated-worker-smoke',
                  training_epochs=6, prediction_epochs=3)


def test_saved_report_rejects_a_score_disagreeing_with_its_interval():
    closed = _closed()
    original = closed.artifact

    def changed(identity, name):
        value = original(identity, name)
        if name == 'withheld-receiver-score.json':
            return dict(value, interval_reason='different_reason')
        return value

    closed.artifact = changed
    with pytest.raises(ValueError, match='matching abstention'):
        summarize(closed, identity='generated-no-refit',
                  group_id='generated-worker-smoke',
                  training_epochs=6, prediction_epochs=3)
