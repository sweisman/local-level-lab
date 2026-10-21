# SPDX-License-Identifier: AGPL-3.0-or-later
"""Once-per-source long-history comparison of compiled conservative bounds."""
from lll.ilvis0_transport_range_preflight import compare_bounds


def evaluate(task,context):
    import numpy as np
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_conditioned_acceleration import ConditionedAcceleration
    from lll.ilvis0_orientation_cover import sector
    from lll import ilvis0_taylor_native as candidate
    from lll.ilvis0_batched_transport import configure_backend
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';directory.mkdir(exist_ok=True)
    arithmetic=configure_backend(directory,source_directory=context.root/'source-freeze/analysis/lll')
    context.save('arithmetic.json',arithmetic)
    from lll.ilvis0_source_stream import load_stream
    source_kernel,source_compilation=load_stream(directory,source_directory=context.root/'source-freeze/analysis/lll')
    if source_compilation['compiler']!=task['payload']['compiler']:raise ValueError('frozen source compiler changed')
    context.save('source-compilation.json',source_compilation)
    from lll.ilvis0_source_derivative_intervals import load_kernel
    derivative_kernel,derivative_compilation=load_kernel(directory,source_directory=context.root/'source-freeze/analysis/lll')
    context.save('source-derivative-compilation.json',derivative_compilation)
    bundle=read(context.input_path());case=read(context.input_path(task['payload']['case_key']))
    parent=read(context.input_path(task['payload']['conditioning_key']));future=bundle['future'];old=future['bound'];spec=task['payload']
    n=len(case['dt']);limits=dict(setups=1,exact_supports=6,source_steps=n,source_body_bounds=n,source_derivative_setups=1,source_derivative_steps=n)
    if n!=1600 or spec['limits']!=limits or not bundle['result']['passed']:raise ValueError('six fixed qualified sources required')
    events=[]
    def persist(event):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:03d}.json',event);events.append(event)
    budget=Allowance(limits,persist);budget.reserve(dict(setups=1))
    conditioning=ConditionedAcceleration(parent['projection_input'],parent['projection'],
        reserve=lambda count:budget.reserve(dict(exact_supports=count)))
    if conditioning.binding!=old['conditioning']['input_binding']:raise ValueError('saved conditioning identity changed')
    box=sector(4);reference=candidate.make_reference(case['configuration'],case['theta'],case['dv'],case['dt'],
        **{k:box[k] for k in ('lower','upper','center')})
    if reference.report()!=future['reference']:raise ValueError('saved native source reference changed')
    left=old['lower'];right=old['upper']
    conditioning.match(reference.report(),left,right)
    context.save('conditioning.json',conditioning.report())
    budget.reserve(dict(source_steps=n,source_body_bounds=n,source_derivative_setups=1,source_derivative_steps=n))
    context.charge(bound_calls=1,bound_steps=8*n)
    import time
    started=time.monotonic()
    report=candidate.enclose(case['configuration'],case['theta'],case['dv'],case['dt'],time=future['time_s'],
        lower=left,upper=right,reference=reference,conditioning=conditioning,maximum_seconds=spec['maximum_bound_seconds'],source_kernel=source_kernel,derivative_kernel=derivative_kernel)
    current=report.report();context.save('bound.json',plain(current))
    scale=parent['projection_input']['training']['region']['coordinate_scale']
    previous=read(context.input_path(spec['baseline_key']))
    compatibility=compare_bounds(old,previous,scale)
    if not compatibility['passed']:raise ValueError('saved baseline maps are incompatible')
    context.save('baseline-comparison.json',compatibility)
    compiled=read(context.input_path(spec['compiled_key']))
    compiled_compatibility=compare_bounds(old,compiled,scale)
    if not compiled_compatibility['passed']:raise ValueError('compiled comparison maps differ')
    context.save('compiled-baseline-comparison.json',compiled_compatibility)
    best=dict(old,unshared_remainder=np.minimum.reduce([old['unshared_remainder'],previous['unshared_remainder'],compiled['unshared_remainder']]).tolist())
    result=compare_bounds(best,current,scale)
    if current['source_reference_steps']>n or current['rounded_source_prefixes']>n:
        raise ValueError('source work exceeds its reserved ceiling')
    return dict(result,identity=task['identity'],model=bundle['result']['model'],profile=bundle['result']['profile'],
        work=budget.counts,bound_elapsed_s=time.monotonic()-started,arithmetic=arithmetic,parameter_count=51,native_evaluations=0,bound_evaluations=1,
        reserved_bound_steps=8*n,source_derivative_steps=current['source_derivative_steps'],source_mean_value_interval_installed=True,source_norm_interval_installed=True,source_reference_steps=current['source_reference_steps'],source_body_bounds=current['rounded_source_prefixes'],baseline_kind='minimum of compatible original, compiled and batched source bounds',original_reads=0,optimizer_starts=0,
        observational_coverage_qualified=False,scientific_decision='abstain')
