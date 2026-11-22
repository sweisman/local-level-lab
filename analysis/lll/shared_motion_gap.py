# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact minimum acceleration energy for a closed position-error path."""
from fractions import Fraction as F


def _inner_product(left, right, durations):
    """Integrate the product of two linear interpolants exactly."""
    return sum(h*((a+b)*(c+d)+a*c+b*d)/6
               for h, a, b, c, d in zip(durations, left[:-1], left[1:], right[:-1], right[1:], strict=True))


def _orthogonal_component(values, directions, durations):
    for basis, squared_norm in directions:
        scale = _inner_product(values, basis, durations)/squared_norm
        values = [x-scale*y for x, y in zip(values, basis, strict=True)]
    return values


def minimum_acceleration(times, taps, target, *, position_anchors=()):
    """Return the lowest-energy acceleration satisfying the supplied fixed position knots."""
    times = list(map(F, times))
    if len(times) < 3 or any(a >= b for a, b in zip(times, times[1:])):
        raise ValueError('at least three strictly increasing times required')
    if len(taps) != len(times)-1 or any(len(row) != 3 for row in taps) or not target:
        raise ValueError('one three-axis score tap per later time and nonzero target required')
    anchors = set(map(F, position_anchors))
    if not anchors <= set(times):
        raise ValueError('fixed positions must occur at declared knots')
    elapsed = [t-times[0] for t in times]
    length = elapsed[-1]
    durations = [b-a for a, b in zip(elapsed, elapsed[1:])]
    target = F(target)
    # The constant representer closes velocity. Each hinge closes position
    # at its knot, including the end of the window.
    directions = [([F(1)]*len(times), length)]
    for anchor in sorted((anchors | {times[-1]}) - {times[0]}):
        basis = _orthogonal_component([max(F(0), anchor-t) for t in times], directions, durations)
        directions.append((basis, _inner_product(basis, basis, durations)))
    columns = []
    squared_integral = F(0)
    for weights in zip(*taps, strict=True):
        kernel = [F(0)]*len(times)
        tail = F(0)
        for j in reversed(range(len(weights))):
            tail += F(weights[j])
            kernel[j] = kernel[j+1]+durations[j]*tail
        projected = _orthogonal_component(kernel, directions, durations)
        columns.append(projected)
        squared_integral += _inner_product(projected, projected, durations)
    if not squared_integral:
        raise ValueError('the closed path cannot change this score')
    factor = target/squared_integral
    return dict(acceleration=[[factor*v for v in row] for row in zip(*columns, strict=True)],
                acceleration_rms_squared=target**2/(squared_integral*length))


def integrate_path(times, accelerations):
    """Integrate the acceleration knots from zero position and velocity."""
    time = list(map(F, times))
    if len(time) != len(accelerations) or any(len(row) != 3 for row in accelerations):
        raise ValueError('one three-axis acceleration per time required')
    pos = [[F(0)]*3]
    speed = [[F(0)]*3]
    for start, end, a, b in zip(time[:-1], time[1:], accelerations[:-1], accelerations[1:], strict=True):
        dt = end-start
        if dt <= 0:
            raise ValueError('strictly increasing times required')
        a, b = list(map(F, a)), list(map(F, b))
        pos.append([x+v*dt+dt**2*(2*p+q)/6
                    for x, v, p, q in zip(pos[-1], speed[-1], a, b, strict=True)])
        speed.append([v+dt*(p+q)/2 for v, p, q in zip(speed[-1], a, b, strict=True)])
    return pos, speed
