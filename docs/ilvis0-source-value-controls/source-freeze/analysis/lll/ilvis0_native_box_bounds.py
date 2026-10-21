# SPDX-License-Identifier: AGPL-3.0-or-later
"""Arbitrary-box adapter for the qualified mathematical native-history bounds.

No global floating-point enclosure or observational coverage is supplied. All
27 parameters, calibration/time cross terms and processing limits are retained.
"""
import math

import numpy as np
from scipy.linalg import expm

from . import ilvis0_geographic_bounds as geo,ilvis0_history_bounds as history
from .ilvis0_local_step_bounds import Value,Matrix
from .ilvis0_increment_remainders import calibrated_box

VERSION='ilvis0-arbitrary-native-parameter-box-v1'
MODELS=('sphere_rotating','sphere_still','flat_still')


def enclose(configuration,theta,dv,dt,*,time,lower,upper,center):
    limits=np.asarray(configuration['limits'],float);lo=np.asarray(lower,float);hi=np.asarray(upper,float);z=np.asarray(center,float)
    theta=np.asarray(theta,float);dv=np.asarray(dv,float);dt=np.asarray(dt,float)
    c=np.asarray(configuration['initial_c'],float);v=np.asarray(configuration['initial_v'],float);r=np.asarray(configuration['initial_r'],float)
    model=configuration['model'];profile=configuration['profile'];gravity=float(configuration['gravity']);radius=float(configuration['radius'])
    if (any(x.shape!=(27,) or not np.all(np.isfinite(x)) for x in (limits,lo,hi,z))
            or np.any(limits<0.) or np.any(lo< -1.) or np.any(hi>1.) or np.any(lo>hi) or np.any(z<lo) or np.any(z>hi)
            or model not in (0,1,2) or isinstance(model,bool) or type(profile) is not bool or limits[26]>1.
            or c.shape!=(3,) or v.shape!=(3,) or r.shape!=(3,3) or not all(np.all(np.isfinite(x)) for x in (c,v,r))
            or not np.allclose(r.T@r,np.eye(3),rtol=0.,atol=1e-10) or abs(np.linalg.det(r)-1.)>1e-10
            or not math.isfinite(time) or not math.isfinite(gravity+radius) or gravity<=0. or radius<=0.
            or dt.ndim!=1 or not len(dt) or theta.shape!=(len(dt),3) or dv.shape!=theta.shape
            or not all(np.all(np.isfinite(x)) for x in (theta,dv,dt)) or np.any(dt<=0.)):
        raise ValueError('complete supported native configuration, increments and normalized box required')
    model_name=MODELS[model];p=limits*z;physical_lower=limits*lo;physical_upper=limits*hi
    delta=limits*np.maximum(z-lo,hi-z)
    vector=lambda section:Value(p[section],float(np.linalg.norm(delta[section])),0.)
    seed=geo.Coordinates(*(geo.Scalar.fixed(x) for x in c))
    displacement=geo.coordinate_map(seed,vector(slice(6,9)),model=model_name,disc_radius_m=radius)
    position=geo.Coordinates(*(geo.plus(a,b) for a,b in zip((seed.latitude,seed.longitude,seed.height),displacement)))
    x,y,zangle=p[:3];skew=np.array([[0.,-zangle,y],[zangle,0.,-x],[-y,x,0.]])
    rotation_radius=float(np.linalg.norm(delta[:3]))
    state=geo.State(position,Value(v+p[3:6],float(np.linalg.norm(delta[3:6])),0.),
        Matrix(r@expm(skew),min(2.,rotation_radius),.5*rotation_radius**2,'rotation'))
    def corrected(raw,period,bias,gain):
        result=calibrated_box(raw,period,bias_center=p[bias],gain_center=p[gain],
            bias_lower=physical_lower[bias],bias_upper=physical_upper[bias],
            gain_lower=physical_lower[gain],gain_upper=physical_upper[gain])
        return Value(result['center'],result['change_radius'],result['remainder_radius'])
    angles=[corrected(raw,period,slice(9,12),slice(15,18)) for raw,period in zip(theta,dt)]
    velocity=[corrected(raw,period,slice(12,15),slice(18,21)) for raw,period in zip(dv,dt)]
    starts=[];clock=0.
    for period in dt:starts.append(clock);clock+=float(period)
    query=geo.Scalar.interval(time+p[25],time+physical_lower[25],time+physical_upper[25])
    removal=geo.Scalar.interval((p[26]+1.)/2.,(physical_lower[26]+1.)/2.,(physical_upper[26]+1.)/2.) if profile else geo.Scalar.fixed(0.)
    result=history.history(initial=state,theta=angles,dv=velocity,durations=dt,starts=np.array(starts),time=query,
        removal=removal,gravity=geo.Scalar.interval(gravity+p[24],gravity+physical_lower[24],gravity+physical_upper[24]),
        lever=vector(slice(21,24)),model=model_name,disc_radius_m=radius)
    output=result.observation;components=(output.latitude,output.longitude,output.height)
    return dict(version=VERSION,center=output.center,remainder=np.array([x.value.remainder for x in components]),
        change=np.array([x.value.change for x in components]),normalized_center=z.copy(),lower=lo.copy(),upper=hi.copy(),
        parameter_count=27,time_s=time,used_packet_count=len(result.packet_indices),boundary_crossings=result.boundary_crossings,
        floating_point_enclosure_verified=False,observational_coverage_qualified=False,scientific_decision='abstain')
