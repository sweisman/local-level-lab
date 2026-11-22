# SPDX-License-Identifier: AGPL-3.0-or-later
"""Disjoint fixed calibration groups for saved-solution sensitivity checks."""

import numpy as np

GROUPS = {
    'time': ('time_offset',),
    'vertical': ('gravity_delta','gyro_bias_z','gyro_gain_z',
                 'accel_bias_z','accel_gain_z'),
    'horizontal': ('gyro_bias_x','gyro_bias_y','gyro_gain_x','gyro_gain_y',
                   'accel_bias_x','accel_bias_y','accel_gain_x','accel_gain_y'),
    'state_mount': ('attitude_x','attitude_y','attitude_z',
                    'velocity_x','velocity_y','velocity_z',
                    'position_x','position_y','position_z',
                    'lever_x','lever_y','lever_z'),
}
VARIANTS = ('baseline',*GROUPS,'all')
NAMES = frozenset(name for group in GROUPS.values() for name in group)


def hybrid(names, anchor, counterpart, variant):
    names = tuple(names)
    a = np.asarray(anchor,dtype=float)
    b = np.asarray(counterpart,dtype=float)
    if (variant not in VARIANTS or len(names) != 26 or
            len(set(names)) != 26 or set(names) != NAMES or
            a.shape != (26,) or b.shape != (26,) or
            not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)) or
            np.any(abs(a)>1) or np.any(abs(b)>1)):
        raise ValueError('exact feasible 26-coordinate calibration pair required')
    point = a.copy()
    changed = (NAMES if variant == 'all' else
               GROUPS.get(variant,()) if variant != 'baseline' else ())
    for index,name in enumerate(names):
        if name in changed:
            point[index] = b[index]
    return point
