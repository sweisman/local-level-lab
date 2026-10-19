# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent Cartesian mathematical controls, not simulated flight evidence.

Reference truth uses no production coordinate, force or navigation function.
Second-order scalar jets differentiate the Cartesian geometry directly.
"""
import math

import numpy as np

MODELS = ('sphere_rotating', 'sphere_still', 'flat_still')
BACKGROUND = 7.292115e-5
GRAVITY = 9.81
RADIUS = 6371000.

_BASE = dict(phi=.55,longitude=.2,height=1200.,p=0.,l=0.,h=0.,pp=0.,ll=0.,hh=0.)
PROFILES = {
    'stationary':dict(_BASE),
    'slow':dict(_BASE,phi=-.9,p=1e-6,l=1e-6),
    'eastbound':dict(_BASE,phi=.65,l=4e-5),
    'northbound':dict(_BASE,phi=-1.1,p=3.5e-5),
    'changing_direction':dict(_BASE,phi=.8,p=2e-5,l=3e-5,pp=-1e-7,ll=8e-8),
    'climbing':dict(_BASE,phi=-.9,p=3e-5,l=-2e-5,h=2.,pp=2e-8,ll=-3e-8,hh=.02),
}


class Jet:
    def __init__(self,value,first=0.,second=0.):
        self.v,self.d,self.dd=float(value),float(first),float(second)

    @staticmethod
    def cast(value):
        return value if isinstance(value,Jet) else Jet(value)

    def __add__(self,other):
        other=self.cast(other)
        return Jet(self.v+other.v,self.d+other.d,self.dd+other.dd)

    __radd__=__add__

    def __neg__(self):return Jet(-self.v,-self.d,-self.dd)
    def __sub__(self,other):return self+-self.cast(other)
    def __rsub__(self,other):return self.cast(other)+-self

    def __mul__(self,other):
        other=self.cast(other)
        return Jet(self.v*other.v,self.d*other.v+self.v*other.d,
                   self.dd*other.v+2*self.d*other.d+self.v*other.dd)

    __rmul__=__mul__

    def power(self,exponent):
        return Jet(self.v**exponent,exponent*self.v**(exponent-1)*self.d,
            exponent*(exponent-1)*self.v**(exponent-2)*self.d**2
            +exponent*self.v**(exponent-1)*self.dd)

    def sin(self):
        return Jet(math.sin(self.v),math.cos(self.v)*self.d,
                   math.cos(self.v)*self.dd-math.sin(self.v)*self.d**2)

    def cos(self):
        return Jet(math.cos(self.v),-math.sin(self.v)*self.d,
                   -math.sin(self.v)*self.dd-math.cos(self.v)*self.d**2)


def _rotation(yaw,pitch,roll):
    cy,sy,cp,sp,cr,sr=math.cos(yaw),math.sin(yaw),math.cos(pitch),math.sin(pitch),math.cos(roll),math.sin(roll)
    return np.array([[cy,-sy,0.],[sy,cy,0.],[0.,0.,1.]]) @ np.array(
        [[cp,0.,sp],[0.,1.,0.],[-sp,0.,cp]]) @ np.array([[1.,0.,0.],[0.,cr,-sr],[0.,sr,cr]])


def reference(model,profile,time_s):
    if model not in MODELS:raise ValueError('unsupported control model')
    def coordinate(value,rate,second):
        return Jet(value+rate*time_s+.5*second*time_s**2,rate+second*time_s,second)
    phi=coordinate(profile['phi'],profile['p'],profile['pp'])
    lam=coordinate(profile['longitude'],profile['l'],profile['ll'])
    height=coordinate(profile['height'],profile['h'],profile['hh'])
    sp,cp,sl,cl=phi.sin(),phi.cos(),lam.sin(),lam.cos()
    if model=='flat_still':
        radius=RADIUS*(math.pi/2-phi)
        position=[radius*cl,radius*sl,height]
        frame=[[-cl,-sl,Jet(0.)],[-sl,cl,Jet(0.)],[Jet(0.),Jet(0.),Jet(-1.)]]
    else:
        # Constants are copied from the declared geometry, not imported from the adapter.
        prime=6378137.*(1.-6.69437999014e-3*sp*sp).power(-.5)
        position=[(prime+height)*cp*cl,(prime+height)*cp*sl,
                  (prime*(1.-6.69437999014e-3)+height)*sp]
        frame=[[-sp*cl,-sl,-cp*cl],[-sp*sl,cl,-cp*sl],[cp,Jet(0.),-sp]]
    # Frame columns map NED into fixed Cartesian axes. Differentiate the frame
    # independently rather than obtaining transport from a geographic formula.
    q=np.array([[x.v for x in row] for row in frame])
    qdot=np.array([[x.d for x in row] for row in frame])
    cartesian_velocity=np.array([x.d for x in position])
    cartesian_acceleration=np.array([x.dd for x in position])
    velocity=q.T@cartesian_velocity
    acceleration=qdot.T@cartesian_velocity+q.T@cartesian_acceleration
    spin=q.T@qdot
    transport=np.array([spin[2,1]-spin[1,2],spin[0,2]-spin[2,0],spin[1,0]-spin[0,1]])/2
    omega=np.array([0.,0.,BACKGROUND if model=='sphere_rotating' else 0.])
    # With apparent gravity, the centrifugal term is already in gravity.
    # Cartesian relative acceleration + Coriolis avoids double-counting it.
    force=q.T@(cartesian_acceleration+2*np.cross(omega,cartesian_velocity))-np.array([0.,0.,GRAVITY])
    rotations=[_rotation(.1+.03*time_s,.04*math.sin(time_s/4),.02*math.cos(time_s/3)),
               _rotation(.8-.02*time_s,-.07+.02*math.sin(time_s/5),.2)]
    return dict(coordinates=np.array([phi.v,lam.v,height.v]),rate=np.array([phi.d,lam.d,height.d]),
        second=np.array([phi.dd,lam.dd,height.dd]),velocity=velocity,acceleration=acceleration,
        transport=transport,force=force,body_forces=[r.T@force for r in rotations])
