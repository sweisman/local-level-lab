# SPDX-License-Identifier: AGPL-3.0-or-later
"""Intersect trained source bounds with separately derived mean-value radii.

Reference values, rows and training certificates are retained. This candidate
requires native qualification; its component tests are not observational
coverage or a whole-program floating-point proof.
"""
from dataclasses import dataclass,fields
import numpy as np
from .ilvis0_batched_source_values import SourceBox,SourceValueStream as Values
from .ilvis0_batched_body_interval import RoundedBodyInterval as Previous
from .ilvis0_batched_transport import Value,backend
from .ilvis0_body_interval import BodyBound
from .ilvis0_source_derivative_intervals import Stream,mean_value_radius


@dataclass(frozen=True)
class TaylorSourceBox(SourceBox):
    derivative_frame:object


class SourceTaylorStream(Values):
    def __init__(self,case,reference,lower,upper,time_s,*,maximum_packets,derivative_kernel):
        super().__init__(case,reference,lower,upper,time_s,maximum_packets=maximum_packets)
        owned=dict(configuration=case['configuration'],theta=self.theta,dv=self.dv,dt=self.dt)
        self.derivatives=Stream(derivative_kernel,owned,reference.parent.center,lower,upper,time_s,
            maximum_packets=maximum_packets)

    def append(self):
        physical=super().append();derivative=self.derivatives.append()
        if physical['packet_index']!=derivative['packet_index']:raise ValueError('derivative and physical prefixes differ')
        phases=tuple(TaylorSourceBox(**{field.name:getattr(proof,field.name) for field in fields(SourceBox)},
            derivative_frame=derivative) for proof in physical['phases'])
        return dict(physical,phases=phases,source_derivative_steps=self.derivatives.visits)

    def close(self):
        super().close()
        if hasattr(self,'derivatives'):self.derivatives.close()


class TaylorBodyInterval(Previous):
    def bound(self,proof,frame,*,phase,centers=None):
        if not isinstance(proof,TaylorSourceBox):raise ValueError('bound source derivative certificate required')
        derivative=proof.derivative_frame
        if (derivative['packet_index']!=proof.packet_index or derivative['lower']!=self.lower
                or derivative['upper']!=self.upper or derivative['center']!=self.center):
            raise ValueError('derivative source/domain/reference mismatch')
        previous=super().bound(proof,frame,phase=phase,centers=centers)
        numerical=np.array(frame['values'],copy=True)
        if centers is not None:numerical[phase]=centers
        remainder=mean_value_radius(derivative,numerical,frame['jacobian'],phase=phase)
        bounded=[]
        for source,value in enumerate((previous.a,previous.b)):
            component=np.minimum(value.component_remainder,remainder[source])
            bounded.append(Value(value.center,value.change,min(value.remainder,backend().norm(component)),
                component_change=value.component_change,component_remainder=component))
        details=dict(previous.details,source_mean_value_interval_installed=True,
            source_derivative_parameter_count=27,source_derivative_state_bytes=derivative['state_bytes'],
            baseline_body_taylor_remainder_reused=False)
        return BodyBound(bounded[0],bounded[1],previous.jacobian,details)
