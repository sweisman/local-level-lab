# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import pytest


def test_positive_clock_path_covers_every_interval_with_correct_boundary_owner():
    from lll.ilvis0_clock_branch_cover import cover
    result=cover([.125]*8,query=.125,clock_center=0,clock_slope=F(1,2))
    assert result.nodes==(F(0),F(1,4),F(1,2),F(3,4),F(1))
    assert tuple(x.packet for x in result.segments)==(1,2,3,4)
    assert result.node_packets==(0,1,2,3,4)  # native <= assigns equality to earlier packet
    assert result.report()['endpoint_owner_mismatches']==[0]
    assert not result.report()['native_floating_point_predicate_covered']


def test_reverse_and_constant_clock_paths_keep_exact_endpoint_ties():
    from lll.ilvis0_clock_branch_cover import cover
    reverse=cover([.125]*8,query=.625,clock_center=0,clock_slope=F(-1,2))
    assert tuple(x.packet for x in reverse.segments)==(4,3,2,1)
    assert reverse.node_packets==(4,3,2,1,0)
    constant=cover([.125]*8,query=.25,clock_center=0,clock_slope=0)
    assert len(constant.segments)==1 and constant.segments[0].packet==1
    assert constant.segments[0].fraction==(F(1),F(1))


def test_rounded_cumulative_starts_expose_fraction_overshoot_instead_of_clipping():
    from lll.ilvis0_clock_branch_cover import cover
    result=cover([.1]*4,query=.28,clock_center=0,clock_slope=F(.04))
    earlier=result.segments[0]
    assert earlier.packet==2 and earlier.fraction[1]>1
    assert earlier.cumulative_error==F(.1+.1+.1)-F(.1+.1)-F(.1)
    assert not result.report()['all_fraction_ranges_within_unit_interval']
    assert result.report()['native_fraction_guard_satisfied']


def test_all_midpoints_and_nodes_match_independent_linear_scan():
    from lll.ilvis0_clock_branch_cover import cover
    periods=[.005,.006,.004,.007,.005,.008]
    result=cover(periods,query=.011,clock_center=F(1,10000),clock_slope=F(13,1000))
    ends=[];current=0.
    for period in periods:current+=period;ends.append(F(current))
    def owner(s):
        q=F(.011)+F(1,10000)+F(13,1000)*s
        return next(k for k,end in enumerate(ends) if q<=end)
    assert result.node_packets==tuple(owner(s) for s in result.nodes)
    for segment,left,right in zip(result.segments,result.nodes,result.nodes[1:]):
        assert segment.packet==owner((left+right)/2)


def test_eight_minute_history_has_complete_plus_minus_one_second_clock_cover():
    from lll.ilvis0_clock_branch_cover import cover
    result=cover([.005]*96000,query=438.,clock_center=-1,clock_slope=2,
        maximum_packets=96000,maximum_branches=401)
    assert len(result.segments)==401 and len(result.nodes)==402
    assert result.nodes[0]==0 and result.nodes[-1]==1
    assert result.report()['native_fraction_guard_satisfied']
    assert all(a.right==b.left for a,b in zip(result.segments,result.segments[1:]))


@pytest.mark.parametrize('change',['nonbinary','negative','outside','branches','slope','packets'])
def test_unsupported_or_incomplete_clock_covers_fail(change):
    from lll.ilvis0_clock_branch_cover import cover
    periods=[.125]*8;kwargs=dict(query=.0625,clock_center=0,clock_slope=F(1,2))
    if change=='nonbinary':periods[0]=F(1,10)
    if change=='negative':periods[0]=-1
    if change=='outside':kwargs['clock_slope']=2
    if change=='branches':kwargs['maximum_branches']=2
    if change=='slope':kwargs['clock_slope']=float('nan')
    if change=='packets':kwargs['maximum_packets']=2
    with pytest.raises(ValueError):cover(periods,**kwargs)
