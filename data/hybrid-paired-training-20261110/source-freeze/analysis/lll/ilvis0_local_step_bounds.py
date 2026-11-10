# SPDX-License-Identifier: AGPL-3.0-or-later
"""Global mathematical bounds for the supplied-context midpoint local step.

No archive observations, covariance calibration or complete geographic predictor.
Assumes valid global input bounds and exact operator structure. Floating-point
enclosure and geographic/time/lever-arm closure remain separate requirements.
"""
from dataclasses import dataclass
import math

import numpy as np

from .ilvis0_forward import exp

OMEGA=7.2921150e-5
VERSION='ilvis0-global-local-step-bounds-v1'


def _radius(value):
    value=float(value)
    if not math.isfinite(value) or value<0.:raise ValueError('finite nonnegative global radius required')
    return value


def _up(value):
    value=_radius(value)
    return float(np.nextafter(value,np.inf)) if value else 0.


@dataclass(frozen=True)
class Value:
    center:object
    change:float=0.
    remainder:float=0.

    def __post_init__(self):
        value=np.array(self.center,float,copy=True)
        if value.shape not in ((),(3,)) or not np.all(np.isfinite(value)):raise ValueError('finite scalar or three-vector required')
        value.setflags(write=False);object.__setattr__(self,'center',value)
        object.__setattr__(self,'change',_radius(self.change));object.__setattr__(self,'remainder',_radius(self.remainder))

    @property
    def norm(self):return float(abs(self.center)) if self.center.ndim==0 else float(np.linalg.norm(self.center))

    def report(self):return dict(center=self.center.tolist(),change=self.change,remainder=self.remainder,norm='Euclidean')


@dataclass(frozen=True)
class Matrix:
    center:object
    change:float
    remainder:float
    structure:str

    def __post_init__(self):
        value=np.array(self.center,float,copy=True)
        if value.shape!=(3,3) or not np.all(np.isfinite(value)) or self.structure not in ('rotation','contraction'):
            raise ValueError('finite structurally bounded three-axis matrix required')
        if self.structure=='rotation':
            if not np.allclose(value.T@value,np.eye(3),atol=1e-8,rtol=0.) or abs(np.linalg.det(value)-1.)>1e-8:
                raise ValueError('proper rotation center required; no repair')
        elif np.linalg.norm(value,ord=2)>1.+1e-10:raise ValueError('contraction center required')
        value.setflags(write=False);object.__setattr__(self,'center',value)
        object.__setattr__(self,'change',_radius(self.change));object.__setattr__(self,'remainder',_radius(self.remainder))

    def report(self):return dict(center=self.center.tolist(),change=self.change,remainder=self.remainder,
        norm='spectral',structure=self.structure,global_operator_norm_cap=1.)


def add(a,b):
    if not isinstance(a,Value) or not isinstance(b,Value) or a.center.shape!=b.center.shape:raise ValueError('aligned bounded values required')
    return Value(a.center+b.center,_up(a.change+b.change),_up(a.remainder+b.remainder))


def scale(a,number):
    if not isinstance(a,Value) or not math.isfinite(number):raise ValueError('bounded value and fixed finite scalar required')
    return Value(a.center*number,_up(a.change*abs(number)),_up(a.remainder*abs(number)))


def scalar_product(scalar,vector):
    if not isinstance(scalar,Value) or scalar.center.shape!=() or not isinstance(vector,Value) or vector.center.shape!=(3,):
        raise ValueError('bounded scalar and three-vector required')
    change=scalar.norm*vector.change+vector.norm*scalar.change+scalar.change*vector.change
    remainder=scalar.norm*vector.remainder+vector.norm*scalar.remainder+scalar.change*vector.change
    return Value(scalar.center*vector.center,_up(change),_up(remainder))


def matrix_product(a,b):
    if not isinstance(a,Matrix) or not isinstance(b,Matrix):raise ValueError('structural matrix bounds required')
    return Matrix(a.center@b.center,_up(min(2.,a.change+b.change)),
        _up(a.remainder+b.remainder+a.change*b.change),
        'rotation' if a.structure==b.structure=='rotation' else 'contraction')


