# SPDX-License-Identifier: AGPL-3.0-or-later
"""Build matched iMAR component increments from one sealed rate sequence."""


def construct(times, angular_rates, accelerations, *, saved_theta, saved_dv,
              saved_dt, training_prefix):
    """Return three alternatives after verifying the saved linear construction.

    The samples' actual integration phase remains unknown. This function does
    not propagate, fit, score receiver observations or change the baseline.
    """
    import numpy as np
    from .esa_rate_hypothesis_audit import compare_rate_integrals

    compare_rate_integrals(
        times, angular_rates, accelerations,
        saved_theta=saved_theta, saved_dv=saved_dv, saved_dt=saved_dt,
        training_prefix=training_prefix)
    dt = np.asarray(saved_dt, dtype=float).copy()
    gyro = np.asarray(angular_rates, dtype=float)
    accel = np.asarray(accelerations, dtype=float)
    result = {}
    for name, g, a in (
            ('linear_points', np.asarray(saved_theta, dtype=float),
             np.asarray(saved_dv, dtype=float)),
            ('left_hold', gyro[:-1]*dt[:, None], accel[:-1]*dt[:, None]),
            ('right_hold', gyro[1:]*dt[:, None], accel[1:]*dt[:, None])):
        result[name] = dict(theta=np.array(g, dtype=float, copy=True, order='C'),
                            dv=np.array(a, dtype=float, copy=True, order='C'),
                            dt=dt.copy(), training_prefix=training_prefix)
    return result
