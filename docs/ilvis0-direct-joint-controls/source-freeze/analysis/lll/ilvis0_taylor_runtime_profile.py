# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite cost diagnosis of source-derivative propagation on generated inputs."""
from copy import deepcopy


def prefix(case,*,model,profile):
    import numpy as np
    config=case['configuration']
    if (config['model']!=model or config['profile'] is not profile
            or any(len(case[k])!=1600 for k in ('dt','theta','dv'))
            or any(v!=.005 for v in case['dt'][:128])):
        raise ValueError('fixed generated source, processing case and 128-packet clock required')
    return dict(configuration=deepcopy(config),
        **{key:np.array(case[key][:128],dtype=float,copy=True) for key in ('dt','theta','dv')})


def evaluate(task,context):
    import cProfile
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_orientation_cover import sector
    from lll.ilvis0_directional_acceleration import DirectionalAcceleration
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_batched_transport import configure_backend
    from lll.ilvis0_source_stream import load_stream
    from lll.ilvis0_source_derivative_intervals import load_kernel
    from lll.ilvis0_source_runtime_profile import profile_statistics
    from lll import ilvis0_taylor_native as candidate
    spec=task['payload'];case=prefix(read(context.input_path()),model=1,profile=spec['profile'])
    n=128;config=case['configuration'];limits=dict(setups=1,source_setups=1,source_steps=n,
        source_body_bounds=n,derivative_setups=1,derivative_steps=n)
    if spec['packets']!=n or spec['limits']!=limits:raise ValueError('fixed diagnostic limits required')
    events=[]
    def persist(event):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:03d}.json',event);events.append(event)
    budget=Allowance(limits,persist);budget.reserve(limits)
    box=sector(4);config=case['configuration']
    reference=candidate.make_reference(config,case['theta'],case['dv'],case['dt'],
        **{k:box[k] for k in ('lower','upper','center')})
    conditioning=DirectionalAcceleration(reference,box['lower'],box['upper'])
    directory=context.directory/'compiled';directory.mkdir(parents=True,exist_ok=True)
    sources=context.root/'source-freeze/analysis/lll'
    arithmetic=configure_backend(directory,source_directory=sources)
    kernel,source_meta=load_stream(directory,source_directory=sources)
    derivative,derivative_meta=load_kernel(directory,source_directory=sources)
    compilations=dict(arithmetic=arithmetic,source=source_meta,derivative=derivative_meta)
    if any(v['compiler']!=spec['compiler'] for v in compilations.values()):
        raise ValueError('frozen compiler changed')
    context.save('compilation.json',compilations)
    context.charge(bound_calls=1,bound_steps=8*n)
    profiler=cProfile.Profile();error=None;report=None;profiler.enable()
    try:
        report=candidate.enclose(config,case['theta'],case['dv'],case['dt'],time=.32,
            lower=box['lower'],upper=box['upper'],reference=reference,conditioning=conditioning,
            maximum_seconds=spec['maximum_bound_seconds'],source_kernel=kernel,derivative_kernel=derivative)
    except Exception as caught:error=dict(type=type(caught).__name__,message=str(caught))
    finally:profiler.disable()
    statistics=profile_statistics(profiler);context.save('profile.json',statistics)
    if report is not None:context.save('bound.json',plain(report.report()))
    return dict(identity=task['identity'],passed=error is None,model=1,processing_profile=spec['profile'],
        packets=n,bound_completed=report is not None,error=error,work=budget.counts,profile=statistics,
        original_reads=0,native_evaluations=0,optimizer_starts=0,numerical_qualification=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
