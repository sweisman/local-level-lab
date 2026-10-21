# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite training-transfer checks; known calibration follows sealed bounds."""


def evaluate(task,context):
    from fractions import Fraction as F
    import time
    import numpy as np
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_conditioned_acceleration import ConditionedAcceleration
    from lll.ilvis0_compiled_transport import configure_backend
    from lll.ilvis0_source_stream import SourceStream,load_stream
    from lll.ilvis0_source_value_stream import SourceValueStream
    from lll.ilvis0_rounded_body_interval import RoundedBodyInterval
    from lll.ilvis0_transform_native import make_reference
    from lll.ilvis0_orientation_cover import sector
    started=time.monotonic();spec=task['payload'];bundle=read(context.input_path())
    case=read(context.input_path(spec['case_key']));parent=read(context.input_path(spec['conditioning_key']))
    future=bundle['future'];n=len(case['dt']);selected=spec['prefixes']
    fixed=[0,15,63,127,511,1023,1438,1439,1440,1599]
    limits=dict(setups=1,source_steps=2*n,exact_supports=6,body_bounds=20,truth_checks=240)
    if n!=1600 or selected!=fixed or spec['limits']!=limits or not bundle['result']['passed']:
        raise ValueError('six fixed generated sources and prefix matrix required')
    events=[]
    def persist(event):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:03d}.json',event);events.append(event)
    def check():
        _check_continue(context.root,context.manifest)
        if time.monotonic()-started>spec['maximum_seconds']:raise TimeoutError('rounded-source identity allowance exhausted')
    budget=Allowance(limits,persist);budget.reserve(dict(setups=1))
    sources=context.root/'source-freeze/analysis/lll'
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';directory.mkdir(exist_ok=True)
    arithmetic=configure_backend(directory,source_directory=sources)
    kernel,compilation=load_stream(directory,source_directory=sources)
    if compilation['compiler']!=spec['compiler']:raise ValueError('frozen compiler changed')
    context.save('compilation.json',dict(arithmetic=arithmetic,source=compilation))
    box=sector(4);reference=make_reference(case['configuration'],case['theta'],case['dv'],case['dt'],
        **{k:box[k] for k in ('lower','upper','center')})
    if reference.report()!=future['reference']:raise ValueError('source/reference changed')
    conditioning=ConditionedAcceleration(parent['projection_input'],parent['projection'],
        reserve=lambda count:budget.reserve(dict(exact_supports=count)))
    if conditioning.binding!=future['bound']['conditioning']['input_binding']:
        raise ValueError('training-conditioning identity changed')
    context.save('conditioning.json',conditioning.report())
    lo=future['lower'][:27];hi=future['upper'][:27]
    adapter=RoundedBodyInterval(reference,conditioning,lo,hi)
    context.save('initial-source-bridge.json',adapter.bridge)
    budget.reserve(dict(source_steps=n));context.charge(bound_calls=1,bound_steps=2*n)
    saved={};body_count=0
    with SourceValueStream(case,reference,lo,hi,future['time_s'],maximum_packets=n) as physical,SourceStream(
            kernel,case,reference.parent.center,future['time_s'],maximum_packets=n) as native:
        for index in range(n):
            if index%16==0:check()
            proof=physical.append();frame=native.append()
            if index not in selected:continue
            for phase,source in enumerate(proof['phases']):
                budget.reserve(dict(body_bounds=1))
                result=adapter.bound(source,frame,phase=phase);body_count+=1
                if not np.array_equal(result.a.center,frame['values'][phase,0]) or not np.array_equal(
                        result.b.center,frame['values'][phase,1]) or not np.array_equal(result.jacobian,frame['jacobian'][phase]):
                    raise ValueError('stated source centers or rows changed')
                metadata={k:v for k,v in result.details.items() if k!='initial_source_bridge'}
                name=f'bound-{index:04d}-{phase}.json'
                context.save(name,plain(dict(metadata=metadata,a=dict(center=result.a.center,change=result.a.component_change,
                    remainder=result.a.component_remainder),b=dict(center=result.b.center,change=result.b.component_change,
                    remainder=result.b.component_remainder),jacobian=result.jacobian)))
                saved[(index,phase)]=name
    if body_count!=20:raise ValueError('incomplete frozen body matrix')
    # These bytes are immutable before the first inspection of the truth field.
    context.save('bounds-sealed.json',dict(bound_artifacts=list(saved.values()),count=20,known_calibration_inspected=False))
    point=case['truth']
    if any(not a<=x<=b for a,x,b in zip(lo,point,hi,strict=True)):raise ValueError('known calibration outside saved domain')
    delta=[F(float(x))-F(float(z)) for x,z in zip(point,reference.parent.center,strict=True)]
    budget.reserve(dict(source_steps=n,truth_checks=240));checks=0;passed=True;first_failure=None
    with SourceStream(kernel,case,point,future['time_s'],maximum_packets=n) as truth:
        for index in range(n):
            if index%32==0:check()
            actual=truth.append()
            if index not in selected:continue
            for phase in (0,1):
                bound=read(context.directory/saved[(index,phase)])
                for source,name in enumerate(('a','b')):
                    value=bound[name];rows=bound['jacobian'][source]
                    for axis in range(3):
                        error=F(float(actual['values'][phase,source,axis]))-F(float(value['center'][axis]))
                        linear=sum((F(float(v))*d for v,d in zip(rows[axis],delta,strict=True)),F(0))
                        for kind,difference,limit in (('value',abs(error),F(float(value['change'][axis]))),
                                ('affine',abs(error-linear),F(float(value['remainder'][axis])))):
                            checks+=1
                            if difference>limit:
                                passed=False
                                if first_failure is None:first_failure=dict(packet=index,phase=phase,source=name,axis=axis,
                                    kind=kind,difference=str(difference),allowance=str(limit))
    if checks!=240:raise ValueError('incomplete known-calibration accounting')
    context.save('truth-comparison.json',plain(dict(point=point,checks=checks,first_failure=first_failure,
        comparison_margin=0,known_calibration_read_after_sealed_bounds=True)))
    return dict(identity=task['identity'],passed=passed,model=bundle['result']['model'],profile=bundle['result']['profile'],
        source_steps=2*n,body_bounds=body_count,truth_checks=checks,exact_supports=conditioning.supports_verified,
        work=budget.counts,elapsed_s=time.monotonic()-started,stated_centers_and_rows_unchanged=True,
        known_calibration_read_after_sealed_bounds=True,physical_parameter_count=27,shared_columns_changed=False,
        full_native_trajectory_evaluations=0,optimizer_starts=0,original_reads=0,native_propagation_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
