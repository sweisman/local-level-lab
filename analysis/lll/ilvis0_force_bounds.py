# SPDX-License-Identifier: AGPL-3.0-or-later
"""Conservative nonlinear geographic-force boxes under explicit input bounds.

This uses the same declared geometry/apparent-gravity convention as the point
adapter, but interval propagation rather than a tangent or sampling envelope.
Arithmetic widens endpoints by one representable float. This is not a formal
libm rounding certificate, a probability distribution or a calibrated test.
"""
import math

import numpy as np

from .models import WGS84_A, WGS84_E2


class _Box:
    def __init__(self, lo, hi=None):
        self.lo, self.hi = float(lo), float(lo if hi is None else hi)
        if not math.isfinite(self.lo) or not math.isfinite(self.hi) or self.lo > self.hi:
            raise ValueError('finite ordered interval required')

    @staticmethod
    def cast(value):
        return value if isinstance(value, _Box) else _Box(value)

    @staticmethod
    def outward(lo, hi):
        return _Box(np.nextafter(lo, -np.inf), np.nextafter(hi, np.inf))

    def __add__(self, other):
        other = self.cast(other)
        return self.outward(self.lo+other.lo, self.hi+other.hi)

    __radd__ = __add__

    def __neg__(self):
        return _Box(-self.hi, -self.lo)

    def __sub__(self, other):
        return self+-self.cast(other)

    def __rsub__(self, other):
        return self.cast(other)+-self

    def __mul__(self, other):
        other = self.cast(other)
        corners = [self.lo*other.lo, self.lo*other.hi, self.hi*other.lo, self.hi*other.hi]
        return self.outward(min(corners), max(corners))

    __rmul__ = __mul__

    def __truediv__(self, other):
        other = self.cast(other)
        if other.lo <= 0. <= other.hi:
            raise ValueError('division interval crosses zero')
        return self*self.outward(1./other.hi, 1./other.lo)

    def square(self):
        lo = 0. if self.lo <= 0. <= self.hi else min(self.lo**2, self.hi**2)
        hi = max(self.lo**2, self.hi**2)
        return _Box(max(0., np.nextafter(lo, -np.inf)), np.nextafter(hi, np.inf))

    def positive_power(self, exponent):
        if self.lo <= 0.:
            raise ValueError('positive interval required for metric power')
        values = [self.lo**exponent, self.hi**exponent]
        return self.outward(min(values), max(values))


def force_bounds(jet_bounds, *, model, background_rate_bounds_rads,
                 gravity_bounds_mps2, disc_radius_m):
    """Enclose force components and magnitude for a nine-dimensional jet box.

    The jet order is lat/lon/height, their rates, then their accelerations;
    units radians/metres/seconds. Component dependence is conservatively
    discarded. Different candidates must receive the same coordinate bounds
    and defensible gravity/calibration allowances. Bounds are not inferred here.
    """
    jet = np.asarray(jet_bounds, float)
    if (jet.shape != (9, 2) or not np.all(np.isfinite(jet))
            or np.any(jet[:, 1] < jet[:, 0])):
        raise ValueError('finite ordered nine-component coordinate-jet box required')
    if model not in ('sphere_rotating', 'sphere_still', 'flat_still'):
        raise ValueError('unsupported physical candidate')
    def physical(value):
        value = np.asarray(value, float)
        if value.shape != (2,):
            raise ValueError('two physical interval endpoints required')
        return _Box(*value)
    omega = physical(background_rate_bounds_rads)
    gravity = physical(gravity_bounds_mps2)
    if (gravity.lo <= 0. or not math.isfinite(disc_radius_m) or disc_radius_m <= 0.
            or (model != 'sphere_rotating' and (omega.lo != 0. or omega.hi != 0.))):
        raise ValueError('positive gravity/radius and model-consistent field bounds required')
    phi, _, height, p, l, h, pp, ll, hh = [_Box(*row) for row in jet]
    if phi.lo <= -math.pi/2+1e-6 or phi.hi >= math.pi/2-1e-6:
        raise ValueError('polar box outside supported coordinate domain')
    s = _Box.outward(math.sin(phi.lo), math.sin(phi.hi))
    c = _Box.outward(min(math.cos(phi.lo), math.cos(phi.hi)),
        1. if phi.lo <= 0. <= phi.hi else max(math.cos(phi.lo), math.cos(phi.hi)))
    if model == 'flat_still':
        radius = disc_radius_m*(math.pi/2-phi)
        velocity = [disc_radius_m*p, radius*l, -h]
        acceleration = [disc_radius_m*pp, radius*ll-disc_radius_m*p*l, -hh]
        transport = [_Box(0.), _Box(0.), -l]
    else:
        d = 1.-WGS84_E2*s.square()
        prime = WGS84_A*d.positive_power(-.5)
        north = WGS84_A*(1.-WGS84_E2)*d.positive_power(-1.5)
        if (prime+height).lo <= 0. or (north+height).lo <= 0.:
            raise ValueError('nonpositive geographic metric box')
        prime_derivative = prime*WGS84_E2*s*c/d
        north_derivative = 3.*north*WGS84_E2*s*c/d
        east = (prime+height)*c
        east_derivative = (prime_derivative*c-(prime+height)*s)*p+c*h
        velocity = [(north+height)*p, east*l, -h]
        acceleration = [(north+height)*pp+(north_derivative*p+h)*p,
                        east*ll+east_derivative*l, -hh]
        transport = [c*l, -p, -s*l]
    background = [omega*c, _Box(0.), -omega*s]
    rate = [2.*background[i]+transport[i] for i in range(3)]
    cross = [rate[1]*velocity[2]-rate[2]*velocity[1],
             rate[2]*velocity[0]-rate[0]*velocity[2],
             rate[0]*velocity[1]-rate[1]*velocity[0]]
    force = [acceleration[i]+cross[i]-(gravity if i == 2 else 0.) for i in range(3)]
    square = sum((component.square() for component in force), _Box(0.))
    magnitude = [max(0., np.nextafter(math.sqrt(max(0., square.lo)), -np.inf)),
                 np.nextafter(math.sqrt(square.hi), np.inf)]
    return dict(force_ned_bounds_mps2=np.array([[item.lo, item.hi] for item in force]),
        magnitude_bounds_mps2=np.array(magnitude), model=model,
        propagation='nonlinear interval box; input dependence discarded',
        statistical_coverage_calibrated=False, formal_libm_rounding_certificate=False,
        scientific_decision='abstain')
