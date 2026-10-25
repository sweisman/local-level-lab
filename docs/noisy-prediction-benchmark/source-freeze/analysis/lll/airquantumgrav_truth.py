# SPDX-License-Identifier: AGPL-3.0-or-later
"""Analytic generated aircraft geometry, independent of navigation code.

No observed recording, instrument calibration or estimated attitude enters this
software truth. NumPy is imported only when a numerical calculation is requested.
"""
import math

MODELS=('sphere_rotating','sphere_still','flat_still')
A=6378137.
F=1/298.257223563
E2=F*(2-F)
DISC_RADIUS=6371000.
FIELD_RATE=7.292115e-5
GRAVITY=9.81
PATTERNS=dict(slow=((.12,120.),(.03,90.),(.06,60.)),
              fast=((.25,25.),(.08,13.),(.15,9.)))


def _skew(v):
    import numpy as np
    result=np.zeros((len(v),3,3));x,y,z=v.T
    result[:,0,1]=-z;result[:,0,2]=y;result[:,1,0]=z
    result[:,1,2]=-x;result[:,2,0]=-y;result[:,2,1]=x
    return result


def _body(angles):
    import numpy as np
    yaw,pitch,roll=angles.T;cy,sy=np.cos(yaw),np.sin(yaw)
    cp,sp=np.cos(pitch),np.sin(pitch);cr,sr=np.cos(roll),np.sin(roll)
    zero=np.zeros(len(angles));one=np.ones(len(angles))
    rx=np.stack((one,zero,zero,zero,cr,-sr,zero,sr,cr),axis=1).reshape(-1,3,3)
    ry=np.stack((cp,zero,sp,zero,one,zero,-sp,zero,cp),axis=1).reshape(-1,3,3)
    rz=np.stack((cy,-sy,zero,sy,cy,zero,zero,zero,one),axis=1).reshape(-1,3,3)
    return rz@ry@rx


