# SPDX-License-Identifier: AGPL-3.0-or-later
"""Geographic adapter that preserves vector coordinates without global patches."""
import math
import numpy as np
from . import ilvis0_geographic_bounds as base
from .ilvis0_geographic_bounds import Scalar,Coordinates,State,_up,_ends,_advance,plus,times,fixed_scale,inverse,power,sine,cosine
from .ilvis0_component_transport import Value,component as _component,_norm


def _pack(values):
    d=[v.value.change for v in values];r=[v.value.remainder for v in values]
    return Value([v.center for v in values],_norm(d),_norm(r),component_change=d,component_remainder=r)


def coordinate_map(position,vector,*,model,disc_radius_m):
    if not math.isfinite(disc_radius_m) or disc_radius_m<=0:raise ValueError('explicit positive disc radius required')
    phi=position.latitude;height=position.height
    if model=='flat_still':
        north=Scalar.fixed(disc_radius_m);east=fixed_scale(plus(Scalar.fixed(math.pi/2),fixed_scale(phi,-1)),disc_radius_m)
    elif model in ('sphere_rotating','sphere_still'):
        d=plus(Scalar.fixed(1),fixed_scale(times(sine(phi),sine(phi)),-base.E2))
        north=plus(fixed_scale(power(d,-1.5),base.A*(1-base.E2)),height)
        east=times(plus(fixed_scale(power(d,-.5),base.A),height),cosine(phi))
    else:raise ValueError('supported physical candidate required')
    if min(north.lower,east.lower)<=0:raise ValueError('nonpositive geographic metric domain')
    return times(_component(vector,0),inverse(north)),times(_component(vector,1),inverse(east)),fixed_scale(_component(vector,2),-1)


def transport_context(latitude,rates,model):
    if model=='flat_still':return _pack((Scalar.fixed(0),Scalar.fixed(0),fixed_scale(rates[1],-1)))
    return _pack((times(cosine(latitude),rates[1]),fixed_scale(rates[0],-1),fixed_scale(times(sine(latitude),rates[1]),-1)))
