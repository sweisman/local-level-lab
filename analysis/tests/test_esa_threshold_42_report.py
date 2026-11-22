"""Whole-history gate, including technical failures."""

from lll.esa_threshold_42_report import summarize
from lll.esa_threshold_42_validation import POLICY


def _rows():
    return [dict(seed=seed, vibration=(seed % 2 == 0),
                 technical_pass=True, range_contained=True,
                 maximum_absolute_standardized_error=2.,
                 endpoint_half_width_m=30.) for seed in POLICY['seeds']]


def test_exact_per_stratum_failure_gate():
    rows = _rows()
    report = summarize(rows)
    assert report['generated_gate_passed'] is True
    rows[0]['maximum_absolute_standardized_error'] = 5.
    rows[0]['range_contained'] = False
    rows[1]['maximum_absolute_standardized_error'] = 5.
    rows[1]['range_contained'] = False
    assert summarize(rows)['generated_gate_passed'] is True
    rows[2]['maximum_absolute_standardized_error'] = 5.
    rows[2]['range_contained'] = False
    report = summarize(rows)
    assert report['generated_gate_passed'] is False
    assert [item['failures'] for item in report['strata']] == [1, 2]
    rows[2]['technical_pass'] = False
    assert summarize(rows)['generated_gate_passed'] is False


def test_missing_or_duplicate_seed_rejected():
    rows = _rows()
    try:
        summarize(rows[:-1])
    except ValueError:
        pass
    else:
        raise AssertionError('missing seed accepted')
    rows[-1]['seed'] = rows[0]['seed']
    try:
        summarize(rows)
    except ValueError:
        pass
    else:
        raise AssertionError('duplicate seed accepted')
