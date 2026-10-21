# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent generated controls; standalone adapter loads after thread guard."""
import math


def evaluate(task,context):
    import numpy as np
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_shared_reference_terms import ReferenceErrors
    from lll.ilvis0_reference_acceleration import AccelerationTerms
    from lll.ilvis0_common_force_transform import ForceTransform
    from lll.ilvis0_control_shards import _check_continue
    config=read(context.input_path())['configuration'];config=dict(config,limits=np.array(config['limits']))
    spec=task['payload'];center=np.full(27,.1);lo=-np.ones(27);hi=np.ones(27)
    if spec['family']=='sector':lo[2]=0.;hi[2]=.25;center[2]=.125
    elif spec['family']=='fixed':lo=center.copy();hi=center.copy()
    elif spec['family']=='gain-boundary':config['limits'][18:21]=.9
    elif spec['family']!='full':raise ValueError('unknown frozen transform control family')
    ref=ReferenceErrors(config,lo,hi,center,source_id=task['identity']);component=ForceTransform(ref)
    context.save('reservation.json',dict(probe_points=64,derivative_point_evaluations=54,weighted_maps=256))
    rng=np.random.default_rng(spec['seed']);points=np.r_[lo[None,:],hi[None,:],lo+(hi-lo)*rng.random((62,27))]
    def oracle(point):
        p=ref.limits*point;v=p[:3];length=float(np.linalg.norm(v));x,y,z=v
        skew=np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
        rotation=np.eye(3) if length==0 else np.eye(3)+math.sin(length)/length*skew+(1-math.cos(length))/length**2*(skew@skew)
        return ref.initial_r@rotation@np.diag(1/(1+p[18:21]))
    maps=[([1.,1.,1.],[0.,0.,0.]),([1.,2.,-1.],[.3,-.7,.9]),([2.,-.5,.1],[25.,-10.,2.]),([.1,.2,-3.],[-1.,1.,.5])]
    oracle_errors=[];map_errors=[];normalized=[]
    for point in points:
        _check_continue(context.root,context.manifest);actual=oracle(point);computed=component.matrix_at(point)
        oracle_errors.append(float(np.max(abs(actual-computed))));gamma=component.normalized_values_at(point);normalized.append(gamma)
        remainder=actual-component.center-np.einsum('ijk,k->ij',component.jacobian,point-center)
        for metric,integral in maps:
            direct=(remainder@np.array(integral))*metric;predicted=component.coefficients(metric,integral).matrix@gamma
            map_errors.append(float(np.max(abs(direct-predicted))))
    derivatives=[];step=2e-6
    for axis in range(27):
        _check_continue(context.root,context.manifest);delta=np.eye(27)[axis]*step
        derivatives.append((oracle(center+delta)-oracle(center-delta))/(2*step)-component.jacobian[:,:,axis])
    accel=AccelerationTerms(ref,[.001,-.002,-.04905],.005,9.81)
    previous=ref.coefficients([1.,1.,1.],1.,[1.,1.,1.]);added=accel.coefficients([1.,1.,1.],clock_center=1.,time_slope=1.)
    design=component.augment(np.zeros((3,27)),accel,previous,added,component.coefficients([1.,1.,1.],[1.,2.,3.]))
    maximum=float(np.max(abs(np.array(normalized))));derivative_error=float(np.max(abs(np.array(derivatives))))
    passed=(max(oracle_errors)<=3e-13 and max(map_errors)<=3e-12 and derivative_error<=3e-10 and maximum<=1+1e-11 and design.shape==(3,51))
    return plain(dict(passed=bool(passed),identity=task['identity'],task=spec,reference=ref.report(),component=component.report(),
        lower=lo,upper=hi,center=center,probe_points=64,derivative_point_evaluations=54,weighted_map_checks=256,
        maximum_oracle_error=max(oracle_errors),maximum_map_error=max(map_errors),maximum_derivative_error=derivative_error,
        maximum_normalized_remainder=maximum,points=points,normalized_remainders=normalized,derivative_errors=derivatives,
        augmented_design=design,physical_parameter_count=27,enclosure_parameter_count=51,
        native_evaluations=0,original_reads=0,optimizer_starts=0,observational_coverage_qualified=False,scientific_decision='abstain'))
