# SPDX-License-Identifier: AGPL-3.0-or-later
"""Training-only receiver-reference assessment; no inertial or Earth-model input."""
from fractions import Fraction as F
import math
import time

import numpy as np
from . import ilvis0_exact_scale as exact


def rational_record(value):
    value=F(value)
    return dict(numerator_hex=hex(value.numerator),denominator_hex=hex(value.denominator))


def training_chart(fixes, *, expected_epochs):
    """Fixed affine chart of exactly the supplied training prefix, no repair.

    The longitude scale is fixed at cos(60 degrees)=1/2, independently of noisy
    positions. These chart metres are not a receiver-dependent local geodesic.
    """
    if type(expected_epochs) is not int or expected_epochs<2 or len(fixes)!=expected_epochs:
        raise ValueError('exact training-only epoch count required; later positions are not accepted')
    times=[];values=[]
    for row in fixes:
        t,lat,lon,h=(float(row[k]) for k in ('time_s','latitude_rad','longitude_rad','height_m'))
        if not all(math.isfinite(v) for v in (t,lat,lon,h)) or abs(lat)>math.pi/2 or abs(lon)>math.pi:
            raise ValueError('finite supported receiver coordinates required')
        times.append(F(t));values.append((F(lat)*6371000,F(lon)*3185500,F(h)))
    if any(t-times[0]!=i for i,t in enumerate(times)):
        raise ValueError('uniform one-second epochs required; no resampling or gap repair')
    return dict(values=values,times=times,chart='fixed-radian-affine-R6371000-cos60-v1',epoch_count=len(values))


def assess(training, *, degree, tau, maximum_seconds=30.):
    if degree not in (3,5,7) or tau not in (10,300) or training['chart']!='fixed-radian-affine-R6371000-cos60-v1':
        raise ValueError('predeclared reference degree, covariance family and chart required')
    started=time.monotonic();values=training['values'];n=len(values)
    if n!=training['epoch_count'] or n<=degree+3:raise ValueError('sufficient fixed training support required')
    rho=F(round(math.exp(-1/tau)*2**24),2**24)
    x=np.vander(np.linspace(-1.,1.,n),degree+1,increasing=True)
    total=F(0);axes=[];steps=0
    for axis,name in enumerate(('north_chart','east_chart','height')):
        y=[row[axis] for row in values];origin=y[0];centered=[v-origin for v in y]
        # Numerical coefficients need no roundoff certificate: the exact norm
        # for ANY coefficients upper-bounds the minimum fixed-space residual.
        coefficients=np.linalg.lstsq(x,np.array([float(v) for v in centered]),rcond=None)[0]
        if not np.all(np.isfinite(coefficients)):raise exact.Unsupported('nonfinite polynomial coefficients')
        residuals=exact.polynomial_residuals(centered,coefficients)
        law=exact.Covariance(rho,F(49,100) if axis==2 else F(9,100),
            F(9) if axis==2 else F(1),F(9) if axis==2 else F(1),F(9) if axis==2 else F(1))
        remaining=maximum_seconds-(time.monotonic()-started)
        if remaining<=0:raise exact.Unsupported('time allowance exhausted')
        budget=exact.Budget(maximum_steps=n,maximum_bits=131072,maximum_seconds=min(10.,remaining))
        quadratic=exact.residual_quadratic(residuals,law,budget=budget);total+=quadratic;steps+=budget.steps
        axes.append(dict(axis=name,quadratic=rational_record(quadratic),origin=rational_record(origin),
            coefficients_binary64=[float(c).hex() for c in coefficients],
            reference_residual_rms_chart_m=exact.sqrt_upper(sum((r*r for r in residuals),F(0))/n)))
    bound=exact.scale_upper(total,observations=3*n,reference_columns=3*(degree+1),alpha=F(1,100))
    return dict(degree=degree,tau_approx_s=tau,rho=str(rho),chart=training['chart'],observations=3*n,
        reference_columns=3*(degree+1),degrees=bound['degrees'],quadratic=rational_record(total),axes=axes,
        scale_upper=bound['upper'],quantile_floor=rational_record(bound['quantile']['q']),
        moment=bound['quantile']['k'],tail_certificate=rational_record(bound['quantile']['tail_bound']),
        failure_probability_per_assumed_law=.01,simultaneous_coverage_established=False,
        future_receiver_positions_used=False,earth_model_residuals_used=False,
        observational_coverage_qualified=False,covariance_shape_established=False,
        maximum_epochs=steps,elapsed_s=time.monotonic()-started,scientific_decision='abstain')
