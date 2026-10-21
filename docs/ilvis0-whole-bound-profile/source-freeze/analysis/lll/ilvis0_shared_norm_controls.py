# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite independent physical-oracle controls for shared vector norms."""
import math


def evaluate(task,context):
    from fractions import Fraction as F
    import numpy as np
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_shared_reference_terms import ReferenceErrors
    from lll.ilvis0_reference_acceleration import AccelerationTerms
    from lll.ilvis0_common_force_transform import ForceTransform
    from lll.ilvis0_shared_norms import build,exact_slacks
    from lll.ilvis0_control_shards import _check_continue
    case=read(context.input_path());cfg=dict(case['configuration']);cfg['limits']=np.array(cfg['limits'],float)
    spec=task['payload'];center=np.full(27,.1);lo=-np.ones(27);hi=np.ones(27)
    if spec['family']=='sector':lo[2]=0.;hi[2]=.25;center[2]=.125
    elif spec['family']=='fixed':lo=center.copy();hi=center.copy()
    elif spec['family']=='gain-boundary':cfg['limits'][18:21]=.9
    elif spec['family']!='full':raise ValueError('unknown shared-norm family')
    if spec['maximum_probes']!=64:raise ValueError('frozen 64-probe allowance required')
    r=ReferenceErrors(cfg,lo,hi,center,source_id=task['identity'])
    a=AccelerationTerms(r,case['dv'][0],case['dt'][0],cfg['gravity']);m=ForceTransform(r);cut=build(a,m)
    context.save('reservation.json',dict(probes=64,vector_norm_checks=448,exact_inequalities=11648))
    rng=np.random.default_rng(spec['seed']);points=[lo,hi]
    for axis in range(27):
        left=center.copy();right=center.copy();left[axis]=lo[axis];right[axis]=hi[axis];points.extend((left,right))
    points.extend(lo+(hi-lo)*rng.random((8,27)))
    def skew(v):
        x,y,z=v;return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
    def rotation(v):
        length=float(np.linalg.norm(v));k=skew(v)
        return np.eye(3) if length==0 else np.eye(3)+math.sin(length)/length*k+(1-math.cos(length))/length**2*(k@k)
    v0=r.limits[:3]*center[:3];length=float(np.linalg.norm(v0));k0=skew(v0)
    def directional(delta):
        dk=skew(delta)
        if length==0:return dk
        da=float(v0@delta)/length;s=math.sin(length)/length;c=(1-math.cos(length))/length**2
        ds=(length*math.cos(length)-math.sin(length))/length**2
        dc=(length*math.sin(length)-2*(1-math.cos(length)))/length**3
        return ds*da*k0+s*dk+dc*da*(k0@k0)+c*(dk@k0+k0@dk)
    pc=r.limits*center;lever0=pc[21:24];max_error=0.;worst_norm=F(0);worst_slack=None;records=[]
    for point in points:
        _check_continue(context.root,context.manifest)
        p=r.limits*point;delta=point-center;rp=r.initial_r@rotation(p[:3])
        matrix=rp@np.diag(1/(1+p[18:21]));accel=matrix@(a.raw_delta_v/a.period-p[12:15])+np.array([0.,0.,a.gravity+p[24]])
        lever=rp@p[21:24]-r._r_center@lever0-r.initial_r@directional(r.limits[:3]*delta[:3])@lever0-r._r_center@(p[21:24]-lever0)
        dt=r.limits[25]*delta[25]
        av=np.r_[.5*accel*dt*dt,(accel-a.center)*dt,accel-a.center-a.jacobian@delta]
        mv=(matrix-m.center-np.einsum('ijk,k->ij',m.jacobian,delta)).ravel()
        observed={
            'initial-lever':lever,'acceleration-clock-square':av[:3],
            'acceleration-clock-linear':av[3:6],'acceleration-taylor':av[6:9],
            **{'force-column-'+label:mv.reshape(3,3)[:,i] for i,label in enumerate(('x','y','z'))}}
        gamma=np.zeros(24)
        for b in cut.blocks:
            values=observed[b['name']]
            if b['cap']:
                normalized=values/b['cap']
            else:
                if float(np.max(abs(values)))>3e-11:raise ValueError('zero-cap physical map contradicted')
                normalized=np.zeros(3)
            if np.array_equal(point,center):normalized=np.zeros(3)
            gamma[np.array(b['indices'])-27]=normalized
            square=sum((F(float(v))**2 for v in normalized),F(0));worst_norm=max(worst_norm,square)
        expected=np.r_[r.normalized_values_at(point),a.normalized_values_at(point),m.normalized_values_at(point)]
        # Velocity/clock is intentionally not subject to the unit-ball claim.
        gamma[:3]=expected[:3]
        max_error=max(max_error,float(np.max(abs(gamma-expected))))
        slack=max(exact_slacks(cut,np.r_[point,gamma]));worst_slack=slack if worst_slack is None else max(worst_slack,slack)
        records.append(dict(point=point,common_error=gamma,maximum_exact_slack=str(slack)))
    return plain(dict(identity=task['identity'],task=spec,passed=worst_norm<=1 and worst_slack<=0 and max_error<=3e-10,
        probe_points=len(points),vector_norm_checks=7*len(points),exact_inequalities=182*len(points),
        maximum_exact_squared_norm=str(worst_norm),maximum_exact_slack=str(worst_slack),
        maximum_oracle_difference=max_error,cuts=cut.report(),probes=records,
        native_evaluations=0,original_reads=0,optimizer_starts=0,physical_parameter_count=27,
        enclosure_parameter_count=51,observational_coverage_qualified=False,scientific_decision='abstain'))
