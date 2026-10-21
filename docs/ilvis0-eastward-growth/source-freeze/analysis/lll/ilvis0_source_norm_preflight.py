# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bound one body-prefix force departure; no full geographic prediction."""
from fractions import Fraction as F


def body_bound(case,reference,lower,upper,time_s,*,check_continue=lambda:None):
    import numpy as np
    from lll import ilvis0_local_step_bounds as local,ilvis0_relative_rotation as relative
    from lll import ilvis0_geographic_bounds as geo,ilvis0_history_bounds as history
    from lll.ilvis0_increment_remainders import calibrated_box
    r=reference.parent;limits=r.limits;z=r.center;lo=limits*np.minimum(lower,z);hi=limits*np.maximum(upper,z);p=limits*z
    delta=limits*np.maximum(z-np.minimum(lower,z),np.maximum(upper,z)-z)
    initial=local.Matrix(r._r_center,min(2.,float(np.linalg.norm(delta[:3]))),.5*float(np.linalg.norm(delta[:3]))**2,'rotation')
    def correct(raw,period,bias,gain):
        value=calibrated_box(raw,period,bias_center=p[bias],gain_center=p[gain],bias_lower=lo[bias],
            bias_upper=hi[bias],gain_lower=lo[gain],gain_upper=hi[gain])
        return local.Value(value['center'],value['change_radius'],value['remainder_radius'])
    force=local.scale(correct(case['dv'][0],case['dt'][0],slice(12,15),slice(18,21)),1/case['dt'][0])
    query=geo.Scalar.interval(time_s+p[25],time_s+lo[25],time_s+hi[25])
    if query.lower<0 or query.upper>sum(case['dt']):raise ValueError('body query outside packet support')
    right=relative.Delta(np.zeros((3,3)));elapsed=0.;visits=0
    for index,(theta,dt) in enumerate(zip(case['theta'],case['dt'],strict=True)):
        if elapsed>query.upper:break
        if index%64==0:check_continue()
        fraction=history.packet_fraction(query,start=elapsed,duration=dt)[0]
        angle=local.scalar_product(fraction.value,correct(theta,dt,slice(9,12),slice(15,18)))
        right=relative.advance_right(right,local.exponential(angle));visits+=1;elapsed+=dt
    result=relative.apply(relative.multiply(initial,right),force)
    return result,visits


def point_oracle(case,point,time_s):
    import numpy as np
    from scipy.spatial.transform import Rotation
    config=case['configuration'];p=np.asarray(config['limits'])*np.asarray(point)
    installation=np.asarray(config['initial_r'])@Rotation.from_rotvec(p[:3]).as_matrix()
    dt0=case['dt'][0];force=(np.asarray(case['dv'][0])-p[12:15]*dt0)/(1+p[18:21])/dt0
    body=np.eye(3);elapsed=0.;query=time_s+p[25];visits=0
    for theta,dt in zip(case['theta'],case['dt'],strict=True):
        if elapsed>query:break
        fraction=max(0.,min(1.,(query-elapsed)/dt))
        angle=(np.asarray(theta)-p[9:12]*dt)/(1+p[15:18])*fraction
        body=body@Rotation.from_rotvec(angle).as_matrix();elapsed+=dt;visits+=1
    return installation@force,installation@(body-np.eye(3))@force,visits


