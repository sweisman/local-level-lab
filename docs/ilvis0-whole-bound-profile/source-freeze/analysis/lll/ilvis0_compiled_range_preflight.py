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
    from lll import ilvis0_compiled_native as candidate
    from lll.ilvis0_compiled_transport import configure_backend
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';directory.mkdir(exist_ok=True)
    arithmetic=configure_backend(directory,source_directory=context.root/'source-freeze/analysis/lll')
    context.save('arithmetic.json',arithmetic)
    bundle=read(context.input_path());case=read(context.input_path(task['payload']['case_key']))
    parent=read(context.input_path(task['payload']['conditioning_key']));future=bundle['future'];old=future['bound'];spec=task['payload']
    n=len(case['dt']);limits=dict(setups=1,exact_supports=6)
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
    context.charge(bound_calls=1,bound_steps=2*n)
    import time
    started=time.monotonic()
    report=candidate.enclose(case['configuration'],case['theta'],case['dv'],case['dt'],time=future['time_s'],
        lower=left,upper=right,reference=reference,conditioning=conditioning,maximum_seconds=spec['maximum_bound_seconds'])
    current=report.report();context.save('bound.json',plain(current))
    scale=parent['projection_input']['training']['region']['coordinate_scale']
    result=compare_bounds(old,current,scale)
    return dict(result,identity=task['identity'],model=bundle['result']['model'],profile=bundle['result']['profile'],
        work=budget.counts,bound_elapsed_s=time.monotonic()-started,arithmetic=arithmetic,parameter_count=51,native_evaluations=0,bound_evaluations=1,
        reserved_bound_steps=2*n,source_norm_interval_installed=False,original_reads=0,optimizer_starts=0,
        observational_coverage_qualified=False,scientific_decision='abstain')
