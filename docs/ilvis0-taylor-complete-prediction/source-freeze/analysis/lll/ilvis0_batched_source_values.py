# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prefix-specific physical source values with explicit reference arithmetic.

The source is the ideal calibrated rotation map on the declared physical box.
No training range, coefficient row or old Taylor radius is substituted for a
physical value interval. Whole-program native roundoff and coverage are separate.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import math
import numpy as np
from .ilvis0_transform_native import TransformReference
from .ilvis0_shared_native import _data
from .ilvis0_forward import exp
from .ilvis0_batched_transport import Value,backend,scalar_product,scale,matrix_vector
from .ilvis0_batched_relative import Delta,multiply,plus
from .ilvis0_calibration_roundoff import enclose as calibration
from .ilvis0_rotation_roundoff import enclose as rotation_reference
from .ilvis0_exact_scale import sqrt_upper
from .ilvis0_saved_prediction_audit import endpoint

VERSION='ilvis0-physical-source-value-stream-v1'


def _up(value):return endpoint(F(value),True)


def _box_value(center,lower,upper):
    center=np.asarray(center,float)
    shape=center.shape
    values=np.asarray([_up(max(abs(F(float(c))-lo),abs(hi-F(float(c)))))
        for c,lo,hi in zip(center.reshape(-1),lower,upper,strict=True)]).reshape(shape)
    radius=backend().norm(values)
    # Zero is the implicit affine row in this value-only calculation.
    return Value(center,radius,radius,component_change=values,component_remainder=values)


def _rotation(angle):
    center=exp(angle.center)
    certificate=rotation_reference(angle.center,center)
    radius=_up(min(F(2),F(angle.change))+F(certificate['norm_error']))
    return Delta(center,radius,radius)


