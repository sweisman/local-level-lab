# SPDX-License-Identifier: AGPL-3.0-or-later
"""Charged physical source-value qualification, with no training substitution."""


def evaluate(task,context):
    from fractions import Fraction as F
    import hashlib,time
    from pathlib import Path
    import numpy as np
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_transform_native import make_reference
    from lll.ilvis0_orientation_cover import sector
    from lll.ilvis0_source_stream import SourceStream,load_stream
    from lll.ilvis0_source_value_stream import SourceValueStream
    from lll.ilvis0_compiled_transport import configure_backend
    from lll.ilvis0_rotation_interval import vertical_interval
    specification=task['payload'];bundle=read(context.input_path())
    case=read(context.input_path(specification['case_key']));n=len(case['dt']);future=bundle['future']
    limits=dict(setups=1,source_steps=n,scalar_comparisons=12*n,norm_closures=2*n)
    if n!=1600 or specification['limits']!=limits or not bundle['result']['passed']:
        raise ValueError('six unchanged qualified generated sources required')
    events=[]
    def persist(event):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:03d}.json',event);events.append(event)
    budget=Allowance(limits,persist);budget.reserve(dict(setups=1))
    sources=context.root/'source-freeze/analysis/lll'
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';directory.mkdir(exist_ok=True)
    arithmetic=configure_backend(directory,source_directory=sources)
    kernel,compilation=load_stream(directory,source_directory=sources)
    if compilation['compiler']!=specification['compiler']:raise ValueError('frozen source compiler changed')
    context.save('compilation.json',dict(arithmetic=arithmetic,source=compilation))
    box=sector(4);reference=make_reference(case['configuration'],case['theta'],case['dv'],case['dt'],
        **{k:box[k] for k in ('lower','upper','center')})
    if reference.report()!=future['reference']:raise ValueError('saved source/reference changed')
    lower=future['lower'][:27];upper=future['upper'][:27]
    budget.reserve(dict(source_steps=n,scalar_comparisons=12*n,norm_closures=2*n))
    context.charge(bound_calls=1,bound_steps=2*n)
    started=time.monotonic();checks=closures=visits=0;passed=True;first_failure=None
    stream_hash=hashlib.sha256();reference_hash=hashlib.sha256();largest_change=0.;selected=[]
    with SourceValueStream(case,reference,lower,upper,future['time_s'],maximum_packets=n) as bound_stream,SourceStream(
            kernel,case,reference.parent.center,future['time_s'],maximum_packets=n) as native:
        for index in range(n):
            if index%16==0:
                _check_continue(context.root,context.manifest)
                if time.monotonic()-started>specification['maximum_seconds']:
                    raise TimeoutError('physical source-value identity allowance exhausted')
            frame=bound_stream.append();actual=native.append();prefix=[]
            for phase,proof in enumerate(frame['phases']):
                if (proof.reference_binding!=reference.binding or proof.lower!=tuple(lower)
                        or proof.upper!=tuple(upper) or proof.packet_index!=index or proof.phase!=phase):
                    raise ValueError('source interval identity mismatch')
                for source,(value,observed) in enumerate(zip((proof.a,proof.b),actual['values'][phase],strict=True)):
                    for axis in range(3):
                        error=abs(F(float(value.center[axis]))-F(float(observed[axis])))
                        allowed=F(float(value.component_change[axis]));checks+=1
                        if error>allowed:
                            passed=False
                            if first_failure is None:first_failure=dict(packet=index,phase=phase,source=source,axis=axis,
                                difference=str(error),allowance=str(allowed))
                    stream_hash.update(value.center.tobytes());stream_hash.update(value.component_change.tobytes())
                    largest_change=max(largest_change,value.change)
                alo,ahi=proof.interval('a');blo,bhi=proof.interval('b')
                closure=vertical_interval(alo,ahi,blo,bhi,norm_identity=True,norm_error=proof.norm_error);closures+=1
                prefix.append(dict(proof.report(),a=dict(center=proof.a.center,change=proof.a.component_change),
                    b=dict(center=proof.b.center,change=proof.b.component_change),closure=closure))
            reference_hash.update(actual['values'].tobytes());visits+=1
            if index in (0,n-1) or actual['time_slope']:
                name=f'prefix-{index:04d}.json';context.save(name,plain(dict(bounds=prefix,reference=actual)));selected.append(name)
    if checks!=12*n or closures!=2*n or visits!=n:raise ValueError('incomplete source-prefix accounting')
    context.save('comparison.json',dict(first_failure=first_failure,bound_stream_sha256=stream_hash.hexdigest(),
        reference_stream_sha256=reference_hash.hexdigest(),selected_prefix_artifacts=selected,
        maximum_value_change=largest_change,comparison_margin=0))
    return dict(identity=task['identity'],passed=passed,model=bundle['result']['model'],profile=bundle['result']['profile'],
        source_steps=visits,scalar_comparisons=checks,norm_closures=closures,bound_evaluations=1,
        reserved_bound_steps=2*n,work=budget.counts,elapsed_s=time.monotonic()-started,
        source_value_intervals=True,training_conditioning_installed=False,affine_rows_qualified=False,
        full_native_trajectory_evaluations=0,optimizer_starts=0,original_reads=0,
        native_propagation_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')
