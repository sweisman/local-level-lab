# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate, unchanged-tolerance test of inherited arithmetic and streaming."""
import ctypes
import time
import tracemalloc

import numpy as np

from .ilvis0_streaming import Stream
from .ilvis0_shape import load_tangent
from .ilvis0_exploratory import load_kernel

POSITION_LIMIT=1e-6;DERIVATIVE_LIMIT=1e-7;SCALE=np.array([6371000.,6371000.,1.])


def tasks():
    rows=[dict(kind='reference',packets=n,tangent=t) for n in (120000,480000) for t in (False,True)]
    rows += [dict(kind='exact-pose',packets=480000,tangent=t) for t in (False,True)]
    return [dict(r,identity=f"{r['kind']}-{i}") for i,r in enumerate(rows)]


def _config(task):
    limits=np.r_[[.01]*3,[2.]*3,[10.]*3,[2e-6]*3,[.01]*3,[.001]*6,[2.]*3,.01,.001,1.]
    return dict(initial_c=np.array([-.9,3.2,11000.]),initial_v=np.zeros(3),initial_r=np.eye(3),
        limits=limits,point=np.zeros(27),model=0 if task['kind']=='reference' else 1,
        profile=task['kind']=='reference',tangent=task['tangent'],
        gravity=9.81 if task['kind']=='reference' else 9.75,radius=6371000.,input_id='generated:'+task['identity'])


def _packets(task,count):
    if task['kind']=='reference':
        dt=np.full(count,1/300.);standard=7.2921150e-5*np.array([np.cos(-.9),0.,-np.sin(-.9)])
        theta=np.tile(standard*.5/300.,(count,1));dv=np.tile([0.,0.,-9.81/300.],(count,1))
    else:
        dt=np.full(count,1/256.);theta=np.zeros((count,3));dv=np.tile([0.,0.,-9.75/256.],(count,1))
    return theta,dv,dt


def evaluate(task,directory,charge):
    config=_config(task);n=task['packets'];stream=Stream(directory,**config)
    # Identical scalar additions define the reference query clock.
    clock=0.;times=[];period=1/(300. if task['kind']=='reference' else 256.)
    for i in range(n):
        clock+=period
        if i%300==299 or i==n-1:times.append(clock)
    times=np.array(times);reference=None;jac=None;reference_boundaries=None;ref_identity=None
    reference_runtime=0.
    if task['kind']=='reference':
        theta,dv,dt=_packets(task,n);reference=np.empty((len(times),3));start=time.monotonic()
        if task['tangent']:
            kernel,ref_identity=load_tangent(directory);jac=np.empty((reference.size,27));b=ctypes.c_int()
            charge(native_calls=1,packet_visits=n)
            code=kernel(n,theta,dv,dt,len(times),times,config['initial_c'],config['initial_v'],config['initial_r'],
                config['limits'],config['point'],config['model'],int(config['profile']),config['gravity'],
                config['radius'],reference,jac,ctypes.byref(b))
            jac=jac.reshape(len(times),3,27);reference_boundaries=b.value
        else:
            kernel,ref_identity=load_kernel(directory);charge(native_calls=1,packet_visits=n)
            code=kernel(n,theta,dv,dt,len(times),times,config['initial_c'],config['initial_v'],config['initial_r'],
                np.zeros(3),config['model'],config['gravity'],config['radius'],.5,reference)
        if code:raise ValueError('whole-array reference failed: '+str(code))
        reference_runtime=time.monotonic()-start;del theta,dv,dt
    largest=0.;largest_j=0.;pose_error=0.;boundary_count=0;query=0;start=time.monotonic()
    tracemalloc.start()
    try:
        for begin in range(0,n,1024):
            count=min(1024,n-begin);theta,dv,dt=_packets(task,count);clock=stream.elapsed_s;end=clock
            for duration in dt:end+=float(duration)
            stop=query
            while stop<len(times) and times[stop]<=end:stop+=1
            if begin+count<n and stop>query and times[stop-1]==end:stop-=1
            charge(native_calls=1,packet_visits=count)
            actual=stream.push(theta,dv,dt,times[query:stop],packet_offset=begin,elapsed_s=clock)
            boundary_count+=actual['boundaries']
            if stop>query:
                pose_error=max(pose_error,float(np.max(abs((actual['positions']-config['initial_c'])*SCALE))))
                expected=reference[query:stop] if reference is not None else config['initial_c']
                largest=max(largest,float(np.max(abs((actual['positions']-expected)*SCALE))))
                if jac is not None:largest_j=max(largest_j,float(np.max(abs((actual['jacobian']-jac[query:stop])*SCALE[None,:,None]))))
            query=stop
            if begin==1024*((n//2)//1024):
                stream=Stream.restore(directory,stream.checkpoint(),input_id=config['input_id'])
        _,peak=tracemalloc.get_traced_memory()
    finally:tracemalloc.stop()
    runtime=time.monotonic()-start
    ref_pose=float(np.max(abs((reference-config['initial_c'])*SCALE))) if reference is not None else 0.
    passed=query==len(times) and largest<=POSITION_LIMIT and largest_j<=DERIVATIVE_LIMIT and peak<8*1024**2
    if reference_boundaries is not None:passed=passed and boundary_count==reference_boundaries
    return dict(identity=task['identity'],kind=task['kind'],input=task,passed=bool(passed),
        maximum_position_difference_m=largest,maximum_derivative_difference_m=largest_j if jac is not None else None,
        maximum_exact_pose_error_m=pose_error,reference_exact_pose_error_m=ref_pose,
        absolute_pose_criterion_passed=pose_error<=POSITION_LIMIT,
        maximum_block_packets=1024,peak_traced_bytes=peak,state_bytes=stream.state_bytes,
        native_clock_s=stream.elapsed_s,packet_count=stream.packet_count,queries= query,
        boundaries=boundary_count,reference_boundaries=reference_boundaries,
        runtime_s=runtime,reference_runtime_s=reference_runtime,streaming_kernel=stream.identity,reference_kernel=ref_identity,
        original_reads=0,optimizer_starts=0,scientific_decision='abstain')
