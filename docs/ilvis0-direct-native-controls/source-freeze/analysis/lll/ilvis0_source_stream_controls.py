# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent streamed analytic rows and finite generated-source controls."""


def analytic_prefixes(case,point,time_s):
    import numpy as np
    from lll.ilvis0_source_reference import _inputs,_rotation_and_jacobian
    dt,theta,dv,initial,limits,z=_inputs(case,point,time_s);p=limits*z
    directions=np.zeros((3,27));directions[:,:3]=np.diag(limits[:3])
    mount,jmount=_rotation_and_jacobian(p[:3],directions)
    r=initial@mount;jr=np.einsum('ik,kja->ija',initial,jmount)
    force=(dv[0]-p[12:15]*dt[0])/(1+p[18:21])/dt[0];jf=np.zeros((3,27))
    for i in range(3):
        jf[i,12+i]=-limits[12+i]/(1+p[18+i])
        jf[i,18+i]=-force[i]*limits[18+i]/(1+p[18+i])
    a=r@force;ja=np.einsum('ija,j->ia',jr,force)+r@jf
    body=np.eye(3);jbody=np.zeros((3,3,27));query=time_s+p[25];start=0.
    for index,period in enumerate(dt):
        end=start+period;slope=1/period if (start<query<=end or start==query==0) else 0.
        fraction=(query-start)/period if slope else float(query>end)
        corrected=(theta[index]-p[9:12]*period)/(1+p[15:18]);dtheta=np.zeros((3,27))
        for i in range(3):
            dtheta[i,9+i]=-period*limits[9+i]/(1+p[15+i])*fraction
            dtheta[i,15+i]=-corrected[i]*limits[15+i]/(1+p[15+i])*fraction
        dtheta[:,25]=corrected*limits[25]*slope
        values=[];jac=[]
        for part in (.5,1.):
            rotation,jrotation=_rotation_and_jacobian(corrected*fraction*part,dtheta*part)
            current=body@rotation
            jcurrent=np.einsum('ika,kj->ija',jbody,rotation)+np.einsum('ik,kja->ija',body,jrotation)
            departure=current-np.eye(3);local=departure@force
            b=r@local
            jb=np.einsum('ija,j->ia',jr,local)+r@(np.einsum('ija,j->ia',jcurrent,force)+departure@jf)
            values.append([a,b]);jac.append([ja,jb])
        body=current;jbody=jcurrent
        yield dict(values=np.asarray(values),jacobian=np.asarray(jac),packet_index=index,
            fraction=fraction,time_slope=slope,packet_start_s=start,packet_end_s=end,query_time_s=query)
        start=end


def evaluate(task,context):
    import hashlib
    from pathlib import Path
    import numpy as np
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_source_stream import SourceStream,load_stream
    bundle=read(context.input_path());case=read(context.input_path(task['payload']['case_key']))
    spec=task['payload'];n=len(case['dt']);future=bundle['future']
    limits=dict(setups=1,source_steps=n,independent_steps=n,scalar_comparisons=336*n)
    if n!=1600 or spec['limits']!=limits or not bundle['result']['passed']:
        raise ValueError('six fixed qualified 1600-packet sources required')
    events=[]
    def persist(event):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:03d}.json',event);events.append(event)
    budget=Allowance(limits,persist);budget.reserve(dict(setups=1))
    source_directory=context.root/'source-freeze'/'analysis'/'lll'
    kernel,compilation=load_stream(context.directory/'compiled',source_directory=source_directory)
    if compilation['compiler']!=spec['compiler']:raise ValueError('frozen source compiler changed')
    budget.reserve(dict(source_steps=n,independent_steps=n,scalar_comparisons=336*n))
    oracle=analytic_prefixes(case,np.array(spec['reference_center']),future['time_s'])
    maximum_value=maximum_coefficient=0.;worst_value=worst_coefficient=None;passed=True;checked=0
    native_digest=hashlib.sha256();independent_digest=hashlib.sha256();selected=[];unused=[3,4,5,6,7,8,21,22,23,24,26]
    with SourceStream(kernel,case,spec['reference_center'],future['time_s'],maximum_packets=n) as stream:
        for index in range(n):
            if index%32==0:_check_continue(context.root,context.manifest)
            actual=stream.append();expected=next(oracle)
            dvalue=np.abs(actual['values']-expected['values']);djac=np.abs(actual['jacobian']-expected['jacobian'])
            value_ok=dvalue<=1e-10;coefficient_ok=djac<=2e-10+2e-8*np.abs(expected['jacobian'])
            unused_ok=not np.any(actual['jacobian'][...,unused]) and not np.any(expected['jacobian'][...,unused])
            branch_ok=all(actual[k]==expected[k] for k in ('packet_index','fraction','time_slope','packet_start_s','packet_end_s','query_time_s'))
            passed=passed and bool(np.all(value_ok) and np.all(coefficient_ok) and unused_ok and branch_ok)
            if np.max(dvalue)>maximum_value:maximum_value=float(np.max(dvalue));worst_value=index
            if np.max(djac)>maximum_coefficient:maximum_coefficient=float(np.max(djac));worst_coefficient=index
            for digest,row in ((native_digest,actual),(independent_digest,expected)):
                digest.update(row['values'].tobytes());digest.update(row['jacobian'].tobytes())
            if index in (0,n-1) or actual['time_slope']:
                name=f'prefix-{index:04d}.json';context.save(name,plain(dict(native=actual,independent=expected)))
                selected.append(name)
            checked+=336
        visits=stream.visits;state_bytes=stream.state_bytes
    context.save('comparison.json',dict(maximum_value_difference=maximum_value,maximum_coefficient_difference=maximum_coefficient,
        worst_value_prefix=worst_value,worst_coefficient_prefix=worst_coefficient,native_rows_sha256=native_digest.hexdigest(),
        independent_rows_sha256=independent_digest.hexdigest(),selected_prefix_artifacts=selected,compilation=compilation))
    return dict(identity=task['identity'],passed=passed,model=bundle['result']['model'],profile=bundle['result']['profile'],
        source_steps=visits,independent_steps=n,scalar_comparisons=checked,state_bytes=state_bytes,parameter_count=27,
        maximum_value_difference=maximum_value,maximum_coefficient_difference=maximum_coefficient,work=budget.counts,
        full_native_trajectory_evaluations=0,optimizer_starts=0,original_reads=0,
        native_propagation_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')
