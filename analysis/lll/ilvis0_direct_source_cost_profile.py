# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite profiling of unchanged physical/derivative/direct source streams."""
from pathlib import Path


def evaluate(task,context):
    import cProfile,pstats,time
    from lll.ilvis0_sharded_native import read
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_orientation_cover import sector
    from lll.ilvis0_direct_native import make_reference
    from lll.ilvis0_direct_source_taylor import SourceDirectStream
    from lll.ilvis0_batched_transport import configure_backend
    from lll.ilvis0_source_derivative_intervals import load_kernel
    from lll.ilvis0_source_point_derivatives import load_kernel as load_point
    spec=task['payload'];bundle=read(context.input_path());case=read(context.input_path(spec['case_key']))
    n=len(case['dt']);old=bundle['result'];saved=bundle['future']
    limits=dict(setups=1,source_steps=n,derivative_setups=1,derivative_steps=n,point_setups=1,direct_steps=n)
    if (n!=1600 or spec['limits']!=limits or old['task']['sector']!=7
            or (case['configuration']['model'],case['configuration']['profile'])!=(spec['model'],spec['profile'])
            or not old['passed'] or old['excluded'] or saved['time_s']!=7.2):
        raise ValueError('six unchanged complete generated region-seven inputs required')
    events=[]
    def persist(event):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:03d}.json',event);events.append(event)
    budget=Allowance(limits,persist);budget.reserve(limits)
    box=sector(7);reference=make_reference(case['configuration'],case['theta'],case['dv'],case['dt'],
        **{k:box[k] for k in ('lower','upper','center')})
    if reference.report()!=saved['reference']:raise ValueError('qualified source/reference changed')
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';directory.mkdir(parents=True,exist_ok=True)
    sources=context.root/'source-freeze/analysis/lll'
    arithmetic=configure_backend(directory,source_directory=sources)
    derivative,derivative_meta=load_kernel(directory,source_directory=sources)
    point,point_meta=load_point(directory,source_directory=sources)
    compilation=dict(arithmetic=arithmetic,derivative=derivative_meta,point=point_meta)
    if any(v['compiler']!=spec['compiler'] for v in compilation.values()):raise ValueError('frozen compiler changed')
    context.save('compilation.json',compilation)
    stream=SourceDirectStream(case,reference,saved['lower'][:27],saved['upper'][:27],7.2,
        maximum_packets=n,derivative_kernel=derivative,point_kernel=point)
    profiler=cProfile.Profile();error=None;elapsed=0.;expected=0
    for period in case['dt']:
        if elapsed>float(stream.query_upper):break
        expected+=1;elapsed+=period
    context.charge(bound_calls=1,bound_steps=3*n)
    started=time.monotonic();profiler.enable()
    try:
        for _ in range(expected):
            _check_continue(context.root,context.manifest)
            if time.monotonic()-started>=spec['maximum_profile_seconds']:
                raise RuntimeError('source profile time allowance exhausted')
            frame=stream.append()
            if len(frame['phases'])!=2 or tuple(p.phase for p in frame['phases'])!=(0,1):
                raise ValueError('both original source phases must remain')
    except Exception as caught:error=dict(type=type(caught).__name__,message=str(caught))
    finally:
        profiler.disable();stream.close()
    elapsed=time.monotonic()-started;statistics=pstats.Stats(profiler)
    def row(key,value):
        return dict(file=Path(key[0]).name,line=key[1],function=key[2],primitive_calls=value[0],
            calls=value[1],self_time_s=value[2],cumulative_s=value[3])
    all_rows=[row(k,v) for k,v in statistics.stats.items()]
    components=[r for r in all_rows if r['function']=='append' and r['file'] in (
        'ilvis0_batched_source_values.py','ilvis0_source_derivative_intervals.py','ilvis0_direct_source.py')]
    visits=dict(physical=stream.visits,derivative=stream.derivatives.visits,direct=stream.direct.visits)
    if any(v>n for v in visits.values()):raise ValueError('source profile exceeded its reservation')
    result=dict(identity=task['identity'],passed=error is None and all(v==expected for v in visits.values()),
        model=spec['model'],profile=spec['profile'],work=budget.counts,expected_prefixes=expected,actual_visits=visits,
        elapsed_s=elapsed,error=error,components=components,
        profiler_total_time_s=statistics.total_tt,profiler_total_calls=statistics.total_calls,
        bound_evaluations=1,native_evaluations=0,original_reads=0,optimizer_starts=0,
        numerical_qualification=False,observational_coverage_qualified=False,scientific_decision='abstain')
    context.save('profile.json',dict(result,functions=sorted(all_rows,key=lambda r:r['cumulative_s'],reverse=True)[:40]))
    return result
