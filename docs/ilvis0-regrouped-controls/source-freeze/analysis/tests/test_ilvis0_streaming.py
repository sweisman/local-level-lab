# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generated controls; no archive reads or observed optimizer starts."""
import ctypes
import json

import numpy as np
import pytest

from lll import ilvis0_streaming as streaming
from lll.ilvis0_shape import load_tangent
from lll.ilvis0_exploratory import load_kernel
from scipy.spatial.transform import Rotation


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    directory=tmp_path_factory.mktemp('stream-kernels')
    return directory,load_tangent(directory)[0]


def inputs(n=19):
    k=np.arange(n,dtype=float)
    dt=.0048+.0001*(k%4)
    theta=np.column_stack((2e-5*np.cos(k),-3e-5+1e-5*np.sin(k),1e-5*np.cos(.3*k)))
    dv=np.column_stack((.001*np.sin(k),.001*np.cos(k),-9.81*dt))
    ends=np.cumsum(dt)
    times=np.sort(np.r_[0.,ends[4],ends[9],ends[-1],(ends[1:]+ends[:-1])/2])
    c=np.array([-.9,3.2,11000.]);v=np.array([180.,55.,-.1]);r=np.eye(3)
    limits=np.r_[[.01]*3,[2.]*3,[10.]*3,[2e-6]*3,[.01]*3,[.001]*6,[2.]*3,.01,.001,1.]
    point=np.linspace(-.4,.4,27);point[25]=0.
    return theta,dv,dt,times,c,v,r,limits,point


def make_stream(directory,model=0,profile=True,tangent=True):
    *_,c,v,r,limits,point=inputs()
    return streaming.Stream(directory,initial_c=c,initial_v=v,initial_r=r,limits=limits,
        point=point,model=model,profile=profile,gravity=9.81,radius=6371000.,
        input_id='generated-known-packet-order',tangent=tangent)


def reference(kernel,model,profile,arrays):
    theta,dv,dt,times,c,v,r,limits,point=arrays
    out=np.empty((len(times),3));jac=np.empty((out.size,27));boundaries=ctypes.c_int()
    code=kernel(len(dt),theta,dv,dt,len(times),times,c,v,r,limits,point,
        model,int(profile),9.81,6371000.,out,jac,ctypes.byref(boundaries))
    assert code==0
    return out,jac.reshape(len(times),3,27),boundaries.value


def run_chunks(stream,arrays,sizes,*,restart=False,directory=None):
    theta,dv,dt,times,*_=arrays
    outputs=[];jacobians=[];boundary_count=0;index=0;query=0;clock=0.
    for size in sizes:
        end=clock
        for period in dt[index:index+size]:end+=period
        stop=query
        while stop<len(times) and times[stop]+stream.time_offset<=end:stop+=1
        # Deliberately defer exact block-boundary queries to the next block.
        if index+size<len(dt) and stop>query and times[stop-1]+stream.time_offset==end:stop-=1
        result=stream.push(theta[index:index+size],dv[index:index+size],dt[index:index+size],
            times[query:stop],packet_offset=index,elapsed_s=clock)
        outputs.append(result['positions']);boundary_count+=result['boundaries']
        if stream.tangent:jacobians.append(result['jacobian'])
        index+=size;query=stop;clock=end
        if restart:
            saved=json.loads(json.dumps(stream.checkpoint()))
            stream=streaming.Stream.restore(directory,saved,input_id='generated-known-packet-order')
    assert query==len(times)
    return np.concatenate(outputs),np.concatenate(jacobians) if jacobians else None,boundary_count,stream


@pytest.mark.parametrize('model',[0,1,2])
@pytest.mark.parametrize('profile',[False,True])
def test_all_columns_match_unchanged_whole_history(kernels,model,profile):
    directory,kernel=kernels;arrays=inputs()
    expected,ej,eb=reference(kernel,model,profile,arrays)
    actual,aj,ab,_=run_chunks(make_stream(directory,model,profile),arrays,[5,5,9])
    np.testing.assert_allclose(actual,expected,rtol=0.,atol=1e-13)
    np.testing.assert_allclose(aj,ej,rtol=0.,atol=1e-13)
    assert ab==eb


def test_chunk_and_serialized_restart_are_bit_identical(kernels):
    directory,_=kernels;arrays=inputs()
    a,aj,_,_=run_chunks(make_stream(directory),arrays,[19])
    b,bj,_,state=run_chunks(make_stream(directory),arrays,[5,5,9],restart=True,directory=directory)
    np.testing.assert_array_equal(a,b);np.testing.assert_array_equal(aj,bj)
    assert state.packet_count==19
    assert state.elapsed_s==np.cumsum(arrays[2])[-1]


def test_invalid_block_does_not_advance_state(kernels):
    directory,_=kernels;stream=make_stream(directory);theta,dv,dt,*_=inputs()
    before=stream.checkpoint()
    for kwargs in ({'packet_offset':1,'elapsed_s':0.}, {'packet_offset':0,'elapsed_s':.001}):
        with pytest.raises(ValueError):stream.push(theta,dv,dt,np.array([.01]),**kwargs)
        assert stream.checkpoint()==before
    with pytest.raises(ValueError):stream.push(theta,dv,-dt,np.array([.01]),packet_offset=0,elapsed_s=0.)
    assert stream.checkpoint()==before


