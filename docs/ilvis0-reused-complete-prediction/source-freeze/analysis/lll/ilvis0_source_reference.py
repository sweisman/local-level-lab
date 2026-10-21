# SPDX-License-Identifier: AGPL-3.0-or-later
"""Source-only native reference, independent rotation Jacobian and affine bound.

No geographic integration, recorded-aircraft fitting or coverage claim. The
native implementation's branch at packet endpoints is deliberately retained.
"""
import ctypes
from fractions import Fraction as F
import hashlib
import math
from pathlib import Path
import subprocess

import numpy as np
from scipy.spatial.transform import Rotation


def load_source(directory):
    source=Path(__file__).with_suffix('.cpp');parent=source.with_name('ilvis0_tangent.cpp')
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (source,parent)}
    digest=hashlib.sha256(''.join(hashes.values()).encode()).hexdigest()
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    binary=directory/('source-reference-'+digest+'.so');flags=['-O2','-std=c++17','-fPIC','-shared']
    if not binary.exists():
        temporary=binary.with_suffix('.partial.so')
        subprocess.run(['c++',*flags,str(source),'-o',str(temporary)],check=True,capture_output=True)
        temporary.replace(binary)
    function=ctypes.CDLL(str(binary)).ilvis0_body_reference
    array=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
    function.argtypes=[ctypes.c_size_t,array,array,array,array,array,array,ctypes.c_double,
        array,array,ctypes.POINTER(ctypes.c_size_t),array]
    function.restype=ctypes.c_int
    return function,dict(sources=hashes,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0],flags=flags)


def _inputs(case,point,time_s):
    config=case['configuration'];dt=np.ascontiguousarray(case['dt'],dtype=float)
    theta=np.ascontiguousarray(case['theta'],dtype=float);dv=np.ascontiguousarray(case['dv'],dtype=float)
    initial=np.ascontiguousarray(config['initial_r'],dtype=float)
    limits=np.ascontiguousarray(config['limits'],dtype=float);z=np.ascontiguousarray(point,dtype=float)
    if (dt.ndim!=1 or not len(dt) or theta.shape!=(len(dt),3) or dv.shape!=theta.shape
            or initial.shape!=(3,3) or limits.shape!=(27,) or z.shape!=(27,)
            or not all(np.all(np.isfinite(x)) for x in (dt,theta,dv,initial,limits,z))
            or not math.isfinite(time_s) or np.any(dt<=0) or np.any(limits<0)):
        raise ValueError('finite supported packet arrays and all 27 columns required')
    p=limits*z;query=time_s+p[25]
    if query<0 or query>sum(dt):raise ValueError('query outside packet support')
    if np.any(1+p[15:21]<=0):raise ValueError('positive calibration denominator required')
    return dt,theta,dv,initial,limits,z


def _report(values,jacobian,index,query,start,end):
    if not np.all(np.isfinite(values)) or not np.all(np.isfinite(jacobian)):
        raise ValueError('finite source values and coefficients required')
    return dict(values=values,jacobian=jacobian,packet_index=int(index),packet_visits=int(index)+1,
        query_time_s=float(query),packet_start_s=float(start),packet_end_s=float(end),
        boundary_distance_s=float(min(abs(query-start),abs(end-query))),
        clock_branch='preceding packet at an exact endpoint',parameter_count=27)


def native_reference(kernel,case,point,time_s):
    dt,theta,dv,initial,limits,z=_inputs(case,point,time_s)
    values=np.empty((2,3));jac=np.empty((2,3,27));index=ctypes.c_size_t();timing=np.empty(3)
    code=kernel(len(dt),theta,dv,dt,initial,limits,z,float(time_s),values,jac,ctypes.byref(index),timing)
    if code:raise ValueError('unsupported native source reference: '+str(code))
    return _report(values,jac,index.value,*timing)


def _skew(v):
    x,y,z=v
    return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])


def _rotation_and_jacobian(angle,directions):
    """Quaternion values, analytic right SO(3) Jacobian; no native Dual code."""
    q=float(angle@angle);k=_skew(angle)
    if q<1e-8:
        a=.5-q/24+q*q/720-q*q*q/40320
        b=1/6-q/120+q*q/5040-q*q*q/362880
    else:
        t=math.sqrt(q);a=(1-math.cos(t))/q;b=(t-math.sin(t))/(q*t)
    rotation=Rotation.from_rotvec(angle).as_matrix();right=np.eye(3)-a*k+b*(k@k)
    jac=np.stack([rotation@_skew(right@direction) for direction in directions.T],axis=2)
    return rotation,jac


