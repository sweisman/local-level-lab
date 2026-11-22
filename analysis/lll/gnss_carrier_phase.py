# SPDX-License-Identifier: AGPL-3.0-or-later
"""Displacement from successive RT27 GPS L1 carrier phases."""

import math

import numpy as np

from . import gnss_position as gps

L1_WAVELENGTH_M = gps.C/1_575_420_000.
MAX_ITERATIONS = 8
MAX_CONDITION = 100.


def _signals(record):
    if record['format'] != 'RT27':
        raise ValueError('paired RT27 records required')
    signals = {}
    for satellite in record['satellites']:
        if (satellite['system'] != 0 or satellite['antenna'] != 0
                or satellite.get('unhealthy') or satellite.get('raim_fault')
                or (len(satellite['flags']) > 1 and satellite['flags'][1] & 2)):
            continue
        observed = [item for item in satellite['signals'] if item['band'] == item['track_type'] == 0]
        if len(observed) != 1:
            continue
        signal = observed[0]
        if (signal['phase_loaded'] and signal['range_loaded'] and not signal.get('cycle_slip')
                and not signal.get('half_cycle') and not signal.get('unhealthy')
                and type(signal.get('slip_counter')) is int and math.isfinite(signal['phase_cycles'])
                and 1e6 < signal['pseudorange_m'] < 6e7):
            signals[satellite['sv_id']] = (signal, satellite.get('pseudo_iode'))
    return signals


def matched_phase(first, second):
    """Pair only common healthy signals with unchanged slip and ephemeris flags."""
    a, b = _signals(first), _signals(second)
    return {prn: (a[prn][0], b[prn][0]) for prn in sorted(a.keys() & b.keys())
            if a[prn][0]['slip_counter'] == b[prn][0]['slip_counter'] and a[prn][1] == b[prn][1]}


def _geometry(receiver, satellites):
    vector = satellites-receiver
    length = np.linalg.norm(vector, axis=1)
    derivative = -vector/length[:, None]
    x, y, _ = receiver
    rotation = gps.OMEGA/gps.C
    derivative[:, 0] -= rotation*satellites[:, 1]
    derivative[:, 1] += rotation*satellites[:, 0]
    sagnac = rotation*(satellites[:, 0]*y-satellites[:, 1]*x)
    return length+sagnac, np.column_stack((derivative, np.ones(len(satellites))))


def recover_displacement(anchor, start, end, clock_a, clock_b, ion_a, ion_b,
                         trop_a, trop_b, phase_a, phase_b, *, sign):
    """Solve position change and one free common receiver clock change in metres."""
    (anchor, start, end, clock_a, clock_b, ion_a, ion_b, trop_a, trop_b,
     phase_a, phase_b) = map(np.asarray, (anchor, start, end, clock_a, clock_b,
                                        ion_a, ion_b, trop_a, trop_b, phase_a, phase_b))
    count = len(start)
    vectors = (clock_a, clock_b, ion_a, ion_b, trop_a, trop_b, phase_a, phase_b)
    if (sign not in (-1, 1) or anchor.shape != (3,) or start.shape != (count, 3)
            or end.shape != start.shape or any(x.shape != (count,) for x in vectors)
            or any(not np.isfinite(x).all() for x in (anchor, start, end, *vectors))):
        raise ValueError('matched finite carrier endpoints and a qualified sign required')
    if count < 5:
        return dict(status='abstain', reason='fewer than five supported satellites')
    first_range, _ = _geometry(anchor, start)
    measured = sign*L1_WAVELENGTH_M*(phase_b-phase_a)
    correction = -gps.C*(clock_b-clock_a) - (ion_b-ion_a) + (trop_b-trop_a)
    state = np.zeros(4)
    for iteration in range(1, MAX_ITERATIONS+1):
        later_range, design = _geometry(anchor+state[:3], end)
        residual = measured-((later_range-first_range)+correction+state[3])
        condition = float(np.linalg.cond(design))
        if condition > MAX_CONDITION:
            return dict(status='abstain', reason='ill-conditioned satellite geometry', iterations=iteration)
        step = np.linalg.lstsq(design, residual, rcond=None)[0]
        if np.linalg.norm(step) < 1e-6:
            return dict(status='converged', displacement_ecef_m=state[:3].tolist(),
                receiver_clock_change_m=float(state[3]), condition=condition, iterations=iteration,
                range_difference_rms_m=float(np.sqrt(np.mean(residual**2))))
        state += step
    return dict(status='abstain', reason='phase displacement solver did not converge', iterations=MAX_ITERATIONS)


