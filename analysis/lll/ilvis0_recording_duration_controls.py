# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-duration/clock API checks; no independent physical validation."""


def evaluate(task,context):
    import ctypes
    from types import SimpleNamespace
    import numpy as np
    import ilvis0_history_worker as legacy
    from lll.ilvis0_legacy_recording import convert
    from lll.ilvis0_recording_fixture import extend
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_sharded_native import read,plain,compare_native
    spec=task['payload'];case=read(context.input_path());parent=read(context.input_path(spec['parent_key']))
    parent_hash=context.manifest['inputs'][spec['parent_key']]['sha256']
    expected=extend(parent,packets=96000,clock_offset_s=1.,parent_sha256=parent_hash)
    old=read(context.input_path(spec['legacy_key']))
    original_hash=context.manifest['inputs'][spec['legacy_key']]['sha256']
    if (case!=expected or parent!=convert(old,profile=spec['profile'],source_sha256=original_hash)
            or case['configuration']['model']!=spec['model']):
        raise ValueError('new duration input or verified legacy prefix changed')
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
    old=dict(old,packets=n,raw_theta=theta,raw_dv=dv,durations=dt,
             starts=np.r_[0.,np.cumsum(dt)[:-1]],limits=config['limits'],profile=spec['profile'])
    def reserve():
        nonlocal calls
        if calls>=4:raise ValueError('four-query duration comparison allowance exhausted')
        context.charge(native_calls=1,packet_visits=n);calls+=1
    class Book:
        def tick(self,kind):
            if kind!='tangent':raise ValueError('only the legacy tangent API is allowed')
            reserve()
    first=np.zeros(27);first[25]=-1.
    second=np.array([(i%5-2)/16 for i in range(27)]);second[25]=1.
    clock_norms=[];warnings=[]
    for ordinal,(time_s,point) in enumerate(zip((438.,478.),(first,second),strict=True)):
        if time_s-1.<0. or time_s+1.>case['provenance']['sequential_endpoint_s']:
            raise ValueError('complete declared clock range is outside input support')
        value,jac,warning=legacy.Kernel.tangent(old_api,dict(old,base_time=time_s),point,Book())
        before=plain(dict(time_s=time_s,point=point,prediction=value,jacobian=jac,warning=warning))
        context.save(f'legacy-{ordinal}.json',before)
        reserve();out=np.empty((1,3));current_jac=np.empty((3,27));flag=ctypes.c_int()
        code=kernel(n,theta,dv,dt,1,np.array([time_s]),config['initial_c'],config['initial_v'],config['initial_r'],
            config['limits'],point,config['model'],int(config['profile']),config['gravity'],config['radius'],
            out,current_jac,ctypes.byref(flag))
        if code:raise ValueError('current native duration query failed')
        after=plain(dict(time_s=time_s,point=point,prediction=out[0],jacobian=current_jac,warning=flag.value))
        context.save(f'current-{ordinal}.json',after);compare_native(after,before)
        norm=float(np.linalg.norm(current_jac[:,25]))
        if not np.isfinite(norm) or norm==0.:raise ValueError('clock derivative column was lost')
        clock_norms.append(norm);warnings.append(flag.value)
    return dict(identity=task['identity'],passed=True,model=spec['model'],profile=spec['profile'],packets=n,
        query_times_s=[438.,478.],clock_offset_limit_s=1.,clock_column_norms=clock_norms,warning_flags=warnings,
        bitwise_api_equivalent=True,physical_parameter_count=27,parameter_points=2,
        independent_physics_validation=False,native_evaluations=calls,bound_evaluations=0,
        original_reads=0,optimizer_starts=0,recording_length_usefulness_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
