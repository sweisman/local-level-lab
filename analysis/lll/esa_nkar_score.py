# SPDX-License-Identifier: AGPL-3.0-or-later
"""Connect actual one-second ground carrier arcs to the saved ESA score weights."""
from .carrier_score_cadence import project_cadence
from .esa_carrier_phase_support import L1_WAVELENGTH, L2_WAVELENGTH
from .gnss_position import GAMMA


def reference_pair(first, last, prns, model):
    """Match unchanged legacy observations, then subtract signed modeled motion."""
    if (first['week'] != last['week'] or last['seconds']-first['seconds'] != 1.
            or first['flag'] or last['flag']):
        return {}
    selected, codes, measured = [], ([], []), {}
    for prn in prns:
        satellite = f'G{prn:02}'
        a, b = (row['measurements'].get(satellite) for row in (first, last))
        if a is None or b is None:
            continue
        marks = first['satellites'][satellite]
        if marks != last['satellites'][satellite] or any(mark & 3 for mark in marks):
            continue
        # Require a single code label across the pair. Legacy L1/L2 cannot
        # establish the exact tracking codes used by either receiver.
        l1_labels = [next((key for key in ('C1', 'P1') if 1e6 < row.get(key, 0.) < 6e7), None) for row in (a, b)]
        l2_labels = [next((key for key in ('P2', 'C2') if 1e6 < row.get(key, 0.) < 6e7), None) for row in (a, b)]
        if None in (*l1_labels, *l2_labels) or len(set(l1_labels)) != 1 or len(set(l2_labels)) != 1:
            continue
        d1 = (b['L1']-a['L1'])*L1_WAVELENGTH
        d2 = (b['L2']-a['L2'])*L2_WAVELENGTH
        selected.append(prn)
        codes[0].append(a[l1_labels[0]])
        codes[1].append(b[l1_labels[1]])
        measured[prn] = (GAMMA*d1-d2)/(GAMMA-1.)
    if not selected:
        return {}
    predicted = model(first, last, selected, list(codes))
    return {prn: measured[prn]-value for prn, value in predicted.items()}


def station_geometry(layout):
    """Return an approximate antenna position, retaining header datum metadata."""
    import numpy as np

    from .gnss_position import geodetic, local_rotation

    if 'approx_xyz_m' not in layout or 'antenna_delta_hen_m' not in layout:
        raise ValueError('station marker coordinates and antenna offset are required')
    marker = np.asarray(layout['approx_xyz_m'], float)
    height, east, north = layout['antenna_delta_hen_m']
    lat, lon, _ = geodetic(marker)
    return marker + local_rotation(lat, lon).T @ [north, east, height]


def final_range_model(navigation, atmosphere, orbits, clocks, antenna):
    """Use the same final satellite conventions as the saved aircraft replay."""
    import numpy as np

    from .esa_final_orbit_replay import interpolate_orbit
    from .esa_relative_clock_replay import interpolate_clock
    from .gnss_carrier_phase import _atmosphere, _geometry, shared_ephemerides
    from .gnss_position import C, satellite_state

    def model(first, last, prns, codes):
        epochs = (first, last)
        ephemerides = shared_ephemerides(navigation, *[dict(gps_week=r['week'], gps_week_seconds=r['seconds'])
                                                      for r in epochs])
        kept = [(i, prn) for i, prn in enumerate(prns) if prn in ephemerides and prn in orbits and prn in clocks]
        if not kept:
            return {}
        endpoint = []
        supported = np.ones(len(kept), dtype=bool)
        for epoch, readings in zip(epochs, codes, strict=True):
            transmit = [satellite_state(ephemerides[prn], epoch['week'], epoch['seconds'], readings[i])[2]
                        for i, prn in kept]
            positions = np.asarray([interpolate_orbit(orbits[prn], time) for (_, prn), time in zip(kept, transmit)])
            clock = np.asarray([interpolate_clock(clocks[prn], time) for (_, prn), time in zip(kept, transmit)])
            ranges, _ = _geometry(antenna, positions)
            mask, _, delay = _atmosphere(antenna, positions, epoch['seconds'], atmosphere)
            supported &= mask
            endpoint.append(ranges-C*clock+delay)
        return {prn: float(delta) for (_, prn), use, delta in zip(kept, supported, endpoint[1]-endpoint[0], strict=True) if use}

    return model


def compare_score(ranges, dual, start, station, observed, *, before_interval=None):
    """Apply signed carrier weights only where both receivers actually observed."""
    import numpy as np

    pairs = len(ranges)
    if pairs % 2 or [row['seconds'] for row in ranges] != [start+.5*i for i in range(1, pairs+1)]:
        raise ValueError('complete adjacent half-second aircraft grid required')
    support = [row['common_satellites'] for row in ranges]
    available, ground, intervals = {}, {}, []
    for i in range(0, pairs, 2):
        if before_interval is not None:
            before_interval()
        first, last = start+i*.5, start+i*.5+1.
        if first not in station or last not in station:
            continue
        prns = sorted(set(support[i]) & set(support[i+1]))
        measured = observed(station[first], station[last], prns)
        if not set(measured) <= set(prns) or not all(np.isfinite(v) for v in measured.values()):
            raise ValueError('finite residuals on continuous matched supports required')
        if len(measured) < 5:
            continue
        key = (i, i+2)
        available[key] = tuple(measured)
        ground[key] = measured
        intervals.append(key)
    projection = project_cadence(support, dual, intervals, interval_satellites=available)
    a_total = g_total = 0.
    for row in projection['intervals']:
        first, last = row['first'], row['last']
        prns = row['satellites']
        aircraft = np.array([sum(ranges[i]['fixed_residual_m'][support[i].index(prn)] for i in (first, first+1))
                             for prn in prns])
        measured = np.array([ground[first, last][prn] for prn in prns])
        # Each term is a separate receiver-clock-free range difference.
        aircraft -= aircraft.mean()
        measured -= measured.mean()
        weights = row['aggregate_weights']
        a_score, g_score = float(np.dot(weights, aircraft)), float(np.dot(weights, measured))
        a_total += a_score
        g_total += g_score
        row.update(start_gps_s=start+.5*first, stop_gps_s=start+.5*last, air_range_m=aircraft.tolist(),
                   ground_range_m=measured.tolist(), aircraft_score=a_score, ground_score=g_score)
    return dict(projection, matched_intervals=len(intervals), planned_intervals=pairs//2,
                ground_score_equivalent=g_total, aircraft_score_equivalent=a_total,
                air_minus_ground_score_equivalent=a_total-g_total)