def test_checkpoint_rejects_wrong_input_or_tampered_state(kernels):
    directory,_=kernels;saved=make_stream(directory).checkpoint()
    with pytest.raises(ValueError):streaming.Stream.restore(directory,saved,input_id='different-recording')
    saved['packet_count']=3
    with pytest.raises(ValueError):streaming.Stream.restore(directory,saved,input_id='generated-known-packet-order')


@pytest.mark.parametrize('model',[0,1,2])
@pytest.mark.parametrize('profile',[False,True])
def test_value_stream_matches_independently_calibrated_original_c(kernels,model,profile):
    directory,_=kernels;arrays=inputs();theta,dv,dt,times,c,v,r,limits,point=arrays
    p=point*limits;removal=(p[26]+1)/2 if profile else 0.
    corrected_theta=np.ascontiguousarray((theta-p[9:12]*dt[:,None])/(1+p[15:18]))
    corrected_dv=np.ascontiguousarray((dv-p[12:15]*dt[:,None])/(1+p[18:21]))
    # Independent initialization and calibration, passed to unchanged C API.
    if model==2:mn=6371000.;me=mn*(np.pi/2-c[0])
    else:
        denominator=1-6.69437999014e-3*np.sin(c[0])**2
        mn=6378137.*(1-6.69437999014e-3)/denominator**1.5+c[2]
        me=(6378137./np.sqrt(denominator)+c[2])*np.cos(c[0])
    seed=np.array(c+[p[6]/mn,p[7]/me,-p[8]])
    rotation=np.ascontiguousarray(r@Rotation.from_rotvec(p[:3]).as_matrix())
    expected=np.empty((len(times),3));kernel=load_kernel(directory)[0]
    code=kernel(len(dt),corrected_theta,corrected_dv,dt,len(times),times,seed,
        np.ascontiguousarray(v+p[3:6]),rotation,np.ascontiguousarray(p[21:24]),model,
        9.81+p[24],6371000.,removal,expected)
    assert code==0
    actual,_,_,_=run_chunks(make_stream(directory,model,profile,tangent=False),arrays,[5,5,9],restart=True,directory=directory)
    scale=np.array([6371000.,6371000.,1.])
    assert np.max(abs((actual-expected)*scale))<1e-6


@pytest.mark.parametrize('model',[0,1,2])
@pytest.mark.parametrize('removal',[0.,.5,1.])
def test_independent_stationary_pose_with_background_compensation(kernels,model,removal):
    directory,_=kernels;n=53;dt=np.full(n,.005);c=np.array([.8,1.2,400.])
    standard=7.2921150e-5*np.array([np.cos(c[0]),0.,-np.sin(c[0])])
    theta=np.tile(standard*((1. if model==0 else 0.)-removal)*.005,(n,1))
    dv=np.tile([0.,0.,-9.81*.005],(n,1));limits=np.zeros(27);limits[26]=1.
    point=np.zeros(27);point[26]=2*removal-1.
    stream=streaming.Stream(directory,initial_c=c,initial_v=np.zeros(3),initial_r=np.eye(3),
        limits=limits,point=point,model=model,profile=True,gravity=9.81,radius=6371000.,input_id='constant-pose')
    times=np.cumsum(dt)[::4]
    result=stream.push(theta,dv,dt,times,packet_offset=0,elapsed_s=0.)
    assert np.max(abs((result['positions']-c)*[6371000.,6371000.,1.]))<1e-6


def test_bad_queries_and_native_failure_leave_checkpoint_unchanged(kernels):
    directory,_=kernels;stream=make_stream(directory);theta,dv,dt,*_=inputs()
    before=stream.checkpoint()
    for times in ([-.001],[.1],[.03,.02],[float('nan')]):
        with pytest.raises(ValueError):stream.push(theta,dv,dt,times,packet_offset=0,elapsed_s=0.)
        assert stream.checkpoint()==before
    dv=dv.copy();dv[:,2]=1e308
    with pytest.raises(ValueError):stream.push(theta,dv,dt,[.01],packet_offset=0,elapsed_s=0.)
    assert stream.checkpoint()==before


def test_restart_rejects_changed_environment_even_with_valid_integrity_hash(kernels):
    directory,_=kernels;saved=make_stream(directory).checkpoint()
    saved['environment']['numpy']='different'
    payload={k:v for k,v in saved.items() if k!='sha256'};saved['sha256']=streaming._digest(payload)
    with pytest.raises(ValueError,match='environment'):streaming.Stream.restore(directory,saved,input_id='generated-known-packet-order')


def test_applied_gravity_must_remain_positive(kernels):
    directory,_=kernels;*_,c,v,r,limits,point=inputs()
    limits=limits.copy();limits[24]=10.;point=point.copy();point[24]=-1.
    with pytest.raises(ValueError):streaming.Stream(directory,initial_c=c,initial_v=v,initial_r=r,
        limits=limits,point=point,model=0,profile=False,gravity=9.81,radius=6371000.,input_id='invalid-gravity')
