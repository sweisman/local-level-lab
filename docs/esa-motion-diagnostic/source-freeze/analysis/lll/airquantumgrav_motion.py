# SPDX-License-Identifier: AGPL-3.0-or-later
"""Receiver-only velocity trends; supplied error assumptions are not calibration."""
import math

import numpy as np
from scipy.stats import norm

from .airquantumgrav_receiver import records as receiver_records

VERSION='esa-receiver-motion-trend-v1'


def velocity_records(lines):
    """Extend the frozen strict reader without changing its earlier evidence."""
    current={}
    def tracked():
        for number,line in enumerate(lines,1):
            current.update(number=number,line=line);yield line
    for row in receiver_records(tracked()):
        if row['line_number']!=current['number']:raise ValueError('receiver stream association failed')
        fields=current['line'].split();values=[float(v) for v in fields[13:19]]
        nn,ee,hh,en,nh,eh=values
        yield dict(row,source_covariance_fields=values,
            velocity_covariance_m2_s2=[[nn,en,nh],[en,ee,eh],[nh,eh,hh]])


def _product(a,b):
    values=[x*y for x in a for y in b]
    return np.array([np.nextafter(min(values),-np.inf),np.nextafter(max(values),np.inf)])


def _square(a):
    low=0. if a[0]<=0.<=a[1] else min(a*a)
    return np.array([max(0.,np.nextafter(low,-np.inf)),np.nextafter(max(a*a),np.inf)])


def course_interval(coefficients,half_width):
    bounds=np.column_stack((coefficients-half_width,coefficients+half_width))
    bounds[:,0]=np.nextafter(bounds[:,0],-np.inf);bounds[:,1]=np.nextafter(bounds[:,1],np.inf)
    north,east,dnorth,deast=bounds
    a=_product(north,deast);b=_product(east,dnorth)
    numerator=np.array([np.nextafter(a[0]-b[1],-np.inf),np.nextafter(a[1]-b[0],np.inf)])
    denominator=_square(north)+_square(east)
    denominator[0]=max(0.,np.nextafter(denominator[0],-np.inf));denominator[1]=np.nextafter(denominator[1],np.inf)
    if denominator[0]<=0.:return dict(supported=False,reason='speed_interval_includes_zero')
    ratios=[n/d for n in numerator for d in denominator]
    return dict(supported=True,lower_deg_s=float(np.nextafter(math.degrees(min(ratios)),-np.inf)),
        upper_deg_s=float(np.nextafter(math.degrees(max(ratios)),np.inf)))


def _correlation(values):
    if len(values)<3 or np.std(values[:-1])==0. or np.std(values[1:])==0.:return None
    return float(np.corrcoef(values[:-1],values[1:])[0,1])


def assess(times,velocity_ne,vertical_mps,covariance,*,center_s,alpha=.01,rounding_mps=.0005,time_constant_s=None):
    t=np.asarray(times,float);v=np.asarray(velocity_ne,float);up=np.asarray(vertical_mps,float);c=np.asarray(covariance,float)
    n=len(t)
    if (t.ndim!=1 or n<3 or v.shape!=(n,2) or up.shape!=(n,) or c.shape!=(n,3,3)
            or not all(np.all(np.isfinite(x)) for x in (t,v,up,c))
            or np.any(np.diff(t)<=0.) or np.any(np.diff(t)>.75)
            or not math.isfinite(center_s) or not t[0]<=center_s<=t[-1]):
        raise ValueError('finite ordered continuous receiver window required')
    if not 0.<alpha<1. or not math.isfinite(rounding_mps) or rounding_mps<0.:
        raise ValueError('explicit failure allowance and nonnegative rounding bound required')
    if time_constant_s is not None and (not math.isfinite(time_constant_s) or time_constant_s<=0.):
        raise ValueError('positive supplied correlation time required')
    x=np.column_stack((np.ones(n),t-center_s));weights=np.linalg.solve(x.T@x,x.T)
    coefficients=weights@v;intercept,slope=coefficients;speed2=float(intercept@intercept)
    rate=math.degrees(float(intercept[0]*slope[1]-intercept[1]*slope[0])/speed2) if speed2>0. else None
    course=np.arctan2(v[:,1],v[:,0]);differences=np.arctan2(np.sin(np.diff(course)),np.cos(np.diff(course)))
    adjacent=float(np.median(abs(np.rad2deg(differences)/np.diff(t)))) if np.all(np.hypot(v[:,0],v[:,1])>0.) else None
    residual=v-x@coefficients
    result=dict(version=VERSION,center_s=float(center_s),epochs=n,intercept_ne_mps=intercept.tolist(),
        slope_ne_mps2=slope.tolist(),course_rate_deg_s=rate,adjacent_median_abs_course_rate_deg_s=adjacent,
        median_abs_vertical_speed_mps=float(np.median(abs(up))),mean_speed_mps=float(np.mean(np.hypot(v[:,0],v[:,1]))),
        residual_rms_ne_mps=np.sqrt(np.mean(residual**2,axis=0)).tolist(),
        residual_lag1_ne=[_correlation(residual[:,axis]) for axis in (0,1)],
        intervals={},observational_coverage_calibrated=False,instantaneous_course_derivative_established=False,
        scientific_decision='abstain')
    valid=bool(np.allclose(c,c.transpose(0,2,1),rtol=1e-12,atol=0.)
        and np.all(np.linalg.eigvalsh(c)>=0.) and np.all(np.diagonal(c,axis1=1,axis2=2)>0.))
    names=['independent','arbitrary_correlation']+(['supplied_correlation'] if time_constant_s is not None else [])
    if not valid:
        result['intervals']={name:dict(supported=False,reason='unsupported_reported_velocity_covariance') for name in names}
        return result
    sd=np.sqrt(np.diagonal(c,axis1=1,axis2=2)[:,:2]);critical=float(norm.isf(alpha/8.))
    for name in names:
        variances=[];rounding=[]
        for power,axis in ((0,0),(0,1),(1,0),(1,1)):
            w=weights[power];scaled=w*sd[:,axis]
            if name=='arbitrary_correlation':variance=float(np.sum(abs(scaled))**2)
            elif name=='independent':variance=float(scaled@scaled)
            else:
                corr=np.exp(-abs(t[:,None]-t[None,:])/time_constant_s)
                variance=float(scaled@corr@scaled)
            variances.append(variance);rounding.append(rounding_mps*float(np.sum(abs(w))))
        half=critical*np.sqrt(variances)+rounding
        interval=course_interval(coefficients.ravel(),half)
        interval.update(coefficient_variance=variances,coefficient_half_width=half.tolist(),
            nominal_failure_allowance=alpha,gaussian_marginal_assumption=True,
            reported_covariance_verified=False,rounding_bound_mps=rounding_mps,
            noise_free_window_trend_target=True)
        result['intervals'][name]=interval
    return result
