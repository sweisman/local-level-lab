# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separately qualified diagnostic arithmetic; original wide kernel unchanged.

The alternative timing slope applies only at the normalized lower offset bound.
Interior packet knots still have two branches, not a unique smooth derivative.
Relative longitude changes the accumulation origin, not the physical equations.
"""
import math
from pathlib import Path

VERSION='diagnostic-boundary-relative-longitude-v1'


def recentered(kernel):
    """Wrap an explicitly supplied native provider; no process-global patching."""
    import numpy as np
    if not callable(kernel):raise ValueError('explicit native provider required')
    def relative(*args,observations=None,difference=None):
        if len(args)!=18:raise ValueError('original complete tangent ABI required')
        coordinates=np.array(args[6],dtype=float,copy=True,order='C')
        origin=float(coordinates[1]);coordinates[1]=0.
        observations=np.zeros((args[4],3)) if observations is None else np.array(observations,dtype=float,copy=True,order='C')
        observations[:,1]-=origin
        if not np.all(np.isfinite(observations)):raise ValueError('relative receiver coordinates overflow')
        values=list(args);values[6]=coordinates
        code=kernel(*values,observations=observations,difference=difference)
        if code==0:args[15][:,1]+=origin
        return code
    return relative


def derive(source,*,expected_sha256,right_at_lower):
    from lll.ilvis0_wide_tangent import derive as wide
    if type(right_at_lower) is not bool:raise ValueError('explicit boolean timing alternative required')
    text=wide(source,expected_sha256=expected_sha256)
    if not right_at_lower:return text
    old=b'while(j<m && times[j]+static_cast<double>(p[25].v)<=end) {'
    new=(b'while(j<m && times[j]+static_cast<double>(p[25].v)<=end && '
         b'!(point[25]==-1. && times[j]+static_cast<double>(p[25].v)==end)) {')
    if text.count(old)!=1:raise ValueError('unsupported exact packet-dispatch layout')
    return text.replace(old,new)


def load(directory,*,right_at_lower,relative_longitude,reserve_build,
         gravity_anchor_height_m=None,expected_source_sha256=None):
    from lll.native_tangent import load as native
    from lll.studies.artifacts import digest
    if (type(right_at_lower) is not bool or type(relative_longitude) is not bool
            or not callable(reserve_build) or (gravity_anchor_height_m is not None
            and (not math.isfinite(gravity_anchor_height_m) or gravity_anchor_height_m<=-6371000.))):
        raise ValueError('explicit diagnostic choices, charged build and supported gravity anchor required')
    original=Path(__file__).with_name('ilvis0_tangent.cpp').read_bytes();sha=digest(original)
    raw=derive(original,expected_sha256=sha if expected_source_sha256 is None else expected_source_sha256,
        right_at_lower=right_at_lower)
    kernel,meta=native(directory,raw,prefix='timing-arithmetic',expected_sha256=digest(raw),
        reserve_build=reserve_build,gravity_anchor_height_m=gravity_anchor_height_m)
    return (recentered(kernel) if relative_longitude else kernel),dict(meta,version=VERSION,original_source_sha256=sha,
        right_branch_at_normalized_lower_bound=right_at_lower,relative_longitude=relative_longitude,
        upper_bound_branch='original-left',interior_knot_derivative='original-left-not-unique',
        gravity_anchor_height_m=gravity_anchor_height_m,physical_equations_changed=False,
        fit_acceptance_changed=False,production_qualified=False)
