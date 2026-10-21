# SPDX-License-Identifier: AGPL-3.0-or-later
"""Necessary matrix supports retaining the declared orientation domain."""
from fractions import Fraction as F
import hashlib
import itertools
import json
import numpy as np
from .ilvis0_rotation_gain_support import RotationGainCuts,reciprocal_chord,exact_slacks
from .ilvis0_calibration_consistency import rotation_polynomial
from .ilvis0_exact_scale import sqrt_upper
from .ilvis0_shared_reference_terms import _upper
from .ilvis0_reference_acceleration import AccelerationTerms
from .ilvis0_common_force_transform import ForceTransform

VERSION='ilvis0-orientation-constrained-gain-support-v1'


def _norm(values):return F(sqrt_upper(sum((v*v for v in values),F(0))))


def gain_upper(support,lower,upper,center):
    h,left,right,c=map(F,(support,lower,upper,center))
    a,b=reciprocal_chord(left,right)
    if not left<=c<=right:raise ValueError('gain center must remain in its original interval')
    if h>=0:return h*a,h*b,'chord'
    value=1/(1+c);slope=-value*value
    return h*(value-slope*c),h*slope,'tangent'


def orientation_upper(vector,polynomial_column,tail,distance):
    u=tuple(map(F,vector));p=tuple(map(F,polynomial_column));t=F(tail);d=F(distance)
    if len(u)!=3 or len(p)!=3 or t<0 or not 0<=d<=2:raise ValueError('three-vectors and nonnegative bounded allowances required')
    length=_norm(u);a=sum((v*w for v,w in zip(u,p)),F(0));error=length*t
    transverse=_norm(v-a*w for v,w in zip(u,p))+t*(length+abs(a))
    bound=a+error+(abs(a)+error)*d*d/2+transverse*d
    return min(length,bound)


class OrientationGainCuts(RotationGainCuts):
    def report(self):return dict(super().report(),version=VERSION)


def build(acceleration,transform):
    if (not isinstance(acceleration,AccelerationTerms) or not isinstance(transform,ForceTransform)
            or acceleration.reference.binding!=transform.reference.binding):
        raise ValueError('typed acceleration/matrix components with one source required')
    r=transform.reference
    lo=[F(float(v)) for v in r.lower]+[F(-1)]*24
    hi=[F(float(v)) for v in r.upper]+[F(1)]*24
    z=[F(float(v)) for v in r.center];lim=[F(float(v)) for v in r.limits]
    initial=[[F(float(v)) for v in row] for row in r.initial_r]
    mc=[[F(float(v)) for v in row] for row in transform.center]
    jm=[[[F(float(v)) for v in col] for col in row] for row in transform.jacobian]
    caps=[F(float(v)) for v in transform.caps]
    polynomial,tail=rotation_polynomial([lim[j]*z[j] for j in range(3)])
    distance=min(F(2),_norm(lim[j]*max(z[j]-lo[j],hi[j]-z[j]) for j in range(3)))
    directions=[v for v in itertools.product((-1,0,1),repeat=3) if any(v)]
    rows=[];bounds=[];descriptions=[];relaxations=[];exports=[]
    for column in range(3):
        gain=18+column
        for direction in directions:
            q=[F(float(v)) for v in r._r_center@np.array(direction,float)]
            u=[sum((initial[i][j]*q[i] for i in range(3)),F(0)) for j in range(3)]
            h=orientation_upper(u,[polynomial[i][column] for i in range(3)],tail,distance)
            alpha,beta,kind=gain_upper(h,lim[gain]*lo[gain],lim[gain]*hi[gain],lim[gain]*z[gain])
            constant=sum((q[i]*mc[i][column] for i in range(3)),F(0))
            linear=[sum((q[i]*jm[i][column][k] for i in range(3)),F(0)) for k in range(27)]
            exact=linear+[F(0)]*24;exact[gain]-=beta*lim[gain]
            for i in range(3):exact[42+3*i+column]=q[i]*caps[3*i+column]
            relaxation=max(F(0),constant-h/(1+lim[gain]*z[gain]))
            right=alpha-constant+sum((a*b for a,b in zip(linear,z)),F(0))+relaxation
            binary=[float(v) for v in exact]
            export=sum(((F(v)-a)*(b if F(v)>=a else left)
                for v,a,left,b in zip(binary,exact,lo,hi)),F(0))
            rows.append(binary);bounds.append(_upper(right+export))
            relaxations.append(str(relaxation));exports.append(str(export))
            descriptions.append(dict(column=column,direction=list(direction),q=[float(v) for v in q],
                signed_support=str(h),gain_intercept=str(alpha),gain_slope=str(beta),gain_bound=kind))
    metadata=dict(supports=descriptions,center_relaxations=relaxations,exact_export_allowances=exports,
        lower=r.lower.tolist(),upper=r.upper.tolist(),distance_upper=str(distance),
        polynomial_degree=40,polynomial_tail=str(tail),
        derivation='unit-vector distance identity, source orientation domain and signed reciprocal chord/tangent')
    definition=dict(version=VERSION,reference=r.binding,acceleration=acceleration.binding,
        transform=transform.binding,design=rows,upper=bounds,metadata=metadata)
    binding=hashlib.sha256(json.dumps(definition,sort_keys=True,allow_nan=False).encode()).hexdigest()
    return OrientationGainCuts(rows,bounds,binding,r.binding,acceleration.binding,transform.binding,r.source_id,metadata)
