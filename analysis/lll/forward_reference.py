# SPDX-License-Identifier: AGPL-3.0-or-later
"""Opt-in matched roll reference with a joint GPS/IMU moment covariance."""
import numpy as np
from .attitude import course_rate, unit
from .models import G0

FORWARD_REFERENCE_POLICY = dict(version='matched-forward-1', window_seconds=30.,
    course_difference_seconds=5., hac_seconds=60., minimum_covariance_windows=4,
    minimum_bank_energy=1e-4, minimum_gain=.1, minimum_r2=.05, maximum_gps_interval_seconds=2.,
    coverage_status='development; independent calibration and real-device checks pending')


def matched_filter(t, values, valid, window_seconds=30.):
    """Same Hann kernel on all columns; complete regular runs only, no gap bridging."""
    t, values = np.asarray(t, float), np.asarray(values, float)
    valid = np.asarray(valid, bool) & np.isfinite(values).all(axis=1)
    filtered, keep = np.full_like(values, np.nan), np.zeros(len(t), bool)
    if len(t) < 3:
        return filtered, keep
    step = float(np.median(np.diff(t)))
    if step <= 0 or window_seconds <= 0:
        raise ValueError('positive timestamps and filter duration required')
    half = max(1, int(np.ceil(window_seconds/step/2)))
    kernel = np.hanning(2*half+1); kernel /= kernel.sum()
    cuts = np.r_[0, np.flatnonzero(abs(np.diff(t)-step) > .05*step)+1, len(t)]
    for left, right in zip(cuts[:-1], cuts[1:]):
        good = valid[left:right]
        starts = np.flatnonzero(good & ~np.r_[False, good[:-1]])+left
        ends = np.flatnonzero(good & ~np.r_[good[1:], False])+left+1
        for start, end in zip(starts, ends):
            if end-start < len(kernel): continue
            target = slice(start+half, end-half)
            for column in range(values.shape[1]):
                filtered[target, column] = np.convolve(values[start:end, column], kernel, mode='valid')
            keep[target] = True
    return filtered, keep


def matched_rows(gyro_t, gyro, gps_t, speed, course, up):
    gyro_t, gyro, gps_t = np.asarray(gyro_t,float), np.asarray(gyro,float), np.asarray(gps_t,float)
    speed, course = np.asarray(speed,float), np.asarray(course,float)
    if len(gps_t)<3 or len(gyro_t)<3:
        return None, 'too little GPS or gyro'
    if not np.isfinite(gps_t).all() or not np.isfinite(gyro_t).all() or np.any(np.diff(gps_t)<=0) or np.any(np.diff(gyro_t)<=0):
        raise ValueError('finite increasing GPS and gyro timestamps required')
    if not np.isfinite(gyro).all(): return None, 'nonfinite gyro'
    proxy = np.full(len(gps_t), np.nan)
    step = np.median(np.diff(gps_t))
    if step > FORWARD_REFERENCE_POLICY['maximum_gps_interval_seconds']:
        return None, 'matched forward reference requires frequent GPS'
    cuts = np.r_[0, np.flatnonzero(abs(np.diff(gps_t)-step)>.05*step)+1, len(gps_t)]
    for left, right in zip(cuts[:-1], cuts[1:]):
        if right-left<7: continue
        sl = slice(left,right)
        bank = np.arctan(speed[sl]*course_rate(gps_t[sl],course[sl],
                        FORWARD_REFERENCE_POLICY['course_difference_seconds'])/G0)
        proxy[sl] = np.gradient(bank,gps_t[sl])
        edge = max(1,int(round(FORWARD_REFERENCE_POLICY['course_difference_seconds']/step/2)))+1
        proxy[left:left+edge] = np.nan; proxy[max(left,right-edge):right] = np.nan
    lo, hi = np.searchsorted(gyro_t,gps_t-.5), np.searchsorted(gyro_t,gps_t+.5)
    cs = np.vstack([np.zeros(3),np.cumsum(gyro,axis=0)])
    averaged = (cs[hi]-cs[lo])/np.maximum(hi-lo,1)[:,None]
    normal = unit(up)
    horizontal = averaged-(averaged@normal)[:,None]*normal
    supported = (hi>lo)&(gps_t-.5>=gyro_t[0])&(gps_t+.5<=gyro_t[-1])
    for gap in np.flatnonzero(np.diff(gyro_t)>3*np.median(np.diff(gyro_t))):
        supported &= ~((gps_t+.5>=gyro_t[gap])&(gps_t-.5<=gyro_t[gap+1]))
    values, valid = matched_filter(gps_t,np.column_stack([proxy,horizontal]),supported,
                                   FORWARD_REFERENCE_POLICY['window_seconds'])
    indices = np.flatnonzero(valid)
    runs = np.cumsum(np.r_[True,np.diff(indices)>1]) if len(indices) else np.array([],int)
    return dict(t=gps_t[valid],x=values[valid,0],g=values[valid,1:],run=runs,step=step,up=normal), None