def matrix_vector(a,b):
    if not isinstance(a,Matrix) or not isinstance(b,Value) or b.center.shape!=(3,):raise ValueError('structural matrix and vector bounds required')
    return Value(a.center@b.center,_up(a.change*b.norm+b.change),_up(a.remainder*b.norm+b.remainder+a.change*b.change))


def exponential(angle):
    if not isinstance(angle,Value) or angle.center.shape!=(3,):raise ValueError('bounded rotation vector required')
    return Matrix(exp(angle.center),_up(min(2.,angle.change)),_up(.5*angle.change**2+angle.remainder),'rotation')


def _skew(a):
    x,y,z=a;return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])


def inverse_skew(a):
    if not isinstance(a,Value) or a.center.shape!=(3,):raise ValueError('bounded skew argument required')
    center=np.linalg.solve(np.eye(3)+_skew(a.center),np.eye(3))
    return Matrix(center,_up(min(2.,a.change)),_up(a.change**2+a.remainder),'contraction')


def _cayley(a,b):
    return Matrix(2.*b.center-np.eye(3),_up(min(2.,2.*a.change)),_up(2.*a.change**2+2.*a.remainder),'rotation')


def cayley(a):return _cayley(a,inverse_skew(a))


def standard_field(latitude):
    if not isinstance(latitude,Value) or latitude.center.shape!=() or abs(float(latitude.center))+latitude.change>=math.pi/2-1e-6:
        raise ValueError('global latitude region outside supported domain')
    phi=float(latitude.center)
    return Value(OMEGA*np.array([math.cos(phi),0.,-math.sin(phi)]),
        _up(min(2.*OMEGA,OMEGA*latitude.change)),_up(.5*OMEGA*latitude.change**2+OMEGA*latitude.remainder))


def local_bound(*,model,attitude,velocity,theta,dv,latitude,transport,removal,gravity,dt):
    if model not in ('sphere_rotating','sphere_still','flat_still'):raise ValueError('supported physical candidate required')
    if not isinstance(attitude,Matrix) or attitude.structure!='rotation':raise ValueError('globally orthogonal attitude bound required')
    for value in (velocity,theta,dv,transport):
        if not isinstance(value,Value) or value.center.shape!=(3,):raise ValueError('all vector input bounds required')
    for value in (removal,gravity):
        if not isinstance(value,Value) or value.center.shape!=():raise ValueError('scalar physical bounds required')
    if (float(removal.center)-removal.change<0. or float(removal.center)+removal.change>1.
            or float(gravity.center)-gravity.change<=0. or not math.isfinite(dt) or dt<=0.):
        raise ValueError('valid complete removal/gravity region and fixed positive duration required')
    standard=standard_field(latitude);earth=standard if model=='sphere_rotating' else Value(np.zeros(3))
    win=add(add(earth,transport),scale(scalar_product(removal,standard),-1.))
    a=scale(add(scale(earth,2.),transport),dt/2.)
    middle=matrix_product(matrix_product(exponential(scale(win,-dt/2.)),attitude),exponential(scale(theta,.5)))
    next_attitude=matrix_product(matrix_product(exponential(scale(win,-dt)),attitude),exponential(theta))
    force=matrix_vector(middle,dv)
    gravity_vector=Value([0.,0.,float(gravity.center)],gravity.change,gravity.remainder)
    rhs=add(force,scale(gravity_vector,dt));inverse=inverse_skew(a)
    next_velocity=add(matrix_vector(_cayley(a,inverse),velocity),matrix_vector(inverse,rhs))
    displacement=scale(add(velocity,next_velocity),dt/2.)
    return dict(version=VERSION,attitude=next_attitude,velocity=next_velocity,local_displacement=displacement,
        context=dict(standard_background=standard,physical_background=earth,win=win,coriolis_argument=a),
        scope='midpoint_local_step_given_global_inputs',native_full_map_covered=False,
        floating_point_enclosure_verified=False,scientific_decision='abstain')
