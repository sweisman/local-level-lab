# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prepare two equal-horizon forecasts without leaking receiver positions."""
import math


def split_origins(measurements, scoring):
    """Separate first-third and two-thirds training from their later scores."""
    if set(measurements) != {'segment_id', 'layout', 'times', 'values', 'training_gps'}:
        raise ValueError('fit input must contain no future receiver positions')
    if set(scoring) != {'segment_id', 'prediction_gps'}:
        raise ValueError('separate later receiver scoring input required')
    layout = measurements['layout']
    times = measurements['times']
    count = layout['receiver_epochs']
    outer_cut = layout['training_epochs']
    if (not isinstance(count, int) or count < 9 or len(times) != count or
            outer_cut != 2*count//3 or
            len(measurements['training_gps']) != outer_cut):
        raise ValueError('unchanged two-thirds receiver layout required')
    if (scoring['segment_id'] != measurements['segment_id'] or
            len(scoring['prediction_gps']) != count-outer_cut):
        raise ValueError('complete later receiver positions required')
    if (any(not isinstance(value, (int, float)) or not math.isfinite(value)
            for value in times) or
            any(right <= left for left, right in zip(times[:-1], times[1:]))):
        raise ValueError('increasing finite receiver times required')
    inner_cut = count//3
    horizon = min(outer_cut-inner_cut, count-outer_cut)
    def make(cut, future):
        training = dict(segment_id=measurements['segment_id'], cut_epoch=cut,
                        horizon_epochs=horizon,
                        training_gps=measurements['training_gps'][:cut])
        return dict(training=training,
                    scoring=dict(segment_id=measurements['segment_id'],
                                 prediction_gps=future[:horizon]))
    return dict(horizon_epochs=horizon,
                common={key: measurements[key] for key in
                        ('segment_id', 'layout', 'times', 'values')},
                inner=make(inner_cut, measurements['training_gps'][inner_cut:outer_cut]),
                outer=make(outer_cut, scoring['prediction_gps']))
