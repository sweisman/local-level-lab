# SPDX-License-Identifier: AGPL-3.0-or-later
"""Break the ionosphere-free phase path into its two measured bands."""


def bands(air, base, air_first, base_first, combined_position, gradient):
    """Recover single-band positions through linearity of the shared geometry."""
    import numpy as np

    from .differential_phase import relative_position
    from .esa_carrier_phase_support import GAMMA, L1_WAVELENGTH, L2_WAVELENGTH

    values = [np.asarray(row, float) for row in (air, base, air_first, base_first)]
    if (values[0].ndim != 2 or values[0].shape[1] != 2 or
            any(row.shape != values[0].shape or not np.isfinite(row).all() for row in values)):
        raise ValueError('aligned complete dual-frequency measurements required')
    position = np.asarray(combined_position, float)
    if position.shape != (3,) or not np.isfinite(position).all():
        raise ValueError('sealed three-axis combined position required')
    units = np.array([L1_WAVELENGTH, L2_WAVELENGTH])
    air_change = (values[0]-values[2])*units
    station_change = (values[1]-values[3])*units
    air_contrast = air_change[:, 0]-air_change[:, 1]
    base_contrast = station_change[:, 0]-station_change[:, 1]
    contrast = air_contrast-base_contrast
    fit = relative_position(contrast, np.zeros(len(contrast)), gradient)
    position_difference = fit['position_change_m']
    l1 = position-position_difference/(GAMMA-1.)
    return dict(l1_position=l1, l2_position=l1-position_difference,
                l1_minus_l2_position=position_difference, aircraft_band_change=air_contrast,
                station_band_change=base_contrast, residual=fit['residual_m'])
