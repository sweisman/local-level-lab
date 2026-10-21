# SPDX-License-Identifier: AGPL-3.0-or-later
from copy import deepcopy
import pytest


def baseline():
    return dict(case_id='same-case',frame_sha256='a'*64,complete=True,lower=[-10.]*3,upper=[10.]*3)


def regions():
    return [dict(region_id=i,case_id='same-case',frame_sha256='a'*64,passed=True,excluded=False,
        lower=[-2.+i/8]*3,upper=[1.+i/8]*3) for i in range(8)]


def test_complete_cover_is_unioned_before_intersecting_inherited_range():
    from lll.ilvis0_reused_cover import combine
    result=combine(baseline(),regions(),expected_regions=8)
    assert result['fresh_complete'] and result['inherited_complete'] and result['combined_complete']
    assert result['fresh_lower']==[-2.]*3 and result['fresh_upper']==[1.875]*3
    assert result['lower']==[-2.]*3 and result['upper']==[1.875]*3
    assert result['mode']=='complete-intersection'


@pytest.mark.parametrize('kind',('missing','failed'))
def test_incomplete_fresh_cover_uses_only_complete_inherited_range(kind):
    from lll.ilvis0_reused_cover import combine
    rows=regions()
    if kind=='missing':rows.pop()
    else:rows[-1]=dict(rows[-1],passed=False)
    result=combine(baseline(),rows,expected_regions=8)
    assert not result['fresh_complete'] and result['combined_complete']
    assert result['fresh_lower'] is None and result['fresh_upper'] is None
    assert result['lower']==[-10.]*3 and result['upper']==[10.]*3
    assert result['mode']=='inherited-only'


def test_certified_empty_regions_count_toward_coverage_but_not_the_union():
    from lll.ilvis0_reused_cover import combine
    rows=regions();rows[0]=dict(rows[0],excluded=True)
    result=combine(baseline(),rows,expected_regions=8)
    assert result['fresh_complete'] and result['excluded_regions']==1
    assert result['fresh_lower']==[-1.875]*3


@pytest.mark.parametrize('kind',('frame','case','duplicate','unexpected','incomplete-baseline','disjoint','all-empty','invalid-range'))
def test_unsupported_coverage_or_coordinate_assumptions_are_rejected(kind):
    from lll.ilvis0_reused_cover import combine
    old=baseline();rows=regions()
    if kind=='frame':rows[0]['frame_sha256']='b'*64
    if kind=='case':rows[0]['case_id']='other-case'
    if kind=='duplicate':rows[-1]['region_id']=0
    if kind=='unexpected':rows[-1]['region_id']=8
    if kind=='incomplete-baseline':old['complete']=False
    if kind=='disjoint':old.update(lower=[20.]*3,upper=[30.]*3)
    if kind=='all-empty':
        for row in rows:row['excluded']=True
    if kind=='invalid-range':rows[0]['upper']=[-100.]*3
    with pytest.raises(ValueError):combine(old,rows,expected_regions=8)
