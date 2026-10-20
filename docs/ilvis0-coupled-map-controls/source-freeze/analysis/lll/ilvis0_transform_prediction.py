# SPDX-License-Identifier: AGPL-3.0-or-later
"""Charged multiprocess adapter; qualified complete 51-column prediction experiment."""
import ctypes
import subprocess


def evaluate(task,context):
    import numpy as np
    from lll.ilvis0_sharded_native import plain,read
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_orientation_cover import sector
    from lll import ilvis0_transform_native as shared,ilvis0_transform_sector_experiment as experiment
    specification=task['payload'];case=read(context.input_path());config=case['configuration']
    for compiler,version in specification.get('compilers',{}).items():
        if subprocess.check_output([compiler,'--version'],text=True).splitlines()[0]!=version:
            raise ValueError('native compiler differs from frozen qualification')
    config={k:np.ascontiguousarray(v) if k in ('initial_c','initial_v','initial_r','limits') else v for k,v in config.items()}
    case=dict(case,configuration=config);theta=np.ascontiguousarray(case['theta']);dv=np.ascontiguousarray(case['dv']);dt=np.ascontiguousarray(case['dt']);n=len(dt)
    if n!=specification['packets'] or config['model']!=specification['model'] or config['profile']!=specification['profile']:
        raise ValueError('generated prediction input/candidate mismatch')
    box=sector(specification['sector']);reference=shared.make_reference(config,theta,dv,dt,
        lower=box['lower'],upper=box['upper'],center=box['center'])
    scale=np.array([6371000.,6371000.*np.cos(config['initial_c'][0]),1.])
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';directory.mkdir(exist_ok=True)
    kernel,kernel_identity=load_tangent(directory);calls=0;bounds=0;maximum=0.
    def native(times,point):
        nonlocal calls
        times=np.ascontiguousarray(times,dtype=float);out=np.empty((len(times),3));jac=np.empty((len(times)*3,27));warning=ctypes.c_int()
        context.charge(native_calls=1,packet_visits=n);calls+=1
        code=kernel(n,theta,dv,dt,len(times),times,config['initial_c'],config['initial_v'],config['initial_r'],config['limits'],
            np.ascontiguousarray(point),config['model'],int(config['profile']),config['gravity'],config['radius'],out,jac,ctypes.byref(warning))
        if code:raise ValueError('native generated prediction outside support')
        context.save(f'native-{calls:02d}.json',plain(dict(times=times,point=point,prediction=out,jacobian=jac,warning=warning.value)))
        return out,jac.reshape(len(times),3,27)
    def bound(time,left,right,position):
        nonlocal bounds,maximum
        context.charge(bound_calls=1,bound_steps=2*n);bounds+=1
        report=shared.enclose(config,theta,dv,dt,time=float(time),lower=left,upper=right,reference=reference,
            maximum_seconds=specification['maximum_bound_seconds'])
        error=float(np.max(abs((report.center-position)*scale)));maximum=max(maximum,error)
        context.save(f'bound-{bounds:02d}.json',plain(dict(report.report(),reference=reference.report(),
            previous_reference=reference.parent.report(),native_center_difference_m=error)))
        return report
    def emit(label,value):
        if label not in ('training','future'):raise ValueError('unrecognized prediction evidence')
        context.save(label+'.json',plain(value))
    result=experiment.evaluate(specification,case,reference=reference,native=native,bound=bound,emit=emit)
    return plain(dict(result,passed=result['passed'] and maximum<=1e-6,kernel=kernel_identity,
        maximum_center_difference_m=maximum,bound_evaluations=bounds,native_evaluations=calls,reserved_bound_steps=2*bounds*n))
