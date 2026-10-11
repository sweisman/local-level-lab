# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent reintegration of continuous controls at finer intervals.

No measured packets are subdivided or interpolated. Frozen geographic controls
provide the trajectory, calibration and receiver observations; this new generator
integrates analytic rates at newly defined physical sampling intervals.
"""
import math
import numpy as np

from . import ilvis0_geographic_controls as original

VERSION='ilvis0-interval-resolution-controls-v1'


def fixture(model,factor,geometry='original',clock='nominal'):
    if type(factor) is not int or factor not in (1,2,4) or geometry not in ('original','roll'):
        raise ValueError('declared resolution and geometry required')
    f=original.fixture(model,clock)
    dt=np.repeat(f['dt']/factor,factor)
    ends=np.cumsum(dt); starts=ends-dt
    x,w=np.polynomial.legendre.leggauss(8)
    t=starts[:,None]+dt[:,None]*(x+1)/2
    psi=.06*np.sin(2*math.pi*t/4.3)
    pitch=f['truth']['attitude_y']+.05*np.sin(2*math.pi*t/3.7)
    roll=.35*np.sin(2*math.pi*t/5.1) if geometry=='roll' else np.zeros_like(t)
    dpsi=.06*2*math.pi/4.3*np.cos(2*math.pi*t/4.3)
    dpitch=.05*2*math.pi/3.7*np.cos(2*math.pi*t/3.7)
    droll=.35*2*math.pi/5.1*np.cos(2*math.pi*t/5.1) if geometry=='roll' else np.zeros_like(t)
    cp,sp,ct,st,cr,sr=np.cos(psi),np.sin(psi),np.cos(pitch),np.sin(pitch),np.cos(roll),np.sin(roll)
    # C = Rz(psi) Ry(pitch) Rx(roll); C(0) has the unchanged initial pitch.
    def body(vector):
        vx,vy,vz=vector
        horizontal=cp*vx+sp*vy
        bx=ct*horizontal-st*vz
        by=-sp*vx+cp*vy
        bz=st*horizontal+ct*vz
        return np.stack((bx,cr*by+sr*bz,-sr*by+cr*bz),axis=-1)
    ve=220.
    earth=np.array([7.292115e-5,0.,0.]) if model=='sphere_rotating' else np.zeros(3)
    transport=np.array([0.,0.,-ve/f['metric'][1]]) if model=='flat_still' else np.array([ve/f['metric'][1],0.,0.])
    relative=np.stack((-dpsi*st+droll,cr*dpitch+sr*dpsi*ct,-sr*dpitch+cr*dpsi*ct),axis=-1)
    rates=body(earth+transport)+relative
    force=np.cross(2*earth+transport,[0.,ve,0.])-np.array([0.,0.,9.81+f['truth']['gravity_delta']])
    theta=np.sum(rates*w[None,:,None],axis=1)*dt[:,None]/2
    dv=np.sum(body(force)*w[None,:,None],axis=1)*dt[:,None]/2
    theta[:,2]=theta[:,2]*(1+f['truth']['gyro_gain_z'])+f['truth']['gyro_bias_z']*dt
    # The existing fitter accepts explicit known elapsed intervals. Its metadata
    # must not call 400/800 Hz controls nominal 200 Hz.
    return dict(f,theta=theta,dv=dv,dt=dt,clock=f'{clock}-r{factor}-{geometry}',
        original_construction=clock,refinement_factor=factor,geometry=geometry)


def run_fit(model,factor,geometry,kernel,tangent):
    f=fixture(model,factor,geometry)
    row=original.run_fit(f,kernel,tangent,strategy='original',start_id='zero')
    fit=row['fit']; parameters=fit['parameters']
    row.update(refinement_factor=factor,geometry=geometry,sample_count=len(f['dt']),
        duration_s=float(np.sum(f['dt'])),receiver_observations_unchanged=True,
        nominal_increment_interval_s=.005/factor,
        gyro_bias_z_error_dph=(parameters['gyro_bias_z']-f['truth']['gyro_bias_z'])*648000/math.pi,
        gyro_gain_z_error=parameters['gyro_gain_z']-f['truth']['gyro_gain_z'])
    return row
