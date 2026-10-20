# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated-only equivalence, known-pose and memory-scaling controls."""
import ctypes
import time
import tracemalloc

import numpy as np
from scipy.spatial.transform import Rotation

from .ilvis0_streaming import Stream
from .ilvis0_shape import load_tangent
from .ilvis0_exploratory import load_kernel

SCALE=np.array([6371000.,6371000.,1.])


def tasks():
    result=[]
    for model in range(3):
        for profile in (False,True):
            for tangent in (False,True):
                for offset in (-.3,.4):
                    result.append(dict(kind='equivalence',model=model,profile=profile,tangent=tangent,
                        offset=offset,packets=513))
    for model in range(3):
        for removal in (0.,.5,1.):
            for tangent in (False,True):
                result.append(dict(kind='pose',model=model,profile=True,tangent=tangent,removal=removal,packets=3000))
    for n in (30000,120000,480000):
        for tangent in (False,True):
            result.append(dict(kind='scaling',model=0,profile=True,tangent=tangent,removal=.5,packets=n))
    return [dict(t,identity=f"{t['kind']}-{i:02d}") for i,t in enumerate(result)]


def _config(task):
    c=np.array([-.9,3.2,11000.]);v=np.array([180.,55.,-.1]);r=np.eye(3)
    limits=np.r_[[.01]*3,[2.]*3,[10.]*3,[2e-6]*3,[.01]*3,[.001]*6,[2.]*3,.01,.001,1.]
    point=np.linspace(-.4,.4,27);point[25]=task.get('offset',0.)
    if task['kind']!='equivalence':
        v[:]=0.;point[:]=0.;point[26]=2*task['removal']-1.
    return dict(initial_c=c,initial_v=v,initial_r=r,limits=limits,point=point,
        model=task['model'],profile=task['profile'],tangent=task['tangent'],
        gravity=9.81,radius=6371000.,input_id='generated:'+task['identity'])


def packets(task,begin,count):
    k=np.arange(begin,begin+count,dtype=float)
    if task['kind']=='equivalence':
        dt=.0048+.0001*(k%4)
        theta=np.column_stack((2e-5*np.cos(k),-3e-5+1e-5*np.sin(k),1e-5*np.cos(.3*k)))
        dv=np.column_stack((.001*np.sin(k),.001*np.cos(k),-9.81*dt))
    else:
        dt=np.full(count,1/300.)
        phi=-.9;standard=7.2921150e-5*np.array([np.cos(phi),0.,-np.sin(phi)])
        theta=np.tile(standard*((1. if task['model']==0 else 0.)-task['removal'])/300.,(count,1))
        dv=np.tile([0.,0.,-9.81/300.],(count,1))
    return theta,dv,dt


def _whole(directory,task,config,theta,dv,dt,times,charge):
    out=np.empty((len(times),3));n=len(dt)
    if task['tangent']:
        kernel,kernel_identity=load_tangent(directory);jac=np.empty((out.size,27));boundary=ctypes.c_int()
        charge(native_calls=1,packet_visits=n)
        code=kernel(n,theta,dv,dt,len(times),times,config['initial_c'],config['initial_v'],config['initial_r'],
            config['limits'],config['point'],task['model'],int(task['profile']),9.81,6371000.,out,jac,ctypes.byref(boundary))
        jac=jac.reshape(len(times),3,27)
    else:
        p=config['point']*config['limits'];c=config['initial_c'];model=task['model']
        theta=np.ascontiguousarray((theta-p[9:12]*dt[:,None])/(1+p[15:18]))
        dv=np.ascontiguousarray((dv-p[12:15]*dt[:,None])/(1+p[18:21]))
        if model==2:mn=6371000.;me=mn*(np.pi/2-c[0])
        else:
            denominator=1-6.69437999014e-3*np.sin(c[0])**2
            mn=6378137.*(1-6.69437999014e-3)/denominator**1.5+c[2]
            me=(6378137./np.sqrt(denominator)+c[2])*np.cos(c[0])
        seed=np.array(c+[p[6]/mn,p[7]/me,-p[8]])
        rotation=np.ascontiguousarray(config['initial_r']@Rotation.from_rotvec(p[:3]).as_matrix())
        kernel,kernel_identity=load_kernel(directory);charge(native_calls=1,packet_visits=n)
        code=kernel(n,theta,dv,dt,len(times),times+float(p[25]),seed,
            np.ascontiguousarray(config['initial_v']+p[3:6]),rotation,np.ascontiguousarray(p[21:24]),
            model,9.81+p[24],6371000.,(p[26]+1)/2 if task['profile'] else 0.,out)
        jac=None;boundary=None
    if code:raise ValueError('unchanged whole-history reference returned '+str(code))
    return out,jac,boundary.value if boundary is not None else None,kernel_identity


