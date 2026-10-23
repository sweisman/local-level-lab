# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact affine-clock branch cover using binary64 cumulative packet times.

This covers the ideal affine query with the native recorded boundary constants.
It does not cover rounding in the native query predicate, trajectory derivatives
or one-sided trajectory jumps. No measurement is interpolated or repaired.
"""
from bisect import bisect_left
from dataclasses import dataclass
from fractions import Fraction as F
import math
from .ilvis0_piecewise_trapezoid import _number


def _binary(value):
    value=_number(value)
    try:out=float(value)
    except OverflowError:raise ValueError('finite unchanged binary64 constant required') from None
    if not math.isfinite(out) or F(out)!=value:
        raise ValueError('finite unchanged binary64 constant required')
    return out


@dataclass(frozen=True)
class Segment:
    left:F
    right:F
    packet:int
    fraction:tuple
    cumulative_error:F


@dataclass(frozen=True)
class Cover:
    nodes:tuple
    segments:tuple
    node_packets:tuple

    def report(self):
        mismatches=[]
        if self.node_packets[0]!=self.segments[0].packet:mismatches.append(0)
        if self.node_packets[-1]!=self.segments[-1].packet:mismatches.append(1)
        return dict(version='ilvis0-affine-clock-branch-cover-v1',partition=list(map(str,self.nodes)),
            node_packets=list(self.node_packets),segments=[dict(left=str(s.left),right=str(s.right),
                packet=s.packet,fraction=list(map(str,s.fraction)),cumulative_error_s=str(s.cumulative_error))
                for s in self.segments],endpoint_owner_mismatches=mismatches,
            all_fraction_ranges_within_unit_interval=all(0<=s.fraction[0]<=s.fraction[1]<=1 for s in self.segments),
            native_fraction_guard_satisfied=all(F(-1e-10)<=s.fraction[0]<=s.fraction[1]<=F(1+1e-10)
                for s in self.segments),ideal_affine_query_partition_complete=True,
            native_cumulative_constants_preserved=True,native_nearest_rounding_assumed=True,
            native_floating_point_predicate_covered=False,trajectory_jump_bounds_verified=False,
            native_history_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')


def cover(periods,*,query,clock_center,clock_slope,maximum_packets=1000000,maximum_branches=4095):
    """Cover s in [0,1] for exact query+center+s*slope.

Segments describe open interiors; node_packets preserves equality ownership
separately. The native <= predicate assigns exact boundary equality to the
earlier packet, including when that is only an isolated endpoint of this path.
Packet starts use sequential binary64 additions, not an exact sum of periods.
"""
    if (type(maximum_packets) is not int or not 1<=maximum_packets<=1000000
            or not 1<=len(periods)<=maximum_packets or type(maximum_branches) is not int
            or not 1<=maximum_branches<=4095):
        raise ValueError('finite packet and branch allowances required')
    dt=tuple(_binary(t) for t in periods)
    if any(t<=0 for t in dt):raise ValueError('strictly positive packet periods required')
    q=F(_binary(query))+_number(clock_center);slope=_number(clock_slope)
    ends=[];current=0.
    for t in dt:
        end=current+t
        if not math.isfinite(end) or end<=current:raise ValueError('finite strictly ordered native timestamps required')
        ends.append(F(end));current=end
    low,high=sorted((q,q+slope))
    if low<0 or high>ends[-1]:raise ValueError('entire query path must be covered; clipping forbidden')
    nodes=[F(0),F(1)]
    if slope:
        for t in ends[bisect_left(ends,low):bisect_left(ends,high)+1]:
            value=(t-q)/slope
            if 0<value<1:nodes.append(value)
    nodes=tuple(sorted(set(nodes)))
    if len(nodes)-1>maximum_branches:raise ValueError('clock branch allowance exhausted')
    owner=lambda s:bisect_left(ends,q+slope*s)
    segments=[]
    for left,right in zip(nodes,nodes[1:]):
        k=owner((left+right)/2);start=ends[k-1] if k else F(0);period=F(dt[k])
        fraction=tuple(sorted(((q+slope*left-start)/period,(q+slope*right-start)/period)))
        segments.append(Segment(left,right,k,fraction,ends[k]-start-period))
    return Cover(nodes,tuple(segments),tuple(owner(s) for s in nodes))
