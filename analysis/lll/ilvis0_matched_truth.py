# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent analytic motion for matched field and geometry controls."""

import numpy as np

from .airquantumgrav_truth import truth
from .ilvis0_receiver_force import DISC_WITH_FIELD, MATCHED_MODELS


def matched_truth(model, times, *, latitude_deg, route, removal):
    if model not in MATCHED_MODELS:
        raise ValueError('declared matched candidate required')
    base = 'flat_still' if model == DISC_WITH_FIELD else model
    result = truth(base, times, latitude_deg=latitude_deg, pattern='fast',
                   removal=removal, route=route, height_profile='level')
    if model == DISC_WITH_FIELD:
        # The original analytic disc geometry supplies velocity and attitude.
        # Introduce the prescribed field in NED before projecting to body axes.
        latitude = result['coordinates'][:, 0]
        field = 7.292115e-5 * np.column_stack(
            (np.cos(latitude), np.zeros_like(latitude), -np.sin(latitude)))
        local_to_body = result['attitude_body_to_local'].swapaxes(1, 2)
        result['angular_rate_rads'] += np.einsum('nij,nj->ni', local_to_body, field)
        coriolis = 2. * np.cross(field, result['velocity_local_mps'])
        result['specific_force_mps2'] += np.einsum('nij,nj->ni', local_to_body, coriolis)
    return result
