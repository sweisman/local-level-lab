# SPDX-License-Identifier: AGPL-3.0-or-later
"""Charged all-model qualification for component-preserving native transport."""
import ctypes


def evaluate(task,context):
    import subprocess
    import numpy as np
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_sharded_native import read,plain
    from lll import ilvis0_direct_native as candidate
    from lll.ilvis0_directional_acceleration import DirectionalAcceleration
    from lll.ilvis0_transform_control_case import evaluate_case
    specification=task['payload'];baseline=read(context.input_path(specification['baseline_key']));case=read(context.input_path());config=case['configuration']
    if subprocess.check_output(['c++','--version'],text=True).splitlines()[0]!=specification['compiler']:
        raise ValueError('native compiler changed from freeze')
    config={k:np.ascontiguousarray(v) if k in ('initial_c','initial_v','initial_r','limits') else v for k,v in config.items()}
    theta=np.ascontiguousarray(case['theta']);dv=np.ascontiguousarray(case['dv']);dt=np.ascontiguousarray(case['dt']);n=len(dt)
    if n!=specification['packets'] or config['model']!=specification['model'] or config['profile']!=specification['profile']:
        raise ValueError('native candidate/input identity mismatch')
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';directory.mkdir(exist_ok=True)
    from lll.ilvis0_batched_transport import configure_backend
    arithmetic=configure_backend(directory,source_directory=context.root/'source-freeze/analysis/lll')
    from lll.ilvis0_source_stream import load_stream
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_control_shards import _check_continue
    source_kernel,source_compilation=load_stream(directory,source_directory=context.root/'source-freeze/analysis/lll')
    from lll.ilvis0_source_derivative_intervals import load_kernel as load_derivatives
    derivative_kernel,derivative_compilation=load_derivatives(directory,source_directory=context.root/'source-freeze/analysis/lll')
    from lll.ilvis0_source_point_derivatives import load_kernel as load_point
    point_kernel,point_compilation=load_point(directory,source_directory=context.root/'source-freeze/analysis/lll')
    events=[]
    def persist(event):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:03d}.json',event);events.append(event)
    budget=Allowance(specification['source_limits'],persist)
    kernel,kernel_id=load_tangent(directory);calls=0;bounds=0;source_steps=body_bounds=derivative_steps=0
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
        nonlocal bounds,source_steps,body_bounds,derivative_steps
        context.charge(bound_calls=1,bound_steps=9*n);bounds+=1
        budget.reserve(dict(source_setups=1,source_steps=n,source_body_bounds=n,source_derivative_setups=1,source_derivative_steps=n,source_point_setups=1,source_point_steps=n,source_direct_steps=n))
        reference=candidate.make_reference(config,theta,dv,dt,lower=left,upper=right,center=point)
        proof=DirectionalAcceleration(reference,left,right)
        context.save(f'component-source-{bounds:02d}.json',proof.report())
        report=candidate.enclose(config,theta,dv,dt,time=case['time_s'],lower=left,upper=right,reference=reference,conditioning=proof,maximum_seconds=60.,source_kernel=source_kernel,derivative_kernel=derivative_kernel,point_kernel=point_kernel)
        source_steps+=report.metadata['source_reference_steps'];body_bounds+=report.metadata['rounded_source_prefixes']
        derivative_steps+=report.metadata['source_derivative_steps']
        saved=plain(dict(report.report(),reference=reference.report()))
        fields=baseline["fields"];expected=baseline["bounds"][str(bounds)]
        if {key:saved[key] for key in fields}!=expected:
            differing=[key for key in fields if saved[key]!=expected[key]]
            raise ValueError("batched bound differs from sealed predecessor: "+str(differing))
        for key,ceiling in baseline["ceilings"][str(bounds)].items():
            if np.any(np.asarray(saved[key])>np.asarray(ceiling)):raise ValueError("source Taylor bound widened: "+key)
        context.save(f"bound-{bounds:02d}.json",saved)
        return report,reference
    result=evaluate_case(specification,case,native=native,bound=bound)
    return plain(dict(result,matched_maps_preserved=bounds==len(baseline["bounds"]),native_evaluations=calls,bound_evaluations=bounds,reserved_bound_steps=9*bounds*n,kernel=kernel_id,arithmetic=arithmetic,source_compilation=source_compilation,source_derivative_compilation=derivative_compilation,source_point_compilation=point_compilation,source_derivative_steps=derivative_steps,work=budget.counts,source_steps=source_steps,source_body_bounds=body_bounds))