def truth(model,times,*,latitude_deg,pattern,removal,height_profile=None,gravity_model='constant'):
    """Return positions, derivative channels and body rates from fixed geometry.

    The acceleration equation uses the declared effective downward gravity and
    fixed-frame Coriolis term. A common conventional-field removal changes only
    the simulated logged gyro channels, including for the zero-field candidates.
    """
    import numpy as np
    t=np.asarray(times,dtype=float)
    if (model not in MODELS or pattern not in (*PATTERNS,'stationary')
            or t.ndim!=1 or not len(t) or not np.all(np.isfinite(t))
            or not math.isfinite(latitude_deg) or not -80<=latitude_deg<=80
            or not math.isfinite(removal) or not 0<=removal<=1
            or height_profile not in (None,'climb','descend')
            or gravity_model not in ('constant','inverse_square_height')
            or (height_profile is not None and pattern=='stationary')
            or (gravity_model!='constant' and height_profile is None)):
        raise ValueError('declared model/pattern and finite generated times, latitude and removal required')
    n=len(t);p0=math.radians(latitude_deg);zero=np.zeros(n)
    if pattern=='stationary':
        phi=np.full(n,p0);longitude=np.full(n,math.radians(-40.));height=np.full(n,600.)
        pd,ld,hd,pdd,ldd,hdd=(zero.copy() for _ in range(6))
        angles=np.tile([math.pi/2,0.,0.],(n,1));angle_rates=np.zeros((n,3))
    else:
        kp,kl,kh=(2*math.pi/v for v in (300.,180.,240.))
        amplitude=8/(A*kp);base=75/(A*math.cos(p0))
        if height_profile=='descend':amplitude=-amplitude
        phi=p0+amplitude*np.sin(kp*t);pd=amplitude*kp*np.cos(kp*t);pdd=-amplitude*kp*kp*np.sin(kp*t)
        longitude=math.radians(-40.)+base*(t+.1*np.sin(kl*t)/kl)
        ld=base*(1+.1*np.cos(kl*t));ldd=-base*.1*kl*np.sin(kl*t)
        height=600+10*np.sin(kh*t);hd=10*kh*np.cos(kh*t);hdd=-10*kh*kh*np.sin(kh*t)
        if height_profile is not None:
            sign=-1. if height_profile=='climb' else 1.;k=math.pi/1200.
            height=2500.+sign*1000.*np.cos(k*t)
            hd=-sign*1000.*k*np.sin(k*t);hdd=-sign*1000.*k*k*np.cos(k*t)
        angles=[];angle_rates=[]
        for amplitude,period in PATTERNS[pattern]:
            k=2*math.pi/period;angles.append(amplitude*np.sin(k*t));angle_rates.append(amplitude*k*np.cos(k*t))
        angles=np.column_stack(angles);angles[:,0]+=math.pi/2;angle_rates=np.column_stack(angle_rates)
    sp,cp=np.sin(phi),np.cos(phi);sl,cl=np.sin(longitude),np.cos(longitude)
    er=np.column_stack((cl,sl,zero));et=np.column_stack((-sl,cl,zero))
    if model.startswith('sphere'):
        q=1-E2*sp*sp;qd=-2*E2*sp*cp*pd
        qdd=-2*E2*((cp*cp-sp*sp)*pd*pd+sp*cp*pdd)
        rn=A/q**.5;rd=-A*.5*qd/q**1.5;rdd=A*.75*qd*qd/q**2.5-A*.5*qdd/q**1.5
        radial=(rn+height)*cp
        radial_d=(rd+hd)*cp-(rn+height)*sp*pd
        radial_dd=(rdd+hdd)*cp-2*(rd+hd)*sp*pd-(rn+height)*(cp*pd*pd+sp*pdd)
        vertical=(rn*(1-E2)+height)*sp
        vertical_d=(rd*(1-E2)+hd)*sp+(rn*(1-E2)+height)*cp*pd
        vertical_dd=((rdd*(1-E2)+hdd)*sp+2*(rd*(1-E2)+hd)*cp*pd
            +(rn*(1-E2)+height)*(-sp*pd*pd+cp*pdd))
        north=np.column_stack((-sp*cl,-sp*sl,cp));east=et
        down=np.column_stack((-cp*cl,-cp*sl,-sp))
        north_d=np.column_stack((-cp*pd*cl+sp*sl*ld,-cp*pd*sl-sp*cl*ld,-sp*pd))
        east_d=np.column_stack((-cl*ld,-sl*ld,zero))
        down_d=np.column_stack((sp*pd*cl+cp*sl*ld,sp*pd*sl-cp*cl*ld,-cp*pd))
    else:
        radial=DISC_RADIUS*(math.pi/2-phi);radial_d=-DISC_RADIUS*pd;radial_dd=-DISC_RADIUS*pdd
        vertical,vertical_d,vertical_dd=height,hd,hdd
        north=-er;east=et;down=np.tile([0.,0.,-1.],(n,1))
        north_d=-et*ld[:,None];east_d=-er*ld[:,None];down_d=np.zeros((n,3))
    position=radial[:,None]*er;position[:,2]=vertical
    velocity=radial_d[:,None]*er+(radial*ld)[:,None]*et;velocity[:,2]=vertical_d
    acceleration=(radial_dd-radial*ld*ld)[:,None]*er+(2*radial_d*ld+radial*ldd)[:,None]*et
    acceleration[:,2]=vertical_dd
    local=np.stack((north,east,down),axis=2);local_d=np.stack((north_d,east_d,down_d),axis=2)
    body=_body(angles);roll=angles[:,2];pitch=angles[:,1];yaw_d,pitch_d,roll_d=angle_rates.T
    relative=np.column_stack((roll_d-yaw_d*np.sin(pitch),
        pitch_d*np.cos(roll)+yaw_d*np.sin(roll)*np.cos(pitch),
        -pitch_d*np.sin(roll)+yaw_d*np.cos(roll)*np.cos(pitch)))
    axes=local@body;axes_d=local_d@body+axes@_skew(relative)
    generator=axes.swapaxes(1,2)@axes_d
    angular=np.column_stack((generator[:,2,1]-generator[:,1,2],
        generator[:,0,2]-generator[:,2,0],generator[:,1,0]-generator[:,0,1]))/2
    world_field=np.array([0.,0.,FIELD_RATE if model=='sphere_rotating' else 0.])
    angular+=np.einsum('nji,j->ni',axes,world_field)
    conventional=FIELD_RATE*np.column_stack((cp,zero,-sp))
    angular-=removal*np.einsum('nji,nj->ni',body,conventional)
    if gravity_model=='constant':required=acceleration+2*np.cross(world_field,velocity)-GRAVITY*down
    else:
        anchor=1500. if height_profile=='climb' else 3500.
        magnitude=GRAVITY/(1+(height-anchor)/(DISC_RADIUS+anchor))**2
        required=acceleration+2*np.cross(world_field,velocity)-magnitude[:,None]*down
    force=np.einsum('nji,nj->ni',axes,required)
    return dict(coordinates=np.column_stack((phi,longitude,height)),
        coordinate_rates=np.column_stack((pd,ld,hd)),position_world_m=position,
        velocity_world_mps=velocity,acceleration_world_mps2=acceleration,
        velocity_local_mps=np.einsum('nji,nj->ni',local,velocity),
        attitude_body_to_local=body,body_axes_world=axes,body_axes_derivative_per_s=axes_d,
        angular_rate_rads=angular,specific_force_mps2=force)
