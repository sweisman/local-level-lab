# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent non-equatorial controls and a defined finite-increment convention.

No production predictor generates measurements. Already-compensated here means
an exact finite body rotation plus midpoint-frame integrated specific force.
It does not identify an Applanix output convention.
"""
import math
import numpy as np
from scipy.spatial.transform import Rotation

from . import ilvis0_geographic_controls as original
from . import ilvis0_compensation as correction, ilvis0_exploratory as explore
from . import ilvis0_shape as shape

VERSION='ilvis0-independent-latitude-convention-controls-v1'


def environment(model,degrees):
    if model not in explore.MODELS or not math.isfinite(degrees) or abs(degrees)>=80:
        raise ValueError('supported model and nonpolar finite latitude required')
    phi=math.radians(degrees);height=1000.;ve=220.
    earth=np.array([7.292115e-5*math.cos(phi),0.,-7.292115e-5*math.sin(phi)]) if model=='sphere_rotating' else np.zeros(3)
    if model=='flat_still':
        north=6371000.;east=6371000.*(math.pi/2-phi)
        transport=np.array([0.,0.,-ve/east])
    else:
        d=1-6.69437999014e-3*math.sin(phi)**2
        prime=6378137./math.sqrt(d)+height
        north=6378137.*(1-6.69437999014e-3)/d**1.5+height
        east=prime*math.cos(phi)
        transport=np.array([ve/prime,0.,-ve*math.tan(phi)/prime])
    return earth,transport,np.array([north,east,1.])


def motion(time,truth,roll):
    t=np.asarray(time,float)
    yaw=.06*np.sin(2*math.pi*t/4.3)
    pitch=truth['attitude_y']+.05*np.sin(2*math.pi*t/3.7)
    bank=.35*np.sin(2*math.pi*t/5.1) if roll else np.zeros_like(t)
    dy=.06*2*math.pi/4.3*np.cos(2*math.pi*t/4.3)
    dp=.05*2*math.pi/3.7*np.cos(2*math.pi*t/3.7)
    db=.35*2*math.pi/5.1*np.cos(2*math.pi*t/5.1) if roll else np.zeros_like(t)
    cp,sp,ct,st,cr,sr=np.cos(yaw),np.sin(yaw),np.cos(pitch),np.sin(pitch),np.cos(bank),np.sin(bank)
    # Body-to-NED Rz(yaw) Ry(pitch) Rx(bank), from analytic Euler geometry.
    r=np.stack((np.stack((cp*ct,cp*st*sr-sp*cr,cp*st*cr+sp*sr),axis=-1),
        np.stack((sp*ct,sp*st*sr+cp*cr,sp*st*cr-cp*sr),axis=-1),
        np.stack((-st,ct*sr,ct*cr),axis=-1)),axis=-2)
    relative=np.stack((-dy*st+db,cr*dp+sr*dy*ct,-sr*dp+cr*dy*ct),axis=-1)
    return r,relative


def fixture(model,degrees,construction,*,convention='ordinary_rate_integrals'):
    earth,transport,metric=environment(model,degrees)
    if construction not in ('interior','near_roll') or convention not in ('ordinary_rate_integrals','already_compensated'):
        raise ValueError('explicit supported construction and convention required')
    roll=construction=='near_roll'
    f=original.fixture(model,'variable' if roll else 'nominal')
    dt=f['dt'];ends=np.cumsum(dt);starts=ends-dt;truth=f['truth']
    nodes,weights=np.polynomial.legendre.leggauss(8)
    within=dt[:,None]*(nodes+1)/2;time=starts[:,None]+within
    c,relative=motion(time,truth,roll)
    force=np.cross(2*earth+transport,[0.,220.,0.])-np.array([0.,0.,9.81+truth['gravity_delta']])
    if convention=='ordinary_rate_integrals':
        rates=np.einsum('...ji,j->...i',c,earth+transport)+relative
        body_force=np.einsum('...ji,j->...i',c,force)
        theta=np.sum(rates*weights[None,:,None],axis=1)*dt[:,None]/2
        dv=np.sum(body_force*weights[None,:,None],axis=1)*dt[:,None]/2
        gps_times=f['gps_times'];physical=gps_times+truth['time_offset']
    else:
        first,_=motion(starts,truth,roll);last,_=motion(ends,truth,roll)
        navigation=Rotation.from_rotvec(dt[:,None]*(earth+transport)).as_matrix()
        finite=np.swapaxes(first,-1,-2)@navigation@last
        theta=Rotation.from_matrix(finite).as_rotvec()
        # Inertialized force integral in the starting body frame. The analytic
        # navigation-frame force is constant; C(t) C(t)^T cancels exactly.
        navigation=Rotation.from_rotvec((within[...,None]*(earth+transport)).reshape(-1,3)).as_matrix().reshape(len(dt),8,3,3)
        rotated=np.einsum('...ij,j->...i',navigation,force)
        integral=np.sum(rotated*weights[None,:,None],axis=1)*dt[:,None]/2
        starting_body=np.einsum('...ji,...j->...i',first,integral)
        dv=Rotation.from_rotvec(-theta/2).apply(starting_body)
        physical=ends[np.linspace(43,len(dt)-44,24,dtype=int)]
        gps_times=physical-truth['time_offset']
    theta[:,2]=theta[:,2]*(1+truth['gyro_gain_z'])+truth['gyro_bias_z']*dt
    phi=math.radians(degrees)
    gps=np.column_stack((np.full(len(physical),phi),220.*physical/metric[1],np.full(len(physical),1000.)))
    return dict(f,theta=theta,dv=dv,gps_times=gps_times,gps=gps,metric=metric,
        latitude_deg=degrees,construction=construction,increment_convention=convention,
        initial=dict(latitude_rad=phi,longitude_rad=0.,height_m=1000.,
            velocity_ned_mps=np.array([0.,220.-truth['velocity_y'],0.]),attitude_body_to_ned=np.eye(3)))


def identity(model,degrees,construction,start):
    return f'{model}::{degrees:+.0f}::{construction}::{start}'


def run_fit(model,degrees,construction,start,kernel):
    if start not in ('zero','opposed'):raise ValueError('declared start required')
    f=fixture(model,degrees,construction)
    p=correction.problem(f,kernel,'combined',convention=f['increment_convention'])
    truth=original.truth_point(f,p)
    initial=np.zeros(len(truth)) if start=='zero' else -.8*np.sign(truth)
    counted=original.CountedProblem(p)
    row=dict(identity=identity(model,degrees,construction,start),model=model,latitude_deg=degrees,
        construction=construction,start_id=start,start=initial.tolist(),truth=f['truth'],
        increment_convention=f['increment_convention'],observed_fit_starts=0)
    try:
        fit=shape.fit_shape_candidate(counted,model,start=initial,maximum_evaluations=200)
        point=np.array(fit['normalized_parameters'])
        predicted=counted.predict(point,model);reference=counted.predict(truth,model)
        residual=p.whiten(reference-p.gps);error=original.position_error(f,predicted)
        reference_error=original.position_error(f,reference)
        row.update(fit=fit,gyro_bias_z_error_dph=(fit['parameters']['gyro_bias_z']-f['truth']['gyro_bias_z'])*648000/math.pi,
            gyro_gain_z_error=fit['parameters']['gyro_gain_z']-f['truth']['gyro_gain_z'],
            maximum_position_error_m=error,truth_maximum_position_error_m=reference_error,
            truth_objective=float(residual@residual),
            passed=bool(fit['converged'] and error<.002 and reference_error<.002 and fit['residual_sum_squares']<=float(residual@residual)+.01))
    except Exception as error:
        row.update(passed=False,error=f'{type(error).__name__}: {error}')
    row.update(actual_tangent_sweeps=counted.tangents,actual_value_sweeps=counted.values)
    return row
