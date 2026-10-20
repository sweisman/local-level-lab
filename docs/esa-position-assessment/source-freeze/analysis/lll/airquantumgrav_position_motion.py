# SPDX-License-Identifier: AGPL-3.0-or-later
"""Position-derived receiver trends under declared, uncalibrated error laws.

Geodetic metrics here interpret receiver coordinates for motion screening; they
are not an independent test of Earth geometry. Polynomial-trend and instantaneous
motion uncertainty are deliberately separate. No eligibility policy is changed.
"""
import math
import numpy as np
from scipy.stats import norm
from .models import WGS84_A,WGS84_E2
from .ilvis0_receiver_derivatives import LocalPolynomial
from .ilvis0_derivative_bounds import jet_error_bounds
from .ilvis0_force_bounds import _Box

VERSION='esa-position-motion-trend-v1'


def _radii(phi,height):
    s=np.sin(phi);d=1.-WGS84_E2*s*s
    prime=WGS84_A/np.sqrt(d);north=WGS84_A*(1.-WGS84_E2)/d**1.5
    return north+height,(prime+height)*np.cos(phi)


def course_box(jet_bounds):
    """Enclose geographic course rate, retaining the changing local metric."""
    values=np.asarray(jet_bounds,float)
    if values.shape!=(9,2) or not np.all(np.isfinite(values)) or np.any(values[:,0]>values[:,1]):
        raise ValueError('complete finite ordered geodetic jet box required')
    phi,_,height,p,l,h,pp,ll,_=[_Box(*v) for v in values]
    if phi.lo<=-math.pi/2+1e-6 or phi.hi>=math.pi/2-1e-6:
        return dict(supported=False,reason='polar_coordinate_box')
    s=_Box.outward(math.sin(phi.lo),math.sin(phi.hi))
    c=_Box.outward(min(math.cos(phi.lo),math.cos(phi.hi)),
        1. if phi.lo<=0.<=phi.hi else max(math.cos(phi.lo),math.cos(phi.hi)))
    d=1.-WGS84_E2*s.square();prime=WGS84_A*d.positive_power(-.5)
    north=WGS84_A*(1.-WGS84_E2)*d.positive_power(-1.5)
    if (north+height).lo<=0. or (prime+height).lo<=0.:
        return dict(supported=False,reason='nonpositive_coordinate_metric')
    prime_phi=prime*WGS84_E2*s*c/d;north_phi=3.*north*WGS84_E2*s*c/d
    east=(prime+height)*c
    vn=(north+height)*p;ve=east*l
    an=(north+height)*pp+(north_phi*p+h)*p
    ae=east*ll+((prime_phi*c-(prime+height)*s)*p+c*h)*l
    speed2=vn.square()+ve.square()
    if speed2.lo<=0.:return dict(supported=False,reason='speed_interval_includes_zero')
    rate=(vn*ae-ve*an)/speed2
    return dict(supported=True,lower_deg_s=float(np.nextafter(math.degrees(rate.lo),-np.inf)),
        upper_deg_s=float(np.nextafter(math.degrees(rate.hi),np.inf)),
        north_mps=[vn.lo,vn.hi],east_mps=[ve.lo,ve.hi],up_mps=[h.lo,h.hi],
        speed_mps=[math.sqrt(speed2.lo),math.sqrt(speed2.hi)],
        formal_libm_rounding_certificate=False)


def _interval(jet,half,scales,origin):
    geo=np.asarray(jet)/np.tile(scales,3);geo[:3]+=origin
    error=np.asarray(half)/np.tile(scales,3)
    bounds=np.column_stack((np.nextafter(geo-error,-np.inf),np.nextafter(geo+error,np.inf)))
    return course_box(bounds)|dict(geodetic_jet=geo.tolist(),geodetic_jet_half_width=error.tolist(),
        up_mps=bounds[5].tolist())


