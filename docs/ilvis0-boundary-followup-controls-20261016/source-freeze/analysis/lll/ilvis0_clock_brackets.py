# SPDX-License-Identifier: AGPL-3.0-or-later
"""Locate representable native-clock transitions using saved timing geometry only."""
import numpy as np
from .ilvis0_boundary_stop import POLICY

VERSION='ilvis0-representable-clock-brackets-v1'


def indices(ends,times,scale,point):
    # The compiled comparison uses a double product followed by a double sum.
    shifted=np.asarray(times,float)+float(np.float64(point)*np.float64(scale))
    return np.searchsorted(ends,shifted,side='left')


def bracket(times,packet_count,scale,point,*,maximum_queries=1024):
    times=np.asarray(times,float);point=float(point);scale=float(scale)
    if (times.ndim!=1 or len(times)<2 or not np.all(np.isfinite(times)) or np.any(np.diff(times)<=0)
            or type(packet_count) is not int or packet_count<1 or not np.isfinite(scale) or scale<=0
            or not np.isfinite(point) or abs(point)>1 or type(maximum_queries) is not int or maximum_queries<1):
        raise ValueError('finite ordered saved geometry and bounded time required')
    ends=np.cumsum(np.full(packet_count,.005))
    if times[0]-scale<0 or times[-1]+scale>ends[-1]:raise ValueError('saved receiver times lack full clock support')
    calls=0
    def query(u):
        nonlocal calls
        if calls>=maximum_queries:raise RuntimeError('clock query budget exhausted')
        calls+=1
        return indices(ends,times,scale,u)
    def plateau(u):
        base=query(u);left=query(-1.);right=query(1.)
        if np.array_equal(base,left):first=-1.;before=None
        else:
            a,b=-1.,u
            for _ in range(128):
                if np.nextafter(a,b)>=b:break
                mid=a+(b-a)/2
                if np.array_equal(query(mid),base):b=mid
                else:a=mid
            else:raise ValueError('left clock transition did not bracket')
            first,before=b,a
        if np.array_equal(base,right):after=None
        else:
            a,b=u,1.
            for _ in range(128):
                if np.nextafter(a,b)>=b:break
                mid=a+(b-a)/2
                if np.array_equal(query(mid),base):a=mid
                else:b=mid
            else:raise ValueError('right clock transition did not bracket')
            after=b
        return dict(first=first,before=before,after=after,indices=base)
    current=plateau(point)
    choices=[u for u in (current['first'],current['after']) if u is not None and u not in (-1.,1.)]
    if not choices:raise ValueError('no interior clock transition in physical range')
    knot=min(choices,key=lambda u:abs(u-point));center=plateau(knot)
    if center['first']!=knot or center['before'] is None:raise ValueError('canonical clock transition mismatch')
    previous=plateau(center['before']);lo=previous['first'];hi=center['after'] if center['after'] is not None else 1.
    delta=min(POLICY['side_step'],(knot-lo)/4,(hi-knot)/4)
    samples=[knot-delta,knot-delta/4,knot+delta,knot+delta/4]
    supported=delta/4>=POLICY['minimum_side_step']
    for n,u in enumerate(samples):
        expected=previous['indices'] if n<2 else center['indices']
        supported=bool(np.array_equal(query(u),expected) and supported)
    return dict(version=VERSION,point=knot,original_point=point,knots=sorted(set([-1.,lo,knot,hi,1.])),
        center_relocation_s=(knot-point)*scale,left_interval_width_s=(knot-lo)*scale,
        right_interval_width_s=(hi-knot)*scale,minimum_side_probe_s=delta/4*scale,
        boundary_changed_epochs=int(np.sum(center['indices']!=previous['indices'])),
        side_points=samples,side_geometry_supported=bool(supported),queries=calls,
        maximum_queries=maximum_queries,native_predictions=0,observed_fit_starts=0)
