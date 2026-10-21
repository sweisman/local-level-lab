# SPDX-License-Identifier: AGPL-3.0-or-later
"""Outer polytope for source-qualified Euclidean shared-error blocks.

Repeated component caps are insufficient provenance. This component accepts
only the known typed constructions whose defining bounds are vector norms.
Physical bounds, column count and observation/error assumptions are unchanged.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
import itertools
import json
import numpy as np
from .ilvis0_exact_scale import sqrt_upper
from .ilvis0_shared_reference_terms import _readonly,_norm
from .ilvis0_reference_acceleration import AccelerationTerms
from .ilvis0_common_force_transform import ForceTransform

VERSION='ilvis0-shared-error-vector-norms-v1'


@dataclass(frozen=True)
class NormCuts:
    design:object
    upper:object
    blocks:tuple
    binding:str
    reference_binding:str
    acceleration_binding:str
    transform_binding:str
    source_id:str

    def __post_init__(self):
        a=np.asarray(self.design,float);b=np.asarray(self.upper,float)
        if (a.shape!=(26*len(self.blocks),51) or not len(self.blocks) or b.shape!=(len(a),)
                or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)) or np.any(b<0)):
            raise ValueError('complete finite source-qualified norm constraints required')
        object.__setattr__(self,'design',_readonly(a));object.__setattr__(self,'upper',_readonly(b))

    def report(self):
        return dict(version=VERSION,design=self.design.tolist(),upper=self.upper.tolist(),blocks=list(self.blocks),
            binding=self.binding,reference_binding=self.reference_binding,acceleration_binding=self.acceleration_binding,
            transform_binding=self.transform_binding,source_id=self.source_id,parameter_count=51,
            physical_parameter_count=27,new_observations=0,native_evaluations=0,
            floating_point_enclosure_verified=False,observational_coverage_qualified=False,scientific_decision='abstain')


def build(acceleration,transform,*,block_names=None):
    if (not isinstance(acceleration,AccelerationTerms) or not isinstance(transform,ForceTransform)
            or acceleration.reference.binding!=transform.reference.binding):
        raise ValueError('typed acceleration/matrix norm derivations with one reference required')
    r=transform.reference;a=acceleration;m=transform
    # These formula checks bind the acceleration norm interpretation to its
    # actual constructor, rather than treating arbitrary equal caps as a ball.
    dt=max(abs(F(float(r.lower[25]))-F(float(r.center[25]))),
        abs(F(float(r.upper[25]))-F(float(r.center[25]))))*F(float(r.limits[25]))
    norm_center=F(_norm(F(float(v)) for v in a.center))
    required=[(norm_center+F(a.change))*dt*dt/2,F(a.change)*dt,F(a.remainder)]
    for group,minimum in zip((a.caps[:3],a.caps[3:6],a.caps[6:9]),required):
        if not all(F(float(v))==F(float(group[0])) and F(float(v))>=minimum for v in group):
            raise ValueError('acceleration constructor vector-norm caps changed')
    definitions=[('initial-lever',[30,31,32],r.caps[3:],
        'operator rotation Taylor remainder times lever norm plus rotation change times lever-change norm'),
        ('acceleration-clock-square',[33,34,35],a.caps[:3],
        'half acceleration norm times squared common clock displacement'),
        ('acceleration-clock-linear',[36,37,38],a.caps[3:6],
        'acceleration-change Euclidean norm times common clock displacement'),
        ('acceleration-taylor',[39,40,41],a.caps[6:9],
        'matrix-vector Taylor remainder in Euclidean norm')]
    for col,label in enumerate(('x','y','z')):
        definitions.append(('force-column-'+label,[42+col,45+col,48+col],m.caps.reshape(3,3)[:,col],
            'Euclidean remainder of rotation acting on one reciprocal-gain basis vector'))
    names=[v[0] for v in definitions]
    selected=names if block_names is None else list(block_names)
    if not selected or len(set(selected))!=len(selected) or any(v not in names for v in selected):
        raise ValueError('only declared vector-norm blocks are supported; velocity-clock is componentwise')
    blocks=[];rows=[];bounds=[]
    directions=[d for d in itertools.product((-1,0,1),repeat=3) if any(d)]
    for name,indices,caps,proof in definitions:
        if name not in selected:continue
        if not np.all(np.isfinite(caps)) or np.any(np.asarray(caps)<0) or not np.all(caps==caps[0]):
            raise ValueError('qualified equal normalization for this vector block required')
        zero=bool(caps[0]==0)
        blocks.append(dict(name=name,indices=indices,cap=float(caps[0]),norm='Euclidean',
            derivation=proof,normalization='zero cap maps to zero' if zero else 'divide vector by its Euclidean cap'))
        for d in directions:
            row=np.zeros(51);row[indices]=d
            rows.append(row.tolist());bounds.append(0. if zero else sqrt_upper(sum((F(v*v) for v in d),F(0))))
    definition=dict(version=VERSION,reference=r.binding,acceleration=a.binding,transform=m.binding,
        blocks=blocks,design=rows,upper=bounds)
    binding=hashlib.sha256(json.dumps(definition,sort_keys=True,allow_nan=False).encode()).hexdigest()
    return NormCuts(rows,bounds,tuple(blocks),binding,r.binding,a.binding,m.binding,r.source_id)


def exact_slacks(cuts,point):
    x=np.asarray(point,float)
    if not isinstance(cuts,NormCuts) or x.shape!=(51,) or not np.all(np.isfinite(x)):
        raise ValueError('source-qualified norm cuts and a finite 51-vector required')
    return tuple(sum((F(float(v))*F(float(w)) for v,w in zip(row,x) if v),F(0))-F(float(b))
        for row,b in zip(cuts.design,cuts.upper))
