# SPDX-License-Identifier: AGPL-3.0-or-later
"""Constructive force-compatible attitude histories with gyro observations absent.

This is a geometric control. It does not fit an aircraft, infer heading, or
replace the missing gyroscope with a navigation solution.
"""

import numpy as np

from .ilvis0_channel_controls import force_attitude


def attitude_histories(body_force, required_navigation_force, twist_radians):
    """Return one sampled attitude path for arbitrary unobserved twists.

    When the two nonzero force vectors have equal norms at each sample, a
    proper attitude exists. A base path takes the smallest direction-matching
    step from its previous sampled attitude. A separate twist around each
    required navigation force gives another compatible path. No rate bound is
    imposed: applying such a bound requires independent motion information.
    """
    body = np.asarray(body_force, dtype=float)
    required = np.asarray(required_navigation_force, dtype=float)
    twists = np.asarray(twist_radians, dtype=float)
    if (body.ndim != 2 or body.shape[1] != 3 or len(body) < 2 or
            required.shape != body.shape or twists.shape != (len(body),) or
            not np.all(np.isfinite(body)) or
            not np.all(np.isfinite(required)) or
            not np.all(np.isfinite(twists))):
        raise ValueError('finite aligned force histories and twist values required')
    body_length = np.linalg.norm(body, axis=1)
    required_length = np.linalg.norm(required, axis=1)
    if (np.any(body_length <= 0) or np.any(required_length <= 0) or
            not np.allclose(body_length, required_length,
                            rtol=1e-12, atol=1e-12)):
        raise ValueError('matching nonzero force magnitudes required at every sample')
    base = force_attitude(body[0], required[0], 0.)
    out = []
    for index in range(len(body)):
        if index:
            adjustment = force_attitude(base @ body[index], required[index], 0.)
            base = adjustment @ base
        twist = force_attitude(required[index], required[index],
                              float(twists[index]))
        out.append(twist @ base)
    return np.stack(out)
