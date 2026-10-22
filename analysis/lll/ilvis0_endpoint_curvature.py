# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved endpoint-derivative diagnostic; no certified curvature enclosure."""
from fractions import Fraction as F

GROUPS=dict(attitude=(0,3),initial_velocity=(3,6),initial_position=(6,9),
    gyro_offset=(9,12),accel_offset=(12,15),gyro_gain=(15,18),accel_gain=(18,21),
    lever_arm=(21,24),gravity=(24,25),clock=(25,26),removal=(26,27))


def compare(reference_jacobian,probe_jacobian,point,actual):
    import numpy as np
    j0=np.asarray(reference_jacobian,float);jp=np.asarray(probe_jacobian,float);p=np.asarray(point,float)
    try:
        truth=[[F(v) if isinstance(v,str) else F(float(v)) for v in row] for row in actual]
        values=np.array(truth,float)
    except (ValueError,TypeError,OverflowError):raise ValueError('finite saved coordinate changes required') from None
    if (j0.ndim!=3 or j0.shape[1:]!=(3,27) or jp.shape!=j0.shape or p.shape!=(27,)
            or values.shape!=j0.shape[:2] or len(j0)<2
            or any(not np.all(np.isfinite(v)) for v in (j0,jp,p,values))):
        raise ValueError('complete finite reference/probe derivatives and all 27 columns required')
    exact=list(map(F,map(float,p)));linear=[];endpoint=[];groups={name:[] for name in GROUPS}
    for e,(left,right) in enumerate(zip(j0,jp,strict=True)):
        le=[];ee=[];group_epoch={name:[] for name in GROUPS}
        for axis,(a,b) in enumerate(zip(left,right,strict=True)):
            a=list(map(F,map(float,a)));b=list(map(F,map(float,b)))
            base=sum((v*x for v,x in zip(a,exact,strict=True)),F(0))
            terms=[(v-u)*x/2 for u,v,x in zip(a,b,exact,strict=True)]
            le.append(float(truth[e][axis]-base));ee.append(float(truth[e][axis]-base-sum(terms,F(0))))
            for name,(lo,hi) in GROUPS.items():group_epoch[name].append(float(sum(terms[lo:hi],F(0))))
        linear.append(le);endpoint.append(ee)
        for name in GROUPS:groups[name].append(group_epoch[name])
    linear=np.array(linear);endpoint=np.array(endpoint)
    return dict(physical_parameter_count=27,epochs=len(j0),
        maximum_linear_error_m=float(np.max(abs(linear))),maximum_endpoint_error_m=float(np.max(abs(endpoint))),
        rms_linear_error_m=float(np.sqrt(np.mean(linear**2))),rms_endpoint_error_m=float(np.sqrt(np.mean(endpoint**2))),
        linear_error_m=linear.tolist(),endpoint_error_m=endpoint.tolist(),
        future_group_curvature_m={name:value[-1] for name,value in groups.items()},
        group_rms_m={name:float(np.sqrt(np.mean(np.array(value)**2))) for name,value in groups.items()},
        numerical_coverage_qualified=False,coefficients_fitted=False)


def evaluate(task,context):
    import numpy as np
    from lll import ilvis0_control_shards as runner
    from lll.ilvis0_coupled_map_controls import Allowance
    bundle=runner._load(context.input_path());project=context.root.parents[1];events=0
    def read(record):
        path=runner.path_within(project,record['path'])
        if runner._sha(path)!=record['sha256']:raise ValueError('sealed referenced input changed')
        return runner._load(path)
    baseline=read(bundle['baseline']);nominal=np.asarray(baseline['prediction'],float)
    scale=np.array(bundle['coordinate_scale']);j0=np.array(baseline['jacobian'])*scale[None,:,None]
    if nominal.shape!=(293,3) or j0.shape!=(293,3,27):raise ValueError('complete saved reference required')
    maximum=dict(comparisons=6,source_crosschecks=6,coordinate_comparisons=5274,column_products=284796)
    def persist(record):
        nonlocal events
        runner._check_continue(context.root,context.manifest);events+=1
        context.save(f'reservation-{events:02d}.json',record)
    budget=Allowance(maximum,persist);indices=[0,8,28,178,288,292];rows=[]
    for ordinal,item in enumerate(bundle['probes']):
        budget.reserve(dict(comparisons=1,source_crosschecks=1,coordinate_comparisons=879,column_products=47466))
        native=read(item['native']);shared=read(item['shared']);point=native['point']
        if native['status']!=0 or point!=shared['point'] or len(native['prediction'])!=293:
            raise ValueError('same fixed successful native probe required')
        delta=[[(F(a)-F(b))*F(float(u)) for a,b,u in zip(actual,base,scale,strict=True)]
            for actual,base in zip(native['prediction'],nominal,strict=True)]
        result=compare(j0,np.array(native['jacobian'])*scale[None,:,None],point,
            [list(map(str,row)) for row in delta])
        common=np.array(result['linear_error_m'])[indices];old=np.array(shared['linear_error_m'])
        if old.shape!=(6,3) or np.max(abs(common-old))>1e-6:
            raise ValueError('source audit/reference expression differs beyond frozen 1 micrometre crosscheck')
        ep=np.array(result['endpoint_error_m'])[indices];source=np.array(shared['shared_error_m'])
        record=dict(identity=item['identity'],**result,
            common_rms_linear_m=float(np.sqrt(np.mean(common**2))),
            common_rms_shared_m=float(np.sqrt(np.mean(source**2))),common_rms_endpoint_m=float(np.sqrt(np.mean(ep**2))))
        context.save(f'probe-{ordinal:02d}.json',record);rows.append(record)
    if len(rows)!=6 or budget.counts!=maximum:raise ValueError('six complete endpoint comparisons required')
    context.save('accounting.json',budget.counts)
    return dict(identity=task['identity'],passed=True,profile=task['payload']['profile'],physical_parameter_count=27,
        probes=6,epochs_per_probe=293,shared_comparison_epochs=6,work=budget.counts,
        common_rms_linear_m=float(np.sqrt(np.mean([r['common_rms_linear_m']**2 for r in rows]))),
        common_rms_shared_m=float(np.sqrt(np.mean([r['common_rms_shared_m']**2 for r in rows]))),
        common_rms_endpoint_m=float(np.sqrt(np.mean([r['common_rms_endpoint_m']**2 for r in rows]))),
        maximum_endpoint_error_m=max(r['maximum_endpoint_error_m'] for r in rows),
        endpoint_improves_shared=sum(r['common_rms_endpoint_m']<r['common_rms_shared_m'] for r in rows),
        group_rms_m={name:float(np.sqrt(np.mean([r['group_rms_m'][name]**2 for r in rows]))) for name in GROUPS},
        native_evaluations=0,optimizer_starts=0,original_reads=0,numerical_coverage_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
