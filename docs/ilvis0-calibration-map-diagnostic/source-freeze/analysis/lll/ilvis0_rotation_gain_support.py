# SPDX-License-Identifier: AGPL-3.0-or-later
"""Necessary directional supports of a rotation/reciprocal-gain matrix.

Exact coefficient algebra and outward exports qualify these mathematical
constraints, not whole-program floating-point or observational coverage.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
import itertools
import json
import numpy as np
from .ilvis0_shared_reference_terms import _readonly, _upper
from .ilvis0_exact_scale import sqrt_upper
from .ilvis0_reference_acceleration import AccelerationTerms
from .ilvis0_common_force_transform import ForceTransform

VERSION = 'ilvis0-rotation-reciprocal-gain-support-v1'


def reciprocal_chord(lower, upper):
    left, right = F(lower), F(upper)
    if left <= -1 or right < left:
        raise ValueError('ordered gain domain strictly above minus one required')
    if left == right:
        return 1/(1+left), F(0)
    beta = -1/((1+left)*(1+right))
    return 1/(1+left)-beta*left, beta


@dataclass(frozen=True)
class RotationGainCuts:
    design: object
    upper: object
    binding: str
    reference_binding: str
    acceleration_binding: str
    transform_binding: str
    source_id: str
    metadata: dict

    def __post_init__(self):
        a = np.asarray(self.design,float); b = np.asarray(self.upper,float)
        if a.shape != (78,51) or b.shape != (78,) or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
            raise ValueError('78 complete finite rotation/gain supports required')
        object.__setattr__(self,'design',_readonly(a)); object.__setattr__(self,'upper',_readonly(b))

    def report(self):
        return dict(version=VERSION,design=self.design.tolist(),upper=self.upper.tolist(),
            binding=self.binding,reference_binding=self.reference_binding,
            acceleration_binding=self.acceleration_binding,transform_binding=self.transform_binding,
            source_id=self.source_id,metadata=self.metadata,physical_parameter_count=27,
            parameter_count=51,new_observations=0,native_evaluations=0,
            floating_point_enclosure_verified=False,observational_coverage_qualified=False,
            scientific_decision='abstain')


def build(acceleration, transform):
    if (not isinstance(acceleration,AccelerationTerms) or not isinstance(transform,ForceTransform)
            or acceleration.reference.binding != transform.reference.binding):
        raise ValueError('typed force/acceleration components with one source required')
    r = transform.reference
    lo = [F(float(v)) for v in r.lower]+[F(-1)]*24
    hi = [F(float(v)) for v in r.upper]+[F(1)]*24
    center = [F(float(v)) for v in r.center]
    limits = [F(float(v)) for v in r.limits]
    initial = [[F(float(v)) for v in row] for row in r.initial_r]
    mc = [[F(float(v)) for v in row] for row in transform.center]
    jm = [[[F(float(v)) for v in col] for col in row] for row in transform.jacobian]
    caps = [F(float(v)) for v in transform.caps]
    directions = [d for d in itertools.product((-1,0,1),repeat=3) if any(d)]
    rows=[]; bounds=[]; descriptions=[]; relaxations=[]; exports=[]
    for column in range(3):
        gain = 18+column
        alpha,beta = reciprocal_chord(limits[gain]*lo[gain],limits[gain]*hi[gain])
        for d in directions:
            q = [F(float(v)) for v in r._r_center@np.array(d,float)]
            initial_transpose_q = [sum((initial[i][j]*q[i] for i in range(3)),F(0)) for j in range(3)]
            h = F(sqrt_upper(sum((v*v for v in initial_transpose_q),F(0))))
            constant = sum((q[i]*mc[i][column] for i in range(3)),F(0))
            linear = [sum((q[i]*jm[i][column][k] for i in range(3)),F(0)) for k in range(27)]
            exact = linear+[F(0)]*24
            exact[gain] -= h*beta*limits[gain]
            for i in range(3):
                exact[42+3*i+column] = q[i]*caps[3*i+column]
            # Preserve the earlier exact-zero remainder convention at the
            # floating expansion center, without asserting it is an exact rotation.
            relaxation = max(F(0),constant-h/(1+limits[gain]*center[gain]))
            upper = h*alpha-constant+sum((a*b for a,b in zip(linear,center)),F(0))+relaxation
            binary = [float(v) for v in exact]
            export = sum(((F(v)-a)*(right if F(v)>=a else left)
                for v,a,left,right in zip(binary,exact,lo,hi)),F(0))
            rows.append(binary); bounds.append(_upper(upper+export))
            relaxations.append(str(relaxation)); exports.append(str(export))
            descriptions.append(dict(column=column,direction=list(d),q=[float(v) for v in q],
                initial_transpose_norm_upper=str(h),chord_alpha=str(alpha),chord_beta=str(beta)))
    metadata = dict(supports=descriptions,center_relaxations=relaxations,
        exact_export_allowances=exports,lower=r.lower.tolist(),upper=r.upper.tolist(),
        derivation='Cauchy-Schwarz for fixed initial matrix and rotation, with exact reciprocal-gain upper chord')
    definition = dict(version=VERSION,reference=r.binding,acceleration=acceleration.binding,
        transform=transform.binding,design=rows,upper=bounds,metadata=metadata)
    binding = hashlib.sha256(json.dumps(definition,sort_keys=True,allow_nan=False).encode()).hexdigest()
    return RotationGainCuts(rows,bounds,binding,r.binding,acceleration.binding,transform.binding,r.source_id,metadata)


def exact_slacks(cuts, point):
    x = np.asarray(point,float)
    if not isinstance(cuts,RotationGainCuts) or x.shape != (51,) or not np.all(np.isfinite(x)):
        raise ValueError('complete rotation/gain supports and finite 51-vector required')
    return tuple(sum((F(float(v))*F(float(w)) for v,w in zip(row,x) if v),F(0))-F(float(b))
        for row,b in zip(cuts.design,cuts.upper))
