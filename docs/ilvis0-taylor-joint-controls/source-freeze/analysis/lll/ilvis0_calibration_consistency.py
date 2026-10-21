# SPDX-License-Identifier: AGPL-3.0-or-later
"""Necessary coupling of existing acceleration and force-matrix remainders.

The exact identity supplies six additional inequalities, not physical bounds
or additional observations. Mathematical export rounding is outward; this is
not a certificate for every floating-point operation in the native predictor.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
import json
import math
import numpy as np
from .ilvis0_shared_reference_terms import _norm,_readonly,_upper
from .ilvis0_reference_acceleration import AccelerationTerms
from .ilvis0_common_force_transform import ForceTransform

VERSION='ilvis0-calibration-consistency-v1'


def _matrix_product(a,b):
    return [[sum((a[i][k]*b[k][j] for k in range(3)),F(0)) for j in range(3)] for i in range(3)]


def rotation_polynomial(vector):
    """Exact degree-40 exponential polynomial and an operator-norm tail.

    For skew(v), ||skew(v)||_2=||v||_2. The factorial tail is bounded by
    its first omitted term times a geometric series of decreasing ratios.
    No floating-point sine, cosine or matrix exponential is used here.
    """
    if len(vector)!=3:raise ValueError('three finite rotation coordinates required')
    x,y,z=[F(v) for v in vector];a=F(_norm((x,y,z)))
    if a>8:raise ValueError('rotation polynomial supports norm at most eight radians')
    k=[[F(0),-z,y],[z,F(0),-x],[-y,x,F(0)]]
    term=[[F(int(i==j)) for j in range(3)] for i in range(3)]
    result=[row[:] for row in term]
    for n in range(1,41):
        term=[[v/n for v in row] for row in _matrix_product(term,k)]
        result=[[result[i][j]+term[i][j] for j in range(3)] for i in range(3)]
    tail=a**41/F(math.factorial(41))/(1-a/42)
    return result,tail


@dataclass(frozen=True)
class ConsistencyCuts:
    design:object
    upper:object
    binding:str
    source_id:str
    acceleration_binding:str
    transform_binding:str
    product_allowance:float
    metadata:dict

    def __post_init__(self):
        a=np.asarray(self.design,float);b=np.asarray(self.upper,float)
        if a.shape!=(6,51) or b.shape!=(6,) or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
            raise ValueError('six finite complete consistency inequalities required')
        object.__setattr__(self,'design',_readonly(a));object.__setattr__(self,'upper',_readonly(b))

    def report(self):
        return dict(version=VERSION,design=self.design.tolist(),upper=self.upper.tolist(),
            binding=self.binding,source_id=self.source_id,acceleration_binding=self.acceleration_binding,
            transform_binding=self.transform_binding,product_allowance=self.product_allowance,
            metadata=self.metadata,parameter_count=51,physical_parameter_count=27,
            new_observations=0,native_evaluations=0,observational_coverage_qualified=False,
            floating_point_enclosure_verified=False,scientific_decision='abstain')


def build(acceleration,transform):
    if (not isinstance(acceleration,AccelerationTerms) or not isinstance(transform,ForceTransform)
            or acceleration.reference.binding!=transform.reference.binding):
        raise ValueError('complete acceleration/matrix components must share a reference')
    r=transform.reference;lim=[F(float(v)) for v in r.limits];z=[F(float(v)) for v in r.center]
    lower=[F(float(v)) for v in r.lower];upper=[F(float(v)) for v in r.upper]
    p=[a*b for a,b in zip(lim,z)]
    lo=[a*b for a,b in zip(lim,lower)];hi=[a*b for a,b in zip(lim,upper)]
    if any(v<=-1 for v in lo[18:21]):raise ValueError('positive reciprocal-gain domain required')
    f=[F(float(v))/F(acceleration.period)-p[12+j] for j,v in enumerate(acceleration.raw_delta_v)]
    mc=[[F(float(v)) for v in row] for row in transform.center]
    jm=[[[F(float(v)) for v in col] for col in row] for row in transform.jacobian]
    ja=[[F(float(v)) for v in row] for row in acceleration.jacobian]
    initial=[[F(float(v)) for v in row] for row in r.initial_r]
    initial_norm=F(_norm(v for row in initial for v in row))
    polynomial,tail=rotation_polynomial(p[:3]);rotation=_matrix_product(initial,polynomial)
    angle=F(_norm(lim[j]*max(z[j]-lower[j],upper[j]-z[j]) for j in range(3)))
    changes=[]
    for k in range(3):
        dc=1/(1+p[18+k]);dl=1/(1+lo[18+k]);dh=1/(1+hi[18+k])
        offset=F(_norm(rotation[i][k]*dc-mc[i][k] for i in range(3)))+initial_norm*abs(dc)*tail
        changes.append(initial_norm*(min(F(2),angle)*abs(dc)+max(abs(dl-dc),abs(dh-dc)))+offset)
    bias_change=[lim[12+j]*max(z[12+j]-lower[12+j],upper[12+j]-z[12+j]) for j in range(3)]
    product=sum((a*b for a,b in zip(changes,bias_change)),F(0))
    all_lower=lower+[F(-1)]*24;all_upper=upper+[F(1)]*24
    rows=[];bounds=[];centres=[];linear_errors=[];exports=[]
    for i in range(3):
        d0=sum((mc[i][k]*f[k] for k in range(3)),F(0))
        if i==2:d0+=F(acceleration.gravity)+p[24]
        d0-=F(float(acceleration.center[i]));centres.append(str(d0))
        linear=[sum((jm[i][k][j]*f[k] for k in range(3)),F(0))-ja[i][j]
            -(mc[i][j-12]*lim[j] if 12<=j<15 else F(0))
            +(lim[24] if i==2 and j==24 else F(0)) for j in range(27)]
        linear_errors.append([str(v) for v in linear])
        row=[-v for v in linear]+[F(0)]*24
        row[39+i]=F(float(acceleration.caps[6+i]))
        for k in range(3):row[42+3*i+k]=-F(float(transform.caps[3*i+k]))*f[k]
        origin=d0-sum((a*b for a,b in zip(linear,z)),F(0))
        # This extra, explicitly reported relaxation also retains the exact
        # zero-error convention of the existing point-domain components.
        radius=product+abs(d0)
        for sign in (1,-1):
            exact=[sign*v for v in row];binary=[float(v) for v in exact]
            export=sum(((F(v)-q)*(b if F(v)>=q else a)
                for v,q,a,b in zip(binary,exact,all_lower,all_upper)),F(0))
            rows.append(binary);bounds.append(_upper(sign*origin+radius+export));exports.append(str(export))
    definition=dict(version=VERSION,reference=r.binding,acceleration=acceleration.binding,
        transform=transform.binding,design=rows,upper=bounds)
    binding=hashlib.sha256(json.dumps(definition,sort_keys=True,allow_nan=False).encode()).hexdigest()
    return ConsistencyCuts(rows,bounds,binding,r.source_id,acceleration.binding,transform.binding,_upper(product),
        dict(column_change_bounds=[str(v) for v in changes],bias_change_bounds=[str(v) for v in bias_change],
            exact_product_allowance=str(product),rotation_polynomial_degree=40,rotation_tail=str(tail),
            exact_centre_mismatches=centres,exact_linear_mismatches=linear_errors,
            exact_export_allowances=exports,centre_relaxation='absolute exact centre mismatch',
            reference_binding=r.binding,lower=r.lower.tolist(),upper=r.upper.tolist()))


def exact_slacks(cuts,point):
    x=np.asarray(point,float)
    if not isinstance(cuts,ConsistencyCuts) or x.shape!=(51,) or not np.all(np.isfinite(x)):
        raise ValueError('complete consistency cuts and finite 51-vector required')
    return tuple(sum((F(float(a))*F(float(b)) for a,b in zip(row,x)),F(0))-F(float(bound))
        for row,bound in zip(cuts.design,cuts.upper))