@dataclass(frozen=True)
class SourceBox:
    a:Value
    b:Value
    reference_binding:str
    source_id:str
    lower:tuple
    upper:tuple
    nominal_time_s:float
    packet_index:int
    packet_start_s:float
    packet_end_s:float
    phase:int
    norm_error:F

    def interval(self,source):
        if source not in ('a','b'):raise ValueError('source A or B required')
        value=getattr(self,source)
        return tuple(F(float(c))-F(float(d)) for c,d in zip(value.center,value.component_change,strict=True)),tuple(
            F(float(c))+F(float(d)) for c,d in zip(value.center,value.component_change,strict=True))

    def report(self):
        return dict(version=VERSION,reference_binding=self.reference_binding,source_id=self.source_id,
            lower=self.lower,upper=self.upper,nominal_time_s=self.nominal_time_s,
            packet_index=self.packet_index,packet_start_s=self.packet_start_s,packet_end_s=self.packet_end_s,
            phase=self.phase,norm_error=str(self.norm_error),physical_parameter_count=27,
            physical_value_intervals=True,affine_reference_rows_supplied=False,
            training_conditioning_installed=False,whole_native_rounding_qualified=False,
            native_propagation_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')


class SourceValueStream:
    def __init__(self,case,reference,lower,upper,time_s,*,maximum_packets):
        if not isinstance(reference,TransformReference):raise ValueError('typed source reference required')
        (theta,dv,dt),source=_data(case['configuration'],case['theta'],case['dv'],case['dt'])
        if source!=reference.parent.source_id:raise ValueError('source/reference identity mismatch')
        lower=np.asarray(lower,float);upper=np.asarray(upper,float);r=reference.parent
        if (lower.shape!=(27,) or upper.shape!=(27,) or not np.all(np.isfinite(lower))
                or not np.all(np.isfinite(upper)) or np.any(lower>upper)
                or np.any(lower<r.lower) or np.any(upper>r.upper)
                or not math.isfinite(time_s) or type(maximum_packets) is not int
                or not 0<maximum_packets<=len(dt)):
            raise ValueError('contained source domain and finite packet allowance required')
        self.theta=np.array(theta,copy=True);self.dv=np.array(dv,copy=True);self.dt=np.array(dt,copy=True)
        for array in (self.theta,self.dv,self.dt):array.setflags(write=False)
        self.reference=reference;self.lower=tuple(lower);self.upper=tuple(upper);self.time_s=float(time_s)
        self.maximum_packets=maximum_packets;self.visits=0;self.elapsed=0.;self.closed=False
        self.p=r.limits*r.center
        self.p.setflags(write=False)
        self.physical_center=tuple(F(float(v))*F(float(z)) for v,z in zip(r.limits,r.center,strict=True))
        self.plo=tuple(F(float(v))*F(float(min(lo,z))) for v,lo,z in zip(r.limits,lower,r.center,strict=True))
        self.phi=tuple(F(float(v))*F(float(max(hi,z))) for v,hi,z in zip(r.limits,upper,r.center,strict=True))
        self.query_lower=F(time_s)+self.plo[25];self.query_upper=F(time_s)+self.phi[25]
        if self.query_lower<0 or self.query_upper>F(float(sum(self.dt))):
            raise ValueError('complete source clock domain outside packet support')
        self.nominal_query=float(time_s+self.p[25])
        self.mount=multiply(Delta(r.initial_r),_rotation(_box_value(self.p[:3],self.plo[:3],self.phi[:3])))
        self.body=Delta(np.eye(3))
        self.force,force_certificate=self._correct(self.dv[0],float(self.dt[0]),12,18,as_rate=True)
        self.a=matrix_vector(self.mount,self.force)
        initial=[[F(float(v)) for v in row] for row in r.initial_r]
        gram=[[sum((initial[k][i]*initial[k][j] for k in range(3)),F(0))-int(i==j)
            for j in range(3)] for i in range(3)]
        defect=F(sqrt_upper(sum((v*v for row in gram for v in row),F(0))))
        norm_squared=sum((max(abs(F(lo)),abs(F(hi)))**2 for lo,hi in zip(
            force_certificate['lower'],force_certificate['upper'],strict=True)),F(0))
        self.norm_error=2*defect*norm_squared

    def _correct(self,raw,period,bias,gain,*,as_rate=False):
        center=(raw-self.p[bias:bias+3]*period)/(1+self.p[gain:gain+3])
        if as_rate:center=center/period
        certificate=calibration(raw,period,bias_center=self.physical_center[bias:bias+3],
            gain_center=self.physical_center[gain:gain+3],bias_lower=self.plo[bias:bias+3],bias_upper=self.phi[bias:bias+3],
            gain_lower=self.plo[gain:gain+3],gain_upper=self.phi[gain:gain+3],center=center,as_rate=as_rate)
        d=certificate['component_change'];radius=certificate['change']
        return Value(center,radius,radius,component_change=d,component_remainder=d),certificate

    def append(self):
        if self.closed:raise ValueError('source stream is closed')
        if self.visits>=self.maximum_packets:raise ValueError('source packet allowance exhausted')
        index=self.visits;self.visits+=1;start=self.elapsed;period=float(self.dt[index]);end=start+period
        if not math.isfinite(end) or end<=start:raise ValueError('nonincreasing source packet clock')
        clip=lambda value:max(F(0),min(F(1),value))
        low=clip((self.query_lower-F(start))/F(period));high=clip((self.query_upper-F(start))/F(period))
        nominal=max(0.,min(1.,(self.nominal_query-start)/period))
        fraction=_box_value(nominal,[low],[high])
        corrected,_=self._correct(self.theta[index],period,9,15)
        angle=scalar_product(fraction,corrected);phases=[]
        for phase,factor in enumerate((.5,1.)):
            body=multiply(self.body,_rotation(scale(angle,factor)))
            departure=plus(body,Delta(-np.eye(3)))
            b=matrix_vector(multiply(self.mount,departure),self.force)
            phases.append(SourceBox(self.a,b,self.reference.binding,self.reference.parent.source_id,
                self.lower,self.upper,self.time_s,index,start,end,phase,self.norm_error))
        self.body=body;self.elapsed=end
        return dict(packet_index=index,phases=tuple(phases),reserved_source_steps=2,
            physical_value_intervals=True,whole_native_rounding_qualified=False)

    def close(self):self.closed=True
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
