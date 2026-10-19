# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent geographic IMU/receiver controls; no observed-data fitting.

Generate continuous body rates and specific force by closed-form kinematics and
Gauss quadrature. Do not call the production navigation predictor to make truth.
The finite-interval strapdown approximation has a measured, nonzero truth error.
"""
import math
import numpy as np

from . import ilvis0_estimator as estimator, ilvis0_exploratory as explore
from . import ilvis0_shape as shape, ilvis0_solver_verified_stop as verified

VERSION='ilvis0-independent-geographic-controls-v1'
LIMITS=dict(attitude_y=.01,velocity_y=2.,gyro_bias_z=math.pi/648000,
    gyro_gain_z=.02,gravity_delta=.05,time_offset=.1)


def fixture(model,clock):
    if model not in explore.MODELS or clock not in ('nominal','variable'):
        raise ValueError('declared geographic model and clock construction required')
    near=clock=='variable'
    truth=dict(attitude_y=.0098 if near else .003,
        velocity_y=1.98 if near else .5,
        gyro_gain_z=.0198 if near else .005,
        gyro_bias_z=(.99 if near else .25)*math.pi/648000,
        gravity_delta=.0495 if near else .012,time_offset=.099 if near else .023)
    n=2400
    dt=.005*(1+50e-6*np.sin(np.arange(n)*.013)) if near else np.full(n,.005)
    ends=np.cumsum(dt); starts=ends-dt
    x,w=np.polynomial.legendre.leggauss(8)
    t=starts[:,None]+dt[:,None]*(x+1)/2
    psi=.06*np.sin(2*math.pi*t/4.3)
    pitch=truth['attitude_y']+.05*np.sin(2*math.pi*t/3.7)
    dpsi=.06*2*math.pi/4.3*np.cos(2*math.pi*t/4.3)
    dpitch=.05*2*math.pi/3.7*np.cos(2*math.pi*t/3.7)
    cp,sp,ct,st=np.cos(psi),np.sin(psi),np.cos(pitch),np.sin(pitch)
    # C = Rz(psi) Ry(pitch); all vectors are in local NED or sensor axes.
    def body(vector):
        vx,vy,vz=vector
        horizontal=cp*vx+sp*vy
        return np.stack((ct*horizontal-st*vz,-sp*vx+cp*vy,st*horizontal+ct*vz),axis=-1)
    ve=220.; height=1000.; globe_radius=6378137.+height; disc_radius=6371000.
    metric_e=disc_radius*math.pi/2 if model=='flat_still' else globe_radius
    earth=np.array([7.292115e-5,0.,0.]) if model=='sphere_rotating' else np.zeros(3)
    transport=np.array([0.,0.,-ve/metric_e]) if model=='flat_still' else np.array([ve/metric_e,0.,0.])
    relative=np.stack((-dpsi*st,dpitch,dpsi*ct),axis=-1)
    rates=body(earth+transport)+relative
    force=np.cross(2*earth+transport,[0.,ve,0.])-np.array([0.,0.,9.81+truth['gravity_delta']])
    theta=np.sum(rates*w[None,:,None],axis=1)*dt[:,None]/2
    dv=np.sum(body(force)*w[None,:,None],axis=1)*dt[:,None]/2
    theta[:,2]=theta[:,2]*(1+truth['gyro_gain_z'])+truth['gyro_bias_z']*dt
    # Receiver epochs are deliberately off the IMU grid. Their physical time
    # includes known latency, and is not determined by packet index.
    gps_times=np.linspace(.21737,11.71737,24)
    physical=gps_times+truth['time_offset']
    gps=np.column_stack((np.zeros(len(physical)),ve*physical/metric_e,np.full(len(physical),height)))
    return dict(model=model,clock=clock,dt=dt,theta=theta,dv=dv,gps_times=gps_times,gps=gps,
        truth=truth,metric=np.array([disc_radius if model=='flat_still' else 6335439.327292819+height,metric_e,1.]),
        initial=dict(latitude_rad=0.,longitude_rad=0.,height_m=height,
            velocity_ned_mps=np.array([0.,ve-truth['velocity_y'],0.]),attitude_body_to_ned=np.eye(3)))


def problem(f,kernel,tangent):
    sigma=np.tile(.01/f['metric'],len(f['gps_times']))
    return shape.TangentProblem(f['theta'],f['dv'],f['dt'],f['gps_times'],f['gps'],
        np.diag(sigma**2),f['initial'],estimator.Bounds(LIMITS),fit_earth_removal=False,
        kernel=kernel,tangent_kernel=tangent,
        clock_hypothesis='nominal_200Hz' if f['clock']=='nominal' else 'header_elapsed',
        processing_hypothesis='unsubtracted_increment_hypothesis',maximum_interval_s=.0075,
        gravity_mps2=9.81,disc_radius_m=6371000.)


def truth_point(f,p):
    return np.array([f['truth'][name]/p.bounds.limits[name] for name in p.bounds.active])


def position_error(f,prediction):
    return float(np.max(np.linalg.norm((prediction-f['gps'])*f['metric'],axis=1)))


class CountedProblem:
    """Independent accounting includes diagnostic sweeps in addition to fit calls."""
    def __init__(self,p):
        self.problem=p; self.bounds=p.bounds; self.tangents=0; self.values=0

    def residual_tangent(self,point,model):
        if self.tangents>=200: raise estimator.EvaluationLimit('control tangent allowance exhausted')
        self.tangents+=1
        return self.problem.residual_tangent(point,model)

    def predict(self,point,model):
        if self.values>=2: raise estimator.EvaluationLimit('control value allowance exhausted')
        self.values+=1
        return self.problem.predict(point,model)


def run_fit(f,kernel,tangent,*,strategy,start_id):
    if strategy not in ('original','verified') or start_id not in ('zero','opposed'):
        raise ValueError('declared finite strategy/start required')
    p=problem(f,kernel,tangent); counted=CountedProblem(p); truth=truth_point(f,p)
    start=np.zeros(len(truth)) if start_id=='zero' else -.8*np.sign(truth)
    solve=shape.fit_shape_candidate if strategy=='original' else verified.fit_candidate
    fit=solve(counted,f['model'],start=start,maximum_evaluations=200)
    point=np.array(fit['normalized_parameters'])
    prediction=counted.predict(point,f['model']); reference=counted.predict(truth,f['model'])
    r=p.whiten(reference-p.gps)
    error=position_error(f,prediction); reference_error=position_error(f,reference)
    # Numerical checks measure recovery of independent observations. These short
    # controls do not guarantee unique calibration or a global optimum.
    passed=bool(fit['converged'] and error<.002 and reference_error<.002 and
        fit['residual_sum_squares']<=float(r@r)+.01)
    return dict(identity=f"{f['model']}::{f['clock']}::{strategy}::{start_id}",
        fit=fit,truth=f['truth'],start=start.tolist(),maximum_position_error_m=error,
        truth_maximum_position_error_m=reference_error,truth_objective=float(r@r),
        maximum_normalized_parameter_error=float(np.max(abs(point-truth))),
        actual_tangent_sweeps=counted.tangents,actual_value_sweeps=counted.values,
        passed=passed,observed_fit_starts=0,full_archival_solver_qualified=False)
