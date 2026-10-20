# SPDX-License-Identifier: AGPL-3.0-or-later
"""Local body-only approximation bounds for a declared linear-point hypothesis.

No claim about the instrument's actual sampling/averaging or a floating-point
enclosure. Geographic integration and uncertainty propagation remain separate.
"""
import math

VERSION='esa-linear-point-body-approximation-v1'


def _vector(value):
    try:result=tuple(float(x) for x in value)
    except (TypeError,ValueError) as error:raise ValueError('three finite components required') from error
    if len(result)!=3 or not all(math.isfinite(x) for x in result):raise ValueError('three finite components required')
    return result


def local_bounds(omega_left,omega_right,force_left,force_right,dt_s):
    """Bound midpoint rotation and integrated force for linear point channels.

    The rotation error is a dimensionless operator norm; force error is m/s.
    Neither is an angular-rate bias nor a position-error bound.
    """
    if not math.isfinite(dt_s) or dt_s<=0.:raise ValueError('finite positive interval required')
    a,b,f,g=map(_vector,(omega_left,omega_right,force_left,force_right))
    w=tuple((x+y)/2 for x,y in zip(a,b));slope=tuple((y-x)/dt_s for x,y in zip(a,b))
    force_slope=tuple((y-x)/dt_s for x,y in zip(f,g))
    cross=(w[1]*slope[2]-w[2]*slope[1],w[2]*slope[0]-w[0]*slope[2],w[0]*slope[1]-w[1]*slope[0])
    h=dt_s;rate=math.hypot(*w);change=math.hypot(*slope);force=max(math.hypot(*f),math.hypot(*g))
    rotation=min(2.,math.hypot(*cross)*h**3/12+change**2*h**4/32)
    velocity=change*force*h**3/8+(rate**2*force+2*rate*math.hypot(*force_slope))*h**3/24
    if not all(math.isfinite(x) for x in (rotation,velocity)):raise ValueError('local approximation bound overflow')
    return dict(version=VERSION,rotation_operator_error=math.nextafter(rotation,math.inf) if rotation else 0.,
        force_integral_error_mps=math.nextafter(velocity,math.inf) if velocity else 0.,
        sampling_hypothesis='linear_point_rates_and_force',actual_instrument_phase_established=False,
        global_position_bound=False,floating_point_enclosure_verified=False,scientific_decision='abstain')
