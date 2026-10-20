# SPDX-License-Identifier: AGPL-3.0-or-later
"""Global mathematical calibration/preintegration bounds, not full native coverage.

Assumes positive gain denominators, fixed packet durations and exact rotation
maps. No original reads, parameter fitting or empirical uncertainty calibration.
Floating-point enclosure and candidate-dependent geographic terms remain open.
"""
from dataclasses import dataclass
import math

import numpy as np

VERSION='ilvis0-global-increment-remainders-v1'
CONSTANTS={'rotation':(1.,1.,.5),'velocity':(1.,.5,1/6),'position':(.5,1/6,1/24)}


def _vector(value):
    a=np.array(value,float,copy=True)
    if a.shape!=(3,) or not np.all(np.isfinite(a)):raise ValueError('finite signed three-vector required')
    a.setflags(write=False);return a


def _up(value):
    value=float(value)
    if not math.isfinite(value) or value<0.:raise ValueError('finite nonnegative mathematical radius required')
    return float(np.nextafter(value,np.inf)) if value else 0.


def _norm(value):return _up(np.linalg.norm(value))


def calibrated_box(raw,dt,*,bias_center,gain_center,bias_lower,bias_upper,gain_lower,gain_upper):
    raw=_vector(raw);b0=_vector(bias_center);g0=_vector(gain_center)
    bl=_vector(bias_lower);bu=_vector(bias_upper);gl=_vector(gain_lower);gu=_vector(gain_upper)
    if not math.isfinite(dt) or dt<=0.:raise ValueError('fixed positive packet duration required')
    if (np.any(bl>bu) or np.any(gl>gu) or np.any(b0<bl) or np.any(b0>bu) or np.any(g0<gl) or np.any(g0>gu)
            or np.any(gl<=-1.) or np.any(gu>=1.)):
        raise ValueError('feasible center and native gain domain strictly between minus/plus one required')
    a=raw-b0*dt;d=1.+g0;dmin=1.+gl;center=a/d
    corners=np.array([(raw-b*dt)/(1.+g) for b in (bl,bu) for g in (gl,gu)])
    changes=np.max(abs(corners-center),axis=0)
    b=np.maximum(abs(bl-b0),abs(bu-b0));g=np.maximum(abs(gl-g0),abs(gu-g0))
    remainders=abs(a)*g*g/(d*d*dmin)+dt*b*g/(d*dmin)
    if not all(np.all(np.isfinite(v)) for v in (center,corners,remainders)):raise ValueError('unrepresentable corrected increment box')
    center.setflags(write=False)
    return dict(version=VERSION,center=center,change_radius=_norm(changes),remainder_radius=_norm(remainders),
        component_change=changes.tolist(),component_remainder=remainders.tolist(),
        bias_jacobian=np.diag(-dt/d),gain_jacobian=np.diag(-a/(d*d)),
        scope='complete_declared_bias_gain_box',native_full_map_covered=False,floating_point_enclosure_verified=False)


def packet_bound(theta,dv,*,kind):
    if kind not in CONSTANTS:raise ValueError('rotation, velocity or position map required')
    c0,c1,c2=CONSTANTS[kind]
    angle=_up(theta['change_radius']);angle_remainder=_up(theta['remainder_radius'])
    force=_up(dv['change_radius']);force_remainder=_up(dv['remainder_radius']);nominal=_norm(_vector(dv['center']))
    change=min(2*c0,c1*angle)*nominal+c0*force
    remainder=c2*angle*angle*nominal+c1*angle*force+c1*angle_remainder*nominal+c0*force_remainder
    return dict(kind=kind,center_norm=_up(c0*nominal),change_radius=_up(change),remainder_radius=_up(remainder),
        scope='complete_declared_corrected_increment_box',native_full_map_covered=False)


@dataclass(frozen=True)
class PreintegrationBounds:
    samples:int=0
    rotation_change:float=0.
    rotation_remainder:float=0.
    velocity_change:float=0.
    velocity_remainder:float=0.
    position_change:float=0.
    position_remainder:float=0.
    velocity_center_norm:float=0.
    position_center_norm:float=0.

    def __post_init__(self):
        if type(self.samples) is not int or self.samples<0:raise ValueError('nonnegative sample count required')
        for key,value in vars(self).items():
            if key!='samples':_up(value)

    def advance(self,theta,dv,dt):
        if not math.isfinite(dt) or dt<=0.:raise ValueError('fixed positive packet duration required')
        j=packet_bound(theta,dv,kind='velocity');k=packet_bound(theta,dv,kind='position')
        def product(box):
            change=self.rotation_change*box['center_norm']+box['change_radius']
            remainder=(self.rotation_remainder*box['center_norm']+box['remainder_radius']
                +self.rotation_change*box['change_radius'])
            return change,remainder
        dv_change,dv_error=product(j);dp_change,dp_error=product(k)
        angle=_up(theta['change_radius']);delta_rotation=min(2.,angle)
        rotation_error=.5*angle*angle+_up(theta['remainder_radius'])
        return PreintegrationBounds(samples=self.samples+1,
            rotation_change=_up(min(2.,self.rotation_change+delta_rotation)),
            rotation_remainder=_up(self.rotation_remainder+rotation_error+self.rotation_change*delta_rotation),
            velocity_change=_up(self.velocity_change+dv_change),velocity_remainder=_up(self.velocity_remainder+dv_error),
            position_change=_up(self.position_change+dt*(self.velocity_change+dp_change)),
            position_remainder=_up(self.position_remainder+dt*(self.velocity_remainder+dp_error)),
            velocity_center_norm=_up(self.velocity_center_norm+j['center_norm']),
            position_center_norm=_up(self.position_center_norm+dt*(self.velocity_center_norm+k['center_norm'])))

    def report(self):
        return dict(vars(self),version=VERSION,scope='fixed_time_body_preintegration_only',
            native_full_map_covered=False,floating_point_enclosure_verified=False,
            original_reads=0,scientific_decision='abstain')
