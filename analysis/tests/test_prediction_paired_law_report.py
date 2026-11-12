# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only paired-law totals distinguish rankings from qualified decisions."""
import copy

import pytest


def case(truth_law='increment', *, converged=True):
    score = dict(epochs=40, marginal_covered=[38, 37, 36],
                 marginal_total=120, confidence_calibrated=False)
    candidate = dict(converged=converged,
                     physical_prediction_passed=converged,
                     marginal_coverage=dict(physical_position=score,
                                            receiver_measurement=score),
                     scientific_decision='abstain')
    comparison = dict(
        status='training_only_unqualified' if converged else 'numerically_unqualified',
        training_ranking=([dict(law_id='increment', delta_nll=0.),
                           dict(law_id='point', delta_nll=2.)]
                          if converged else None),
        active_bounds_by_law={'increment': [], 'point': []},
        maximum_future_sigma_ratio=1.25 if converged else None,
        selected_law=None, later_observations_used=False,
        coverage_calibrated=False, scientific_decision='abstain')
    return dict(truth_law=truth_law, passed=True,
                technical_pair_complete=True, native_calls=1,
                comparison_status=comparison['status'],
                scientific_decision='abstain', original_reads=0,
                protected_reads=0,
                candidate_results={'increment': copy.deepcopy(candidate),
                                   'point': copy.deepcopy(candidate)},
                comparison=comparison)


def test_aggregate_counts_fits_rankings_and_uncalibrated_marginals():
    from lll.prediction_paired_law_report import aggregate
    first = case()
    second = case('point', converged=False)
    result = aggregate([first, second])
    assert result['recordings'] == 2
    assert result['fits'] == 4
    assert result['numerically_passing_fits'] == 2
    assert result['physical_passing_fits'] == 2
    assert result['ranking_cases'] == 1
    assert result['ranking_favors_generating_law'] == 1
    assert result['largest_training_delta_nll'] == 2.
    assert result['largest_future_sigma_ratio'] == 1.25
    assert result['comparison_statuses'] == {
        'training_only_unqualified': 1, 'numerically_unqualified': 1}
    assert result['fixed_parameter_coverage']['physical_position'] == {
        'covered': 444, 'total': 480}
    assert not result['coverage_calibrated']
    assert result['scientific_decision'] == 'abstain'


def test_aggregate_rejects_a_selected_law_or_missing_candidate():
    from lll.prediction_paired_law_report import aggregate
    row = case()
    row['comparison']['selected_law'] = 'increment'
    with pytest.raises(ValueError, match='training-only abstention'):
        aggregate([row])
    row = case()
    row['candidate_results'].pop('point')
    with pytest.raises(ValueError, match='both candidate fits'):
        aggregate([row])


def test_build_requires_complete_matching_saved_study(tmp_path):
    from lll.prediction_paired_law_report import build
    from lll.prediction_paired_law_study import SCOPE, limits, recipe, tasks
    r = recipe()
    work = tasks(r)
    records = {task['identity']:case(task['payload']['truth_law'])
               for task in work}

    class FakeClosed:
        completion = dict(state='complete', summary_sha256='summary')
        summary = dict(state='complete', passed=True, completed=12, total=12,
                       charged=dict(native_calls=12*limits(r)['native_calls'],
                                    packet_visits=12*limits(r)['packet_visits'],
                                    bound_calls=0, bound_steps=0))
        manifest = dict(scope=SCOPE, tasks=work, sources={'source.py':'hash'})
        tasks = {task['identity']:task for task in work}

        def __init__(self):
            self.rows = {identity:None for identity in records}

        def input(self, key):
            return r if key == 'recipe' else {'sources':{'source.py':'hash'}}

        def envelope(self, identity):
            return dict(result={key:value for key,value in records[identity].items()
                                if key != 'comparison'})

        def artifact(self, identity, name):
            assert name == 'training-law-comparison.json'
            return records[identity]['comparison']

        def close(self):
            pass

    report = build(tmp_path, opener=lambda *args:FakeClosed(),
                   source_verifier=lambda *args, **kwargs:{'verified':True})
    assert report['verified'] and report['total']['recordings'] == 12
    assert report['total']['fits'] == 24
    missing = records.pop(work[-1]['identity'])
    with pytest.raises(ValueError, match='complete twelve-case'):
        build(tmp_path, opener=lambda *args:FakeClosed(),
              source_verifier=lambda *args, **kwargs:{'verified':True})
    records[work[-1]['identity']] = missing


def test_publish_writes_plain_result_and_recounted_evidence(tmp_path, monkeypatch):
    from lll import prediction_paired_law_report as report_module
    rows = [dict(identity=f'case-{index}', **case()) for index in range(12)]
    report = dict(verified=True, rows=rows,
                  total=report_module.aggregate(rows),
                  scientific_decision='abstain',
                  confidence_calibrated=False)
    monkeypatch.setattr(report_module, 'build', lambda root: report)
    outcome = report_module.publish(tmp_path)
    target = tmp_path/'docs/prediction-paired-law'
    assert outcome['recordings'] == 12
    text = (target/'RESULT.md').read_text()
    assert '12 generated recordings' in text
    assert '24 candidate fits' in text
    assert 'not a calibrated' in text
    assert 'largest training-score separation' in text
    assert 'abstain' in text
    assert (target/'verified-report.json').is_file()
    assert (target/'results.csv').is_file()
