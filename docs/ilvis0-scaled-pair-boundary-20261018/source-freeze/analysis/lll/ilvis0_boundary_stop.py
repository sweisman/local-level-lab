# SPDX-License-Identifier: AGPL-3.0-or-later
"""Candidate local stopping check at a supplied exact timing knot; no promotion."""
import numpy as np
from scipy.optimize import lsq_linear
from .ilvis0_solver_refinement import POLICY as STOPPING
from .ilvis0_solver_position import POLICY as POSITION

VERSION='ilvis0-two-sided-boundary-stop-v1'
POLICY=dict(stationarity_tolerance=STOPPING['stationarity_tolerance'],
    relative_cost_tolerance=STOPPING['relative_cost_tolerance'],
    position_rms_tolerance_m=POSITION['position_rms_tolerance_m'],
    position_max_tolerance_m=POSITION['position_max_tolerance_m'],
    maximum_evaluations=10,maximum_affine_solves=2,side_step=1e-6,
    minimum_side_step=64*np.finfo(float).eps,
    scope='local numerical check at a qualified exact knot, not a global optimum or statistical decision')


def stationarity(point,residual,jac,index,knot,side):
    gradient=jac.T@residual;projected=gradient.copy()
    tolerance=STOPPING['bound_projection_tolerance']
    projected[(point<=-1+tolerance)&(gradient>0)]=0.
    projected[(point>=1-tolerance)&(gradient<0)]=0.
    if point[index]==knot and ((side=='left' and gradient[index]<0) or (side=='right' and gradient[index]>0)):
        projected[index]=0.
    scale=np.maximum(np.linalg.norm(jac,axis=0),1.)*max(np.linalg.norm(residual),1.)
    return float(np.max(abs(projected)/scale))


