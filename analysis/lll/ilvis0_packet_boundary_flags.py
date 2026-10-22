# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check the native single-query packet-boundary counter from its timestamps.

This classifies the kernel's counter; it does not prove differentiability at
the boundary or a whole-program enclosure. Integration failure remains fatal.
"""
import math


def validate(*,status,counter,dt,time_s,clock_offset_s):
    import numpy as np
    durations=np.asarray(dt,float);query=float(time_s)+float(clock_offset_s)
    if (status!=0 or type(counter) is not int or counter not in (0,1)
            or durations.ndim!=1 or not len(durations) or not np.all(np.isfinite(durations))
            or np.any(durations<=0.) or not math.isfinite(query) or query<0.):
        raise ValueError('successful single query and valid integration support required')
    ends=np.cumsum(durations);index=int(np.searchsorted(ends,query,side='left'))
    if index>=len(ends):raise ValueError('query outside complete packet support')
    start=0. if index==0 else float(ends[index-1])
    fraction=(query-start)/float(durations[index])
    if fraction < -1e-10 or fraction > 1.+1e-10:
        raise ValueError('query outside its declared packet')
    expected=int(fraction<1e-8 or fraction>1.-1e-8)
    if counter!=expected:raise ValueError('native boundary counter disagrees with timestamps')
    return dict(query_supported=True,packet_boundary=bool(expected),packet_index=index,
        fraction=fraction,counter=counter,derivative_smoothness_qualified=False)
