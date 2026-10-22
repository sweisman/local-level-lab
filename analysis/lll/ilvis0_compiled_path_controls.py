# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite compiled multi-packet comparison, not full-history coverage."""
from lll.ilvis0_path_native_controls import compare


def recipe():
    return dict(packets=64,query_fraction=.5,center=[0.]*27,columns=list(range(27)),
        native_calls_per_case=1,interval_steps_per_case=1728,maximum_bound_seconds=30.,
        comparison_tolerance_m=1e-6,original_reads=0,optimizer_starts=0)


def validate_recipe(value):
    if value!=recipe():raise ValueError('fixed64-packet all-column recipe required')


def evaluate(task,context):
    import ctypes
    import numpy as np
    from lll import ilvis0_control_shards as runner
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_training_density import boundary_count
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_compiled_path_packets import load_backend
    from lll.ilvis0_sharded_native import plain
    spec=task['payload'];settings=runner._load(context.input_path());validate_recipe(settings)
    case=runner._load(context.input_path(spec['case_key']));config=case['configuration']
    if (len(case['dt'])!=64 or case['center']!=settings['center']
            or config['model']!=spec['model'] or config['profile']!=spec['profile'] or config['limits'][25]!=1.):
        raise ValueError('unchanged qualified prefix and configuration required')
    arrays={k:np.ascontiguousarray(config[k],float) for k in ('initial_c','initial_v','initial_r','limits')}
    theta,dv,dt=(np.ascontiguousarray(case[k],float) for k in ('theta','dv','dt'))
    start=0.
    for period in dt[:-1]:start+=float(period)
    query=start+float(dt[-1])*settings['query_fraction']
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';directory.mkdir(parents=True,exist_ok=True)
    kernel,metadata=load_tangent(directory)
    if (metadata['compiler']!=spec['compiler'] or
            metadata['source_sha256']!=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp']):
        raise ValueError('frozen native source/compiler changed')
    context.save('kernel.json',metadata);context.charge(native_calls=1,packet_visits=64)
    output=np.full((1,3),np.nan);jac=np.full((3,27),np.nan);flag=ctypes.c_int()
    code=kernel(64,theta,dv,dt,1,np.array([query]),arrays['initial_c'],arrays['initial_v'],arrays['initial_r'],
        arrays['limits'],np.zeros(27),config['model'],int(config['profile']),config['gravity'],config['radius'],
        output,jac,ctypes.byref(flag))
    raw=dict(status=int(code),boundary_counter=flag.value,query_s=query)
    if code==0:raw.update(prediction=output[0],jacobian=jac)
    context.save('native.json',plain(raw))
    context.save('boundary.json',boundary_count(status=int(code),counter=flag.value,dt=dt,times=[query]))
    if code!=0 or not np.all(np.isfinite(output)) or not np.all(np.isfinite(jac)):
        raise ValueError('successful finite native values and all27 derivatives required')
    compiled,compiled_metadata=load_backend(directory,source_directory=context.root/'source-freeze/analysis/lll')
    if compiled_metadata['compiler']!=spec['compiler']:raise ValueError('compiled compiler changed')
    for name,digest in compiled_metadata['sources'].items():
        if digest!=context.manifest['sources']['analysis/lll/'+name]:raise ValueError('compiled source closure changed')
    context.save('compiled-kernel.json',compiled_metadata);bounds=[]
    for column in settings['columns']:
        runner._check_continue(context.root,context.manifest)
        context.charge(bound_calls=1,bound_steps=64)
        parameters=[J.constant(0)]*27;parameters[column]=J(((0,0),(1,1),(0,0),(0,0)))
        answer=compiled.predict_branch(config,case['theta'],case['dv'],case['dt'],parameters,
            time=query,packet_index=63,maximum_packets=64,maximum_seconds=settings['maximum_bound_seconds'])
        record=dict(column=column,**answer.report());bounds.append(record)
        context.save(f'direction-{column:02d}.json',record)
    metrics=compare(output[0].tolist(),jac.tolist(),bounds,spec['coordinate_scale'])
    context.save('comparison.json',metrics)
    return dict(identity=task['identity'],model=spec['model'],profile=spec['profile'],**metrics,
        native_evaluations=1,interval_packet_steps=1728,original_reads=0,optimizer_starts=0,
        higher_order_native_reference=False,scientific_decision='abstain')
