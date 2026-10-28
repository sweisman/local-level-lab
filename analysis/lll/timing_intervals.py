# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded native-clock dispatch partitions; no snapping of scientific times."""
import math
import numpy as np

WINDOW_S=1e-5
MAXIMUM_TRANSITIONS=16
MAXIMUM_BISECTIONS=128
MAXIMUM_CANDIDATE_EDGES=100000


def partition(transitions,*,lower,upper):
    """Partition representable normalized floats, retaining singleton cells."""
    if not math.isfinite(lower) or not math.isfinite(upper) or not -1<=lower<=upper<=1:
        raise ValueError('finite physical timing range required')
    cursor=float(lower);cells=[]
    def append(lo,hi):
        if lo>hi:raise ValueError('overlapping or unordered dispatch transitions')
        anchor=float(lo+(hi-lo)/2)
        cells.append(dict(lower=float(lo),upper=float(hi),anchor=anchor,
            has_representable_interior=bool(lo<anchor<hi)))
    for left,right in transitions:
        if (not math.isfinite(left) or not math.isfinite(right) or not cursor<=left<right<=upper
                or float(np.nextafter(left,np.inf))!=right):
            raise ValueError('ordered adjacent-float transition brackets required')
        append(cursor,left);cursor=right
    append(cursor,upper)
    return cells


def _transition(time,end,scale):
    # Match the wide tangent ABI: offset product is evaluated in long double,
    # rounded to double, then added to the double receiver time for dispatch.
    def query(u):return time+float(np.longdouble(u)*np.longdouble(scale))
    lower,upper=-1.,1.
    if query(lower)>end or query(upper)<=end:return None
    for _ in range(MAXIMUM_BISECTIONS):
        if float(np.nextafter(lower,np.inf))==upper:return lower,upper
        middle=lower+(upper-lower)/2
        if not lower<middle<upper:break
        if query(middle)<=end:lower=middle
        else:upper=middle
    raise ValueError('dispatch transition cannot be resolved within finite bisection allowance')


def local_cells(dt,times,*,scale,point):
    """Return every dispatch cell in a fixed neighborhood plus its outer cells.

    The native provider's derivative override at the exact physical lower bound
    remains the evaluator's responsibility; this does not replace its Jacobian.
    Only identical transition brackets are deduplicated. A large local union
    fails conservatively rather than omitting any receiver transition.
    """
    dt,times=(np.asarray(v,float) for v in (dt,times))
    if (dt.ndim!=1 or not 1<=len(dt)<=2000000 or times.ndim!=1 or not 1<=len(times)<=10000
            or not np.all(np.isfinite(dt)) or np.any(dt<=0)
            or not np.all(np.isfinite(times)) or np.any(np.diff(times)<=0)
            or isinstance(scale,(bool,np.bool_)) or isinstance(point,(bool,np.bool_))
            or not math.isfinite(scale) or scale<=0 or not math.isfinite(point) or not -1<=point<=1):
        raise ValueError('bounded finite native clock, queries, offset scale and feasible point required')
    ends=np.cumsum(dt,dtype=np.float64)
    if (not np.all(np.isfinite(ends)) or np.any(np.diff(ends)<=0)
            or times[0]-scale<0 or times[-1]+scale>ends[-1]):
        raise ValueError('full physical timing support and strictly increasing native clock required')
    low=max(-1.,point-WINDOW_S/scale);high=min(1.,point+WINDOW_S/scale)
    qlow=times+float(np.longdouble(low)*np.longdouble(scale))
    qhigh=times+float(np.longdouble(high)*np.longdouble(scale))
    starts=np.maximum(0,np.searchsorted(ends,qlow,side='left')-1)
    stops=np.minimum(len(ends),np.searchsorted(ends,qhigh,side='right')+1)
    candidates=int(np.sum(stops-starts))
    if candidates>MAXIMUM_CANDIDATE_EDGES:raise ValueError('finite clock-edge allowance exceeded')
    pairs=set()
    for time,start,stop in zip(times,starts,stops):
        for end in ends[start:stop]:
            pair=_transition(float(time),float(end),scale)
            if pair is not None:pairs.add(pair)
    pairs=sorted(pairs)
    nearby=[p for p in pairs if p[1]>=low and p[0]<=high]
    if len(nearby)>MAXIMUM_TRANSITIONS:raise ValueError('too many distinct local timing transitions')
    below=[p[1] for p in pairs if p[1]<low];above=[p[0] for p in pairs if p[0]>high]
    cells=partition(nearby,lower=max(below,default=-1.),upper=min(above,default=1.))
    if not any(c['lower']<=point<=c['upper'] for c in cells):
        raise ValueError('current point omitted from timing partition')
    for cell in cells:
        lo=max(low,cell['lower']);hi=min(high,cell['upper'])
        cell['anchor']=float(lo+(hi-lo)/2 if lo<=hi else np.clip(point,cell['lower'],cell['upper']))
        cell['anchor_local_interval']=[float(lo),float(hi)] if lo<=hi else None
        cell['anchor_is_interior']=bool(cell['lower']<cell['anchor']<cell['upper'])
    return dict(version='native-clock-local-cells-v3',anchor_policy='midpoint_of_local_cell_intersection',
        cells=cells,transitions=[list(p) for p in nearby],
        transition_count=len(nearby),window_s=WINDOW_S,maximum_transitions=MAXIMUM_TRANSITIONS,
        maximum_bisections=MAXIMUM_BISECTIONS,candidate_edges=candidates,
        clock='sequential float64 sum of original packet durations',
        dispatch='float64(query_time + float64(long_double(normalized_offset) * long_double(scale)))',
        timestamps_changed=False,coincident_but_distinct_transitions_merged=False)
