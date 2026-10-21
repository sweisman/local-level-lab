# SPDX-License-Identifier: AGPL-3.0-or-later
"""Charged six-case native qualification of training-conditioned acceleration."""


def evaluate(task,context):
    import ctypes
    import numpy as np
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_orientation_cover import sector
    from lll.ilvis0_conditioned_acceleration import ConditionedAcceleration
    from lll import ilvis0_conditioned_transform_native as candidate
    payload=task['payload'];bundle=read(context.input_path())
    case=read(context.input_path(payload['case_key']));config=case['configuration']
    config={k:np.ascontiguousarray(v) if k in ('initial_c','initial_v','initial_r','limits') else v for k,v in config.items()}
    theta=np.ascontiguousarray(case['theta']);dv=np.ascontiguousarray(case['dv']);dt=np.ascontiguousarray(case['dt']);n=len(dt)
    if n!=payload['packets'] or config['model']!=payload['model'] or config['profile']!=payload['profile']:
        raise ValueError('conditioned native case identity mismatch')
    reservations=[]
    def reserve(count):
        if reservations or count!=6 or payload['maximum_exact_supports']!=6:raise ValueError('six verifier supports required')
        context.save('support-reservation.json',dict(exact_supports=count));reservations.append(count)
    conditioning=ConditionedAcceleration(bundle['projection_input'],bundle['projection'],reserve=reserve)
    box=sector(payload['sector'])
    reference=candidate.make_reference(config,theta,dv,dt,lower=box['lower'],upper=box['upper'],center=box['center'])
    future=bundle['future'];left=future['lower'][:27];right=future['upper'][:27]
    context.charge(bound_calls=1,bound_steps=2*n)
    report=candidate.enclose(config,theta,dv,dt,time=future['time_s'],lower=left,upper=right,
        reference=reference,conditioning=conditioning,maximum_seconds=payload['maximum_bound_seconds'])
    context.save('conditioned-bound.json',plain(report.report()))
    # Both predictions and the source-qualified bound are now fixed.
    old=future['bound'];scale=np.array(bundle['projection_input']['training']['region']['coordinate_scale'])
    coefficient_names=('previous_coefficients','acceleration_coefficients','transform_coefficients')
    coefficients_unchanged=all(np.array_equal(report.report()[name],old[name]) for name in coefficient_names)
    saved_center_unchanged=np.array_equal(report.center,old['center'])
    remainder_unchanged=report.metadata['retained_acceleration_remainder']==reference.acceleration.remainder
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';directory.mkdir(exist_ok=True)
    kernel,kernel_id=load_tangent(directory);calls=[]
    def native(point):
        context.charge(native_calls=1,packet_visits=n)
        out=np.empty((1,3));jac=np.empty((3,27));warning=ctypes.c_int()
        code=kernel(n,theta,dv,dt,1,np.array([future['time_s']]),config['initial_c'],config['initial_v'],
            config['initial_r'],config['limits'],np.ascontiguousarray(point),config['model'],int(config['profile']),
            config['gravity'],config['radius'],out,jac,ctypes.byref(warning))
        if code:raise ValueError('conditioned native query outside support')
        calls.append(1);context.save(f'native-{len(calls):02d}.json',plain(dict(point=point,prediction=out[0],jacobian=jac,warning=warning.value)))
        return out[0],jac
    center=reference.parent.center;value,jac=native(center)
    maximum_center=float(np.max(abs((value-report.center)*scale)))
    derivative_unchanged=np.array_equal(jac,np.array(future['jacobian']))
    design=report.design(jac,reference)
    if design.shape!=(3,51) or not np.array_equal(design[:,:27],jac):raise ValueError('complete tangent columns required')
    anchor=read(context.input_path(payload['anchor_key']))['point']
    actual,_=native(anchor[:27]);gamma=np.array(anchor[27:])
    error=abs((actual-value-design@np.r_[np.array(anchor[:27])-center,gamma])*scale)
    contained=bool(np.all(error<=report.unshared_remainder*scale+1e-5))
    passed=bool(coefficients_unchanged and saved_center_unchanged and remainder_unchanged
        and derivative_unchanged and maximum_center<=1e-6 and contained)
    return plain(dict(identity=task['identity'],model=payload['model'],profile=payload['profile'],passed=passed,
        coefficients_unchanged=coefficients_unchanged,saved_center_unchanged=saved_center_unchanged,
        acceleration_remainder_unchanged=remainder_unchanged,native_derivative_unchanged=derivative_unchanged,
        maximum_center_difference_m=maximum_center,known_probe_contained=contained,probe_error_m=error,
        source_remainder_m=np.array(old['unshared_remainder'])*scale,
        conditioned_remainder_m=report.unshared_remainder*scale,parameter_count=51,
        conditioned_acceleration=conditioning.report(),exact_supports_reserved=sum(reservations),
        native_evaluations=len(calls),bound_evaluations=1,reserved_bound_steps=2*n,kernel=kernel_id,
        original_reads=0,optimizer_starts=0,floating_point_enclosure_verified=False,
        observational_coverage_qualified=False,scientific_decision='abstain'))
