# SPDX-License-Identifier: AGPL-3.0-or-later
"""Ground and aircraft carrier changes on the frozen Nuuk overlap."""


def centred_band_residuals(measured, model):
    """Subtract each fixed path's range changes and project out the clock."""
    import numpy as np

    phase, ranges = np.asarray(measured, float), np.asarray(model, float)
    if (phase.ndim != 3 or phase.shape[0] < 2 or phase.shape[2] != 2 or ranges.shape != phase.shape[:2]
            or not np.isfinite(phase).all() or not np.isfinite(ranges).all()):
        raise ValueError('finite matched phase and range sequences required')
    residual = np.diff(phase, axis=0)-np.diff(ranges, axis=0)[..., None]
    return residual-residual.mean(axis=1, keepdims=True)


def carrier_comparison(air_metres, ground_metres, air_model, ground_model, shifted_air_model):
    """Compare fixed position paths after removing a common clock per change."""
    import numpy as np

    from .gnss_position import GAMMA
    from .shared_motion_carrier import compare_signatures

    air, ground, air_model, ground_model, shifted = map(
        lambda x: np.asarray(x, float), (air_metres, ground_metres, air_model, ground_model, shifted_air_model))
    if (air.ndim != 3 or air.shape[0] < 2 or air.shape[1] < 5 or air.shape[2] != 2 or ground.shape != air.shape
            or any(arr.shape != air.shape[:2] for arr in (air_model, ground_model, shifted))
            or any(not np.isfinite(arr).all() for arr in (air, ground, air_model, ground_model, shifted))):
        raise ValueError('finite matched carrier and geometry epochs required')

    def centred(change):
        return change - change.mean(axis=1, keepdims=True)

    air_bands = centred_band_residuals(air, air_model)
    ground_bands = centred_band_residuals(ground, ground_model)
    scale = np.asarray([GAMMA, -1.]) / (GAMMA-1.)
    aircraft, station = air_bands@scale, ground_bands@scale
    required = centred(np.diff(air_model-shifted, axis=0))
    residual = aircraft-station
    shifted_residual = residual+required

    def statistics(signal, ground_error, delta):
        reference = signal.reshape(-1)
        observed = ground_error.reshape(-1)
        energy = reference@reference
        return compare_signatures(reference, observed) | dict(
            ground_aligned_fraction=float(reference@observed/energy) if energy else None,
            unshifted_differential_rms_m=float(np.sqrt(np.mean(delta**2))),
            shifted_differential_rms_m=float(np.sqrt(np.mean((delta+signal)**2))))

    summary = statistics(required, station, residual)
    pairs = [dict(required_correction_m=required[i].tolist(), ground_residual_m=station[i].tolist(),
                  air_residual_m=aircraft[i].tolist(), air_minus_ground_residual_m=residual[i].tolist(),
                  shifted_air_minus_ground_residual_m=shifted_residual[i].tolist(),
                  air_band_residual_m=air_bands[i].tolist(), ground_band_residual_m=ground_bands[i].tolist())
             for i in range(len(required))]
    omissions = []
    for omit in range(air.shape[1]):
        keep = np.arange(air.shape[1]) != omit
        matched = [centred(row[:, keep]) for row in (required, station, residual)]
        omissions.append(statistics(*matched) | {'omitted_index': omit})
    summary['ground_rms_m'] = summary.pop('clock_rms_m')
    for row in omissions:
        row['ground_rms_m'] = row.pop('clock_rms_m')
    return dict(summary=summary, pairs=pairs, omissions=omissions)
