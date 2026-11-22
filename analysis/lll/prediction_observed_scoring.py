# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score withheld receiver reports; archival physical truth is unavailable."""

import math


def score_recording(result, *, training_rows, times, time_origin_s, save):
    import numpy as np
    from .airquantumgrav_scoring import receiver_errors, sections
    from .bounded_nonlinear_case import _score as score_interval
    from .studies.artifacts import digest, encoded

    if not callable(save) or not isinstance(result, dict):
        raise ValueError('complete saved forecast and score writer required')
    rows = result.get('withheld_truth')
    cut = len(training_rows)
    times = np.asarray(times, dtype=float)
    if (not isinstance(rows, list) or not 2 <= cut < len(rows) or
            len(rows) != len(times) or not np.all(np.isfinite(times)) or
            not np.array_equal(np.array([row['time_s'] for row in rows],
                                        dtype=float)-time_origin_s, times) or
            encoded(rows[:cut]) != encoded(training_rows)):
        raise ValueError('withheld and earlier receiver rows differ from frozen split')
    candidates = result.get('candidates')
    intervals = result.get('simultaneous_law_family')
    if (not isinstance(candidates, dict) or
            set(candidates) != {'increment', 'point'} or
            not isinstance(intervals, dict) or
            set(intervals) != {'physical_position', 'receiver_measurement'}):
        raise ValueError('complete matched two-law forecast required')
    receiver = np.array([[math.radians(row['latitude_deg']),
                          math.radians(row['longitude_deg']), row['height_m']]
                         for row in rows], dtype=float)
    if receiver.shape != (len(times), 3) or not np.all(np.isfinite(receiver)):
        raise ValueError('complete finite receiver-coordinate target required')
    descriptions = {}
    for law in ('increment', 'point'):
        forecast = candidates[law].get('forecast')
        coordinates = (forecast.get('coordinates')
                       if isinstance(forecast, dict) else None)
        if coordinates is None:
            descriptions[law] = None
            continue
        errors = receiver_errors(coordinates, receiver)
        descriptions[law] = sections(errors, cut)
    interval = intervals['receiver_measurement']
    if not isinstance(interval, dict) or interval.get('prediction_target') not in (
            None, 'receiver_measurement'):
        raise ValueError('receiver interval target differs from withheld score')
    if interval.get('supported') is True:
        score = score_interval(interval, receiver, cut)
        reason = None
    elif interval.get('supported') is False:
        score = None
        reason = interval.get('reason')
        if not isinstance(reason, str) or not reason:
            raise ValueError('unsupported interval requires an abstention reason')
    else:
        raise ValueError('explicit receiver interval support required')
    value = dict(training_epochs=cut, prediction_epochs=len(rows)-cut,
                 earlier_receiver_sha256=digest(encoded(training_rows)),
                 withheld_receiver_sha256=digest(encoded(rows)),
                 candidate_receiver_sections=descriptions,
                 receiver_interval_score=score, interval_reason=reason,
                 physical_position_truth_available=False,
                 physical_position_interval_scored=False,
                 receiver_values_used_for_training=False,
                 confidence_calibrated=False, scientific_decision='abstain')
    save('withheld-receiver-score.json', value)
    return value