def shared_ephemerides(ephemerides, first, second):
    """Pick one valid broadcast record per satellite using only epoch metadata."""
    week = first['gps_week']
    if second['gps_week'] != week:
        raise ValueError('GPS week rollover requires separate phase timing qualification')
    targets = (first['gps_week_seconds'], second['gps_week_seconds'])
    usable = {}
    for item in ephemerides:
        delta = tuple(abs((week-item['gps_week'])*604800+t-item['toe_s']) for t in targets)
        if item['health'] or item['ura_index']==15 or (item['iodc'] & 255)!=item['iode'] or max(delta)>7200:
            continue
        prn = item['sv_id']
        score = (max(delta), item['payload_sha256'])
        if prn not in usable or score < usable[prn][0]:
            usable[prn] = (score, item)
    return {prn: value[1] for prn, value in usable.items()}


def _atmosphere(anchor, satellites, second, ionosphere, *, neutral_delay=gps.troposphere):
    latitude, longitude, height = gps.geodetic(anchor)
    delta = satellites-anchor
    directions = (gps.local_rotation(latitude, longitude)@delta.T).T
    elevation = np.arcsin(np.clip(directions[:, 2]/np.linalg.norm(delta, axis=1), -1., 1.))
    azimuth = np.arctan2(directions[:, 1], directions[:, 0]) % (2*math.pi)
    supported = elevation >= np.deg2rad(5.)
    ion = np.zeros(len(satellites))
    trop = np.zeros(len(satellites))
    for i in np.flatnonzero(supported):
        ion[i] = gps.klobuchar(second, latitude, longitude, azimuth[i], elevation[i], ionosphere)
        trop[i] = neutral_delay(latitude, height, elevation[i])
    return supported, ion, trop


def solve_pair(first, second, ephemerides, ionosphere, anchor, *, sign):
    ephem = shared_ephemerides(ephemerides, first, second)
    pairs = matched_phase(first, second)
    prns = sorted(pairs.keys() & ephem.keys())
    if len(prns) < 5:
        return dict(status='abstain', reason='fewer than five continuous phases with shared ephemerides',
                    common_phase_satellites=len(pairs))
    endpoints = []
    for side, epoch in enumerate((first, second)):
        seconds = epoch['gps_week_seconds']
        states = [gps.satellite_state(ephem[prn], epoch['gps_week'], seconds,
                  pairs[prn][side]['pseudorange_m']) for prn in prns]
        sats = np.asarray([x[0] for x in states])
        supported, ion, trop = _atmosphere(anchor, sats, seconds, ionosphere)
        phases = np.array([pairs[prn][side]['phase_cycles'] for prn in prns])
        endpoints.append((supported, sats, np.array([x[1] for x in states]), ion, trop, phases))
    a, b = endpoints
    valid = a[0] & b[0]
    args = [values[valid] for left, right in zip(a[1:], b[1:], strict=True) for values in (left, right)]
    result = recover_displacement(anchor, *args, sign=sign)
    used = [prn for prn, keep in zip(prns, valid, strict=True) if keep]
    result.update(common_phase_satellites=len(pairs), satellites=used,
                 broadcast_ephemerides=[ephem[prn]['payload_sha256'] for prn in used])
    return result