def _stream(directory,task,config,charge,*,block_size,times=None,restart=False):
    stream=Stream(directory,**config);outputs=[];jacobians=[];bounds=0;query=0
    started=time.monotonic();initial_state_bytes=stream.state_bytes
    for begin in range(0,task['packets'],block_size):
        count=min(block_size,task['packets']-begin);theta,dv,dt=packets(task,begin,count)
        clock=stream.elapsed_s;end=clock
        for duration in dt:end+=float(duration)
        if times is None:
            # One observation per block; constant output size for memory benchmark.
            requested=np.array([end-stream.time_offset])
        else:
            stop=query
            while stop<len(times) and times[stop]+stream.time_offset<=end:stop+=1
            if begin+count<task['packets'] and stop>query and times[stop-1]+stream.time_offset==end:stop-=1
            requested=times[query:stop];query=stop
        charge(native_calls=1,packet_visits=count)
        result=stream.push(theta,dv,dt,requested,packet_offset=begin,elapsed_s=clock)
        bounds+=result['boundaries']
        if times is not None:
            outputs.append(result['positions']);jacobians.append(result['jacobian'])
        if restart and begin==0:
            stream=Stream.restore(directory,stream.checkpoint(),input_id=config['input_id'])
    if times is not None and query!=len(times):raise ValueError('unconsumed generated query')
    return dict(positions=np.concatenate(outputs) if times is not None else result['positions'],
        jacobian=np.concatenate(jacobians) if times is not None and task['tangent'] else None,
        boundaries=bounds,packet_count=stream.packet_count,elapsed_s=stream.elapsed_s,
        state_bytes=stream.state_bytes,state_size_constant=initial_state_bytes==stream.state_bytes,
        runtime_s=time.monotonic()-started)


def evaluate(task,directory,charge):
    config=_config(task);result=dict(identity=task['identity'],kind=task['kind'],input=task,
        original_reads=0,optimizer_starts=0,scientific_decision='abstain')
    result['streaming_kernel']=Stream(directory,**config).identity
    if task['kind']=='scaling':
        # Compile before tracing; no full recording arrays are constructed.
        Stream(directory,**config)
        tracemalloc.start()
        try:
            actual=_stream(directory,task,config,charge,block_size=1024)
            _,peak=tracemalloc.get_traced_memory()
        finally:tracemalloc.stop()
        error=float(np.max(abs((actual['positions']-config['initial_c'])*SCALE)))
        result.update(maximum_pose_error_m=error,peak_traced_bytes=peak,
            state_bytes=actual['state_bytes'],state_size_constant=actual['state_size_constant'],
            runtime_s=actual['runtime_s'],packet_count=actual['packet_count'],elapsed_s=actual['elapsed_s'],
            maximum_block_packets=1024,passed=error<=1e-6 and peak<8*1024**2 and actual['state_size_constant'])
    else:
        theta,dv,dt=packets(task,0,task['packets']);ends=np.cumsum(dt)
        shift=config['limits'][25]*config['point'][25]
        times=np.sort(np.unique(np.r_[0.,ends[30],ends[61],ends[-1],(ends[1::13]+ends[:-1:13])/2]))-shift
        expected,ej,eb,reference_identity=_whole(directory,task,config,theta,dv,dt,times,charge)
        result['reference_kernel']=reference_identity
        a=_stream(directory,task,config,charge,block_size=task['packets'],times=times)
        b=_stream(directory,task,config,charge,block_size=31 if task['kind']=='equivalence' else 257,times=times,restart=True)
        error=float(np.max(abs((b['positions']-expected)*SCALE)))
        derivative_error=float(np.max(abs((b['jacobian']-ej)*SCALE[None,:,None]))) if ej is not None else None
        identical=np.array_equal(a['positions'],b['positions']) and (ej is None or np.array_equal(a['jacobian'],b['jacobian']))
        pose_error=float(np.max(abs((expected-config['initial_c'])*SCALE))) if task['kind']=='pose' else None
        passed=error<=1e-6 and identical and (ej is None or (derivative_error<=1e-7 and b['boundaries']==eb))
        if pose_error is not None:passed=passed and pose_error<=1e-6
        result.update(passed=bool(passed),maximum_position_difference_m=error,maximum_derivative_difference_m=derivative_error,
            chunk_bit_identical=bool(identical),maximum_pose_error_m=pose_error,
            boundaries=b['boundaries'],reference_boundaries=eb,state_bytes=b['state_bytes'],
            runtime_s=a['runtime_s']+b['runtime_s'],packet_count=b['packet_count'])
    return result
