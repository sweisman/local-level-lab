# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate timing candidate: verify actual representable clock states.

The geometry guard changes; scientific stationarity/cost/position limits do not.
Frozen adapter and stopping modules are executed privately, never modified.
"""
import math
from pathlib import Path
import types

import numpy as np

from . import ilvis0_clock_brackets as clock
from . import ilvis0_boundary_adapter as adapter
from . import ilvis0_boundary_stop as stopping
from . import ilvis0_clustered_boundary as clustered

VERSION='ilvis0-representable-side-clock-v1'
MINIMUM_PARAMETER_ULPS=8


def probe_geometry(knot,left,right,delta=None):
    knot,left,right=map(float,(knot,left,right))
    if (not all(math.isfinite(v) for v in (knot,left,right)) or not -1<=left<knot<right<=1):
        raise ValueError('finite interior knot and adjacent intervals required')
    expected=min(stopping.POLICY['side_step'],(knot-left)/4,(right-knot)/4)
    delta=expected if delta is None else float(delta)
    if not math.isfinite(delta) or delta<0 or delta!=expected:raise ValueError('unchanged side-probe construction required')
    points=[knot-delta,knot-delta/4,knot+delta,knot+delta/4]
    required=MINIMUM_PARAMETER_ULPS*math.ulp(knot)
    distinct=len(set(points+[knot]))==5
    inside=left<points[0]<points[1]<knot<points[3]<points[2]<right
    resolved=all(abs(p-knot)>=required for p in points)
    return dict(passed=bool(distinct and inside and resolved),side_points=points,delta=delta,
        minimum_parameter_ulps=MINIMUM_PARAMETER_ULPS,minimum_required_spacing=required,
        minimum_actual_spacing=min(abs(p-knot) for p in points),
        reason='distinct_representable_side_probes' if distinct and inside and resolved else 'unresolved_side_probes')


def bracket(times,packet_count,scale,point,*,maximum_queries=1024):
    if type(maximum_queries) is not int or maximum_queries<7:raise ValueError('geometry budget must reserve six direct clock checks')
    result=clock.bracket(times,packet_count,scale,point,maximum_queries=maximum_queries-6)
    knot=result['point'];knots=result['knots'];i=knots.index(knot)
    geometry=probe_geometry(knot,knots[i-1],knots[i+1])
    ends=np.cumsum(np.full(packet_count,.005));times=np.asarray(times,float)
    before=clock.indices(ends,times,scale,math.nextafter(knot,-math.inf))
    at=clock.indices(ends,times,scale,knot)
    matches=[]
    for n,value in enumerate(geometry['side_points']):
        actual=clock.indices(ends,times,scale,value)
        matches.append(bool(np.array_equal(actual,before if n<2 else at)))
    geometry.update(clock_state_matches=matches,adjacent_clock_states_distinct=not np.array_equal(before,at))
    result.update(original_side_geometry_supported=result['side_geometry_supported'],representability=geometry,
        side_geometry_supported=bool(geometry['passed'] and geometry['adjacent_clock_states_distinct'] and all(matches)
            and geometry['side_points']==result['side_points']),
        queries=result['queries']+6,maximum_queries=maximum_queries,representability_version=VERSION)
    return result


def private_module(name,path,source=None):
    result=types.ModuleType('lll.'+name);result.__file__=str(path);result.__package__='lll'
    exec(compile(path.read_text() if source is None else source,str(path),'exec'),result.__dict__)
    return result


def build_candidate():
    path=Path(stopping.__file__);source=path.read_text()
    old="if delta/4<POLICY['minimum_side_step']:raise ValueError('neighbor knots insufficiently separated')"
    new="if not probe_geometry(knot,edges[0],edges[1],delta)['passed']:raise ValueError('unrepresentable adjacent side probes')"
    if source.count(old)!=1:raise ValueError('unrecognized frozen stopping guard')
    side=private_module('_representable_boundary_stop',path,source.replace(old,new))
    side.probe_geometry=probe_geometry
    side.POLICY.update(minimum_side_step=None,minimum_parameter_ulps=MINIMUM_PARAMETER_ULPS,
        geometry_guard='distinct probes inside exact adjacent clock states',geometry_version=VERSION)
    core=private_module('_representable_boundary_adapter',Path(adapter.__file__))
    core.clock=types.SimpleNamespace(bracket=bracket,indices=clock.indices)
    core.stopping=side
    helper=private_module('_representable_clustered_boundary',Path(clustered.__file__))
    helper.adapter=core
    return helper


def check_endpoint(*args,**kwargs):
    result=build_candidate().check_endpoint(*args,**kwargs)
    result.update(representability_version=VERSION,scientific_stopping_limits_changed=False)
    return result
