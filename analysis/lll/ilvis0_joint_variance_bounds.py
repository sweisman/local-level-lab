# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact marginal variance bounds for the supplied constant-coupling law.

Receiver components and linear accumulated IMU noise are explicit assumptions.
The bounds cover the declared clock interval but do not validate an aircraft
law, nonlinear propagation, unknown processing or a training scale assessment.
"""
from fractions import Fraction as F
import hashlib
import json
import math


def _scalar(value):
    try:
        result=float(value)
        if not math.isfinite(result):raise ValueError('finite coefficient required')
        return F(result)
    except (TypeError,ValueError,OverflowError):raise ValueError('finite explicit coefficient required') from None


def _matrix(value,*,psd=False,positive=False):
    import numpy as np
    a=np.asarray(value)
    if a.shape!=(3,3):raise ValueError('explicit three-by-three matrix required')
    r=[[_scalar(a[i,j]) for j in range(3)] for i in range(3)]
    if psd or positive:
        if any(r[i][j]!=r[j][i] for i in range(3) for j in range(3)):
            raise ValueError('exact symmetric covariance required')
        minors=[r[i][i] for i in range(3)]
        minors.extend(r[i][i]*r[j][j]-r[i][j]**2 for i,j in ((0,1),(0,2),(1,2)))
        minors.append(r[0][0]*(r[1][1]*r[2][2]-r[1][2]*r[2][1])
            -r[0][1]*(r[1][0]*r[2][2]-r[1][2]*r[2][0])
            +r[0][2]*(r[1][0]*r[2][1]-r[1][1]*r[2][0]))
        if any(v<0 or (positive and v==0) for v in minors):
            raise ValueError('exact positive semidefinite covariance required')
    return r


def marginal_variance_bounds(times,*,receiver,origin_s,accel_psd,gyro_psd,coupling,clock_interval_s):
    """Return outward variance bounds in metres squared, at all declared epochs.

