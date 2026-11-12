"""Rolling-origin publication must choose starts without withheld scores."""

import math

import pytest

from lll.ilvis0_rolling_origin_report import (select_primary, transfer_rows,
                                             selected_detail, fit_audit_row,
                                             csv_bytes)


def _case(origin, start, cost, later_rms, *, passed=True):
    return dict(identity=f's-{origin}-0-header_elapsed-{start}',
                segment_id='s', origin=origin, profile=False,
                clock='header_elapsed', start=start, passed=passed,
                training_cost=cost,
                prediction=dict(north_rms_m=later_rms,
                                east_rms_m=later_rms,
                                vertical_rms_m=later_rms))


def test_primary_uses_training_cost_even_if_later_error_is_worse():
    choices = [_case('inner', 0, 2., .1),
               _case('inner', 1, 1., 3.)]
    assert select_primary(choices)['start'] == 1
    choices[0]['training_cost'] = 1.
    assert select_primary(choices)['start'] == 0


def test_transfer_preserves_abstention_and_matched_ratio():
    cases = [_case('inner', 0, 1., 2.), _case('inner', 1, 2., 200.),
             _case('outer', 0, 1., 4.), _case('outer', 1, 2., 400.)]
    row = transfer_rows(cases)[0]
    assert row['status'] == 'matched'
    assert row['north_ratio'] == 2.
    assert row['inner_identity'] == cases[0]['identity']
    cases[0]['passed'] = cases[1]['passed'] = False
    row = transfer_rows(cases)[0]
    assert row['status'] == 'abstain_inner'
    assert row['north_ratio'] is None


def test_transfer_rejects_nonfinite_saved_error():
    cases = [_case('inner', 0, 1., 2.), _case('inner', 1, 2., 3.),
             _case('outer', 0, 1., 4.), _case('outer', 1, 2., 5.)]
    cases[2]['prediction']['north_rms_m'] = math.nan
    with pytest.raises(ValueError, match='finite'):
        transfer_rows(cases)


def test_selected_detail_reduces_saved_epochs_and_checks_score():
    epochs = [dict(epoch=i, time_s=float(i),
                   role='training' if i < 4 else 'prediction',
                   north_direct_error_m=float(i-4),
                   east_direct_error_m=0., up_direct_error_m=-1.)
              for i in range(8)]
    from lll.ilvis0_saved_prediction import summarize
    score = summarize(epochs, training_epochs=4, prediction_epochs=4)
    detail = selected_detail(epochs, score)
    assert [part['north_rms_m'] for part in detail['quarters']] == [0., 1., 2., 3.]
    assert detail['mean_north_m'] == 1.5
    assert detail['final_signed_up_m'] == -1.
    cases = [_case(origin, start, 1.+start, 2.)
             for origin in ('inner', 'outer') for start in (0, 1)]
    cases[0]['detail'] = cases[2]['detail'] = detail
    row = transfer_rows(cases)[0]
    output = csv_bytes({'rows': [row]}).decode()
    assert 'inner_quarter_4_north_rms_m' in output
    assert 'outer_quarter_4_epochs' in output
    changed = dict(score, prediction=dict(score['prediction'], north_rms_m=9.))
    with pytest.raises(ValueError, match='score'):
        selected_detail(epochs, changed)


def test_fit_audit_keeps_failed_starts_and_bound_activity():
    case = _case('outer', 1, 3., 2., passed=False)
    row = fit_audit_row(case, dict(converged=False, termination='budget',
                                  evaluations=200,
                                  normalized_parameters=[-1., 0., .9999999]))
    assert row['passed'] is False
    assert row['termination'] == 'budget'
    assert row['normalized_parameters_at_bound'] == 2
    assert fit_audit_row(case, None)['normalized_parameters_at_bound'] is None


def test_publication_requires_complete_grid_and_keeps_abstentions(monkeypatch):
    from lll import ilvis0_rolling_origin_report as report
    from lll.ilvis0_saved_prediction import summarize
    epochs = [dict(epoch=i, time_s=float(i),
                   role='training' if i < 4 else 'prediction',
                   north_direct_error_m=1., east_direct_error_m=0.,
                   up_direct_error_m=0.) for i in range(8)]
    score = summarize(epochs, training_epochs=4, prediction_epochs=4)
    class Study:
        completion = {'manifest_sha256': report.MANIFEST_SHA256,
                      'summary_sha256': 'summary', 'state': 'complete'}
        manifest = {'allocation': {'total': 4},
                    'limits': {'maximum_identities': 48},
                    'scope': ('same-source inner/outer NASA development forecasts; '
                              'no originals, protected groups or scientific decision')}
        summary = {'charged': {'native_calls': 48}}
        tasks = {}
        rows = {}
        closed = False
        def envelope(self, identity):
            payload = self.tasks[identity]['payload']
            passed = self.rows[identity]['passed']
            return {'result': dict(training_cost=1. if passed else None,
                                   prediction=score['prediction'] if passed else None,
                                   training=score['training'] if passed else None,
                                   scientific_decision='abstain'),
                    'artifacts': {}}
        def artifact(self, identity, name):
            return score if name == 'scores.json' else epochs
        def close(self):
            self.closed = True
    study = Study()
    for segment in ('s0', 's1', 's2'):
        for origin in ('inner', 'outer'):
            for profile in (False, True):
                for clock in ('header_elapsed', 'nominal_200Hz'):
                    for start in (0, 1):
                        identity = f'{segment}-{origin}-{int(profile)}-{clock}-{start}'
                        study.tasks[identity] = {'payload': dict(
                            segment_id=segment, origin=origin, profile=profile,
                            clock=clock, start=start)}
                        study.rows[identity] = {'passed': (segment == 's0'
                            and profile is False and clock == 'header_elapsed'
                            and start == 0)}
    monkeypatch.setattr(report, 'ClosedStudy', lambda *_: study)
    monkeypatch.setattr(report, 'qualification_sources', lambda *_: [])
    from lll.studies import qualification
    monkeypatch.setattr(qualification, 'checked', lambda *_, **__: (b'q', b't'))
    result = report.build()
    assert study.closed
    assert result['tasks'] == 48
    assert result['matched_settings'] == 1
    assert result['passing_tasks'] == 2
    assert len(result['fit_audit']) == 48
    assert len(result['rows']) == 12
