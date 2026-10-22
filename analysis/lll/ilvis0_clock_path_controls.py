# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite native boundary checks; not complete trajectory-clock coverage."""
import math
from lll.ilvis0_path_native_controls import compare


def recipe():
    return dict(packets=16,boundary_packet=6,center=[0.]*27,columns=list(range(27)),
        native_calls_per_case=1,interval_calls_per_case=81,interval_steps_per_case=513,
        maximum_bound_seconds=30.,comparison_tolerance_m=1e-6,original_reads=0,optimizer_starts=0)


def validate_recipe(value):
    if value!=recipe():raise ValueError('fixed six-case three-query boundary recipe required')


def schedule(dt):
    if len(dt)!=16 or any(not math.isfinite(float(t)) or float(t)<=0 for t in dt):
        raise ValueError('complete16 positive periods required')
    start=0.;ends=[]
    for t in dt:start+=float(t);ends.append(start)
    boundary=ends[5];queries=[math.nextafter(boundary,-math.inf),boundary,math.nextafter(boundary,math.inf)]
    owners=[next(k for k,end in enumerate(ends) if t<=end) for t in queries]
    if owners!=[5,5,6]:raise ValueError('three distinct supported boundary probes required')
    return queries,owners


def evaluate(task,context):
    import ctypes
    import numpy as np
    from lll import ilvis0_control_shards as runner
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_training_density import boundary_count
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_clock_path_packets import load_backend
    from lll.ilvis0_sharded_native import plain
    spec=task['payload'];settings=runner._load(context.input_path());validate_recipe(settings)
    case=runner._load(context.input_path(spec['case_key']));config=case['configuration']
    if (len(case['dt'])!=16 or case['center']!=settings['center'] or config['model']!=spec['model']
            or config['profile']!=spec['profile'] or config['limits'][25]!=1.):
        raise ValueError('qualified unchanged16-packet prefix required')
    arrays={k:np.ascontiguousarray(config[k],float) for k in ('initial_c','initial_v','initial_r','limits')}
    theta,dv,dt=(np.ascontiguousarray(case[k],float) for k in ('theta','dv','dt'))
    times,owners=schedule(dt);context.save('queries-before-native.json',dict(times=times,packet_owners=owners))
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';directory.mkdir(parents=True,exist_ok=True)
    kernel,metadata=load_tangent(directory)
    if (metadata['compiler']!=spec['compiler'] or
            metadata['source_sha256']!=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp']):
        raise ValueError('native compiler/source changed')
    context.save('kernel.json',metadata);context.charge(native_calls=1,packet_visits=48)
    out=np.full((3,3),np.nan);jac=np.full((9,27),np.nan);flag=ctypes.c_int()
    code=kernel(16,theta,dv,dt,3,np.array(times),arrays['initial_c'],arrays['initial_v'],arrays['initial_r'],
        arrays['limits'],np.zeros(27),config['model'],int(config['profile']),config['gravity'],config['radius'],
        out,jac,ctypes.byref(flag))
    raw=dict(status=int(code),boundary_counter=flag.value,times_s=times)
    if code==0:raw.update(prediction=out,jacobian=jac)
    context.save('native.json',plain(raw))
    context.save('boundary.json',boundary_count(status=int(code),counter=flag.value,dt=dt,times=times))
    if code!=0 or not np.all(np.isfinite(out)) or not np.all(np.isfinite(jac)):
        raise ValueError('successful finite native boundary outputs required')
    compiled,metadata=load_backend(directory,source_directory=context.root/'source-freeze/analysis/lll')
    if metadata['compiler']!=spec['compiler']:raise ValueError('compiled compiler changed')
    if any(d!=context.manifest['sources']['analysis/lll/'+n] for n,d in metadata['sources'].items()):
        raise ValueError('compiled source closure changed')
    context.save('compiled-kernel.json',metadata);metrics=[]
    for ordinal,(query,k) in enumerate(zip(times,owners,strict=True)):
        bounds=[]
        for column in settings['columns']:
            runner._check_continue(context.root,context.manifest)
            context.charge(bound_calls=1,bound_steps=k+1)
            p=[J.constant(0)]*27;p[column]=J(((0,0),(1,1),(0,0),(0,0)))
            answer=compiled.predict_branch(config,case['theta'],case['dv'],case['dt'],p,
                time=query,packet_index=k,maximum_packets=16,maximum_seconds=30.)
            record=dict(column=column,**answer.report());bounds.append(record)
            context.save(f'query-{ordinal}-direction-{column:02d}.json',record)
        metrics.append(compare(out[ordinal].tolist(),jac[3*ordinal:3*ordinal+3].tolist(),bounds,spec['coordinate_scale']))
    context.save('comparison.json',dict(queries=metrics))
    return dict(identity=task['identity'],model=spec['model'],profile=spec['profile'],
        passed=all(m['passed'] for m in metrics),physical_columns=27,native_evaluations=1,interval_packet_steps=513,
        position_checks=243,derivative_checks=243,maximum_position_gap_m=max(m['maximum_position_gap_m'] for m in metrics),
        maximum_derivative_gap_m=max(m['maximum_derivative_gap_m'] for m in metrics),
        boundary_queries=3,whole_history_qualified=False,observational_coverage_qualified=False,
        higher_order_native_reference=False,original_reads=0,optimizer_starts=0,scientific_decision='abstain')
