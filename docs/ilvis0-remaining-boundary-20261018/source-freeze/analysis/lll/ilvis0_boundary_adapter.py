# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite timing-only search and fresh two-sided diagnostics; no scientific gate."""
import numpy as np
from . import ilvis0_clock_brackets as clock,ilvis0_boundary_stop as stopping

VERSION='ilvis0-cluster-timing-adapter-v1'
POLICY=dict(window_s=1e-6,maximum_clock_queries=200000,maximum_geometry_queries=1024,
            maximum_search_evaluations=12,maximum_evaluations=26,
            time_only_search=True,joint_nuisance_fit_starts=0,
            scope='local sign-change search, not a global or statistical decision')


def transitions(times,packet_count,scale,point,*,window_s=1e-6,maximum_queries=200000):
    """Enumerate first-right representable doubles, without merging nearby events."""
    times=np.asarray(times,float);scale=float(scale);point=float(point)
    if (times.ndim!=1 or len(times)<2 or not np.all(np.isfinite(times)) or np.any(np.diff(times)<=0)
            or type(packet_count) is not int or packet_count<1 or not np.isfinite(scale) or scale<=0
            or not np.isfinite(point) or abs(point)>1 or not np.isfinite(window_s) or not 0<window_s<.0025
            or type(maximum_queries) is not int or maximum_queries<1):
        raise ValueError('finite supported geometry and sub-packet search window required')
    ends=np.cumsum(np.full(packet_count,.005))
    if times[0]-scale<0 or times[-1]+scale>ends[-1]:raise ValueError('receiver times lack full clock support')
    low=max(-1.,point-window_s/scale);high=min(1.,point+window_s/scale);queries=0
    def charge():
        nonlocal queries
        if queries>=maximum_queries:raise RuntimeError('clock query budget exhausted')
        queries+=1
    def indices(u):charge();return clock.indices(ends,times,scale,u)
    left,right=indices(low),indices(high);roots=[]
    if np.any(right-left>1):raise ValueError('search window crosses multiple packets per epoch')
    for i in np.flatnonzero(right!=left):
        edge=ends[left[i]];a,b=low,high
        for _ in range(128):
            if np.nextafter(a,b)>=b:break
            mid=a+(b-a)/2;charge()
            # Same double product, double sum and <= comparison as the native loop.
            if times[i]+float(np.float64(mid)*np.float64(scale))<=edge:a=mid
            else:b=mid
        else:raise ValueError('representable transition failed to bracket')
        if not low<b<high:raise ValueError('transition at search-window edge')
        roots.append(float(b))
    return dict(knots=sorted(set(roots)),left=low,right=high,clock_queries=queries,
                maximum_queries=maximum_queries,window_s=window_s)


def locate(knots,left,right,derivative,*,maximum_evaluations=12):
    """Find some negative-to-positive adjacent crossing; no monotonicity assumed."""
    knots=np.asarray(knots,float);samples=[]
    if (knots.ndim!=1 or not np.all(np.isfinite(knots)) or np.any(np.diff(knots)<=0)
            or not np.isfinite(left) or not np.isfinite(right) or not -1<=left<right<=1
            or np.any(knots<=left) or np.any(knots>=right)
            or type(maximum_evaluations) is not int or not 2<=maximum_evaluations<=12):
        raise ValueError('finite ordered search partition and bounded allowance required')
    def result(passed,reason,**extra):return dict(passed=passed,reason=reason,evaluations=len(samples),samples=samples,**extra)
    if not len(knots):return result(False,'no_transition_in_window')
    def sample(u):
        value=float(derivative(float(u)))
        if not np.isfinite(value):raise ValueError('nonfinite timing derivative')
        samples.append(dict(point=float(u),gradient=value));return value
    a,b=sample(left),sample(right)
    if not a<0<b:return result(False,'no_negative_to_positive_bracket')
    lo,hi=0,len(knots)
    while hi-lo>1:
        if len(samples)>=maximum_evaluations:return result(False,'search_budget_exhausted')
        mid=(lo+hi)//2;u=knots[mid-1]+(knots[mid]-knots[mid-1])/2
        if not knots[mid-1]<u<knots[mid]:return result(False,'unrepresentable_plateau')
        g=sample(u)
        if g<0:lo=mid
        elif g>0:hi=mid
        else:return result(False,'smooth_zero_requires_separate_check')
    return result(True,'adjacent_sign_change',point=float(knots[lo]))


