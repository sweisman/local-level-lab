# SPDX-License-Identifier: AGPL-3.0-or-later
"""A recording, not a correlated coordinate, is the coverage unit."""
import pytest

from lll.prediction_simultaneous_report import aggregate, condition_summary_bytes, render


def _row(index, *, covered=True, technical=True):
    targets = ({target:dict(epochs=60, covered=[60, 60, 60],
                            median_width=[1., 1., 1.])
                for target in ('physical_position', 'receiver_measurement')}
               if technical else {})
    if not covered:
        targets['physical_position']['covered'][2] = 59
    return dict(identity=f'case-{index:03d}', status='complete' if technical
                else 'interrupted', technical=technical,
                numerical_passing_fits=2 if technical else 0,
                physical_passing_fits=2 if technical else 0,
                targets=targets)


def test_zero_or_one_failure_meets_the_predeclared_mixture_bound():
    full = aggregate([_row(i) for i in range(96)])
    assert full['whole_recording_successes'] == 96
    assert full['failures'] == 0
    assert full['failure_upper_95'] == pytest.approx(.0307236768)
    assert full['coverage_gate_passed'] is True
    one = aggregate([_row(i, covered=i != 7) for i in range(96)])
    assert one['failures'] == 1
    assert one['failure_upper_95'] == pytest.approx(.0484620717)
    assert one['coverage_gate_passed'] is True


def test_two_failures_or_missing_technical_result_fail_the_gate():
    two = aggregate([_row(i, covered=i not in (7, 8)) for i in range(96)])
    assert two['failures'] == 2
    assert two['coverage_gate_passed'] is False
    lost = aggregate([_row(i, technical=i != 7) for i in range(96)])
    assert lost['failures'] == 1
    assert lost['technical'] == 95


def test_duplicate_or_partial_matrix_rejected():
    with pytest.raises(ValueError):
        aggregate([_row(i) for i in range(95)])
    with pytest.raises(ValueError):
        aggregate([_row(0) for _ in range(96)])


def test_unqualified_intervals_remain_recording_failures():
    rows = [_row(i) for i in range(96)]
    rows[7]['targets'] = {}
    outcome = aggregate(rows)
    assert outcome['technical'] == 96
    assert outcome['whole_recording_successes'] == 95
    assert outcome['targets']['physical_position']['recordings'] == 95


def test_condition_table_counts_recordings_not_coordinates():
    import csv
    import io
    rows = [_row(i) for i in range(96)]
    for row in rows:
        row.update(model='sphere_rotating', profile='retained',
                   truth_law='increment', sensor_case='nominal')
    rows[7]['targets'] = {}
    report = {'rows':rows}
    table = list(csv.DictReader(io.StringIO(
        condition_summary_bytes(report).decode())))
    assert len(table) == 1
    assert table[0]['recordings'] == '96'
    assert table[0]['whole_recording_successes'] == '95'


def test_report_distinguishes_deadline_stops_from_scored_interval_misses():
    rows = [_row(i) for i in range(96)]
    for row in rows:
        row.update(error_type=None, reason=None)
    for index in range(80, 84):
        rows[index] = _row(index, technical=False)
        rows[index]['status'] = 'complete'
        rows[index]['error_type'] = 'BudgetStopped'
        rows[index]['reason'] = 'original cooperative deadline exhausted'
    report = dict(totals=aggregate(rows), rows=rows,
                  charges={'native_calls':1},
                  continuation_lineage_sha256='verified')
    page = render(report)
    assert '4 recordings stopped at the original eight-hour' in page
    assert 'All 92 scored recordings contained every later coordinate' in page
    assert 'technical stops keep the predefined 5% gate from passing' in page
