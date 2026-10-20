# SPDX-License-Identifier: AGPL-3.0-or-later
"""Standalone finite controls with an independent Rodrigues/force oracle."""
import math


def evaluate(task,context):
    import numpy as np
    from fractions import Fraction as F
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_shared_reference_terms import ReferenceErrors
    from lll.ilvis0_reference_acceleration import AccelerationTerms
    from lll.ilvis0_common_force_transform import ForceTransform
    from lll.ilvis0_calibration_consistency import build,exact_slacks
    from lll.ilvis0_control_shards import _check_continue
    case=read(context.input_path());cfg=dict(case['configuration'])
    cfg['limits']=np.array(cfg['limits'],float);spec=task['payload']
    center=np.full(27,.1);lo=-np.ones(27);hi=np.ones(27)
    if spec['family']=='sector':lo[2]=0.;hi[2]=.25;center[2]=.125
    elif spec['family']=='fixed':lo=center.copy();hi=center.copy()
    elif spec['family']=='gain-boundary':cfg['limits'][18:21]=.9
    elif spec['family']!='full':raise ValueError('unknown consistency family')
    ref=ReferenceErrors(cfg,lo,hi,center,source_id=task['identity'])
    a=AccelerationTerms(ref,case['dv'][0],case['dt'][0],cfg['gravity']);m=ForceTransform(ref);cut=build(a,m)
    if spec['maximum_probes']!=64:raise ValueError('frozen 64-probe allowance required')
    context.save('reservation.json',dict(probe_points=64,exact_inequalities=384,column_checks=192))
    rng=np.random.default_rng(spec['seed'])
    points=[lo,hi]
    for axis in range(27):
        left=center.copy();right=center.copy();left[axis]=lo[axis];right[axis]=hi[axis]
        points.extend((left,right))
    points.extend(lo+(hi-lo)*rng.random((8,27)))
    records=[];max_oracle=0.;max_normalized=0.;max_slack=None;column_good=True
    changes=[F(v) for v in cut.metadata['column_change_bounds']]
    for point in points:
        _check_continue(context.root,context.manifest)
        p=ref.limits*point;vector=p[:3];length=float(np.linalg.norm(vector));x,y,z=vector
        k=np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
        rotation=np.eye(3) if length==0 else np.eye(3)+math.sin(length)/length*k+(1-math.cos(length))/length**2*(k@k)
        matrix=ref.initial_r@rotation@np.diag(1/(1+p[18:21]))
        acceleration=matrix@(a.raw_delta_v/a.period-p[12:15])+np.array([0.,0.,a.gravity+p[24]])
        max_oracle=max(max_oracle,float(np.max(abs(matrix-m.matrix_at(point)))),
            float(np.max(abs(acceleration-a.acceleration_at(point)))))
        da=acceleration-a.center-a.jacobian@(point-center)
        dm=(matrix-m.center-np.einsum('ijk,k->ij',m.jacobian,point-center)).ravel()
        ga=np.zeros(9);gm=np.zeros(9)
        for i,v in enumerate(da):
            if a.caps[6+i]:ga[6+i]=v/a.caps[6+i]
            elif abs(v)>3e-12:raise ValueError('zero acceleration cap contradicted')
        for i,v in enumerate(dm):
            if m.caps[i]:gm[i]=v/m.caps[i]
            elif abs(v)>3e-12:raise ValueError('zero matrix cap contradicted')
        if np.array_equal(point,center):ga[:]=0.;gm[:]=0.
        extended=np.r_[point,np.zeros(6),ga,gm]
        slacks=exact_slacks(cut,extended);worst=max(slacks)
        max_slack=worst if max_slack is None else max(max_slack,worst)
        max_normalized=max(max_normalized,float(np.max(abs(np.r_[ga,gm]))))
        for j in range(3):
            # The independent oracle's binary trig error is reported above;
            # a tiny comparison allowance is not added to the exported cuts.
            column_good=column_good and np.linalg.norm(matrix[:,j]-m.center[:,j])<=float(changes[j])+3e-13
        records.append(dict(point=point,common_error=extended[27:],maximum_exact_slack=str(worst)))
    violation=max(sum((F(float(v))*F(float(x)) for v,x in zip(row,np.r_[center,np.where(row[27:]>=0,1.,-1.)])),F(0))-F(float(b))
        for row,b in zip(cut.design,cut.upper))
    passed=(max_slack<=0 and column_good and max_oracle<=3e-12 and max_normalized<=1+1e-10
        and (spec['family']=='fixed' or violation>0))
    return plain(dict(passed=bool(passed),identity=task['identity'],task=spec,cuts=cut.report(),
        probe_points=len(points),exact_inequalities=len(points)*6,column_checks=len(points)*3,
        maximum_oracle_error=max_oracle,maximum_normalized_error=max_normalized,
        maximum_exact_slack=str(max_slack),independent_box_violation=str(violation),
        column_checks_pass=bool(column_good),probes=records,physical_parameter_count=27,
        enclosure_parameter_count=51,native_evaluations=0,original_reads=0,optimizer_starts=0,
        observational_coverage_qualified=False,scientific_decision='abstain'))
