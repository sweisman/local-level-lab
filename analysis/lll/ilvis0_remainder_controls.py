# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite native checks of a conditional Taylor remainder; generated data only."""
from fractions import Fraction as F


def recipe():
    physical=[[0.]*27,[-1.]*27,[1.]*27,[.5*(i%3-1) for i in range(27)]]
    conditioned=[[0.]*27,[-.01]*27,[.01]*27,[.01*(i%3-1) for i in range(27)]]
    conditioned[1][25]=-1.;conditioned[2][25]=1.;conditioned[3][25]=.25
    return dict(packets=800,time_s=2.5,clock_limit_s=1.,lower=[-1.]*27,upper=[1.]*27,
        center=[0.]*27,force_change_mps2=.2,maximum_bound_seconds=180.,
        oracle_arithmetic_allowance_m=1e-5,probes=dict(physical=physical,conditioned=conditioned))


def validate_recipe(value):
    if value!=recipe():raise ValueError('unchanged finite recipe, broad domain and probes required')


def limits(scope):
    if scope not in ('physical','conditioned'):raise ValueError('declared proof scope required')
    return dict(reference_setups=1,physical_proofs=int(scope=='physical'),
        conditional_proofs=int(scope=='conditioned'),lp_proposals=6*int(scope=='conditioned'),
        exact_supports=24*int(scope=='conditioned'),source_setups=2,source_steps=1600,
        source_body_bounds=1600,source_derivative_setups=2,source_derivative_steps=1600,
        source_point_setups=2,source_point_steps=1600,source_direct_steps=1600,
        algebra_certificates=2,oracle_checks=4,matched_comparisons=1)


def force_region(reference,lower,upper,change):
    """Synthetic force constraint, not a receiver observation or learned bound."""
    if list(reference.parent.center)!=[0.]*27 or change!=.2:
        raise ValueError('fixed zero expansion and independently declared force constraint required')
    a=reference.acceleration;rows=[]
    for i in range(3):
        row=list(a.jacobian[i])+[0.]*24;row[39+i]=float(a.caps[6+i]);rows.append(row)
    region=dict(parameter_count=51,center=[0.]*51,lower=list(lower)+[-1.]*24,upper=list(upper)+[1.]*24,
        inequality_design=rows+[[-v for v in row] for row in rows],inequality_upper=[change]*6,
        binding=reference.binding,source_id=reference.parent.source_id,future_truth_used=False)
    return dict(training=dict(region=region),reference=reference.report(),lower=region['lower'],upper=region['upper'])


def check_witness(region,witness):
    if len(witness)!=51 or any(not F(a)<=F(v)<=F(b) for a,v,b in
            zip(region['lower'],witness,region['upper'],strict=True)):
        raise ValueError('complete probe lies outside declared source box')
    slacks=[sum((F(a)*F(v) for a,v in zip(row,witness,strict=True)),F(0))-F(b)
        for row,b in zip(region['inequality_design'],region['inequality_upper'],strict=True)]
    if not slacks or max(slacks)>0:raise ValueError('fixed probe lies outside declared force region')
    return dict(feasible=True,maximum_exact_slack=str(max(slacks)))


class Runtime:
    def __init__(self,context,spec):
        from lll.ilvis0_coupled_map_controls import Allowance
        from lll.ilvis0_control_shards import _check_continue
        self.context=context;self.spec=spec;self.events=0;self.calls=0;self.bounds=0
        if spec['limits']!=limits(spec['scope']):raise ValueError('fixed auxiliary allowance required')
        def persist(event):
            _check_continue(context.root,context.manifest);self.events+=1
            context.save(f'reservation-{self.events:03d}.json',event)
        self.budget=Allowance(spec['limits'],persist)

    def reserve(self,**values):self.budget.reserve(values)

    def save(self,name,value):
        from lll.ilvis0_sharded_native import plain
        self.context.save(name,plain(value))

    def before_bound(self,n):
        if n!=800 or self.bounds>=2:raise ValueError('two prefix bounds per identity required')
        self.reserve(source_setups=1,source_steps=n,source_body_bounds=n,source_derivative_setups=1,
            source_derivative_steps=n,source_point_setups=1,source_point_steps=n,source_direct_steps=n)
        self.context.charge(bound_calls=1,bound_steps=9*n);self.bounds+=1

    def native(self,kernel,config,theta,dv,dt,time_s,parameters):
        import ctypes
        import numpy as np
        from lll.ilvis0_packet_boundary_flags import validate
        if len(dt)!=800 or self.calls>=4:raise ValueError('four fixed prefix queries per identity required')
        self.context.charge(native_calls=1,packet_visits=len(dt));self.calls+=1
        out=np.empty((1,3));jac=np.empty((3,27));flag=ctypes.c_int()
        code=kernel(len(dt),theta,dv,dt,1,np.array([time_s]),config['initial_c'],config['initial_v'],
            config['initial_r'],config['limits'],np.ascontiguousarray(parameters,float),config['model'],
            int(config['profile']),config['gravity'],config['radius'],out,jac,ctypes.byref(flag))
        record=dict(time_s=time_s,point=parameters,status=int(code),warning=flag.value)
        if not code:record.update(prediction=out[0],jacobian=jac)
        self.save(f'native-{self.calls:02d}.json',record)
        checked=validate(status=int(code),counter=flag.value,dt=dt,time_s=time_s,
            clock_offset_s=float(config['limits'][25])*float(parameters[25]))
        self.save(f'native-{self.calls:02d}-boundary.json',checked)
        return out[0],jac


