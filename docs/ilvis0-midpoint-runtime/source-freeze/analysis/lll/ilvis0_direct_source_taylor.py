# SPDX-License-Identifier: AGPL-3.0-or-later
"""Intersect the existing valid source radii with a direct reference remainder."""
from dataclasses import dataclass,fields
import numpy as np
from .ilvis0_dyadic_source_taylor import TaylorSourceBox,SourceTaylorStream,TaylorBodyInterval
from .ilvis0_direct_source import DirectStream,radius
from .ilvis0_batched_transport import Value,backend
from .ilvis0_body_interval import BodyBound


@dataclass(frozen=True)
class DirectSourceBox(TaylorSourceBox):
    direct_frame:object


class SourceDirectStream(SourceTaylorStream):
    def __init__(self,case,reference,lower,upper,time_s,*,maximum_packets,derivative_kernel,point_kernel):
        super().__init__(case,reference,lower,upper,time_s,maximum_packets=maximum_packets,
            derivative_kernel=derivative_kernel)
        owned=dict(configuration=case['configuration'],theta=self.theta,dv=self.dv,dt=self.dt)
        self.direct=DirectStream(point_kernel,owned,reference.parent.center,lower,upper,time_s,
            maximum_packets=maximum_packets)

    def append(self):
        physical=super().append();direct=self.direct.append()
        if physical['packet_index']!=direct.packet_index:raise ValueError('direct and physical source prefixes differ')
        phases=tuple(DirectSourceBox(**{field.name:getattr(proof,field.name) for field in fields(TaylorSourceBox)},
            direct_frame=direct) for proof in physical['phases'])
        return dict(physical,phases=phases,source_direct_steps=self.direct.visits)

    def close(self):
        super().close()
        if hasattr(self,'direct'):self.direct.close()


class DirectBodyInterval(TaylorBodyInterval):
    def __init__(self,reference,conditioning,lower,upper,*,direct_source_binding):
        super().__init__(reference,conditioning,lower,upper)
        if not isinstance(direct_source_binding,str) or len(direct_source_binding)!=64:
            raise ValueError('complete direct-source binding required')
        self.direct_source_binding=direct_source_binding

    def bound(self,proof,frame,*,phase,centers=None):
        if not isinstance(proof,DirectSourceBox):raise ValueError('typed direct source certificate required')
        direct=proof.direct_frame
        if (direct.source_binding!=self.direct_source_binding or direct.packet_index!=proof.packet_index
                or direct.center!=self.center or direct.lower!=self.lower or direct.upper!=self.upper
                or direct.nominal_time_s!=proof.nominal_time_s or direct.packet_start_s!=proof.packet_start_s
                or direct.packet_end_s!=proof.packet_end_s):
            raise ValueError('direct source/reference/domain/clock mismatch')
        previous=super().bound(proof,frame,phase=phase,centers=centers)
        numerical=np.array(frame['values'],copy=True)
        if centers is not None:numerical[phase]=centers
        remainder=radius(direct,numerical,frame['jacobian'],phase=phase);bounded=[]
        for component,value in enumerate((previous.a,previous.b)):
            parts=np.minimum(value.component_remainder,remainder[component])
            bounded.append(Value(value.center,value.change,min(value.remainder,backend().norm(parts)),
                component_change=value.component_change,component_remainder=parts))
        details=dict(previous.details,source_direct_remainder_installed=True,
            direct_source_binding=direct.source_binding,source_point_state_bytes=direct.state_bytes,
            source_direct_parameter_count=27)
        return BodyBound(bounded[0],bounded[1],previous.jacobian,details)