def analytic_reference(case,point,time_s):
    dt,theta,dv,initial,limits,z=_inputs(case,point,time_s);p=limits*z
    mount_directions=np.zeros((3,27));mount_directions[:,:3]=np.diag(limits[:3])
    rotation,jr=_rotation_and_jacobian(p[:3],mount_directions)
    r=initial@rotation;jr=np.einsum('ik,kja->ija',initial,jr)
    f=(dv[0]-p[12:15]*dt[0])/(1+p[18:21])/dt[0];jf=np.zeros((3,27))
    for i in range(3):
        jf[i,12+i]=-limits[12+i]/(1+p[18+i])
        jf[i,18+i]=-f[i]*limits[18+i]/(1+p[18+i])
    body=np.eye(3);jb=np.zeros((3,3,27));query=time_s+p[25];start=0.
    for index,period in enumerate(dt):
        end=start+period;partial=query<=end;fraction=(query-start)/period if partial else 1.
        corrected=(theta[index]-p[9:12]*period)/(1+p[15:18]);directions=np.zeros((3,27))
        for i in range(3):
            directions[i,9+i]=-period*limits[9+i]/(1+p[15+i])*fraction
            directions[i,15+i]=-corrected[i]*limits[15+i]/(1+p[15+i])*fraction
        if partial:directions[:,25]=corrected*limits[25]/period
        step,js=_rotation_and_jacobian(corrected*fraction,directions)
        jb=np.einsum('ika,kj->ija',jb,step)+np.einsum('ik,kja->ija',body,js)
        body=body@step
        if partial:break
        start=end
    departure=body-np.eye(3);local=departure@f
    a=r@f;b=r@local
    ja=np.einsum('ija,j->ia',jr,f)+r@jf
    jdeparture=np.einsum('ija,j->ia',jb,f)+departure@jf
    j_b=np.einsum('ija,j->ia',jr,local)+r@jdeparture
    return _report(np.array([a,b]),np.array([ja,j_b]),index,query,start,end)


def affine_radius(lower_value,upper_value,center,jacobian,lower,upper,reference):
    """Exact bound about ANY specified row, retaining center and column errors."""
    low,high,c=map(F,(lower_value,upper_value,center))
    if low>high:raise ValueError('ordered value interval required')
    radius=F(0)
    for j,lo,hi,z in zip(jacobian,lower,upper,reference,strict=True):
        j,lo,hi,z=map(F,(j,lo,hi,z))
        if lo>hi:raise ValueError('ordered parameter domain required')
        radius+=abs(j)*max(abs(lo-z),abs(hi-z))
    value=max(abs(low-c),abs(high-c));total=value+radius;upper_float=float(total)
    if F(upper_float)<total:upper_float=math.nextafter(upper_float,math.inf)
    return dict(value_radius=str(value),linear_radius=str(radius),affine_radius=str(total),upper_float=upper_float)


def evaluate(task,context):
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_coupled_map_controls import Allowance
    bundle=read(context.input_path());case=read(context.input_path(task['payload']['case_key']))
    future=bundle['future'];interval=bundle['range'];spec=task['payload'];n=len(case['dt'])
    limits=dict(setups=1,source_calls=1,source_packets=n,independent_calls=1,independent_packets=n,affine_bounds=1)
    if n!=1600 or limits!=spec['limits'] or not bundle['result']['passed']:
        raise ValueError('six fixed previously qualified source identities required')
    events=[]
    def persist(event):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:03d}.json',event);events.append(event)
    budget=Allowance(limits,persist);budget.reserve(dict(setups=1))
    # Adapter globals, including __file__, identify the sealed source snapshot.
    kernel,compiler=load_source(context.directory/'compiled')
    if compiler['compiler']!=spec['compiler']:raise ValueError('frozen compiler changed')
    center=np.asarray(spec['reference_center'])
    budget.reserve(dict(source_calls=1,source_packets=n))
    native=native_reference(kernel,case,center,future['time_s'])
    context.save('native-reference.json',plain(dict(native,compilation=compiler)))
    budget.reserve(dict(independent_calls=1,independent_packets=n))
    independent=analytic_reference(case,center,future['time_s'])
    context.save('independent-reference.json',plain(independent))
    values=np.abs(native['values']-independent['values']);coefficients=np.abs(native['jacobian']-independent['jacobian'])
    coefficient_ok=coefficients<=2e-10+2e-8*np.abs(independent['jacobian'])
    unused=[3,4,5,6,7,8,21,22,23,24,26]
    zero_ok=not np.any(native['jacobian'][:,:,unused]) and not np.any(independent['jacobian'][:,:,unused])
    branch_ok=all(native[k]==independent[k] for k in ('packet_index','packet_start_s','packet_end_s','query_time_s'))
    budget.reserve(dict(affine_bounds=1))
    bound=affine_radius(F(interval['combined_lower']),F(interval['combined_upper']),float(native['values'][1,2]),
        native['jacobian'][1,2],future['lower'][:27],future['upper'][:27],center)
    original=F(interval['departure']['remainder']);improved=F(bound['affine_radius'])<original
    context.save('affine-bound.json',dict(bound,original_remainder=str(original),improved=improved,
        original_center_difference=float(native['values'][1,2]-interval['departure']['center'][2]),
        row_source='unchanged native tangent primitives; source-only A/B exposure',
        mathematical_source_map=True,floating_execution_enclosure_verified=False))
    passed=bool(np.all(values<=1e-10) and np.all(coefficient_ok) and zero_ok and branch_ok)
    return dict(identity=task['identity'],passed=passed,model=bundle['result']['model'],profile=bundle['result']['profile'],
        value_max_difference=float(np.max(values)),coefficient_max_difference=float(np.max(coefficients)),
        coefficient_checks=int(coefficient_ok.size),value_checks=int(values.size),unused_columns=unused,
        unused_columns_zero=zero_ok,clock_branch_agrees=branch_ok,boundary_distance_s=native['boundary_distance_s'],
        actual_source_packets=native['packet_visits'],actual_independent_packets=independent['packet_visits'],
        original_remainder=float(original),affine_radius=bound['upper_float'],radius_ratio=float(F(bound['affine_radius'])/original),
        improved=improved,parameter_count=27,work=budget.counts,native_source_evaluations=1,
        full_native_trajectory_evaluations=0,optimizer_starts=0,original_reads=0,
        native_propagation_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')
