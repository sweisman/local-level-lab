# SPDX-License-Identifier: AGPL-3.0-or-later
"""Immutable, independently checked acceleration bound for one training region.

No optimization, future observations, or known truth. This consumes a supplied
certificate; its physical assumptions and whole-program roundoff remain open.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
import json


def _digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True,init=False)
class ConditionedAcceleration:
    binding:str
    region_binding:str
    reference_binding:str
    source_id:str
    norm_change:float
    component_changes:tuple
    original_remainder:float
    lower:tuple
    upper:tuple
    reference_digest:str
    supports_verified:int

    def __init__(self,bundle,certificate,*,reserve):
        from lll.ilvis0_acceleration_projection import _validate
        from lll.ilvis0_saved_prediction_audit import support,endpoint
        from lll.ilvis0_exact_scale import sqrt_upper
        region,acc=_validate(**bundle)
        if (certificate.get('version')!='ilvis0-training-acceleration-projection-v1'
                or certificate.get('input_binding')!=_digest(bundle)
                or certificate.get('parameter_count')!=51
                or certificate.get('region_binding')!=region['binding']
                or certificate.get('acceleration_binding')!=acc['binding']
                or certificate.get('source_id')!=region['source_id']
                or len(certificate.get('axes',[]))!=3):
            raise ValueError('complete acceleration certificate/source identity required')
        reserve(6)  # six independent exact support checks, charged before execution
        changes=[]
        for i,axis in enumerate(certificate['axes']):
            objective=list(acc['jacobian'][i])+[0.]*24;objective[39+i]=acc['caps'][6+i]
            shift=F(acc['center'][i])-sum((F(a)*F(z) for a,z in zip(objective[:27],region['center'][:27])),F(0))
            if (axis.get('axis')!=i or axis.get('objective')!=objective or F(axis['shift'])!=shift
                    or len(axis.get('certificates',[]))!=2):
                raise ValueError('acceleration coefficient or shift mismatch')
            values=[]
            for sign,cert in zip((1,-1),axis['certificates']):
                if cert.get('sign')!=sign:raise ValueError('signed support mismatch')
                value=support(bundle['lower'],bundle['upper'],region['inequality_design'],
                    region['inequality_upper'],[sign*v for v in objective],cert['multipliers'])
                if value!=F(cert['exact_upper']):raise ValueError('exact acceleration support mismatch')
                values.append(value)
            low=shift-values[1];high=shift+values[0]
            if low>high or F(axis['exact_lower'])!=low or F(axis['exact_upper'])!=high:
                raise ValueError('exact acceleration endpoints mismatch')
            left=endpoint(low,False);right=endpoint(high,True)
            change=endpoint(max(abs(F(left)-F(acc['center'][i])),abs(F(right)-F(acc['center'][i]))),True)
            if axis['lower']!=left or axis['upper']!=right or axis['change']!=change:
                raise ValueError('outward acceleration change mismatch')
            changes.append(change)
        radius=sqrt_upper(sum((F(v)**2 for v in changes),F(0)))
        if radius!=certificate['norm_change'] or certificate['source_norm_change']!=acc['change']:
            raise ValueError('acceleration radius mismatch')
        values=dict(binding=certificate['input_binding'],region_binding=region['binding'],
            reference_binding=bundle['reference']['binding'],source_id=region['source_id'],
            norm_change=radius,component_changes=tuple(changes),original_remainder=acc['remainder'],
            lower=tuple(bundle['lower'][:27]),upper=tuple(bundle['upper'][:27]),
            reference_digest=_digest(bundle['reference']),supports_verified=6)
        for name,value in values.items():object.__setattr__(self,name,value)

    def match(self,reference_report,lower,upper):
        if _digest(reference_report)!=self.reference_digest:raise ValueError('conditioned reference mismatch')
        if tuple(lower)!=self.lower or tuple(upper)!=self.upper:raise ValueError('conditioned physical domain mismatch')
        return self.norm_change,self.component_changes

    def report(self):
        return dict(version='ilvis0-verified-training-acceleration-v1',input_binding=self.binding,
            region_binding=self.region_binding,reference_binding=self.reference_binding,source_id=self.source_id,
            norm_change=self.norm_change,component_changes=list(self.component_changes),
            original_remainder=self.original_remainder,supports_verified=self.supports_verified,
            applies_only_to_training_region=True,global_physical_box_bound=False,
            prediction_method_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')
