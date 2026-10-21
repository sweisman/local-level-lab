# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small-problem linear inertial-noise covariance, with supplied error law.

State order is position, velocity, small orientation error (three axes each).
Units are metres, metres/second and radians. Independent acceleration and gyro
white-noise spectral matrices have units m^2/s^3 and rad^2/s. The supplied
constant coupling maps orientation error to acceleration. No hardware defaults,
parameter fitting, nonlinear propagation guarantee or observational coverage.
"""
import math

import numpy as np

from .ilvis0_error_model import component, covariance, factor


def _duration(value):
    dt=float(value)
    if not math.isfinite(dt) or dt<0.:
        raise ValueError('finite nonnegative duration required')
    return dt


def _coupling(value):
    matrix=np.asarray(value,dtype=float)
    if matrix.shape!=(3,3) or not np.all(np.isfinite(matrix)):
        raise ValueError('finite three-by-three acceleration/orientation coupling required')
    return matrix


def _finite(matrix):
    if not np.all(np.isfinite(matrix)):
        raise ValueError('unrepresentable linear covariance or transition')
    return matrix


def transition(dt,coupling):
    """Exact constant-coefficient linear transition; no stochastic fit."""
    dt=_duration(dt); g=_coupling(coupling)
    result=np.eye(9)
    result[:3,3:6]=np.eye(3)*dt
    result[:3,6:]=g*(dt**2/2.)
    result[3:6,6:]=g*dt
    return _finite(result)


def process_covariance(dt,accel_psd,gyro_psd,coupling):
    """Integral of F(s) Q F(s)^T for the declared independent white drives.

    Zero/rank-deficient driving spectra are supported without adding jitter or
    clipping eigenvalues. Initial-state/calibration uncertainty is not included.
    """
    dt=_duration(dt); g=_coupling(coupling)
    qa=component(accel_psd); qg=component(gyro_psd)
    gq=g@qg; gqgt=gq@g.T
    result=np.zeros((9,9))
    result[:3,:3]=qa*(dt**3/3.)+gqgt*(dt**5/20.)
    result[:3,3:6]=qa*(dt**2/2.)+gqgt*(dt**4/8.)
    result[:3,6:]=gq*(dt**3/6.)
    result[3:6,3:6]=qa*dt+gqgt*(dt**3/3.)
    result[3:6,6:]=gq*(dt**2/2.)
    result[6:,6:]=qg*dt
    result[3:6,:3]=result[:3,3:6].T
    result[6:,:3]=result[:3,6:].T
    result[6:,3:6]=result[3:6,6:].T
    return _finite((result+result.T)/2.)


def position_covariance(times,*,origin_s,accel_psd,gyro_psd,coupling):
    """Dense diagnostic covariance, preserving a supplied noise-integration origin.

    At most 512 epochs. Epoch-major three-coordinate order. A later subset does
    not reset the integration origin. All cross-training/future terms survive.
    """
    t=np.asarray(times,dtype=float); origin=float(origin_s)
    if (t.ndim!=1 or not len(t) or not np.all(np.isfinite(t))
            or not math.isfinite(origin) or np.any(np.diff(t)<=0.) or t[0]<origin):
        raise ValueError('ordered finite epochs at or after the declared origin required')
    if len(t)>512:
        raise ValueError('dense diagnostic supports at most 512 epochs')
    g=_coupling(coupling); qa=component(accel_psd); qg=component(gyro_psd)
    result=np.empty((3*len(t),3*len(t)))
    for i,time in enumerate(t):
        prior=process_covariance(time-origin,qa,qg,g)
        for j in range(i,len(t)):
            block=(prior@transition(t[j]-time,g).T)[:3,:3]
            result[3*i:3*i+3,3*j:3*j+3]=block
            result[3*j:3*j+3,3*i:3*i+3]=block.T
    return _finite((result+result.T)/2.)


def joint_covariance(times,receiver_spec,*,origin_s,accel_psd,gyro_psd,coupling,transforms=None):
    """Sum independent receiver and integrated inertial errors, then transform.

    Receiver/inertial independence and the linear stochastic approximation are
    supplied assumptions. The output is not a calibrated aircraft error law.
    """
    result=position_covariance(times,origin_s=origin_s,accel_psd=accel_psd,
                               gyro_psd=gyro_psd,coupling=coupling)
    result+=covariance(times,receiver_spec)
    if transforms is not None:
        n=len(times); a=np.asarray(transforms,dtype=float)
        if (a.shape!=(n,3,3) or not np.all(np.isfinite(a))
                or np.any(np.linalg.slogdet(a)[0]==0)):
            raise ValueError('finite invertible per-epoch transforms required')
        result=np.einsum('iab,ibjc,jdc->iajd',a,result.reshape(n,3,n,3),a).reshape(3*n,3*n)
    result=_finite((result+result.T)/2.)
    factor(result)  # Reject numerical failure; do not repair the covariance.
    return result
