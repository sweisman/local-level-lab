# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known synthetic sensor errors and antenna geometry, without navigation code.

Values here define software fixtures, not ESA device specifications or an
estimator. Recorded channels and fused navigation never enter this module.
"""
import math

from lll.airquantumgrav_truth import A,E2,DISC_RADIUS,GRAVITY,MODELS


def _check(case,sign):
    import numpy as np
    if type(sign) is not int or sign not in (-1,1):
        raise ValueError('one of the two declared calibration signs required')
    shapes=dict(coordinates=(3,),velocity_local_mps=(3,),attitude_body_to_local=(3,3),
        position_world_m=(3,),body_axes_world=(3,3),angular_rate_rads=(3,),specific_force_mps2=(3,))
    n=len(case.get('coordinates',[]))
    if not n:raise ValueError('nonempty independent geometric truth required')
    for name,shape in shapes.items():
        value=np.asarray(case.get(name),float)
        if value.shape!=(n,*shape) or not np.all(np.isfinite(value)):
            raise ValueError('aligned finite independent geometric channels required')


def _parameters(sign):
    vectors=dict(attitude=(.002,-.003,.004),velocity=(.1,-.2,.15),
        gyro_bias=tuple(math.radians(v)/3600 for v in (.15,-.2,.25)),
        accel_bias=(.01,-.02,.015),gyro_gain=(.002,-.0015,.001),
        accel_gain=(.003,-.002,.004),lever=(1.5,-.7,.4))
    result={name+'_'+axis:sign*v for name,values in vectors.items() for axis,v in zip('xyz',values)}
    result.update(gravity_delta=sign*.01,time_offset=sign*.0007)
    return result


def observe(case,*,sign):
    """Apply a known affine sensor error to engineering-unit rate samples."""
    import numpy as np
    _check(case,sign);p=_parameters(sign)
    vector=lambda name:np.array([p[name+'_'+a] for a in 'xyz'])
    return dict(angular_rate_rads=np.asarray(case['angular_rate_rads'])*(1+vector('gyro_gain'))+vector('gyro_bias'),
        specific_force_mps2=np.asarray(case['specific_force_mps2'])*(1+vector('accel_gain'))+vector('accel_bias'),
        generated_not_observed=True)


def antenna(case,*,sign):
    """Move the answer point in Cartesian space, independently of coordinate rates."""
    import numpy as np
    _check(case,sign);lever=sign*np.array([1.5,-.7,.4]);answer=dict(case)
    answer['position_world_m']=np.asarray(case['position_world_m'])+np.einsum('nij,j->ni',case['body_axes_world'],lever)
    return answer


def receiver_coordinates(position_world_m,*,model):
    """Convert independent Cartesian antenna truth to receiver coordinates.

    This inverse uses ellipsoid normal geometry, never a navigation prediction.
    It creates generated receiver samples only; it repairs no recorded data.
    """
    import numpy as np
    xyz=np.asarray(position_world_m,float)
    if (model not in MODELS or xyz.ndim!=2 or xyz.shape[1:]!=(3,) or not len(xyz)
            or not np.all(np.isfinite(xyz))):
        raise ValueError('finite nonempty Cartesian points and declared geometry required')
    x,y,z=xyz.T;rho=np.hypot(x,y)
    if np.any(rho<=0):raise ValueError('nonpolar nonzero horizontal position required')
    longitude=np.arctan2(y,x)
    if model=='flat_still':
        phi=math.pi/2-rho/DISC_RADIUS;height=z.copy()
        if np.any(abs(phi)>=math.pi/2):raise ValueError('Cartesian point outside the declared disc coordinate domain')
    else:
        phi=np.arctan2(z,rho*(1-E2))
        for _ in range(20):
            radius=A/np.sqrt(1-E2*np.sin(phi)**2)
            following=np.arctan2(z+E2*radius*np.sin(phi),rho)
            difference=float(np.max(abs(following-phi)));phi=following
            if difference<=2e-15:break
        else:raise ValueError('independent ellipsoid inversion did not converge')
        height=rho*np.cos(phi)+z*np.sin(phi)-A*np.sqrt(1-E2*np.sin(phi)**2)
    result=np.column_stack((phi,longitude,height))
    if not np.all(np.isfinite(result)):raise ValueError('finite generated receiver coordinates required')
    return result


def receiver_samples(model,times,*,latitude_deg,pattern,removal,sign,height_profile=None,gravity_model='constant'):
    """Generate just the requested receiver observations, including antenna latency.

    No true starting state or correction vector is returned to the estimator.
    Caller-owned construction accounting must precede this numerical operation.
    """
    import numpy as np
    from lll.airquantumgrav_truth import truth
    if type(sign) is not int or sign not in (-1,1):raise ValueError('declared calibration sign required')
    case=truth(model,np.asarray(times,float)+_parameters(sign)['time_offset'],
        latitude_deg=latitude_deg,pattern=pattern,removal=removal,height_profile=height_profile,gravity_model=gravity_model)
    answer=antenna(case,sign=sign)
    answer['coordinates']=receiver_coordinates(answer['position_world_m'],model=model)
    return {k:answer[k] for k in ('coordinates','position_world_m','body_axes_world','attitude_body_to_local')}


def start(case,*,model,sign):
    """Give a perturbed starting state and its exact declared correction vector.

    Supplying this vector checks application, not recovery from observations.
    The local metric is derived from the independent geometric definition.
    """
    import numpy as np
    _check(case,sign)
    if model not in MODELS:raise ValueError('declared generating geometry required')
    p=_parameters(sign);true=np.asarray(case['coordinates'][0]);base=true+sign*np.array([.5e-6,-.4e-6,2.])
    phi,h=base[0],base[2]
    if model=='flat_still':mn,me=DISC_RADIUS,DISC_RADIUS*(math.pi/2-phi)
    else:
        q=1-E2*math.sin(phi)**2;mn=A*(1-E2)/q**1.5+h;me=(A/math.sqrt(q)+h)*math.cos(phi)
    for axis,value in zip('xyz',(true-base)*[mn,me,-1.]):p['position_'+axis]=float(value)
    rotation_vector=-np.array([p['attitude_'+a] for a in 'xyz']);angle=float(np.linalg.norm(rotation_vector))
    x,y,z=rotation_vector;cross=np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
    undo=np.eye(3)+math.sin(angle)/angle*cross+(1-math.cos(angle))/angle**2*(cross@cross)
    initial=dict(latitude_rad=float(base[0]),longitude_rad=float(base[1]),height_m=float(base[2]),
        velocity_ned_mps=np.asarray(case['velocity_local_mps'][0])-[p['velocity_'+a] for a in 'xyz'],
        attitude_body_to_ned=np.asarray(case['attitude_body_to_local'][0])@undo)
    return dict(initial=initial,parameters=p,gravity_mps2=GRAVITY-p['gravity_delta'],
        corrections_supplied_not_fitted=True,generated_not_observed=True)
