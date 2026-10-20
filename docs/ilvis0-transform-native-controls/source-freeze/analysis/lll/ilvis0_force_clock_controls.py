# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent component controls; imported after the worker's numerical guard."""
from fractions import Fraction as F
import math


def evaluate(task,context):
    import numpy as np
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_shared_reference_terms import ReferenceErrors
    from lll.ilvis0_common_force_transform import ForceTransform
    from lll.ilvis0_clocked_force_transform import ClockedForceTransform
    from lll.ilvis0_force_integrals import enclose
    from lll.ilvis0_reference_acceleration import AccelerationTerms
    from lll.ilvis0_control_shards import _check_continue
    source=read(context.input_path());spec=task['payload'];n=spec['packets']
    config=source['configuration'];periods=np.array(source['dt'][:n]);raw=np.array(source['dv'][:n]);differences=raw/periods[:,None]-raw[0]/periods[0]
    center=np.full(27,.1);lower=-np.ones(27);upper=np.ones(27);lower[2]=0.;upper[2]=.25;center[2]=.125
    if spec['family']=='short':lower[25]=-.1;upper[25]=.1;center[25]=0.
    elif spec['family']=='fixed':lower[25]=upper[25]=center[25]
    reference=ReferenceErrors(config,lower,upper,center,source_id=task['identity']);matrix=ForceTransform(reference)
    nominal=F(spec['nominal_time']);limit=F(float(reference.limits[25]));at=lambda p:nominal+limit*F(float(p[25]))
    context.save('integral-reservation.json',dict(maximum_packets=n,maximum_seconds=30))
    profile=enclose(periods,differences,center=at(center),lower=at(lower),upper=at(upper),maximum_packets=n)
    metric=np.array([1.,.7,-1.]);component=ClockedForceTransform(matrix,profile,nominal_time=nominal,metric=metric)
    context.save('component.json',dict(integral=profile.report(),weighted=component.report()))
    context.save('probe-reservation.json',dict(probes=12,derivative_evaluations=54,exact_inequalities=72,maximum_histories=14))
    histories={};calls=0
    def history(query):
        nonlocal calls
        if query in histories:return histories[query]
        _check_continue(context.root,context.manifest)
        if calls>=14:raise ValueError('frozen independent-history allowance exhausted')
        calls+=1;context.save(f'history-{calls:02d}.json',dict(query=str(query),maximum_packet_visits=n))
        tag=0.;pieces=[]
        for i,(period,force) in enumerate(zip(periods,differences,strict=True)):
            if i%256==0:_check_continue(context.root,context.manifest)
            q=min(max(query-F(tag),F(0)),F(float(period)));pieces.append((q,tuple(F(float(v)) for v in force)));tag+=float(period)
        g=[F(0)]*3;h=[F(0)]*3;later=F(0)
        for q,force in reversed(pieces):
            for axis in range(3):g[axis]+=q*force[axis];h[axis]+=force[axis]*q*(q/2+later)
            later+=q
        histories[query]=(tuple(g),tuple(h));return histories[query]
    def rotation(point):
        p=reference.limits*point;v=p[:3];length=float(np.linalg.norm(v));x,y,z=v
        k=np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
        r=np.eye(3) if length==0 else np.eye(3)+math.sin(length)/length*k+(1-math.cos(length))/length**2*(k@k)
        return reference.initial_r@r@np.diag(1/(1+p[18:21]))
    def actual(point):
        g,h=history(at(point));return (rotation(point)@np.array([float(v) for v in h]))*metric,g,h
    gc,hc=history(at(center));passed=gc==profile.g_center and hc==profile.h_center
    rng=np.random.default_rng(spec['seed']);points=np.r_[lower[None,:],upper[None,:],center[None,:],lower+(upper-lower)*rng.random((9,27))]
    probe_rows=[];maximum=0.;exact_checks=0
    for point in points:
        observed,g,h=actual(point);tau=at(point)-at(center);exact=True
        for axis in range(3):
            first=abs(g[axis]-gc[axis]-profile.g_linear[axis]*tau)<=profile.g_remainder[axis]
            second=abs(h[axis]-hc[axis]-profile.h_linear[axis]*tau)<=profile.h_remainder[axis]
            exact=exact and first and second
            exact_checks+=2
        gamma=matrix.normalized_values_at(point);prediction=component.center+component.jacobian@(point-center)+component.coefficients.matrix@gamma
        residual=abs(observed-prediction);contained=bool(np.all(residual<=component.unshared_remainder+3e-12))
        passed=passed and exact and contained and bool(np.all(abs(gamma)<=1+1e-11));maximum=max(maximum,float(np.max(residual)))
        probe_rows.append(dict(point=point,exact_clock_checks=exact,weighted_contained=contained,residual=residual))
    step=2e-6;errors=[]
    for axis in range(27):
        delta=np.eye(27)[axis]*step
        errors.append((actual(center+delta)[0]-actual(center-delta)[0])/(2*step)-component.jacobian[:,axis])
    derivative_error=float(np.max(abs(np.array(errors))))
    accel=AccelerationTerms(reference,raw[0],float(periods[0]),config['gravity'])
    previous=reference.coefficients(metric,1.,metric);added=accel.coefficients(metric,clock_center=float(profile.query_center),time_slope=1.)
    design=matrix.augment(component.jacobian,accel,previous,added,component.coefficients)
    passed=passed and derivative_error<=3e-8 and design.shape==(3,51)
    return plain(dict(passed=bool(passed),identity=task['identity'],task=spec,probe_points=12,derivative_evaluations=54,
        exact_integral_checks=exact_checks,independent_histories=calls,history_packet_visits=calls*n,integral_packet_visits=n,
        maximum_weighted_residual=maximum,maximum_derivative_error=derivative_error,probes=probe_rows,derivative_errors=errors,
        augmented_design=design,physical_parameter_count=27,enclosure_parameter_count=51,
        original_reads=0,native_evaluations=0,optimizer_starts=0,observational_coverage_qualified=False,scientific_decision='abstain'))
