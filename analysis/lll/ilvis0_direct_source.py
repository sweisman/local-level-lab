# SPDX-License-Identifier: AGPL-3.0-or-later
"""Direct ideal-source remainder with explicit numerical-reference transfer.

Exact rational calibration and rotation-product norm bounds precede the
point-value/derivative enclosure. No training certificate or geographic
integration is supplied here. Native installation requires separate controls.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
import math
import numpy as np
from .ilvis0_source_reference import _inputs
from .ilvis0_source_point_derivatives import Stream as PointStream
from .ilvis0_source_remainder import calibration,clipped_fraction,multiply,force_products
from .ilvis0_exact_scale import sqrt_upper
from .ilvis0_saved_prediction_audit import endpoint

VERSION='ilvis0-direct-source-remainder-v1'


def _norm(values):return F(sqrt_upper(sum((F(v)**2 for v in values),F(0))))


@dataclass(frozen=True)
class DirectFrame:
    source_binding:str
    center:tuple
    lower:tuple
    upper:tuple
    packet_index:int
    packet_start_s:float
    packet_end_s:float
    nominal_time_s:float
    point_values:object
    point_jacobian:object
    ideal_remainder:tuple
    state_bytes:int


class DirectStream:
    def __init__(self,kernel,case,point,lower,upper,time_s,*,maximum_packets):
        dt,theta,dv,initial,limits,z=_inputs(case,point,time_s)
        lo=np.asarray(lower,float);hi=np.asarray(upper,float)
        if (lo.shape!=(27,) or hi.shape!=(27,) or not np.all(np.isfinite(lo)) or not np.all(np.isfinite(hi))
                or np.any(lo>hi) or type(maximum_packets) is not int or not 0<maximum_packets<=len(dt)):
            raise ValueError('finite ordered source domain and explicit packet allowance required')
        self.center=tuple(map(float,z));self.lower=tuple(map(float,lo));self.upper=tuple(map(float,hi))
        self.pc=tuple(F(float(a))*F(float(b)) for a,b in zip(limits,z,strict=True))
        self.plo=tuple(F(float(a))*F(float(min(b,c))) for a,b,c in zip(limits,lo,z,strict=True))
        self.phi=tuple(F(float(a))*F(float(max(b,c))) for a,b,c in zip(limits,hi,z,strict=True))
        self.query=F(time_s)+self.pc[25];self.qlo=F(time_s)+self.plo[25];self.qhi=F(time_s)+self.phi[25]
        if self.qlo<0 or self.qhi>F(float(sum(dt))):raise ValueError('complete source clock domain outside support')
        if any(1+p<=0 for p in self.plo[15:21]):raise ValueError('strictly positive calibration denominators required')
        self.time_s=float(time_s);self.points=PointStream(kernel,case,point,time_s,maximum_packets=maximum_packets)
        self.theta=self.points.theta;self.dt=self.points.dt;self.maximum_packets=maximum_packets;self.visits=0
        self.elapsed=0.;self.closed=False;self.prefix_d=F(0);self.prefix_r=F(0);self.prefix_n=F(0)
        digest=hashlib.sha256()
        for array in (dt,theta,dv,initial,limits,z,lo,hi,np.array([time_s])):
            a=np.ascontiguousarray(array,dtype=float);digest.update(str(a.shape).encode());digest.update(a.tobytes())
        self.source_binding=digest.hexdigest()
        gram=[[sum((F(float(initial[k,i]))*F(float(initial[k,j])) for k in range(3)),F(0))-int(i==j)
            for j in range(3)] for i in range(3)]
        defect=_norm(v for row in gram for v in row)
        self.mount_norm=F(sqrt_upper(1+defect))
        displacement=_norm(max(abs(a-c),abs(b-c)) for a,b,c in zip(self.plo[:3],self.phi[:3],self.pc[:3],strict=True))
        self.mount_change=self.mount_norm*min(F(2),displacement)
        self.mount_remainder=self.mount_norm*displacement**2/2
        force=self._correct(dv[0],float(dt[0]),12,18,as_rate=True)
        self.force_norm=_norm(F(a['center']) for a in force)
        self.force_change=_norm(F(a['change']) for a in force)
        self.force_remainder=_norm(F(a['remainder']) for a in force)

    def _correct(self,raw,period,bias,gain,*,as_rate=False):
        return [calibration(F(float(raw[i])),F(period),bias_center=self.pc[bias+i],gain_center=self.pc[gain+i],
            bias_lower=self.plo[bias+i],bias_upper=self.phi[bias+i],gain_lower=self.plo[gain+i],
            gain_upper=self.phi[gain+i],as_rate=as_rate) for i in range(3)]

    def append(self):
        if self.closed or self.visits>=self.maximum_packets:raise ValueError('direct source closed or packet allowance exhausted')
        index=self.visits;self.visits+=1;start=self.elapsed;t=float(self.dt[index]);end=start+t
        if not math.isfinite(end) or end<=start:self.close();raise ValueError('nonincreasing source clock')
        fraction=clipped_fraction(self.query,self.qlo,self.qhi,start=F(start),period=F(t))
        angle=[multiply(value,fraction) for value in self._correct(self.theta[index],t,9,15)]
        d=_norm(F(a['change']) for a in angle);r=_norm(F(a['remainder']) for a in angle)
        n=_norm(F(a['center']) for a in angle);phases=[]
        for factor in (F(1,2),F(1)):
            change=self.prefix_d+factor*d;remainder=self.prefix_r+factor*r+change**2/2
            nominal=min(F(2),self.prefix_n+factor*n)
            proof=force_products(mount_norm=self.mount_norm,nominal_departure=nominal,force_norm=self.force_norm,
                mount_change=self.mount_change,mount_remainder=self.mount_remainder,
                prefix_change=min(F(2),change),prefix_remainder=remainder,
                force_change=self.force_change,force_remainder=self.force_remainder)
            phases.append((proof['a_remainder'],proof['b_remainder']))
        point=self.points.append()
        if point['packet_index']!=index:self.close();raise ValueError('point and exact source prefixes disagree')
        self.prefix_d+=d;self.prefix_r+=r;self.prefix_n+=n;self.elapsed=end
        return DirectFrame(self.source_binding,self.center,self.lower,self.upper,index,start,end,self.time_s,
            point['point_values'],point['point_jacobian'],tuple(phases),point['state_bytes'])

    def close(self):self.closed=True;self.points.close()
    def __enter__(self):return self
    def __exit__(self,*args):self.close()


def radius(frame,values,rows,*,phase):
    """Transfer the ideal remainder to arbitrary stated numeric values/rows.

    Every point-value mismatch and all 27 derivative-column mismatches are
    included. The consumer must additionally match the same source/domain.
    """
    if not isinstance(frame,DirectFrame) or type(phase) is not int or phase not in (0,1):
        raise ValueError('typed direct source frame and matching phase required')
    arrays=[np.asarray(a,float) for a in (values,rows,frame.point_values,frame.point_jacobian)]
    if (tuple(a.shape for a in arrays)!=((2,2,3),(2,2,3,27),(2,2,3,2),(2,2,3,27,2))
            or not all(np.all(np.isfinite(a)) for a in arrays)):
        raise ValueError('complete finite source values and all 27 rows required')
    numerical,jac,point,derivative=arrays
    if np.any(point[...,0]>point[...,1]) or np.any(derivative[...,0]>derivative[...,1]):
        raise ValueError('ordered point intervals required')
    widths=[max(abs(F(a)-F(c)),abs(F(b)-F(c))) for a,b,c in zip(frame.lower,frame.upper,frame.center,strict=True)]
    out=np.empty((2,3))
    for component in range(2):
        remainder=F(frame.ideal_remainder[phase][component])
        if remainder<0:raise ValueError('nonnegative ideal source remainder required')
        for axis in range(3):
            value=F(float(numerical[phase,component,axis]));ends=point[phase,component,axis]
            total=remainder+max(abs(F(float(v))-value) for v in ends)
            for col in range(27):
                row=F(float(jac[phase,component,axis,col]));ends=derivative[phase,component,axis,col]
                total+=widths[col]*max(abs(F(float(v))-row) for v in ends)
            out[component,axis]=endpoint(total,True)
    out.setflags(write=False);return out
