# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare legacy and current argument construction through the same kernel."""


def evaluate(task,context):
    import ctypes
    from types import SimpleNamespace
    import numpy as np
    import ilvis0_history_worker as legacy
    from lll.ilvis0_legacy_recording import convert
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_sharded_native import read,plain,compare_native
    spec=task['payload'];old=read(context.input_path());case=read(context.input_path(spec['case_key']))
    source_hash=context.manifest['inputs'][task['input_key']]['sha256']
    expected=convert(old,profile=spec['profile'],source_sha256=source_hash,expected_packets=48000)
    if case!=expected or case['configuration']['model']!=spec['model']:
        raise ValueError('converted case differs from the frozen original')
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';directory.mkdir(parents=True,exist_ok=True)
    kernel,metadata=load_tangent(directory)
    if metadata['compiler']!=spec['compiler'] or metadata['source_sha256']!=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp']:
        raise ValueError('qualified compiler/source mismatch')
    context.save('kernel.json',metadata)
    ptr=ctypes.POINTER(ctypes.c_double)
    prototype=ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_size_t,ptr,ptr,ptr,ctypes.c_size_t,
        ptr,ptr,ptr,ptr,ptr,ptr,ctypes.c_int,ctypes.c_int,ctypes.c_double,ctypes.c_double,
        ptr,ptr,ctypes.POINTER(ctypes.c_int))
    old_api=SimpleNamespace(cpp=prototype(ctypes.cast(kernel,ctypes.c_void_p).value))
    config=case['configuration'];config={k:np.ascontiguousarray(v,float) if k in ('initial_c','initial_v','initial_r','limits') else v
        for k,v in config.items()}
    theta,dv,dt=(np.ascontiguousarray(case[k],float) for k in ('theta','dv','dt'));n=len(dt);calls=0
    def reserve():
        nonlocal calls
        if calls>=4:raise ValueError('four-query format comparison allowance exhausted')
        context.charge(native_calls=1,packet_visits=n);calls+=1
    class Book:
        def tick(self,kind):
            if kind!='tangent':raise ValueError('only the legacy tangent API is allowed')
            reserve()
    points=(np.zeros(27),np.array([(i%5-2)/16 for i in range(27)]))
    for ordinal,point in enumerate(points):
        legacy_case=dict(old,profile=spec['profile'],base_time=5.)
        value,jac,warning=legacy.Kernel.tangent(old_api,legacy_case,point,Book())
        before=plain(dict(point=point,prediction=value,jacobian=jac,warning=warning))
        context.save(f'legacy-{ordinal}.json',before)
        reserve();out=np.empty((1,3));current_jac=np.empty((3,27));flag=ctypes.c_int()
        code=kernel(n,theta,dv,dt,1,np.array([5.]),config['initial_c'],config['initial_v'],config['initial_r'],
            config['limits'],point,config['model'],int(config['profile']),config['gravity'],config['radius'],
            out,current_jac,ctypes.byref(flag))
        if code:raise ValueError('current native API query failed')
        after=plain(dict(point=point,prediction=out[0],jacobian=current_jac,warning=flag.value))
        context.save(f'current-{ordinal}.json',after);compare_native(after,before)
    return dict(identity=task['identity'],passed=True,model=spec['model'],profile=spec['profile'],
        packets=n,query_time_s=5.,parameter_points=2,physical_parameter_count=27,
        bitwise_api_equivalent=True,independent_physics_validation=False,
        original_clock_fixed=case['provenance']['clock_offset_fixed'],native_evaluations=calls,
        bound_evaluations=0,original_reads=0,optimizer_starts=0,
        observational_coverage_qualified=False,scientific_decision='abstain')
