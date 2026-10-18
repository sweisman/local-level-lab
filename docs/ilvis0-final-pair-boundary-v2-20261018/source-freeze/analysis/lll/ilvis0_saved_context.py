# SPDX-License-Identifier: AGPL-3.0-or-later
"""Attach independently saved receiver context without changing fit arrays."""
import gzip
import json
import math


def finite(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)


def context_bytes(saved,epochs,receiver_fixes,*,initial_time_s):
    try:
        times=epochs['times_s'];names=saved['active_parameters'];point=saved['normalized_parameters']
        residual=saved['residual'];jacobian=saved['jacobian']
        gps=[[r['latitude_rad'],r['longitude_rad'],r['height_m']] for r in receiver_fixes]
        absolute=[r['time_s'] for r in receiver_fixes]
        if (not finite(initial_time_s) or len(times)<2 or len(times)!=len(gps)
                or not names or len(set(names))!=len(names) or len(point)!=len(names)
                or len(residual)!=3*len(times) or len(jacobian)!=len(residual)
                or any(len(row)!=len(names) for row in jacobian)
                or any(not finite(v) for v in times+absolute+point+residual)
                or any(not finite(v) for row in gps+jacobian for v in row)
                or any(b<=a for a,b in zip(absolute,absolute[1:]))
                or times!=[t-initial_time_s for t in absolute]
                or ('times_s' in saved and saved['times_s']!=times)
                or ('gps' in saved and saved['gps']!=gps)):
            raise ValueError('exact finite saved context and array layout required')
    except (KeyError,TypeError) as error:
        raise ValueError('complete receiver records and saved arrays required') from error
    payload=dict(saved,times_s=times,gps=gps)
    return gzip.compress(json.dumps(payload,sort_keys=True,allow_nan=False).encode(),mtime=0)
