# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate trained-source candidate with explicit arithmetic reconciliation.

Physical norm closure precedes conversion to numerical reference centers and
arbitrary supplied rows. No frozen implementation or shared column is changed.
The training-transfer interpretation still requires its finite qualification.
"""
from fractions import Fraction as F
import numpy as np
from .ilvis0_transform_native import TransformReference
from .ilvis0_conditioned_acceleration import ConditionedAcceleration
from .ilvis0_directional_acceleration import DirectionalAcceleration
from .ilvis0_initial_source_bridge_v2 import certify
from .ilvis0_source_value_stream import SourceBox
from .ilvis0_rotation_interval import vertical_interval
from .ilvis0_source_reference import affine_radius
from .ilvis0_compiled_transport import Value,backend
from .ilvis0_body_interval import BodyBound
from .ilvis0_saved_prediction_audit import endpoint

VERSION='ilvis0-rounded-trained-body-interval-v2'


class RoundedBodyInterval:
    def __init__(self,reference,conditioning,lower,upper):
        if not isinstance(reference,TransformReference) or not isinstance(conditioning,(ConditionedAcceleration,DirectionalAcceleration)):
            raise ValueError('typed reference and verified conditioning required')
        self.lower=tuple(map(float,lower));self.upper=tuple(map(float,upper))
        if len(self.lower)!=27 or len(self.upper)!=27 or any(not a<=x<=y<=b for a,x,y,b in zip(
                conditioning.lower,self.lower,self.upper,conditioning.upper,strict=True)):
            raise ValueError('domain must be contained in verified conditioning')
        _,components=conditioning.match(reference.report(),conditioning.lower,conditioning.upper)
        bridge=certify(reference,self.lower,self.upper)
        if not bridge['nonlinear_cap_sufficient']:
            raise ValueError('initial source nonlinear cap is insufficient; no expansion permitted')
        self.reference=reference;self.conditioning=conditioning;self.padding=tuple(F(v) for v in bridge['padding'])
        self.bridge=bridge;self.components=tuple(F(v) for v in components)
        self.center=tuple(map(float,reference.parent.center))

    def bound(self,proof,frame,*,phase,centers=None):
        if type(phase) is not int or phase not in (0,1) or not isinstance(proof,SourceBox) or proof.phase!=phase:
            raise ValueError('matching source packet phase required')
        r=self.reference.parent
        if (proof.reference_binding!=self.reference.binding or proof.source_id!=r.source_id
                or proof.lower!=self.lower or proof.upper!=self.upper):
            raise ValueError('source/reference/domain identity mismatch')
        if any(frame.get(name)!=getattr(proof,name) for name in ('packet_index','packet_start_s','packet_end_s')):
            raise ValueError('source prefix reference mismatch')
        if frame.get('query_time_s')!=proof.nominal_time_s+float(r.limits[25]*r.center[25]):
            raise ValueError('source clock reference mismatch')
        values=np.asarray(frame.get('values'),float);jac=np.asarray(frame.get('jacobian'),float)
        if values.shape!=(2,2,3) or jac.shape!=(2,2,3,27) or not np.all(np.isfinite(values)) or not np.all(np.isfinite(jac)):
            raise ValueError('two complete finite source phases and all 27 reference rows required')
        nominal=values[phase];rows=jac[phase]
        for value,observed in zip((proof.a,proof.b),nominal,strict=True):
            for c,v,d in zip(value.center,observed,value.component_change,strict=True):
                if abs(F(float(c))-F(float(v)))>F(float(d)):
                    raise ValueError('source nominal reference is outside its arithmetic certificate')
        centers=nominal if centers is None else np.asarray(centers,float)
        if centers.shape!=(2,3) or not np.all(np.isfinite(centers)):raise ValueError('two finite stated source centers required')
        alo,ahi=proof.interval('a');alo=list(alo);ahi=list(ahi)
        a=self.reference.acceleration;limits=r.limits
        for axis in range(3):
            low=F(float(a.center[axis]))-self.components[axis]-self.padding[axis]
            high=F(float(a.center[axis]))+self.components[axis]+self.padding[axis]
            if axis==2:
                low-=F(a.gravity)+F(float(limits[24]))*F(self.upper[24])
                high-=F(a.gravity)+F(float(limits[24]))*F(self.lower[24])
            alo[axis]=max(alo[axis],low);ahi[axis]=min(ahi[axis],high)
            if alo[axis]>ahi[axis]:raise ValueError('training and physical source intervals contradict')
        blo,bhi=proof.interval('b');blo=list(blo);bhi=list(bhi)
        closure=vertical_interval(alo,ahi,blo,bhi,norm_identity=True,norm_error=proof.norm_error)
        blo[2]=F(closure['combined_lower']);bhi[2]=F(closure['combined_upper'])
        bounded=[]
        for source,(lo,hi) in enumerate(((alo,ahi),(blo,bhi))):
            changes=[];remainders=[]
            for axis in range(3):
                bound=affine_radius(lo[axis],hi[axis],float(centers[source,axis]),rows[source,axis],
                    self.lower,self.upper,self.center)
                alias=abs(F(float(nominal[source,axis]))-F(float(centers[source,axis])))
                changes.append(endpoint(max(F(bound['value_radius']),alias),True))
                remainders.append(endpoint(max(F(bound['affine_radius']),alias),True))
            bounded.append(Value(centers[source],backend().norm(changes),backend().norm(remainders),
                component_change=changes,component_remainder=remainders))
        rows=np.array(rows,copy=True);rows.setflags(write=False)
        details=dict(version=VERSION,reference_binding=self.reference.binding,source_id=r.source_id,
            parent_conditioning_binding=self.conditioning.binding,lower=self.lower,upper=self.upper,
            packet_index=proof.packet_index,phase=phase,explicit_rounding_bridge=True,
            initial_source_padding=[str(v) for v in self.padding],initial_source_bridge=self.bridge,
            physical_norm_closure=closure,baseline_body_taylor_remainder_reused=False,
            physical_parameter_count=27,shared_columns_changed=False,training_adapter_qualified=False,
            native_propagation_qualified=False,observational_coverage_qualified=False)
        return BodyBound(bounded[0],bounded[1],rows,details)
