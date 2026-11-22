# SPDX-License-Identifier: AGPL-3.0-or-later
"""Solve a short-baseline GPS phase change with an unknown receiver clock."""


def phase_difference(air, station, first_air, first_station):
    """Difference two bands between receivers and from the same reference epoch."""
    import numpy as np

    from .esa_carrier_phase_support import L1_WAVELENGTH, L2_WAVELENGTH
    from .gnss_position import GAMMA

    rows = tuple(np.asarray(values, float) for values in (air, station, first_air, first_station))
    if (rows[0].ndim != 2 or rows[0].shape[1] != 2 or any(base.shape != rows[0].shape for base in rows[1:])
            or any(not np.isfinite(base).all() for base in rows)):
        raise ValueError('aligned finite L1 and L2 carrier phases required')
    difference = ((rows[0]-rows[2])-(rows[1]-rows[3]))*np.array([L1_WAVELENGTH, L2_WAVELENGTH])
    return (GAMMA*difference[:, 0]-difference[:, 1])/(GAMMA-1.)


def relative_position(measured, at_anchor, derivatives):
    """Solve the measured change with a free common clock and report rank."""
    import numpy as np

    observed, geometry, gradient = (np.asarray(arg, float) for arg in (measured, at_anchor, derivatives))
    if (observed.ndim != 1 or len(observed) < 4 or geometry.shape != observed.shape
            or gradient.shape != (len(observed), 3) or any(not np.isfinite(arg).all()
                                                           for arg in (observed, geometry, gradient))):
        raise ValueError('four or more aligned satellite phase changes required')
    design = np.column_stack([gradient, np.ones(len(observed))])
    delta = observed-geometry
    solution, _, rank, singular = np.linalg.lstsq(design, delta, rcond=None)
    if rank != 4:
        raise ValueError('the GPS changes do not identify position and clock')
    return dict(position_change_m=solution[:3], clock_change_m=float(solution[3]),
                residual_m=delta-design@solution, singular_values=singular)


def position_projection(range_residual, derivatives, local_rotation):
    """Separate the position-like range component and bound its amplification."""
    import numpy as np

    ranges, gradient, rotation = (np.asarray(value, float) for value in (range_residual, derivatives, local_rotation))
    if rotation.shape != (3, 3) or not np.isfinite(rotation).all():
        raise ValueError('finite receiver-local coordinate rotation required')
    fit = relative_position(ranges, np.zeros_like(ranges), gradient)
    design = np.column_stack([gradient, np.ones(len(ranges))])
    range_to_position = rotation @ np.linalg.pinv(design)[:3]
    rms = float(np.sqrt(np.mean(fit['residual_m']**2)))
    return dict(equivalent_ecef_m=fit['position_change_m'].tolist(),
                equivalent_neu_m=(rotation@fit['position_change_m']).tolist(),
                receiver_clock_change_m=fit['clock_change_m'], remaining_range_rms_m=rms,
                component_gain_m_per_m=np.sum(abs(range_to_position), axis=1).tolist(),
                geometry_condition=float(fit['singular_values'][0]/fit['singular_values'][-1]))


def receiver_geometry(record, ephemerides, ionosphere, anchor, prns):
    """Evaluate the existing code geometry with receiver clock set to zero."""
    import numpy as np

    from .gnss_position import observations, range_system

    selected, _ = observations(record, ephemerides, 'dual_frequency')
    by_prn = {item['sv_id']: item for item in selected}
    if set(by_prn) != set(prns) or any(item['l2_track_type'] != 1 for item in selected):
        raise ValueError('all continuously tracked satellites need healthy GPS C2W geometry')
    ordered = [by_prn[prn] for prn in prns]
    design, residual, used, _ = range_system(np.r_[anchor, 0.], ordered, record['gps_week_seconds'],
                                              'dual_frequency', ionosphere, elevation_mask_deg=0.)
    if [item['sv_id'] for item in used] != prns:
        raise ValueError('a required satellite is below the geometric horizon')
    prediction = np.asarray([item['observed_corrected_code_m'] for item in used])-residual
    metadata = [{key: item[key] for key in ('sv_id', 'elevation_deg', 'transmit_gps_seconds',
                                          'ephemeris_payload_sha256')} for item in used]
    return prediction, design[:, :3], metadata
