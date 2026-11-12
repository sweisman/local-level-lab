"""A recorded flight, rather than each correlated epoch, is the audit unit."""
import pytest

from lll.prediction_paired_bound_report import aggregate, render, replay_union_scores


def score(*, miss=False):
    return dict(epochs=3, marginal_covered=[2 if miss else 3, 3, 3],
                marginal_total=9, median_width_by_axis=[1., 2., 3.],
                nonlinear_coverage_established=False,
                scientific_decision='abstain')


def rows():
    return [dict(identity=f'case-{index}', status='complete', technical=True,
                 numerical_passing_fits=2, physical_passing_fits=2,
                 union_scores=dict(physical_position=score(miss=index == 0),
                                   receiver_measurement=score()),
                 scientific_decision='abstain')
            for index in range(24)]


def test_coverage_audit_counts_recordings_and_correlated_coordinates_separately():
    total = aggregate(rows())
    assert total['method_gate_passed']
    assert total['union_recordings'] == 24
    assert total['both_targets_whole_recording'] == 23
    assert total['targets']['physical_position']['whole_recordings'] == 23
    assert total['targets']['physical_position']['marginal_covered'] == 215
    assert total['targets']['physical_position']['marginal_total'] == 216
    assert total['targets']['physical_position']['median_case_width_by_axis'] == [1., 2., 3.]
    assert not total['coverage_calibrated']


def test_failed_or_unstarted_recording_remains_failed_gate():
    values = rows()
    values[0] = dict(values[0], status='unstarted', technical=False,
                     numerical_passing_fits=0, physical_passing_fits=0,
                     union_scores=None)
    total = aggregate(values)
    assert total['completed'] == 23
    assert total['technical'] == 23
    assert not total['method_gate_passed']
    assert total['targets']['physical_position']['recordings'] == 23


def test_invalid_coordinate_score_is_rejected():
    values = rows()
    values[0]['union_scores']['physical_position']['marginal_covered'] = [4, 3, 3]
    with pytest.raises(ValueError, match='descriptive withheld interval'):
        aggregate(values)


def test_public_result_keeps_uncertainty_claim_separate():
    text = render(dict(verified=True, total=aggregate(rows()),
                       coverage_calibrated=False, scientific_decision='abstain'))
    assert '24/24 technical gate passed' in text
    assert 'do not establish 95% coverage' in text


def test_saved_union_score_replays_from_later_truth_without_a_refit():
    binding = dict(training_epochs=3, prediction_epochs=3)
    truth = dict(coordinates=[[0., 0., 0.]] * 6)
    receiver = dict(training_prefix_exact=True,
                    later_observations_used_for_training=False,
                    rows=[dict(latitude_deg=0., longitude_deg=0., height_m=0.)] * 6)
    interval = dict(scope='union_of_supplied_affine_known_laws',
                    lower=[-1.] * 9, upper=[1.] * 9)
    result = replay_union_scores(binding, truth, receiver,
                                 dict(physical_position=interval,
                                      receiver_measurement=interval))
    assert result['physical_position']['marginal_covered'] == [3, 3, 3]
    assert result['receiver_measurement']['epochs'] == 3
    truth['coordinates'][-1] = [0., 0., 2.]
    result = replay_union_scores(binding, truth, receiver,
                                 dict(physical_position=interval,
                                      receiver_measurement=interval))
    assert result['physical_position']['marginal_covered'] == [3, 3, 2]


def test_saved_union_replay_rejects_ambiguous_binding():
    with pytest.raises(ValueError, match='withheld scoring binding'):
        replay_union_scores(dict(training_epochs=3, prediction_epochs=3),
                            dict(coordinates=[[0., 0., 0.]] * 6),
                            dict(training_prefix_exact=False,
                                 later_observations_used_for_training=False,
                                 rows=[]),
                            dict(physical_position={}, receiver_measurement={}))


def _sealed_view():
    from types import SimpleNamespace
    from lll.prediction_paired_bound_study import SCOPE, tasks, recipe
    from lll.prediction_paired_bound_report import replay_union_scores

    work = tasks()
    cut = 2*recipe()['queries']//3
    future = recipe()['queries']-cut
    binding = dict(training_epochs=cut, prediction_epochs=future)
    truth = dict(coordinates=[[0., 0., 0.]] * recipe()['queries'])
    receiver = dict(training_prefix_exact=True,
                    later_observations_used_for_training=False,
                    rows=[dict(latitude_deg=0., longitude_deg=0., height_m=0.)]
                    * recipe()['queries'])
    interval = dict(scope='union_of_supplied_affine_known_laws',
                    lower=[-1.] * (3*future), upper=[1.] * (3*future))
    intervals = dict(physical_position=interval,
                     receiver_measurement=interval)
    scores = replay_union_scores(binding, truth, receiver, intervals)
    answers = {}
    for task in work:
        payload = task['payload']
        answers[task['identity']] = dict(
            passed=True, technical_pair_complete=True,
            scientific_decision='abstain', original_reads=0,
            protected_reads=0, native_calls=1,
            truth_law=payload['truth_law'],
            sensor_case=payload['sensor_case'],
            union_scores=scores,
            numerical_passing_fits=2, physical_passing_fits=2,
            candidate_results={law:dict(converged=True,
                                        physical_prediction_passed=True)
                               for law in ('increment', 'point')})

    def artifact(identity, name):
        if name == 'input-binding.json':
            return binding
        if name == 'withheld-physical-truth.json':
            return truth
        if name == 'later-receiver-report.json':
            return receiver
        if name == 'union-bounded-physical.json' or name == 'union-bounded-receiver.json':
            return interval
        if name == 'union-scores.json':
            return scores
        if name.endswith('/fit.json'):
            return dict(converged=True, stopping_rule_verified=True)
        return {}

    study = SimpleNamespace(
        manifest=dict(scope=SCOPE, allocation=dict(workers=4, threads=1),
                      sources={}),
        input=lambda key: recipe() if key == 'recipe' else {'sources':{}},
        tasks={task['identity']:task for task in work},
        rows={task['identity']:dict(status='complete', passed=True)
              for task in work},
        envelope=lambda identity: dict(result=answers[identity]),
        artifact=artifact,
        completion=dict(manifest_sha256='a'*64, summary_sha256='b'*64),
        summary=dict(charged={}), close=lambda: None)
    return study, answers


def test_full_saved_audit_recounts_all_frozen_conditions(monkeypatch):
    from lll import prediction_paired_bound_report as report
    from lll.studies import source_binding
    study, answers = _sealed_view()
    monkeypatch.setattr(report, 'open_view', lambda root: (study, None))
    monkeypatch.setattr(source_binding, 'verify', lambda *args, **kwargs: {})
    result = report.build('.')
    assert result['verified']
    assert result['total']['method_gate_passed']
    assert result['total']['both_targets_whole_recording'] == 24
    assert len(result['rows']) == 24


def test_full_saved_audit_rejects_tampered_coverage(monkeypatch):
    from lll import prediction_paired_bound_report as report
    from lll.studies import source_binding
    study, answers = _sealed_view()
    first = next(iter(answers.values()))
    first['union_scores'] = dict(first['union_scores'],
                                 physical_position=dict(
                                     first['union_scores']['physical_position'],
                                     marginal_covered=[1, 1, 1]))
    monkeypatch.setattr(report, 'open_view', lambda root: (study, None))
    monkeypatch.setattr(source_binding, 'verify', lambda *args, **kwargs: {})
    with pytest.raises(ValueError, match='reported union scores differ'):
        report.build('.')
