# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reconstruct a generated receiver stream for later-only scoring.

The caller must save its aircraft forecast before supplying full geometric
truth. This helper has no fitting operation and checks that the regenerated
earlier receiver prefix equals the measurements already used for training.
"""


def generate_full_report(truth_coordinates, times, training_rows, *, policy_id, seed,
                         reserve=None):
    import math
    import numpy as np
    from lll.airquantumgrav_error_policy import build
    from lll.airquantumgrav_weighted_controls import fixture_rows
    from lll.measurement_noise import receiver_errors
    truth = np.asarray(truth_coordinates, dtype=float)
    times = np.asarray(times, dtype=float)
    training = list(training_rows)
    if (truth.ndim != 2 or truth.shape != (len(times), 3) or
            not 2 <= len(training) < len(times) or
            not np.all(np.isfinite(truth)) or
            (reserve is not None and not callable(reserve))):
        raise ValueError('complete later geometric truth and earlier receiver prefix required')
    clean = fixture_rows(truth, times)
    weight = build(clean, policy_id=policy_id)
    if reserve is not None:
        reserve(noise_normal_variates=3*len(times)*(1+len(weight.spec.components))+6)
    errors = receiver_errors(weight.times, weight.spec, seed=seed,
                             maximum_epochs=len(times), transforms=weight.transforms)
    rows = [dict(row,
                 latitude_deg=row['latitude_deg']+math.degrees(error[0]),
                 longitude_deg=row['longitude_deg']+math.degrees(error[1]),
                 height_m=row['height_m']+error[2])
            for row,error in zip(clean, errors, strict=True)]
    if rows[:len(training)] != training:
        raise ValueError('generated receiver prefix differs from fitted training measurements')
    return dict(rows=rows, coordinate_errors=errors,
                training_prefix_exact=True,
                later_observations_used_for_training=False,
                later_receiver_reports_generated=True,
                receiver_truth_calibrated=False)
