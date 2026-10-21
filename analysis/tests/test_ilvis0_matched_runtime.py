# SPDX-License-Identifier: AGPL-3.0-or-later
from copy import deepcopy
import pytest


def rows():
    return [dict(model=m,profile=p,passed=True,exact_report_match=True,
        predecessor_s=10.,candidate_s=9.) for m in range(3) for p in (False,True)]


def test_complete_balanced_matrix_must_match_and_meet_both_timing_requirements():
    from lll.ilvis0_matched_runtime import assess
    result=assess(rows())
    assert result['qualified'] and result['median_ratio']==.9
    assert result['cases']==6 and not result['observational_coverage_qualified']


@pytest.mark.parametrize('change',('missing','duplicate','failed','changed-report','slow-median','slow-one'))
def test_missing_results_or_favorable_median_cannot_hide_a_failed_pair(change):
    from lll.ilvis0_matched_runtime import assess
    values=deepcopy(rows())
    if change=='missing':values.pop()
    if change=='duplicate':values[-1]=values[0]
    if change=='failed':values[-1]=dict(model=2,profile=True,passed=False)
    if change=='changed-report':values[-1]['exact_report_match']=False
    if change=='slow-median':
        for row in values:row['candidate_s']=9.6
    if change=='slow-one':values[-1]['candidate_s']=11.1
    assert not assess(values)['qualified']


@pytest.mark.parametrize('value',(0.,-1.,float('nan'),float('inf'),True))
def test_invalid_timing_is_rejected(value):
    from lll.ilvis0_matched_runtime import assess
    values=rows();values[0]['candidate_s']=value
    with pytest.raises(ValueError):assess(values)