def displacement_metrics(old,new,physical_step):
    a,b=np.asarray(old,np.longdouble),np.asarray(new,np.longdouble)
    if a.shape!=b.shape:raise ValueError('residual shape changed')
    delta=np.asarray(physical_step(np.asarray(b-a,float)),float)
    if delta.ndim!=2 or delta.shape[1]!=3 or not len(delta) or not np.all(np.isfinite(delta)):
        raise ValueError('finite physical prediction mapping required')
    change=float(b@b-a@a);relative=abs(change)/max(float(a@a),float(b@b),1.)
    rms=np.sqrt(np.mean(delta**2,axis=0));maximum=np.max(abs(delta),axis=0)
    p=stopping.POLICY
    return dict(passed=bool(relative<=p['relative_cost_tolerance'] and np.all(rms<=p['position_rms_tolerance_m'])
        and np.all(maximum<=p['position_max_tolerance_m'])),signed_cost_change=change,relative_cost_change=relative,
        position_rms=rms.tolist(),position_maximum=maximum.tolist())


def diagnose(point,evaluate,physical_step,*,time_index,times,packet_count,scale,maximum_evaluations=26):
    """Time-only observed start followed by full-nuisance local probes (26-call cap)."""
    point=np.array(point,float);calls=0;trace=[];details={}
    if (maximum_evaluations!=26 or type(maximum_evaluations) is not int or point.ndim!=1
            or not len(point) or not np.all(np.isfinite(point)) or np.any(abs(point)>1)
            or type(time_index) is not int or not 0<=time_index<len(point)):
        raise ValueError('finite feasible point, time index and exact 26-call budget required')
    geometry=transitions(times,packet_count,scale,point[time_index])
    details['clock_search']=geometry
    def result(passed,reason):return dict(version=VERSION,passed=bool(passed),reason=reason,evaluations=calls,
        maximum_evaluations=maximum_evaluations,evaluation_trace=trace,policy=POLICY,
        scientific_eligible=False,scientific_decision='abstain',**details)
    def fresh(u,*,fresh=True):
        nonlocal calls
        if calls>=maximum_evaluations:raise RuntimeError('native evaluation budget exhausted')
        if not fresh or np.any(abs(u)>1):raise ValueError('fresh feasible callback required')
        calls+=1
        value=evaluate(np.array(u).copy(),fresh=True)
        r,j=np.asarray(value[0],float),np.asarray(value[1],float)
        if (r.ndim!=1 or not len(r) or j.shape!=(len(r),len(point))
                or not np.all(np.isfinite(r)) or not np.all(np.isfinite(j))):raise ValueError('invalid native residual or Jacobian')
        trace.append(dict(evaluation=calls,point=np.asarray(u).tolist(),cost=float(r.astype(np.longdouble)@r.astype(np.longdouble))))
        return r,j,value[2]
    if not geometry['knots']:return result(False,'no_transition_in_window')
    original,_,_=fresh(point);repeat,_,_=fresh(point)
    details['original_repeat']=displacement_metrics(original,repeat,physical_step)
    if not details['original_repeat']['passed']:return result(False,'original_not_repeatable')
    def derivative(t):
        u=point.copy();u[time_index]=t;r,j,_=fresh(u)
        return float(r.astype(np.longdouble)@j[:,time_index].astype(np.longdouble))
    found=locate(geometry['knots'],geometry['left'],geometry['right'],derivative)
    details['search']=found
    if not found['passed']:return result(False,found['reason'])
    chosen=clock.bracket(times,packet_count,scale,found['point'],maximum_queries=POLICY['maximum_geometry_queries'])
    details['geometry']=chosen
    if not chosen['side_geometry_supported'] or chosen['point']!=found['point']:return result(False,'side_geometry_unsupported')
    target=point.copy();target[time_index]=found['point'];center,_,_=fresh(target)
    details.update(normalized_parameters=target.tolist(),relocation_s=float((target[time_index]-point[time_index])*scale),
        relocation=displacement_metrics(original,center,physical_step))
    if not details['relocation']['passed']:return result(False,'relocation_not_stable')
    checked=stopping.check(target,fresh,physical_step,time_index=time_index,knots=chosen['knots'])
    details['boundary_check']=checked
    return result(checked['passed'],'two_sided_boundary_stability' if checked['passed'] else 'boundary_check_unresolved')
