# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.airquantumgrav_same_point_report import render


def _report():
    comparison = dict(values_bitwise_identical=True,
                      boundary_counts_identical=True,
                      maximum_position_difference_m=0.,
                      largest_column=dict(name='attitude_y',
                                          maximum_difference_m_per_normalized_unit=1e-6))
    return dict(verified=True, complete=3, total=3,
                charged=dict(native_calls=12, packet_visits=2302723200),
                rows=[dict(identity=f'case-{i}', complete=True,
                           comparisons=dict(wide=comparison, hybrid=comparison))
                      for i in range(3)],
                method_substitution_requalified=False,
                original_reads=0, protected_reads=0)


def test_public_report_keeps_method_failure_and_small_derivatives_distinct():
    page = render(_report())
    assert '12 of 12' in page
    assert 'unqualified' in page
    assert '1e-06' in page
    assert 'no new fits' in page


def test_public_report_rejects_incomplete_study():
    report = _report()
    report['complete'] = 2
    with pytest.raises(ValueError, match='complete'):
        render(report)
