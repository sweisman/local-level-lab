# SPDX-License-Identifier: AGPL-3.0-or-later
"""Descriptive logged-rate contrasts; no isolated-noise or physical decision."""
import math

VERSION='logged-rate-variation-v1'
SAMPLING='independent_equal_variance_point_errors_for_normalization_only'


def _arrays(times,values,maximum_points,maximum_gap_s):
    import numpy as np
    t=np.asarray(times,dtype=float);v=np.asarray(values,dtype=float)
    if (type(maximum_points) is not int or not 3<=maximum_points<=360100
            or t.ndim!=1 or not 3<=len(t)<=maximum_points or v.shape!=(len(t),6)
            or not np.all(np.isfinite(t)) or not np.all(np.isfinite(v))):
        raise ValueError('bounded finite timestamps and all six aligned rate channels required')
    dt=np.diff(t)
    if np.any(dt<=0):raise ValueError('strict timestamp order required')
    if maximum_gap_s is not None:
        if not math.isfinite(maximum_gap_s) or maximum_gap_s<=0 or np.any(dt>maximum_gap_s):
            raise ValueError('unsupported timestamp gap')
    return t,v


def training_prefix(times,values,*,last_training_time_s,maximum_points):
    """Copy only the earlier rate values; later channel values are not examined."""
    import numpy as np
    t=np.asarray(times,dtype=float);v=np.asarray(values)
    if (type(maximum_points) is not int or not 3<=maximum_points<=360100
            or t.ndim!=1 or not 3<=len(t)<=maximum_points or v.shape!=(len(t),6)
            or not np.all(np.isfinite(t)) or np.any(np.diff(t)<=0)
            or not math.isfinite(last_training_time_s) or not t[0]<=last_training_time_s<=t[-1]):
        raise ValueError('bounded ordered sample times and explicit supported training cutoff required')
    end=int(np.searchsorted(t,last_training_time_s,side='right'))
    earlier_t=t[:end].copy();earlier_v=np.asarray(v[:end],dtype=float).copy()
    _arrays(earlier_t,earlier_v,maximum_points,None)
    return earlier_t,earlier_v


def contrasts(times,values,*,stride,maximum_points,maximum_gap_s=None):
    """Disjoint three-point contrasts removing a linear trend at actual times."""
    import numpy as np
    t,v=_arrays(times,values,maximum_points,maximum_gap_s)
    if type(stride) is not int or stride<1 or len(t)<2*stride+1:
        raise ValueError('positive finite stride with at least one complete triple required')
    first=np.arange(0,len(t)-2*stride,3*stride)
    indices=first[:,None]+np.array([0,stride,2*stride])
    selected=t[indices];span=selected[:,2]-selected[:,0]
    a=(selected[:,1]-selected[:,0])/span
    c=v[indices[:,1]]-(1-a[:,None])*v[indices[:,0]]-a[:,None]*v[indices[:,2]]
    c=c/np.sqrt(1+(1-a)**2+a*a)[:,None]
    if not np.all(np.isfinite(c)):raise ValueError('unrepresentable rate contrast')
    return dict(values=c,indices=indices,count=len(first),discarded_points=len(t)-3*len(first),
        separation_s=span.tolist(),sampling_assumption=SAMPLING)


def summarize(times,values,*,strides,maximum_points,maximum_gap_s):
    import numpy as np
    t,v=_arrays(times,values,maximum_points,maximum_gap_s)
    strides=tuple(strides)
    if not strides or len(strides)>4 or len(set(strides))!=len(strides):
        raise ValueError('one to four unique fixed strides required')
    rows=[]
    for stride in strides:
        result=contrasts(t,v,stride=stride,maximum_points=maximum_points,maximum_gap_s=maximum_gap_s)
        c=result['values'];spans=result['separation_s']
        row=dict(stride=stride,count=result['count'],unused_sample_count=result['discarded_points'],
            minimum_span_s=min(spans),median_span_s=float(np.median(spans)),maximum_span_s=max(spans),
            rms_native_units=np.sqrt(np.mean(c*c,axis=0)).tolist(),
            median_absolute_native_units=np.median(abs(c),axis=0).tolist(),
            percentile_99_absolute_native_units=np.quantile(abs(c),.99,axis=0).tolist(),
            sampling_assumption=SAMPLING)
        if any(not np.all(np.isfinite(row[k])) for k in ('rms_native_units','median_absolute_native_units',
                'percentile_99_absolute_native_units')):raise ValueError('unrepresentable descriptive statistic')
        rows.append(row)
    return dict(version=VERSION,points=len(t),duration_s=float(t[-1]-t[0]),
        median_interval_s=float(np.median(np.diff(t))),minimum_interval_s=float(np.diff(t).min()),
        maximum_interval_s=float(np.diff(t).max()),channel_order=['gyro_x','gyro_y','gyro_z','force_x','force_y','force_z'],
        channel_units=['rad/s']*3+['m/s^2']*3,
        mean_native_units=np.mean(v,axis=0).tolist(),minimum_native_units=v.min(axis=0).tolist(),
        maximum_native_units=v.max(axis=0).tolist(),contrasts=rows,total_contrasts=sum(r['count'] for r in rows),
        isolated_sensor_noise_estimated=False,error_distribution_established=False,
        nominal_period_white_noise_conversion_applied=False,fitted_parameters=0,interpolated_points=0,
        scientific_decision='abstain')