def evaluate(task,context):
    import numpy as np
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_orientation_cover import sector
    from lll.ilvis0_transform_native import make_reference
    from lll.ilvis0_directional_force import calibrated_force
    from lll.ilvis0_exact_scale import sqrt_upper
    from lll.ilvis0_rotation_interval import vertical_interval
    bundle=read(context.input_path());spec=task['payload'];case=read(context.input_path(spec['case_key']))
    n=len(case['dt']);old=bundle['result'];future=bundle['future'];saved= future['bound'];limits=dict(setups=1,prefixes=1,prefix_packets=n,closures=1,point_oracles=1,oracle_packets=n,checks=14)
    if (n!=1600 or spec['limits']!=limits or old['task']['sector']!=4 or not old['passed']
            or not old['truth_in_sector'] or not old['known_truth_retained']):
        raise ValueError('fixed source identity and known qualified sector required')
    events=[]
    def persist(event):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:03d}.json',event);events.append(event)
    budget=Allowance(limits,persist);budget.reserve(dict(setups=1));box=sector(4)
    reference=make_reference(case['configuration'],case['theta'],case['dv'],case['dt'],**{k:box[k] for k in ('lower','upper','center')})
    if reference.report()!=future['reference']:raise ValueError('original complete source/reference changed')
    lo=future['lower'][:27];hi=future['upper'][:27];conditioning=saved['conditioning'];r=reference.parent
    if (conditioning['reference_binding']!=reference.binding or conditioning['source_id']!=r.source_id
            or any(not a<=b<=c<=d for a,b,c,d in zip(saved['lower'],lo,hi,saved['upper'],strict=True))):
        raise ValueError('saved training range must cover the current source domain')
    physical_lo=[F(float(v))*F(a) for v,a in zip(r.limits,lo)];physical_hi=[F(float(v))*F(a) for v,a in zip(r.limits,hi)]
    a=reference.acceleration;left=[F(float(c))-F(d) for c,d in zip(a.center,conditioning['component_changes'])]
    right=[F(float(c))+F(d) for c,d in zip(a.center,conditioning['component_changes'])]
    left[2]-=F(a.gravity)+physical_hi[24];right[2]-=F(a.gravity)+physical_lo[24]
    budget.reserve(dict(prefixes=1,prefix_packets=n))
    departure,visits=body_bound(case,reference,np.asarray(lo),np.asarray(hi),future['time_s'],
        check_continue=lambda:_check_continue(context.root,context.manifest))
    blo=[F(float(v))-F(departure.change) for v in departure.center];bhi=[F(float(v))+F(departure.change) for v in departure.center]
    # Account for the literal installation matrix's metric defect, without repair.
    matrix=[[F(float(v)) for v in row] for row in r.initial_r]
    gram=[[sum((matrix[k][i]*matrix[k][j] for k in range(3)),F(0))-int(i==j) for j in range(3)] for i in range(3)]
    defect=F(sqrt_upper(sum((v*v for row in gram for v in row),F(0))))
    flo,fhi=calibrated_force(case['dv'][0],case['dt'][0],list(map(list,zip(physical_lo[12:15],physical_hi[12:15]))),list(map(list,zip(physical_lo[18:21],physical_hi[18:21]))))
    norm_error=2*defect*sum((max(abs(x),abs(y))**2 for x,y in zip(flo,fhi)),F(0))
    budget.reserve(dict(closures=1));interval=vertical_interval(left,right,blo,bhi,norm_identity=True,norm_error=norm_error)
    context.save('range.json',dict(interval,a_lower=list(map(str,left)),a_upper=list(map(str,right)),
        departure=departure.report(),reference_binding=reference.binding,source_id=r.source_id,
        installation_metric_defect=str(defect),reserved_prefix_packets=n,actual_prefix_packets=visits))
    # Only after all intervals are fixed may the known calibration be inspected.
    budget.reserve(dict(point_oracles=1,oracle_packets=n,checks=14));point=case['truth']
    if any(not x<=v<=y for x,v,y in zip(lo,point,hi,strict=True)):raise ValueError('known source point escaped its inherited domain')
    actual_a,actual_b,oracle_visits=point_oracle(case,point,future['time_s']);margin=F(1,10000000000)
    tests=[x-margin<=F(float(v))<=y+margin for x,v,y in zip(left,actual_a,right)]
    tests+=[x-margin<=F(float(v))<=y+margin for x,v,y in zip(blo,actual_b,bhi)]
    tests+=[F(interval['combined_lower'])-margin<=F(float(actual_b[2]))<=F(interval['combined_upper'])+margin]
    context.save('point.json',plain(dict(point=point,a=actual_a,b=actual_b,comparisons=tests,actual_packet_visits=oracle_visits,
        point_comparison_margin_mps2=float(margin),calibration_read_after_intervals=True)))
    width=F(interval['combined_upper'])-F(interval['combined_lower']);original=bhi[2]-blo[2]
    return dict(identity=task['identity'],passed=all(tests),model=old['task']['model'],profile=old['task']['profile'],
        baseline_vertical_width=float(original),raw_vertical_width=float(F(interval['raw_upper'])-F(interval['raw_lower'])),
        combined_vertical_width=float(width),width_ratio=float(width/original) if original else None,
        actual_prefix_packets=visits,actual_oracle_packets=oracle_visits,work=budget.counts,parameter_count=27,
        taylor_remainder_qualified=False,native_propagation_qualified=False,original_reads=0,native_evaluations=0,
        optimizer_starts=0,observational_coverage_qualified=False,scientific_decision='abstain')
