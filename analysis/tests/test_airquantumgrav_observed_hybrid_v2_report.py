"""Saved-only three-pair publication preserves unresolved cases."""
import pytest

from lll.airquantumgrav_observed_hybrid_v2_report import pair_row, render


def test_v2_report_keeps_unreturned_and_technical_failures():
    missing = pair_row('case-a', None, None)
    failed = pair_row('case-b', {'passed': False, 'error': 'budget'}, None)
    assert missing['returned'] is False
    assert failed['returned'] is True
    assert failed['reason'] == 'budget'
    assert 'unresolved' in render(dict(rows=[missing, failed],
                                       passing_pairs=0, returned=1))


def test_v2_report_rejects_missing_pair_evidence_and_protected_reads():
    with pytest.raises(ValueError, match='saved result'):
        pair_row('case', {'passed': False, 'protected_reads': 1}, None)
    with pytest.raises(ValueError, match='protected'):
        pair_row('case', dict(passed=False, wide={'passed': False},
                              hybrid={'passed': False},
                              comparison={'passed': False}), None)


def test_v2_report_preserves_matched_numerical_failure():
    result = dict(passed=False, original_reads=0, protected_reads=0,
                  scientific_decision='abstain',
                  wide={'passed': False}, hybrid={'passed': False},
                  comparison={'passed': False, 'reason': 'unqualified fit'})
    row = pair_row('case', result, None)
    assert row['wide_passed'] is False
    assert row['revised_passed'] is False
    assert row['reason'] == 'unqualified fit'


def test_v2_report_replays_passing_pair_before_publication(monkeypatch):
    from lll import airquantumgrav_observed_hybrid_v2_report as report
    comparison = {'passed': True, 'maximum_position_difference_m': .004}
    result = dict(passed=True, original_reads=0, protected_reads=0,
                  scientific_decision='abstain',
                  wide={'passed': True}, hybrid={'passed': True},
                  comparison=comparison)
    seen = []
    def replay(*args, **kwargs):
        seen.append(kwargs['tolerance_m'])
        return comparison
    monkeypatch.setattr(report, 'compare_pair', replay)
    row = pair_row('case', result, lambda name: name)
    assert row['passed'] is True
    assert row['maximum_position_difference_m'] == .004
    assert seen == [.01]
    result['comparison'] = {'passed': True, 'maximum_position_difference_m': .02}
    with pytest.raises(ValueError, match='replay'):
        pair_row('case', result, lambda name: name)
