# SPDX-License-Identifier: AGPL-3.0-or-later
"""Charged all-model qualification for the 51-column native candidate."""
import ctypes


def evaluate(task,context):
    import numpy as np
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_sharded_native import read,plain
    from lll import ilvis0_transform_native as candidate
    from lll.ilvis0_transform_control_case import evaluate_case
    specification=task['payload'];case=read(context.input_path());config=case['configuration']
    config={k:np.ascontiguousarray(v) if k in ('initial_c','initial_v','initial_r','limits') else v for k,v in config.items()}
    theta=np.ascontiguousarray(case['theta']);dv=np.ascontiguousarray(case['dv']);dt=np.ascontiguousarray(case['dt']);n=len(dt)
    if n!=specification['packets'] or config['model']!=specification['model'] or config['profile']!=specification['profile']:
        raise ValueError('native candidate/input identity mismatch')
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';directory.mkdir(exist_ok=True)
    kernel,kernel_id=load_tangent(directory);calls=0;bounds=0
    def native(point):
        nonlocal calls
        context.charge(native_calls=1,packet_visits=n);calls+=1
        out=np.empty((1,3));jac=np.empty((3,27));warning=ctypes.c_int()
        code=kernel(n,theta,dv,dt,1,np.array([case['time_s']]),config['initial_c'],config['initial_v'],config['initial_r'],config['limits'],
            np.ascontiguousarray(point),config['model'],int(config['profile']),config['gravity'],config['radius'],out,jac,ctypes.byref(warning))
        if code:raise ValueError('native transform query outside support')
        context.save(f'native-{calls:02d}.json',plain(dict(point=point,prediction=out[0],jacobian=jac,warning=warning.value)))
        return out[0],jac
    def bound(point,left,right):
        nonlocal bounds
        context.charge(bound_calls=1,bound_steps=n);bounds+=1
        reference=candidate.make_reference(config,theta,dv,dt,lower=left,upper=right,center=point)
        report=candidate.enclose(config,theta,dv,dt,time=case['time_s'],lower=left,upper=right,reference=reference,maximum_seconds=60.)
        context.save(f'bound-{bounds:02d}.json',plain(dict(report.report(),reference=reference.report())))
        return report,reference
    result=evaluate_case(specification,case,native=native,bound=bound)
    return plain(dict(result,native_evaluations=calls,bound_evaluations=bounds,reserved_bound_steps=bounds*n,kernel=kernel_id))
