# SPDX-License-Identifier: AGPL-3.0-or-later
"""Development-only containment check for matched forecast envelopes.

Nominal coverage under an assumed error law is not observed-aircraft
calibration. This helper makes no scientific or operational decision.
"""

import math


def diagnose(envelopes, observation, *, target):
    """Report a unique containing candidate, if one exists, and abstain."""
    import numpy as np

    if (target not in ('physical_position', 'receiver_measurement')
            or not isinstance(envelopes, dict) or not 2 <= len(envelopes) <= 3
            or any(not isinstance(name, str) or not name
                   for name in envelopes)):
        raise ValueError('two or three named matched candidate envelopes required')
    value = np.asarray(observation, dtype=float)
    if (value.ndim != 2 or value.shape[1:] != (3,) or not len(value)
            or not np.all(np.isfinite(value))):
        raise ValueError('complete finite withheld three-coordinate path required')
    covered = {}
    for name, item in envelopes.items():
        if (not isinstance(item, dict)
                or item.get('prediction_target') != target
                or item.get('coordinate_chart') != 'local_unwrapped_geodetic'
                or item.get('later_observations_used') is not False
                or item.get('assumptions_qualified_for_aircraft') not in
                   (True, False)):
            raise ValueError('matched earlier-only target and chart required')
        claim = item.get('nominal_joint_coverage_lower_bound')
        if (type(claim) not in (int, float) or not math.isfinite(claim)
                or not .95 <= claim <= 1):
            raise ValueError('nominal whole-path coverage claim required')
        lower = np.asarray(item.get('lower'), dtype=float)
        upper = np.asarray(item.get('upper'), dtype=float)
        if (lower.shape != (value.size,) or upper.shape != lower.shape
                or not np.all(np.isfinite(lower))
                or not np.all(np.isfinite(upper))
                or np.any(lower >= upper)):
            raise ValueError('complete ordered future intervals required')
        sample = value.ravel()
        covered[name] = bool(np.all((lower <= sample) & (sample <= upper)))
    matching = [name for name, yes in covered.items() if yes]
    return dict(prediction_target=target, coordinate_chart='local_unwrapped_geodetic',
                candidate_count=len(envelopes), future_epochs=len(value),
                covered=covered,
                descriptive_unique_candidate=matching[0] if len(matching) == 1
                else None, observed_aircraft_coverage_established=False,
                scientific_decision='abstain')
