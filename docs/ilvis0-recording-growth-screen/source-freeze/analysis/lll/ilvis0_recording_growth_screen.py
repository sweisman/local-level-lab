# SPDX-License-Identifier: AGPL-3.0-or-later
"""Full-prior growth diagnostic; no training certificate is transferred."""
import ctypes
from fractions import Fraction as F


def evaluate(task,context):
    import time
    import numpy as np
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_directional_acceleration import DirectionalAcceleration
    from lll.ilvis0_recording_case_checks import evaluate_case
    from lll.ilvis0_batched_transport import configure_backend
    from lll.ilvis0_source_stream import load_stream
    from lll.ilvis0_source_derivative_intervals import load_kernel
    from lll.ilvis0_source_point_derivatives import load_kernel as load_point
    from lll.ilvis0_saved_prediction_audit import endpoint
    from lll import ilvis0_direct_native as candidate
    spec=task['payload'];recipe=read(context.input_path());case=read(context.input_path(spec['case_key']))
    if set(recipe)!={'time_s','center','lower','upper','coordinate_scale'}:
        raise ValueError('only a declared query/domain recipe may extend the preserved input')
    case=dict(case,**recipe);n=len(case['dt']);config=case['configuration']
    if (n!=48000 or case['time_s']!=spec['time_s'] or config['model']!=spec['model']
            or config['profile']!=spec['profile'] or config['limits'][25]!=0.
            or case['center']!=[0.]*27 or case['lower']!=[-1.]*27 or case['upper']!=[1.]*27):
        raise ValueError('complete original global region, fixed clock and frozen query required')
    config={k:np.ascontiguousarray(v,float) if k in ('initial_c','initial_v','initial_r','limits') else v for k,v in config.items()}
    theta,dv,dt=(np.ascontiguousarray(case[k],float) for k in ('theta','dv','dt'))
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';directory.mkdir(parents=True,exist_ok=True)
    sources=context.root/'source-freeze/analysis/lll'
    arithmetic=configure_backend(directory,source_directory=sources)
    source,source_meta=load_stream(directory,source_directory=sources)
    derivative,derivative_meta=load_kernel(directory,source_directory=sources)
    point,point_meta=load_point(directory,source_directory=sources)
    kernel,kernel_meta=load_tangent(directory)
    compilation=dict(arithmetic=arithmetic,source=source_meta,derivative=derivative_meta,point=point_meta,native=kernel_meta)
    if any(v['compiler']!=spec['compiler'] for v in compilation.values()):raise ValueError('compiler changed')
    context.save('compilation.json',compilation)
    events=[]
    def persist(event):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:03d}.json',event);events.append(event)
    limits=dict(setups=1,proofs=1,source_setups=1,source_steps=n,source_body_bounds=n,
        source_derivative_setups=1,source_derivative_steps=n,source_point_setups=1,source_point_steps=n,source_direct_steps=n)
    if limits!=spec['limits']:raise ValueError('finite growth-screen recipe changed')
    budget=Allowance(limits,persist);calls=0;bounds=0;native_rows=[];saved_bound=None;bound_elapsed=None
    def native(parameters):
        nonlocal calls
        context.charge(native_calls=1,packet_visits=n);calls+=1
        out=np.empty((1,3));jac=np.empty((3,27));flag=ctypes.c_int()
        code=kernel(n,theta,dv,dt,1,np.array([case['time_s']]),config['initial_c'],config['initial_v'],config['initial_r'],
            config['limits'],np.ascontiguousarray(parameters,float),config['model'],int(config['profile']),
            config['gravity'],config['radius'],out,jac,ctypes.byref(flag))
        if code:raise ValueError('native growth query failed')
        record=plain(dict(point=parameters,prediction=out[0],jacobian=jac,warning=flag.value))
        context.save(f'native-{calls:02d}.json',record);native_rows.append(record)
        return out[0],jac
    def bound(center,lower,upper):
        nonlocal bounds,saved_bound,bound_elapsed
        if bounds:raise ValueError('one bound per fixed identity required')
        budget.reserve(limits);context.charge(bound_calls=1,bound_steps=9*n);bounds+=1
        reference=candidate.make_reference(config,theta,dv,dt,lower=lower,upper=upper,center=center)
        proof=DirectionalAcceleration(reference,lower,upper)
        context.save('physical-proof.json',proof.report());context.save('reference.json',reference.report())
        started=time.monotonic()
        report=candidate.enclose(config,theta,dv,dt,time=case['time_s'],lower=lower,upper=upper,
            reference=reference,conditioning=proof,source_kernel=source,derivative_kernel=derivative,point_kernel=point,
            maximum_seconds=spec['maximum_bound_seconds'])
        bound_elapsed=time.monotonic()-started;saved_bound=report
        context.save('bound.json',plain(report.report()))
        return report,reference
    result=evaluate_case(dict(identity=task['identity'],kind='region'),case,native=native,bound=bound)
    report=saved_bound;scale=case['coordinate_scale'];design=result['augmented_design'];radii=[];remainders=[]
    native_center=native_rows[0]['prediction'];transfer=[]
    for axis,unit in enumerate(scale):
        discrepancy=abs(F(native_center[axis])-F(float(report.center[axis])))
        remainder=F(float(report.unshared_remainder[axis]))+discrepancy
        widths=[max(abs(F(a)-F(c)),abs(F(b)-F(c))) for a,b,c in zip(case['lower'],case['upper'],case['center'],strict=True)]+[F(1)]*24
        radius=remainder+sum((abs(F(float(v)))*w for v,w in zip(design[axis],widths,strict=True)),F(0))
        radii.append(endpoint(radius*F(unit),True));remainders.append(endpoint(remainder*F(unit),True))
        transfer.append(endpoint(discrepancy*F(unit),True))
    if any(report.metadata[k]>n for k in ('source_reference_steps','source_derivative_steps','source_direct_steps','rounded_source_prefixes')):
        raise ValueError('source work exceeds reservation')
    return plain(dict(result,work=budget.counts,native_evaluations=calls,bound_evaluations=bounds,
        bound_elapsed_s=bound_elapsed,query_time_s=case['time_s'],packets=n,
        used_packets=report.metadata['used_packet_count'],source_reference_steps=report.metadata['source_reference_steps'],
        source_derivative_steps=report.metadata['source_derivative_steps'],source_direct_steps=report.metadata['source_direct_steps'],
        conditional_full_domain_radius_m=radii,unshared_radius_m=remainders,center_transfer_m=transfer,
        uses_training_constraints=False,original_clock_fixed=True,recording_length_usefulness_qualified=False,
        mathematical_outer_range_only=True,original_reads=0,optimizer_starts=0,
        observational_coverage_qualified=False,scientific_decision='abstain'))