def check(point,evaluate,physical_step,*,time_index,knots,side_step=1e-6,maximum_evaluations=10):
    point=np.array(point,float);knots=np.asarray(knots,float)
    if type(maximum_evaluations) is not int or maximum_evaluations!=10:
        raise ValueError('exact ten-evaluation budget required')
    if (point.ndim!=1 or not len(point) or not np.all(np.isfinite(point)) or np.any(abs(point)>1)
            or type(time_index) is not int or not 0<=time_index<len(point)):
        raise ValueError('finite feasible point and time index required')
    if (knots.ndim!=1 or len(knots)<3 or not np.all(np.isfinite(knots)) or np.any(np.diff(knots)<=0)
            or knots[0]!=-1. or knots[-1]!=1.):raise ValueError('ordered complete knot partition required')
    knot=float(point[time_index]);matches=np.flatnonzero(knots==knot)
    if len(matches)!=1 or matches[0] in (0,len(knots)-1):raise ValueError('point must be exactly at an interior knot')
    k=int(matches[0]);edges=(float(knots[k-1]),float(knots[k+1]))
    if not np.isfinite(side_step) or side_step<=0:raise ValueError('positive finite side step required')
    delta=min(side_step,(knot-edges[0])/4,(edges[1]-knot)/4)
    if delta/4<POLICY['minimum_side_step']:raise ValueError('neighbor knots insufficiently separated')
    calls=0;branches=[]
    def fresh(u):
        nonlocal calls
        if calls>=maximum_evaluations:raise ValueError('boundary evaluation budget exhausted')
        if np.any(abs(u)>1):raise ValueError('fresh probe outside physical bounds')
        calls+=1
        value=evaluate(u.copy(),fresh=True)
        r,j=np.asarray(value[0],float),np.asarray(value[1],float)
        if (r.ndim!=1 or j.shape!=(len(r),len(point)) or not len(r)
                or not np.all(np.isfinite(r)) or not np.all(np.isfinite(j))):
            raise ValueError('finite compatible residual and Jacobian required')
        return r,j
    def metrics(old,new):
        if old.shape!=new.shape:raise ValueError('residual size changed')
        displacement=np.asarray(physical_step(new-old),float)
        if (displacement.ndim!=2 or displacement.shape[1]!=3 or not len(displacement)
                or not np.all(np.isfinite(displacement))):raise ValueError('finite physical displacement required')
        a,b=old.astype(np.longdouble),new.astype(np.longdouble)
        change=float(b@b-a@a);relative=abs(change)/max(float(a@a),float(b@b),1.)
        rms=np.sqrt(np.mean(displacement**2,axis=0));maximum=np.max(abs(displacement),axis=0)
        return dict(passed=bool(relative<=POLICY['relative_cost_tolerance']
            and np.all(rms<=POLICY['position_rms_tolerance_m']) and np.all(maximum<=POLICY['position_max_tolerance_m'])),
            signed_cost_change=change,relative_cost_change=relative,position_rms=rms.tolist(),position_maximum=maximum.tolist())
    def result(passed,reason,**extra):
        return dict(version=VERSION,passed=bool(passed),reason=reason,evaluations=calls,branches=branches,
                    policy=POLICY,scientific_eligible=False,scientific_decision='abstain',**extra)
    residual,_=fresh(point);repeated,_=fresh(point)
    repeat=metrics(residual,repeated)
    if not repeat['passed']:return result(False,'center_not_repeatable',center_repeat=repeat)
    samples={}
    for side,sign in (('left',-1.),('right',1.)):
        samples[side]=[]
        for fraction in (1.,.25):
            probe=point.copy();probe[time_index]+=sign*delta*fraction
            r,j=fresh(probe);estimated=r+j@(point-probe)
            continuity=metrics(residual,estimated)
            samples[side].append((probe,r,j,continuity))
    if any(not s[3]['passed'] for group in samples.values() for s in group):
        return result(False,'side_values_not_continuous',center_repeat=repeat)
    for side,edge in (('left',edges[0]),('right',edges[1])):
        _,_,jac,_=samples[side][-1]
        gradients=[stationarity(point,residual,s[2],time_index,knot,side) for s in samples[side]]
        lower=-1-point;upper=1-point
        if side=='left':lower[time_index]=edge-knot;upper[time_index]=0.
        else:lower[time_index]=0.;upper[time_index]=edge-knot
        local=lsq_linear(jac,-residual,bounds=(lower,upper),method='bvls',
            tol=STOPPING['stability_probe_linear_tolerance'],max_iter=STOPPING['stability_probe_linear_maximum_iterations'])
        if not local.success or not np.all(np.isfinite(local.x)):
            branches.append(dict(side=side,passed=False,reason='local_linear_solve_unfinished'));continue
        probe=np.clip(point+local.x,-1.,1.)
        interval=(edge,knot) if side=='left' else (knot,edge)
        clamped=float(np.clip(probe[time_index],*interval))
        if abs(clamped-probe[time_index])>4*np.finfo(float).eps:raise ValueError('material branch-bound violation')
        probe[time_index]=clamped
        r,j=fresh(probe);movement=metrics(residual,r)
        unknown_edge=bool(probe[time_index]==edge and edge not in (-1.,1.))
        continuity=None
        if probe[time_index]==knot:
            near=probe.copy();near[time_index]+=(-1 if side=='left' else 1)*delta/4
            nr,nj=fresh(near);continuity=metrics(r,nr+nj@(probe-near));j=nj
        gradient=stationarity(probe,r,j,time_index,knot,side)
        passed=bool(max(gradients)<=POLICY['stationarity_tolerance'] and gradient<=POLICY['stationarity_tolerance']
                    and movement['passed'] and not unknown_edge and (continuity is None or continuity['passed']))
        reason=('unchecked_neighbor_boundary' if unknown_edge else 'side_not_stationary'
                if max(gradients+[gradient])>POLICY['stationarity_tolerance'] else
                'fresh_branch_probe_not_stable' if not passed else 'fresh_branch_stability_verified')
        branches.append(dict(side=side,passed=passed,reason=reason,correction=(probe-point).tolist(),
            side_stationarity=gradients,fresh_stationarity=gradient,probe_continuity=continuity,**{k:v for k,v in movement.items() if k!='passed'}))
    return result(len(branches)==2 and all(b['passed'] for b in branches),
                  'two_sided_boundary_stability' if all(b['passed'] for b in branches) else 'unresolved',
                  center_repeat=repeat,knot=knot,neighbor_edges=list(edges),side_probe_step=delta)
