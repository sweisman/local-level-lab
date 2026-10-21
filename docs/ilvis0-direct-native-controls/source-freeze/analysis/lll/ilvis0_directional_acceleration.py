# SPDX-License-Identifier: AGPL-3.0-or-later
"""Immutable physical-domain acceleration range with original shared errors."""
from dataclasses import dataclass
from fractions import Fraction as F
import hashlib,json,math
from .ilvis0_directional_force import calibrated_force,action
from .ilvis0_exact_scale import sqrt_upper
from .ilvis0_saved_prediction_audit import endpoint
from .ilvis0_transform_native import TransformReference


def _digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True,init=False)
class DirectionalAcceleration:
    binding:str
    reference_binding:str
    source_id:str
    norm_change:float
    component_changes:tuple
    original_remainder:float
    lower:tuple
    upper:tuple
    reference_digest:str
    acceleration_lower:tuple
    acceleration_upper:tuple
    numerical_margin:float

    def __init__(self,reference,lower,upper,*,numerical_margin=1e-10):
        if (not isinstance(reference,TransformReference) or len(lower)!=27 or len(upper)!=27
                or any(not math.isfinite(v) for v in list(lower)+list(upper))
                or not math.isfinite(numerical_margin) or numerical_margin<0):
            raise ValueError('typed full reference, finite physical domain and nonnegative margin required')
        r=reference.parent;a=reference.acceleration
        if any(not x<=p<=q<=y for x,p,q,y in zip(r.lower,lower,upper,r.upper,strict=True)):
            raise ValueError('contained physical domain required')
        lo=[F(float(v))*F(float(x)) for v,x in zip(r.limits,lower)]
        hi=[F(float(v))*F(float(x)) for v,x in zip(r.limits,upper)]
        flo,fhi=calibrated_force(a.raw_delta_v.tolist(),a.period,
            list(map(list,zip(lo[12:15],hi[12:15]))),list(map(list,zip(lo[18:21],hi[18:21]))))
        bounds=action(lo[:3],hi[:3],flo,fhi,installation=r.initial_r.tolist())
        left=list(map(F,bounds['lower']));right=list(map(F,bounds['upper']));margin=F(numerical_margin)
        left[2]+=F(a.gravity)+lo[24];right[2]+=F(a.gravity)+hi[24]
        left=[x-margin for x in left];right=[x+margin for x in right]
        changes=[max(abs(x-F(float(c))),abs(y-F(float(c)))) for x,y,c in zip(left,right,a.center)]
        components=tuple(endpoint(v,True) for v in changes)
        radius=sqrt_upper(sum((F(v)**2 for v in components),F(0)))
        source=reference.report();reference_digest=_digest(source)
        definition=dict(reference=source,lower=list(map(float,lower)),upper=list(map(float,upper)),
            numerical_margin=numerical_margin,acceleration_lower=list(map(str,left)),acceleration_upper=list(map(str,right)))
        values=dict(binding=_digest(definition),reference_binding=reference.binding,source_id=r.source_id,
            norm_change=radius,component_changes=components,original_remainder=a.remainder,
            lower=tuple(map(float,lower)),upper=tuple(map(float,upper)),reference_digest=reference_digest,
            acceleration_lower=tuple(map(str,left)),acceleration_upper=tuple(map(str,right)),numerical_margin=float(numerical_margin))
        for name,value in values.items():object.__setattr__(self,name,value)

    def match(self,reference_report,lower,upper):
        if _digest(reference_report)!=self.reference_digest:raise ValueError('directional reference mismatch')
        if tuple(lower)!=self.lower or tuple(upper)!=self.upper:raise ValueError('directional physical domain mismatch')
        return self.norm_change,self.component_changes

    def report(self):
        return dict(version='ilvis0-physical-directional-acceleration-v1',binding=self.binding,
            reference_binding=self.reference_binding,source_id=self.source_id,physical_parameter_count=27,
            norm_change=self.norm_change,component_changes=list(self.component_changes),
            original_remainder=self.original_remainder,lower=list(self.lower),upper=list(self.upper),
            acceleration_lower=list(self.acceleration_lower),acceleration_upper=list(self.acceleration_upper),
            numerical_margin_mps2=self.numerical_margin,uses_training_data=False,
            preserves_shared_remainders=True,applies_only_to_physical_domain=True,
            native_propagation_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')
