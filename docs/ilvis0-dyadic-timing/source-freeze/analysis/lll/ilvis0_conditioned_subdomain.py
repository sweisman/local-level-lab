# SPDX-License-Identifier: AGPL-3.0-or-later
"""Restrict a verified training bound without recomputing or weakening it.

Every feasible child calibration must satisfy all parent inequalities and box
bounds in the same first 51 coordinates. The remaining 27 lifted coordinates
cannot change those inherited inequalities. No optimization or new supports.
"""
from collections import Counter
from dataclasses import dataclass,fields
import math
from .ilvis0_conditioned_acceleration import ConditionedAcceleration,_digest

VERSION='ilvis0-conditioned-acceleration-subdomain-v1'


def _box(region,n):
    if (region.get('parameter_count')!=n or any(len(region.get(key,[]))!=n for key in ('lower','upper','center'))
            or any(not math.isfinite(value) for key in ('lower','upper','center') for value in region[key])
            or any(a>b for a,b in zip(region['lower'],region['upper'],strict=True))):
        raise ValueError('complete finite ordered calibration coordinates required')


def _rows(region,n,extension=0):
    design=region.get('inequality_design',[]);upper=region.get('inequality_upper',[])
    if (len(design)!=len(upper) or any(len(row)!=n for row in design)
            or any(not math.isfinite(value) for row in design for value in row)
            or any(not math.isfinite(value) for value in upper)):
        raise ValueError('complete finite calibration inequalities required')
    return Counter((tuple(row)+tuple([0.]*extension),value) for row,value in zip(design,upper,strict=True))


@dataclass(frozen=True,init=False)
class SubdomainAcceleration(ConditionedAcceleration):
    parent_input_binding:str
    child_training_binding:str
    inherited_constraint_count:int

    def __init__(self,parent,parent_input,child_training,lower,upper):
        if type(parent) is not ConditionedAcceleration or _digest(parent_input)!=parent.binding:
            raise ValueError('exact verified parent input and root certificate required')
        before=parent_input['training']['region'];after=child_training['region']
        _box(before,51);_box(after,78)
        if (len(lower)!=27 or len(upper)!=27 or list(lower)!=after['lower'][:27] or list(upper)!=after['upper'][:27]
                or after.get('future_truth_used') is not False
                or after['center'][:51]!=before['center']
                or child_training.get('reference')!=parent_input['reference']):
            raise ValueError('unchanged reference, complete child domain and training-only center required')
        for key in ('source_id','binding','force_source_id','coordinate_scale','origin','design','times_s','physical_parameter_count'):
            if before.get(key)!=after.get(key):raise ValueError('parent calibration basis or frame changed: '+key)
        for key in ('times_s','observations','nominal','jacobian','reference'):
            if key in parent_input['training'] and child_training.get(key)!=parent_input['training'][key]:
                raise ValueError('parent training observations changed: '+key)
        if any(not a<=c<=d<=b for a,b,c,d in zip(parent_input['lower'],parent_input['upper'],
                after['lower'][:51],after['upper'][:51],strict=True)):
            raise ValueError('child box escapes the verified parent domain')
        inherited=_rows(before,51,27);actual=_rows(after,78)
        if any(actual[row]<count for row,count in inherited.items()):
            raise ValueError('a necessary parent inequality was removed, changed or loosened')
        child_binding=_digest(child_training)
        definition=dict(parent=parent.report(),parent_input_binding=parent.binding,
            child_training_binding=child_binding,lower=list(lower),upper=list(upper))
        for field in fields(ConditionedAcceleration):object.__setattr__(self,field.name,getattr(parent,field.name))
        for name,value in dict(binding=_digest(definition),lower=tuple(lower),upper=tuple(upper),
                parent_input_binding=parent.binding,child_training_binding=child_binding,
                inherited_constraint_count=sum(inherited.values())).items():
            object.__setattr__(self,name,value)

    def match_training(self,training):
        if _digest(training)!=self.child_training_binding:raise ValueError('restricted training region changed')

    def report(self):
        return dict(super().report(),version=VERSION,parent_input_binding=self.parent_input_binding,
            child_training_binding=self.child_training_binding,lower=list(self.lower),upper=list(self.upper),
            inherited_constraint_count=self.inherited_constraint_count,
            parent_exact_supports_verified=self.supports_verified,additional_exact_supports=0,
            inherited_bounds_unchanged=True,source_domain_restriction_verified=True)
