# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bound a single accelerometer calibration against alternative GPS windows."""

import numpy as np

from .ilvis0_receiver_force import MATCHED_MODELS


def _magnitude_enclosure(measured, error, box):
    gain, bias = box[:3], box[3:]
    min_denominator = np.nextafter(1.+gain[:, 0], -np.inf)
    max_denominator = np.nextafter(1.+gain[:, 1], np.inf)
    min_numerator = np.nextafter(np.nextafter(measured-error, -np.inf)-bias[:, 1], -np.inf)
    max_numerator = np.nextafter(np.nextafter(measured+error, np.inf)-bias[:, 0], np.inf)
    corners = (min_numerator/min_denominator, min_numerator/max_denominator,
               max_numerator/min_denominator, max_numerator/max_denominator)
    low = np.nextafter(np.minimum.reduce(corners), -np.inf)
    high = np.nextafter(np.maximum.reduce(corners), np.inf)
    near = np.where((low <= 0.) & (high >= 0.), 0., np.minimum(abs(low), abs(high)))
    far = np.maximum(abs(low), abs(high))
    lower = np.maximum(0., np.nextafter(np.hypot(np.hypot(near[:, 0], near[:, 1]), near[:, 2]), -np.inf))
    upper = np.nextafter(np.hypot(np.hypot(far[:, 0], far[:, 1]), far[:, 2]), np.inf)
    if not np.isfinite(upper).all():
        raise ValueError('accelerometer magnitude exceeds the supported finite range')
    return lower, upper


def _search(measured, error, required, ranges, targets, widths, box, maximum_boxes):
    """Use one box for every target; each target can use any retained window."""
    pending = [box]
    evaluated = excluded = point_evaluations = 0
    unsplittable = False
    influence = np.r_[np.max(abs(measured)+error, axis=0), np.ones(3)]
    minimum_gain = 1.+box[:3, 0]
    influence[:3] /= minimum_gain**2
    influence[3:] /= minimum_gain

    def matches(space):
        lower, upper = _magnitude_enclosure(measured, error, space)
        return (lower[targets] <= ranges[:, 1]) & (upper[targets] >= ranges[:, 0])

    calibration = matching_windows = None
    status = 'no_required_targets'
    while required.size and pending and evaluated < maximum_boxes:
        space = pending.pop()
        evaluated += 1
        overlap = matches(space)
        if not np.isin(required, targets[overlap]).all():
            excluded += 1
            continue

        low, high = space.T
        center = .5*low + .5*high
        point_evaluations += 1
        witness = matches(np.column_stack((center, center)))
        if np.isin(required, targets[witness]).all():
            status = 'scalar_compatible'
            calibration = center.tolist()
            matching_windows = [widths[witness & (targets == i)].tolist() for i in required]
            break

        splittable = np.flatnonzero((low < center) & (center < high))
        if not splittable.size:
            unsplittable = True
            continue
        scores = (high[splittable]-low[splittable])*influence[splittable]
        dim = splittable[np.argmax(scores)]
        left, right = space.copy(), space.copy()
        left[dim, 1] = right[dim, 0] = center[dim]
        pending.extend((right, left))
    else:
        if required.size:
            status = ('budget_unresolved' if pending else
                      'precision_unresolved' if unsplittable else 'scalar_excluded')
    return dict(status=status, calibration=calibration, matching_windows_s=matching_windows,
                boxes_evaluated=evaluated, boxes_excluded=excluded,
                witness_points_evaluated=point_evaluations, maximum_boxes=maximum_boxes,
                maximum_magnitude_evaluations=2*maximum_boxes)


def compare(assessment, *, measured_specific_force, measurement_error_mps2,
            calibration_bounds, maximum_boxes):
    """Compare four gyro-free necessary conditions under one calibration per model.

    Measurements and declared errors refer to the same target epochs as the
    receiver assessment. The calibration is three dimensionless gain errors
    followed by three offsets in m/s². Predicted magnitude intervals already
    include the declared position, gravity and derivative uncertainties.
    The exclusion uses a relaxation of all shared errors and orientations:
    individual targets may independently select any plausible window, and a
    possible abstention imposes no constraint. Overlap at a single calibration
    only establishes compatibility with these relaxed scalar intervals.
    """
    measured = np.asarray(measured_specific_force, dtype=float)
    error = np.asarray(measurement_error_mps2, dtype=float)
    box = np.asarray(calibration_bounds, dtype=float)
    if (tuple(assessment['model_order']) != MATCHED_MODELS
            or assessment['gyro_observations_used'] is not False
            or assessment['fused_navigation_used'] is not False
            or not assessment['targets'] or measured.shape != (len(assessment['targets']), 3)
            or error.shape != measured.shape or box.shape != (6, 2)
            or not all(np.isfinite(value).all() for value in (measured, error, box))
            or np.any(error < 0.) or np.any(box[:, 1] < box[:, 0])
            or np.any(box[:3, 0] <= -1.)
            or type(maximum_boxes) is not int or maximum_boxes < 1):
        raise ValueError('four receiver-only models, finite measurements and common calibration required')

    branches = []
    required = []
    for i, target in enumerate(assessment['targets']):
        widths = target['possible_choices_s']
        if (not widths or len(set(widths)) != len(widths)
                or any(not np.isfinite(w) or w <= 0. for w in widths if w is not None)):
            raise ValueError('explicit positive possible windows or abstention required')
        branches.extend((i, w) for w in widths if w is not None)
        if None not in widths:
            required.append(i)
    if branches != [tuple(branch) for branch in assessment['branches']]:
        raise ValueError('force ranges must bind each alternative window in order')
    targets = np.asarray([i for i, _ in branches], dtype=int)
    widths = np.asarray([w for _, w in branches], dtype=float)
    required = np.asarray(required, dtype=int)
    active = np.isin(targets, required)
    fits = {}
    for model in MATCHED_MODELS:
        ranges = (np.asarray(assessment['magnitude_ranges_mps2'][model], dtype=float)
                  if branches else np.empty((0, 2)))
        if (ranges.shape != (len(branches), 2) or not np.isfinite(ranges).all()
                or np.any(ranges[:, 0] < 0.) or np.any(ranges[:, 1] < ranges[:, 0])):
            raise ValueError('finite ordered force magnitude ranges required for all branches')
        fits[model] = _search(measured, error, required, ranges[active], targets[active],
                              widths[active], box, maximum_boxes)
    return dict(candidates=fits, required_target_indices=required.tolist(),
                calibration_bounds=box.tolist(), shared_calibration=True,
                attitude_identified=False, common_receiver_error_feasibility_established=False,
                numerical_interval_roundoff_certified=False, statistical_coverage_calibrated=False,
                gyro_observations_used=False, fused_navigation_used=False, scientific_decision='abstain')