def evaluate(task,context):
    import time
    import numpy as np
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_batched_transport import configure_backend
    from lll.ilvis0_source_stream import load_stream
    from lll.ilvis0_source_derivative_intervals import load_kernel
    from lll.ilvis0_source_point_derivatives import load_kernel as load_point
    from lll.ilvis0_directional_acceleration import DirectionalAcceleration
    from lll.ilvis0_acceleration_projection import project
    from lll.ilvis0_conditioned_acceleration import ConditionedAcceleration
    from lll.ilvis0_training_remainder_audit import scaled_design
    from lll import ilvis0_direct_native as original,ilvis0_remainder_native as candidate
    from lll import ilvis0_direct_interface as old_interface,ilvis0_remainder_interface as interface
    spec=task['payload'];settings=read(context.input_path());validate_recipe(settings)
    case=read(context.input_path(spec['case_key']));config=case['configuration'];n=len(case['dt'])
    if (n!=800 or config['model']!=spec['model'] or config['profile']!=spec['profile']
            or config['limits'][25]!=1. or case['center']!=settings['center']):
        raise ValueError('bitwise prefix, broad clock and declared model required')
    config={k:np.ascontiguousarray(v,float) if k in ('initial_c','initial_v','initial_r','limits') else v
        for k,v in config.items()}
    theta,dv,dt=(np.ascontiguousarray(case[k],float) for k in ('theta','dv','dt'))
    lo=np.array(settings['lower']);hi=np.array(settings['upper']);center=np.array(settings['center'])
    runtime=Runtime(context,spec);runtime.reserve(reference_setups=1)
    reference=original.make_reference(config,theta,dv,dt,lower=lo,upper=hi,center=center)
    runtime.save('reference.json',reference.report());region=None
    if spec['scope']=='physical':
        runtime.reserve(physical_proofs=1);proof=DirectionalAcceleration(reference,lo,hi)
    else:
        runtime.reserve(conditional_proofs=1)
        bundle=force_region(reference,lo.tolist(),hi.tolist(),settings['force_change_mps2'])
        runtime.save('conditioning-input.json',bundle)
        certificate=project(**bundle,reserve=lambda p,s:runtime.reserve(lp_proposals=p,exact_supports=s))
        runtime.save('conditioning-certificate.json',certificate)
        proof=ConditionedAcceleration(bundle,certificate,reserve=lambda s:runtime.reserve(exact_supports=s))
        region=bundle['training']['region']
    runtime.save('proof.json',proof.report())
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels'
    directory.mkdir(parents=True,exist_ok=True);sources=context.root/'source-freeze/analysis/lll'
    arithmetic=configure_backend(directory,source_directory=sources)
    source,sm=load_stream(directory,source_directory=sources)
    derivative,dm=load_kernel(directory,source_directory=sources)
    point,pm=load_point(directory,source_directory=sources);kernel,nm=load_tangent(directory)
    compilation=dict(arithmetic=arithmetic,source=sm,derivative=dm,point=pm,native=nm)
    expected=context.manifest['sources']
    for kind,metadata in compilation.items():
        if metadata['compiler']!=spec['compiler']:raise ValueError('frozen compiler changed')
        if kind=='native':
            if metadata['source_sha256']!=expected['analysis/lll/ilvis0_tangent.cpp']:
                raise ValueError('native source changed')
        elif any(digest!=expected['analysis/lll/'+name] for name,digest in metadata['sources'].items()):
            raise ValueError('bound source changed')
    runtime.save('compilation.json',compilation)
    nominal,jac=runtime.native(kernel,config,theta,dv,dt,settings['time_s'],center)
    scale=spec['coordinate_scale'];raw=[];bridged=[]
    # Save both complete bounds before evaluating any off-center outcome.
    for module,mapper,label in ((original,old_interface,'original'),(candidate,interface,'candidate')):
        runtime.before_bound(n);started=time.monotonic()
        if label=='candidate':runtime.reserve(algebra_certificates=2)
        value=module.enclose(config,theta,dv,dt,time=settings['time_s'],lower=lo,upper=hi,
            reference=reference,conditioning=proof,source_kernel=source,derivative_kernel=derivative,
            point_kernel=point,maximum_seconds=settings['maximum_bound_seconds'])
        raw.append(value.report())
        bridge=mapper.bridge(value,reference,proof,nominal,scale);bridged.append(bridge.report())
        runtime.save(label+'-bound.json',dict(raw=raw[-1],bridged=bridged[-1],elapsed_s=time.monotonic()-started))
        if any(value.metadata[k]>n for k in ('source_reference_steps','source_derivative_steps',
                                            'source_direct_steps','rounded_source_prefixes')):
            raise ValueError('source visits exceed reserved complete prefix')
    runtime.reserve(matched_comparisons=1)
    match=interface.matched_bounds(*raw);bridge_match=interface.matched_bounds(*bridged)
    remainder=raw[1]['conditional_acceleration_remainder']
    reduction=F(remainder['remainder_upper'])<F(remainder['original_remainder'])
    runtime.save('comparison.json',dict(raw=match,bridged=bridge_match,force_remainder_reduced=reduction))
    matrix=scaled_design(jac,bridged[1],scale);probes=[]
    for ordinal,coordinates in enumerate(settings['probes'][spec['scope']]):
        runtime.reserve(oracle_checks=1);parameters=np.array(coordinates)
        actual=nominal if ordinal==0 else runtime.native(kernel,config,theta,dv,dt,settings['time_s'],parameters)[0]
        witness=list(parameters-center)+list(reference.normalized_values_at(parameters))
        feasible=check_witness(region,witness) if region is not None else dict(feasible=True,scope='physical box')
        errors=[(F(float(a))-F(float(b)))*F(float(s))-sum((F(c)*F(x) for c,x in zip(row,witness,strict=True)),F(0))
            for a,b,s,row in zip(actual,nominal,scale,matrix,strict=True)]
        radii=[F(v)*F(s) for v,s in zip(bridged[1]['unshared_remainder'],scale,strict=True)]
        contained=all(abs(error)<=radius+F(settings['oracle_arithmetic_allowance_m'])
            for error,radius in zip(errors,radii,strict=True))
        probes.append(dict(point=coordinates,**feasible,contained=contained,residual_m=list(map(str,errors)),
            radius_m=list(map(str,radii))))
        runtime.save(f'probe-{ordinal:02d}.json',probes[-1])
    if runtime.calls!=4 or runtime.bounds!=2 or runtime.budget.counts!=limits(spec['scope']):
        raise ValueError('complete finite native and auxiliary accounting required')
    runtime.save('accounting.json',runtime.budget.counts)
    passed=match['passed'] and bridge_match['passed'] and reduction and all(p['contained'] and p['feasible'] for p in probes)
    return plain(dict(identity=task['identity'],passed=passed,model=spec['model'],profile=spec['profile'],scope=spec['scope'],
        native_evaluations=4,bound_evaluations=2,work=runtime.budget.counts,physical_parameter_count=27,parameter_count=51,
        probe_count=4,all_probes_contained=all(p['contained'] for p in probes),maps_preserved=match['maps_preserved'],
        remainders_nonwidening=match['remainders_nonwidening'] and bridge_match['remainders_nonwidening'],
        original_force_remainder=remainder['original_remainder'],conditional_force_remainder=remainder['remainder_upper'],
        force_remainder_reduced=reduction,original_unshared_m=[v*s for v,s in zip(bridged[0]['unshared_remainder'],scale)],
        candidate_unshared_m=[v*s for v,s in zip(bridged[1]['unshared_remainder'],scale)],
        oracle_arithmetic_allowance_m=settings['oracle_arithmetic_allowance_m'],original_reads=0,optimizer_starts=0,
        recording_length_usefulness_qualified=False,observational_coverage_qualified=False,
        whole_program_roundoff_qualified=False,scientific_decision='abstain'))
