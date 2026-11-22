# SPDX-License-Identifier: AGPL-3.0-or-later
"""Carrier range signature of a receiver-coordinate change."""
import numpy as np

from .gnss_position import C, OMEGA


def displacement_at(rows, elapsed_s, acceleration):
    """Interpolate the constructed motion, never the raw measurements."""
    times = np.array([row['elapsed_s'] for row in rows])
    if elapsed_s <= times[0] or elapsed_s >= times[-1]:
        return np.zeros(3)
    i = int(np.searchsorted(times, elapsed_s, side='right'))-1
    dt, h = elapsed_s-times[i], times[i+1]-times[i]
    pos, vel = map(np.asarray, (rows[i]['position_m'], rows[i]['velocity_mps']))
    return pos+vel*dt+acceleration[i]*dt**2/2+(acceleration[i+1]-acceleration[i])*dt**3/(6*h)


def range_shift(receiver, shifted, satellites):
    """Sagnac-corrected range difference at fixed transmit positions."""
    receiver, shifted, satellites = map(np.asarray, (receiver, shifted, satellites))
    delta = shifted-receiver
    line = satellites-receiver
    first, last = np.linalg.norm(line, axis=1), np.linalg.norm(line-delta, axis=1)
    geometric = (-2*(line@delta)+delta@delta)/(first+last)
    return geometric+OMEGA/C*(satellites[:, 0]*delta[1]-satellites[:, 1]*delta[0])


def centre(values):
    """Remove the same common range change that the receiver clock can absorb."""
    values = np.asarray(values, float)
    return values-values.mean()


def fixed_path_range_residual(measured, ranges, satellite_clock, neutral_delay):
    """Subtract geometry, broadcast clock and neutral-atmosphere changes."""
    measured = np.asarray(measured, float)
    ranges, clock, delay = map(lambda x: np.asarray(x, float), (ranges, satellite_clock, neutral_delay))
    if (measured.ndim != 1 or not len(measured) or not np.isfinite(measured).all()
            or any(x.shape != (2, len(measured)) or not np.isfinite(x).all() for x in (ranges, clock, delay))):
        raise ValueError('finite measured change and two aligned modeled endpoints required')
    modeled = ranges-C*clock+delay
    return centre(measured-(modeled[1]-modeled[0]))


def compare_signatures(required, clock):
    required, clock = map(np.asarray, (required, clock))
    if required.ndim != 1 or required.shape != clock.shape or not len(required):
        raise ValueError('nonempty matched carrier signatures required')
    norm = np.linalg.norm(required)*np.linalg.norm(clock)
    def rms(values):
        return float(np.sqrt(np.mean(values*values)))

    return dict(required_rms_m=rms(required), clock_rms_m=rms(clock), unaccounted_rms_m=rms(required-clock),
                cosine=float(required@clock/norm) if norm else None)


def signed_product_comparison(required, broadcast_residual, orbit, clock):
    """Compare signed changes on the same receiver-clock-free support."""
    products = centre(np.asarray(orbit) + np.asarray(clock))
    fixed = centre(broadcast_residual) - products
    return dict(products_m=products, fixed_residual_m=fixed,
                shifted_residual_m=fixed + centre(required))