def direction(rows):
    x, g = rows['x'], rows['g']
    energy = float(x@x)
    if energy < FORWARD_REFERENCE_POLICY['minimum_bank_energy']:
        return None, dict(reason='insufficient filtered bank energy',bank_energy=energy,samples=len(x))
    coefficient = np.sum(g*x[:,None],axis=0)/energy
    gain = float(np.linalg.norm(coefficient))
    residual = g-x[:,None]*coefficient
    r2 = float(1-np.sum(residual**2)/max(np.sum(g**2),1e-30))
    q = dict(gain=gain,r2=r2,bank_energy=energy,samples=len(x))
    if gain < FORWARD_REFERENCE_POLICY['minimum_gain'] or r2 < FORWARD_REFERENCE_POLICY['minimum_r2']:
        return None, {**q,'reason':'roll/bank correlation too weak'}
    return coefficient, q


def joint_covariance(x, g, run, coefficient, lags):
    """Sandwich for the joint observed moment; neither GPS nor gyro held fixed.

    For the angle, tangent·coefficient=0, so its score is x*(tangent·g).
    Normalizing the cross-moment changes gain but not the direction. This does
    not correct directional bias from correlated measurement errors or model error.
    """
    score = x[:,None]*(g-x[:,None]*coefficient)
    meat = score.T@score
    for lag in range(1,min(lags,len(x)-1)+1):
        same = run[lag:]==run[:-lag]
        cross = score[lag:][same].T@score[:-lag][same]
        meat += (1-lag/(lags+1))*(cross+cross.T)
    return (meat+meat.T)/2/float(x@x)**2


def estimate_forward_axis(gyro_t, gyro, gps_t, speed, course, up):
    rows, reason = matched_rows(gyro_t,gyro,gps_t,speed,course,up)
    q = dict(reference_method='matched',reference_policy=dict(FORWARD_REFERENCE_POLICY))
    if rows is None: return None, {**q,'reason':reason}
    coefficient, quality = direction(rows); q.update(quality)
    if coefficient is None: return None,q
    lags = max(1,int(np.ceil(FORWARD_REFERENCE_POLICY['hac_seconds']/rows['step'])))
    windows = sum(np.sum(rows['run']==run)//(lags+1) for run in np.unique(rows['run']))
    q.update(hac_lags=lags,covariance_support_windows=int(windows))
    if windows < FORWARD_REFERENCE_POLICY['minimum_covariance_windows']:
        return None,{**q,'reason':'insufficient independent-duration covariance support'}
    covariance = joint_covariance(rows['x'],rows['g'],rows['run'],coefficient,lags)
    gain = np.linalg.norm(coefficient); axis = coefficient/gain
    jac = (np.eye(3)-np.outer(axis,axis))/gain
    axis_cov = jac@covariance@jac.T
    tangent = np.cross(rows['up'],axis)
    variance = float(tangent@axis_cov@tangent)
    if not np.isfinite(variance) or variance<=0:
        return None,{**q,'reason':'positive measured angular variance unavailable'}
    q.update(regression_cov=covariance.tolist(),axis_cov=axis_cov.tolist(),
             angle_sigma_rad=float(np.sqrt(variance)),
             uncertainty_method='joint GPS/IMU moment, run-separated Bartlett HAC',
             predictor_treatment='random observed predictor; independent-error direction assumption',
             coverage_status=FORWARD_REFERENCE_POLICY['coverage_status'])
    return axis,q
