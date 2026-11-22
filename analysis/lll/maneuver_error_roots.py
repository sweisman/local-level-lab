# SPDX-License-Identifier: AGPL-3.0-or-later
"""Causal position-error roots from persistent and motion-linked acceleration."""

import math


def turn_exposure(dt, angles_rad, times, *, previous_time, threshold_deg_s):
    """Integrate squared logged angular-rate magnitude over causal report intervals."""
    import numpy as np

    dt, angles, times = (np.asarray(value,float) for value in (dt, angles_rad, times))
    if (dt.ndim!=1 or not len(dt) or angles.shape!=(len(dt),3) or np.any(dt<=0)
            or times.ndim!=1 or not len(times) or np.any(np.diff(times)<=0)
            or not all(np.isfinite(v).all() for v in (dt,angles,times))
            or not math.isfinite(previous_time) or not 0<=previous_time<times[0]
            or not math.isfinite(threshold_deg_s) or threshold_deg_s<=0):
        raise ValueError('timed three-axis logged angular increments and supported ordered queries required')
    ends=np.cumsum(dt)
    query=np.r_[previous_time,times]
    if query[-1]>ends[-1]:
        raise ValueError('complete logged angle support is required for the final query')
    index=np.searchsorted(ends,query,side='left')
    start=np.r_[0.,ends[:-1]]
    rate=np.rad2deg(np.linalg.norm(angles,axis=1))/dt
    squared=rate**2
    left=np.r_[0.,np.cumsum(squared*dt)[:-1]]
    integrated=left[index]+squared[index]*(query-start[index])
    return np.maximum(0.,np.diff(integrated)-np.diff(query)*threshold_deg_s**2)


def roots(times, exposure, *, previous_time, decay_s):
    """Unit acceleration offsets and exponentially decaying maneuver shocks."""
    import numpy as np

    times, exposure=(np.asarray(value,float) for value in (times,exposure))
    if (times.ndim!=1 or not len(times) or exposure.shape!=times.shape
            or np.any(np.diff(times)<=0) or np.any(exposure<0)
            or not np.isfinite(times).all() or not np.isfinite(exposure).all()
            or not math.isfinite(previous_time) or not previous_time<times[0]
            or not math.isfinite(decay_s) or decay_s<=0):
        raise ValueError('aligned ordered queries, causal positive exposure and decay required')
    ages=times-previous_time
    lag=np.maximum(times[:,None]-times[None,:],0.)/decay_s
    receiver_response=decay_s**2*(lag+np.expm1(-lag))*np.sqrt(exposure)[None,:]
    return dict(persistent=np.kron((.5*ages**2)[:,None],np.eye(3)),
                maneuver=np.kron(receiver_response,np.eye(3)[:,:2]))