All finite input binary64 coefficients are interpreted exactly as rationals.
For each time interval, inertial variance is monotone in elapsed time. The
receiver drift uses the endpoint with largest absolute distance from its own
fixed origin. No correlations or integration origins are reset or estimated.
"""
    import numpy as np
    from lll.ilvis0_error_model import Spec
    from lll.ilvis0_saved_prediction_audit import endpoint
    t=np.array(times,float,copy=True)
    if (t.ndim!=1 or not 1<=len(t)<=100000 or not np.all(np.isfinite(t)) or np.any(np.diff(t)<=0.)
            or not isinstance(receiver,Spec) or len(clock_interval_s)!=2):
        raise ValueError('ordered finite epochs, declared Spec and clock interval required')
    origin=_scalar(origin_s);clock=tuple(map(_scalar,clock_interval_s))
    if clock[0]>clock[1] or _scalar(t[0])+clock[0]<origin:
        raise ValueError('entire clock support must follow the declared integration origin')
    qa=_matrix(accel_psd,psd=True);qg=_matrix(gyro_psd,psd=True);g=_matrix(coupling)
    white=_matrix(receiver.white,positive=True);offset=_matrix(receiver.offset,psd=True)
    drift=_matrix(receiver.drift,psd=True)
    stationary=[_matrix(values,psd=True) for _,values in receiver.components]
    drift_origin=_scalar(receiver.drift_origin_s);span=_scalar(receiver.drift_span_s)
    base=[white[i][i]+offset[i][i]+sum((m[i][i] for m in stationary),F(0)) for i in range(3)]
    h=[sum((g[i][j]*qg[j][k]*g[i][k] for j in range(3) for k in range(3)),F(0)) for i in range(3)]
    if any(v<0 for v in h):raise ValueError('nonnegative force-coupled gyro variances required')
    variances=[];exact=[]
    for value in t:
        lo=_scalar(value)+clock[0];hi=_scalar(value)+clock[1];elapsed=hi-origin
        distance=max(abs(lo-drift_origin),abs(hi-drift_origin))/span
        row=[base[i]+drift[i][i]*distance**2+qa[i][i]*elapsed**3/3+h[i]*elapsed**5/20 for i in range(3)]
        exact.append(list(map(str,row)));variances.append([endpoint(v,True) for v in row])
    result=np.array(variances);result.setflags(write=False)
    def strings(matrix):return [list(map(str,row)) for row in matrix]
    law=dict(version='ilvis0-constant-coupling-marginal-variance-v1',times_s=t.tolist(),origin_s=str(origin),
        clock_interval_s=list(map(str,clock)),accel_psd=strings(qa),gyro_psd=strings(qg),coupling=strings(g),
        receiver=dict(white=strings(white),offset=strings(offset),drift=strings(drift),
            components=[dict(tau=str(_scalar(tau)),covariance=strings(matrix))
                for (tau,_),matrix in zip(receiver.components,stationary,strict=True)],
            drift_origin_s=str(drift_origin),drift_span_s=str(span)))
    binding=hashlib.sha256(json.dumps(law,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return dict(variance_upper_m2=result,exact_variance_upper_m2=exact,law=law,covariance_id=binding,
        variance_arithmetic_verified=True,clock_interval_covered=True,law_adequacy_established=False,
        scale_assessment_validity_established=False,nonlinear_inertial_error_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')


def _quadratic(left,matrix,right):
    return sum((left[i]*matrix[i][j]*right[j]
        for i in range(3) for j in range(3) if matrix[i][j]),F(0))


def _exp_negative_bounds(x):
    """Rational enclosure of exp(-x), without floating transcendental calls."""
    if x==0:return F(1),F(1)
    if x>64:return F(0),1/(1+x)
    term=total=F(1)
    for k in range(1,257):term*=x/k;total+=term
    # After term 257, consecutive ratios are bounded by x/258 < 1.
    tail=term*x/257/(1-x/258)
    return 1/(total+tail),1/total


def _ou_variance_upper(times,weights,tau,matrix,cache):
    from lll.ilvis0_saved_prediction_audit import endpoint
    history=[(F(0),F(0)) for _ in range(3)];upper=F(0)
    for i,w in enumerate(weights):
        if i:
            x=(times[i]-times[i-1])/tau
            if x not in cache:cache[x]=_exp_negative_bounds(x)
            rlo,rhi=cache[x];previous=weights[i-1];updated=[]
            for (lo,hi),p in zip(history,previous,strict=True):
                products=[r*(v+p) for r in (rlo,rhi) for v in (lo,hi)]
                # Bound denominator growth while retaining outward rounding.
                updated.append((F(endpoint(min(products),False)),F(endpoint(max(products),True))))
            history=updated
        upper+=_quadratic(w,matrix,w)
        for j in range(3):
            coefficient=2*sum((w[k]*matrix[k][j] for k in range(3)),F(0))
            upper+=coefficient*history[j][1 if coefficient>=0 else 0]
    return upper


def _integrated_variance(times,weights,origin,qa,h):
    """Integrate weighted Brownian kernels exactly, retaining signed axes."""
    s0=[sum((w[j] for w in weights),F(0)) for j in range(3)]
    s1=[sum((w[j]*t for w,t in zip(weights,times,strict=True)),F(0)) for j in range(3)]
    s2=[sum((w[j]*t*t for w,t in zip(weights,times,strict=True)),F(0)) for j in range(3)]
    value=F(0);left=origin
    for right,w in zip(times,weights,strict=True):
        kernels=((qa,[s1,[-v for v in s0]]),
            (h,[[v/2 for v in s2],[-v for v in s1],[v/2 for v in s0]]))
        for matrix,polynomial in kernels:
            if not any(v for row in matrix for v in row):continue
            for a,ca in enumerate(polynomial):
                for b,cb in enumerate(polynomial):
                    coefficient=_quadratic(ca,matrix,cb);power=a+b+1
                    if coefficient:value+=coefficient*(right**power-left**power)/power
        for j in range(3):s0[j]-=w[j];s1[j]-=w[j]*right;s2[j]-=w[j]*right*right
        left=right
    if value<0:raise ValueError('negative exact integrated variance')
    return value


def projected_variance_bounds(times,weights,*,receiver,origin_s,accel_psd,gyro_psd,coupling,clock_interval_s):
    """Certify variances of fixed signed metre summaries under the supplied law.

    Rows must be chosen independently of observations and fitted residuals. The
    identity of the complete parent law is preserved; a separate projection
    identity binds the row coefficients. Common-clock maxima may differ between
    components, so these are upper bounds, not covariance estimates or lower
    bounds. No empirical error-law or nonlinear propagation qualification follows.
    """
    import numpy as np
    from lll.ilvis0_saved_prediction_audit import endpoint
    parent=marginal_variance_bounds(times,receiver=receiver,origin_s=origin_s,accel_psd=accel_psd,
        gyro_psd=gyro_psd,coupling=coupling,clock_interval_s=clock_interval_s)
    t=list(map(_scalar,times));rows=np.array(weights,float,copy=True)
    if (rows.ndim!=2 or not len(rows) or rows.shape[1]!=3*len(t)
            or not np.all(np.isfinite(rows))):
        raise ValueError('nonempty finite fixed rows with three columns per epoch required')
    qa=_matrix(accel_psd,psd=True);qg=_matrix(gyro_psd,psd=True);g=_matrix(coupling)
    h=[[sum((g[i][a]*qg[a][b]*g[j][b] for a in range(3) for b in range(3)),F(0))
        for j in range(3)] for i in range(3)]
    white=_matrix(receiver.white,positive=True);offset=_matrix(receiver.offset,psd=True)
    drift=_matrix(receiver.drift,psd=True);dorigin=_scalar(receiver.drift_origin_s)
    dspan=_scalar(receiver.drift_span_s);origin=_scalar(origin_s)
    clock=tuple(map(_scalar,clock_interval_s));shifted=[v+clock[1] for v in t]
    components=[(_scalar(tau),_matrix(matrix,psd=True)) for tau,matrix in receiver.components]
    exact=[];bound_rows=[];cache={}
    for row in rows:
        rw=list(map(_scalar,row));w=[rw[i:i+3] for i in range(0,len(rw),3)]
        total=sum((_quadratic(v,white,v) for v in w),F(0))
        combined=[sum((v[j] for v in w),F(0)) for j in range(3)]
        total+=_quadratic(combined,offset,combined)
        drift_vectors=[[sum((v[j]*(epoch+theta-dorigin)/dspan
            for v,epoch in zip(w,t,strict=True)),F(0)) for j in range(3)] for theta in clock]
        total+=max(_quadratic(v,drift,v) for v in drift_vectors)
        total+=_integrated_variance(shifted,w,origin,qa,h)
        for tau,matrix in components:total+=_ou_variance_upper(t,w,tau,matrix,cache)
        if total<0:raise ValueError('negative certified variance upper bound')
        exact.append(str(total));bound_rows.append(list(map(str,rw)))
    result=np.array([endpoint(F(v),True) for v in exact]);result.setflags(write=False)
    projection=dict(version='ilvis0-fixed-linear-variance-v1',covariance_id=parent['covariance_id'],weights=bound_rows)
    identity=hashlib.sha256(json.dumps(projection,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return dict(parent,variance_upper_m2=result,exact_variance_upper_m2=exact,projection_id=identity,
        row_count=len(rows),projection=projection,
        variance_arithmetic='exact_polynomial_integrals_and_outward_exponential_recurrence')