def assess(times,coordinates,covariance,*,center_s,degree=3,maximum_gap_s=.75,
        alpha=.01,rounding_m,time_constant_s=None,derivative_envelopes=None):
    """Fit one fixed chart polynomial, then compare supplied error assumptions.

    Coordinates are radians/radians/ellipsoidal metres. Covariance is the full
    per-epoch N/E/up position covariance in square metres. rounding_m is an
    explicit three-axis bound in the fixed chart, not an estimated accuracy.
    Exponential temporal covariance uses the symmetric PSD roots of the reported
    within-epoch matrices. Unknown temporal correlation uses worst marginal
    variances, not a fabricated joint covariance. All laws assume Gaussian errors.
    """
    t=np.asarray(times,float);p=np.asarray(coordinates,float);cov=np.asarray(covariance,float)
    rounding=np.asarray(rounding_m,float);n=len(t)
    if (t.ndim!=1 or not 3<=n<=256 or p.shape!=(n,3) or cov.shape!=(n,3,3)
            or not all(np.all(np.isfinite(v)) for v in (t,p,cov,rounding))
            or rounding.shape!=(3,) or np.any(rounding<0.) or not 0.<alpha<1.
            or np.any(abs(p[:,0])>=math.pi/2-1e-6) or np.any(abs(p[:,1])>math.pi)
            or np.any(np.diff(t)<=0.) or np.any(np.diff(t)>maximum_gap_s)
            or not math.isfinite(center_s) or not t[0]<=center_s<=t[-1]):
        raise ValueError('complete finite ordered receiver chart, covariance and rounding required')
    if time_constant_s is not None and (not math.isfinite(time_constant_s) or time_constant_s<=0.):
        raise ValueError('positive supplied temporal correlation required')
    if not np.allclose(cov,cov.transpose(0,2,1),rtol=1e-12,atol=0.):
        raise ValueError('symmetric reported position covariance required')
    eigen,axes=np.linalg.eigh(cov)
    if np.any(eigen<0.) or np.any(np.diagonal(cov,axis1=1,axis2=2)<=0.):
        raise ValueError('positive semidefinite reported position covariance required; no repair')
    origin=p[int(np.argmin(abs(t-center_s)))].copy();unwrapped=np.unwrap(p[:,1])
    origin[1]=unwrapped[int(np.argmin(abs(t-center_s)))]
    if np.ptp(unwrapped)>=math.pi/2:raise ValueError('local longitude chart exceeds supported span')
    north,east=_radii(p[:,0],p[:,2]);sn,se=_radii(origin[0],origin[2]);scales=np.array([sn,se,1.])
    if min(np.min(north),np.min(east),sn,se)<=0.:raise ValueError('positive local coordinate metrics required')
    chart=np.column_stack(((p[:,0]-origin[0])*sn,(unwrapped-origin[1])*se,p[:,2]-origin[2]))
    # The estimator does not change when a covariance sensitivity law changes.
    operator=LocalPolynomial(t,center_s,np.eye(3*n),degree=degree,maximum_gap_s=maximum_gap_s)
    fit=operator.apply(chart);jet=np.r_[fit['position'],fit['rate'],fit['acceleration']]
    h=operator.weights
    factors=np.column_stack((sn/north,se/east,np.ones(n)))
    chart_cov=cov*factors[:,:,None]*factors[:,None,:]
    eigen,axes=np.linalg.eigh(chart_cov)
    if np.any(eigen<0.):raise ValueError('unrepresentable transformed covariance; no repair')
    roots=(axes*np.sqrt(eigen)[:,None,:])@axes.transpose(0,2,1)
    projected=np.einsum('aij,ijk->aik',h.reshape(9,n,3),roots)
    flat=projected.reshape(9,3*n);independent=flat@flat.T
    models={'independent':independent,'arbitrary_correlation':None}
    if time_constant_s is not None:
        correlation=np.exp(-abs(t[:,None]-t[None,:])/time_constant_s)
        models['supplied_correlation']=np.einsum('aik,ij,bjk->ab',projected,correlation,projected)
    rounding_half=abs(h)@np.tile(rounding,n);critical=float(norm.isf(alpha/18.))
    deterministic=None
    if derivative_envelopes is not None:
        deterministic=jet_error_bounds(h,t,center_s,derivative_envelopes=derivative_envelopes,
            coordinate_error_bounds=np.zeros((n,3)))['total_jet_error_bounds']
    intervals={};instantaneous={}
    for name,matrix in models.items():
        variance=(np.linalg.norm(projected,axis=2).sum(axis=1)**2 if matrix is None else np.diag(matrix))
        if not np.all(np.isfinite(variance)) or np.any(variance<0.):raise ValueError('finite nonnegative propagated variance required')
        half=critical*np.sqrt(variance)+rounding_half
        common=dict(coefficient_variance=variance.tolist(),coefficient_half_width=half.tolist(),
            coefficient_covariance=None if matrix is None else matrix.tolist(),
            rounding_half_width=rounding_half.tolist(),nominal_failure_allowance=alpha,
            gaussian_assumption=True,reported_covariance_verified=False,temporal_model=name,
            target='noise_free_polynomial_trend')
        intervals[name]=_interval(jet,half,scales,origin)|common
        if deterministic is not None:
            instantaneous[name]=_interval(jet,half+deterministic,scales,origin)|dict(
                target='instantaneous_under_supplied_derivative_bounds',higher_derivative_bound_is_assumed=True,
                observational_coverage_calibrated=False)
    point=_interval(jet,np.zeros(9),scales,origin)
    rate=(point['lower_deg_s']+point['upper_deg_s'])/2 if point['supported'] else None
    speed=sum(point['speed_mps'])/2 if point['supported'] else None
    return dict(version=VERSION,supported=True,center_s=float(center_s),epochs=n,degree=degree,
        support_start_s=float(t[0]),support_end_s=float(t[-1]),jet_chart_m=jet.tolist(),
        geodetic_jet=point['geodetic_jet'],chart_origin=origin.tolist(),chart_scales=scales.tolist(),
        point_course_rate_deg_s=rate,point_speed_mps=speed,
        chart_residual_rms_m=np.sqrt(np.mean(fit['coordinate_residuals']**2,axis=0)).tolist(),
        intervals=intervals,instantaneous_intervals=instantaneous,
        instantaneous_motion_supported=deterministic is not None,
        instantaneous_motion_reason=None if deterministic is not None else 'higher_derivative_bounds_not_supplied',
        instantaneous_jet_error_m=None if deterministic is None else deterministic.tolist(),
        coordinate_metric='WGS84 receiver-coordinate interpretation; not independent shape evidence',
        observational_coverage_calibrated=False,eligibility_policy_changed=False,scientific_decision='abstain')
