# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated-prefix runtime diagnosis; no observed-data qualification."""
from pathlib import Path


def profile_statistics(profiler):
    import pstats
    stats=pstats.Stats(profiler)
    rows=sorted(stats.stats.items(),key=lambda pair:pair[1][3],reverse=True)[:40]
    return dict(total_calls=stats.total_calls,total_time_s=stats.total_tt,
        functions=[dict(file=Path(key[0]).name,line=key[1],function=key[2],primitive_calls=value[0],
            calls=value[1],self_time_s=value[2],cumulative_s=value[3]) for key,value in rows])


def evaluate(task,context):
    import cProfile
    import numpy as np
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_orientation_cover import sector
    from lll.ilvis0_directional_acceleration import DirectionalAcceleration
    from lll import ilvis0_source_native_v2 as candidate
    case=read(context.input_path());spec=task['payload'];config=case['configuration'];n=spec['packets']
    if (n!=128 or len(case['dt'])!=1600 or config['model']!=spec['model'] or config['profile']
            or not all(v==.005 for v in case['dt'][:n])):
        raise ValueError('fixed 128-packet zero-removal profiling inputs required')
    theta=np.ascontiguousarray(case['theta'][:n]);dv=np.ascontiguousarray(case['dv'][:n]);dt=np.ascontiguousarray(case['dt'][:n])
    box=sector(4);reference=candidate.make_reference(config,theta,dv,dt,**{k:box[k] for k in ('lower','upper','center')})
    conditioning=DirectionalAcceleration(reference,box['lower'],box['upper'])
    from lll.ilvis0_compiled_transport import configure_backend
    from lll.ilvis0_source_stream import load_stream
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_control_shards import _check_continue
    directory=context.directory/'compiled';directory.mkdir(exist_ok=True)
    sources=context.root/'source-freeze/analysis/lll'
    arithmetic=configure_backend(directory,source_directory=sources)
    kernel,compilation=load_stream(directory,source_directory=sources)
    if compilation['compiler']!=spec['compiler']:raise ValueError('frozen compiler changed')
    context.save('compilation.json',dict(arithmetic=arithmetic,source=compilation))
    events=[]
    def persist(event):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:03d}.json',event);events.append(event)
    limits=dict(setups=1,source_steps=n,source_body_bounds=n)
    if limits!=spec['limits']:raise ValueError('fixed source profiling work required')
    budget=Allowance(limits,persist);budget.reserve(limits)
    context.charge(bound_calls=1,bound_steps=4*n)
    profiler=cProfile.Profile();profiler.enable();error=None;report=None
    try:
        report=candidate.enclose(config,theta,dv,dt,time=float(sum(dt)/2),lower=box['lower'],upper=box['upper'],
            reference=reference,conditioning=conditioning,maximum_seconds=spec['maximum_bound_seconds'],source_kernel=kernel)
    except Exception as caught:error=dict(type=type(caught).__name__,message=str(caught))
    finally:profiler.disable()
    statistics=profile_statistics(profiler);context.save('profile.json',statistics)
    if report is not None:context.save('bound.json',plain(report.report()))
    return dict(identity=task['identity'],passed=error is None,model=config['model'],packets=n,
        bound_completed=report is not None,error=error,work=budget.counts,profile=statistics,clock_limit_s=config['limits'][25],
        original_reads=0,native_evaluations=0,optimizer_starts=0,numerical_qualification=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
