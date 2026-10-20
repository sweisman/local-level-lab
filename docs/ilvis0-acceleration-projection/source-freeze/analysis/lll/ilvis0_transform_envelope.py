# SPDX-License-Identifier: AGPL-3.0-or-later
"""Joint necessary constraints with one 24-vector shared across all epochs.

The extra coordinates enclose nonlinear errors; they are not new physical
calibration parameters. A typed, source-bound native remainder is mandatory.
Supplied native tangents, global bounds and observation allowances remain
assumptions here. No future receiver observation enters the prediction API.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import math

import numpy as np
from . import ilvis0_affine_support as support
from .ilvis0_orientation_cover import _endpoint
from .ilvis0_transform_native import TransformReference,TransformEnclosure

VERSION='ilvis0-joint-transform-error-envelope-v1'


def _array(value,shape):
    result=np.array(value,float,copy=True)
    if result.shape!=shape or not np.all(np.isfinite(result)):
        raise ValueError('complete finite joint-envelope arrays required')
    result.setflags(write=False)
    return result


def _box(lower,upper,shape):
    lo=_array(lower,shape);hi=_array(upper,shape)
    if np.any(lo>hi):raise ValueError('ordered joint domain required')
    return lo,hi


def _force_source(report,reference):
    if not isinstance(reference,TransformReference) or not isinstance(report,TransformEnclosure):
        raise ValueError('typed transform reference and native enclosure required')
    m=report.metadata;force=m.get('force_integrals');clock=m.get('clock_transform');matrix=m.get('transform_reference')
    if not all(isinstance(value,dict) for value in (force,clock,matrix)):
        raise ValueError('complete bound force/clock/matrix source fields required')
    source=force.get('source_id')
    if (not isinstance(source,str) or len(source)!=64 or any(c not in '0123456789abcdef' for c in source)
            or clock.get('source_id')!=source or clock.get('matrix_binding')!=reference.transform.binding
            or matrix.get('binding')!=reference.transform.binding or m.get('reference_binding')!=reference.binding):
        raise ValueError('native force/clock/matrix/reference binding mismatch')
    return source


def _native(report,reference,time,value,jacobian,lower,upper,scale):
    if not isinstance(reference,TransformReference) or not isinstance(report,TransformEnclosure):
        raise ValueError('typed native enclosure and shared reference required')
    _force_source(report,reference)
    m=report.metadata
    if (m.get('source_id')!=reference.parent.source_id or m.get('time_s')!=time
            or not np.array_equal(m.get('normalized_center'),reference.parent.center)):
        raise ValueError('native source, time or expansion mismatch')
    blo,bhi=_box(m.get('bound_lower'),m.get('bound_upper'),(27,))
    if (np.any(blo>lower) or np.any(bhi<upper) or np.any(blo>reference.parent.center)
            or np.any(bhi<reference.parent.center) or np.any(blo<reference.parent.lower) or np.any(bhi>reference.parent.upper)):
        raise ValueError('native bound does not cover the requested domain and expansion')
    value=_array(value,(3,));jacobian=_array(jacobian,(3,27))
    if np.max(abs(report.center-value)*scale)>1e-6:
        raise ValueError('native center disagrees with bound center')
    return value,report.design(jacobian,reference)*scale[:,None]


@dataclass(frozen=True)
class TrainingRegion:
    times:object
    design:object
    target_lower:object
    target_upper:object
    inequality_design:object
    inequality_upper:object
    lower:object
    upper:object
    center:object
    coordinate_scale:object
    origin:object
    binding:str
    source_id:str
    force_source_id:str
    arithmetic_allowance:float

    def __post_init__(self):
        n=len(self.times);rows=3*n
        for name,shape in (('times',(n,)),('design',(rows,51)),('target_lower',(rows,)),
                ('target_upper',(rows,)),('inequality_design',(2*rows,51)),('inequality_upper',(2*rows,)),
                ('lower',(51,)),('upper',(51,)),('center',(51,)),('coordinate_scale',(3,)),('origin',(3,))):
            object.__setattr__(self,name,_array(getattr(self,name),shape))

    def report(self):
        return dict(version=VERSION,binding=self.binding,source_id=self.source_id,force_source_id=self.force_source_id,
            times_s=self.times,design=self.design,target_lower=self.target_lower,target_upper=self.target_upper,
            inequality_design=self.inequality_design,inequality_upper=self.inequality_upper,
            lower=self.lower,upper=self.upper,center=self.center,
            coordinate_scale=self.coordinate_scale,origin=self.origin,arithmetic_allowance=self.arithmetic_allowance,
            parameter_count=51,physical_parameter_count=27,shared_error_count=24,
            future_truth_used=False,floating_point_enclosure_verified=False,
            observational_coverage_qualified=False,scientific_decision='abstain')


def training(*,times,observations,native_values,native_jacobians,reports,reference,
             physical_lower,physical_upper,coordinate_scale,origin,noise_allowance,arithmetic_allowance=1e-5):
    t=np.asarray(times,float)
    if (t.ndim!=1 or not 1<=len(t)<=256 or not np.all(np.isfinite(t)) or np.any(np.diff(t)<=0)
            or t[0]<0 or not isinstance(reference,TransformReference)):
        raise ValueError('ordered finite training times and a bound reference required')
    n=len(t);observed=_array(observations,(n,3));values=_array(native_values,(n,3));j=_array(native_jacobians,(n,3,27))
    scale=_array(coordinate_scale,(3,));origin=_array(origin,(3,));noise=_array(noise_allowance,(n,3))
    lo,hi=_box(physical_lower,physical_upper,(27,))
    if (np.any(scale<=0) or np.any(noise<0) or len(reports)!=n
            or np.any(lo<reference.parent.lower) or np.any(hi>reference.parent.upper)
            or not math.isfinite(arithmetic_allowance) or arithmetic_allowance<0):
        raise ValueError('supported physical region, fixed scale and nonnegative allowances required')
    force_sources={_force_source(report,reference) for report in reports}
    if len(force_sources)!=1:raise ValueError('every training epoch must share the same force source')
    force_source=next(iter(force_sources))
    matrix=[];left=[];right=[];center=np.r_[reference.parent.center,np.zeros(24)]
    for index,time in enumerate(t):
        value,design=_native(reports[index],reference,float(time),values[index],j[index],lo,hi,scale)
        for axis,row in enumerate(design):
            shift=sum((F(float(a))*F(float(b)) for a,b in zip(row,center)),F(0))
            delta=(F(float(observed[index,axis]))-F(float(value[axis])))*F(float(scale[axis]))
            allowance=F(float(reports[index].unshared_remainder[axis]))*F(float(scale[axis]))+F(float(noise[index,axis]))+F(float(arithmetic_allowance))
            matrix.append(row)
            left.append(_endpoint(shift+delta-allowance,False))
            right.append(_endpoint(shift+delta+allowance,True))
    matrix=np.array(matrix);left=np.array(left);right=np.array(right)
    return TrainingRegion(t,matrix,left,right,np.r_[matrix,-matrix],np.r_[right,-left],
        np.r_[lo,-np.ones(24)],np.r_[hi,np.ones(24)],center,scale,origin,
        reference.binding,reference.parent.source_id,force_source,float(arithmetic_allowance))


def future(region,*,time,native_value,native_jacobian,report,reference,lower=None,upper=None):
    if (not isinstance(region,TrainingRegion) or not isinstance(reference,TransformReference)
            or region.binding!=reference.binding or region.source_id!=reference.parent.source_id
            or not np.array_equal(region.center[:27],reference.parent.center)
            or not math.isfinite(time) or time<=region.times[-1]):
        raise ValueError('future time and unchanged joint training/reference binding required')
    if _force_source(report,reference)!=region.force_source_id:
        raise ValueError('future force source differs from joint training')
    if (lower is None)!=(upper is None):raise ValueError('both contracted endpoints required')
    lo,hi=_box(region.lower if lower is None else lower,region.upper if upper is None else upper,(51,))
    if np.any(lo<region.lower) or np.any(hi>region.upper):
        raise ValueError('contracted box must remain inside the complete joint training domain')
    value,design=_native(report,reference,float(time),native_value,native_jacobian,lo[:27],hi[:27],region.coordinate_scale)
    left=[];right=[];certificates=[]
    for axis,row in enumerate(design):
        high=support.propose(lo,hi,region.inequality_design,region.inequality_upper,row)
        low=support.propose(lo,hi,region.inequality_design,region.inequality_upper,-row)
        shift=(F(float(value[axis]))-F(float(region.origin[axis])))*F(float(region.coordinate_scale[axis]))
        shift-=sum((F(float(a))*F(float(b)) for a,b in zip(row,region.center)),F(0))
        radius=F(float(report.unshared_remainder[axis]))*F(float(region.coordinate_scale[axis]))+F(region.arithmetic_allowance)
        left.append(_endpoint(shift-low['exact_upper']-radius,False))
        right.append(_endpoint(shift+high['exact_upper']+radius,True))
        certificates.append(dict(upper=str(high['exact_upper']),negated_lower=str(low['exact_upper']),
            upper_multipliers=high['multipliers'],lower_multipliers=low['multipliers']))
    if np.any(np.array(left)>right):raise ValueError('contradictory joint support requires diagnosis')
    return dict(version=VERSION,lower=np.array(left),upper=np.array(right),certificates=certificates,
        shared_binding=region.binding,source_id=region.source_id,force_source_id=region.force_source_id,parameter_count=51,
        physical_parameter_count=27,shared_error_count=24,future_truth_used=False,
        floating_point_enclosure_verified=False,observational_coverage_qualified=False,scientific_decision='abstain')
