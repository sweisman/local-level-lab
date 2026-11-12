# SPDX-License-Identifier: AGPL-3.0-or-later
"""Earlier-only constant and linear residual forecasts for saved epochs."""

import math
import statistics


AXES = ('north_direct_error_m', 'east_direct_error_m',
        'up_direct_error_m')


def _rms(values):
    return math.sqrt(math.fsum(value * value for value in values) /
                     len(values))


def evaluate(epochs, *, training_window_s=120., minimum_training_epochs=100):
    """Fit two fixed corrections on earlier rows, score later rows only."""
    if (not isinstance(epochs, list) or len(epochs) < 4
            or training_window_s != 120.
            or minimum_training_epochs != 100):
        raise ValueError('frozen earlier-only window required')
    times = []
    training = []
    prediction = []
    seen_prediction = False
    for index, row in enumerate(epochs):
        if row.get('epoch') != index or row.get('role') not in ('training',
                                                               'prediction'):
            raise ValueError('ordered unchanged epoch roles required')
        t = float(row['time_s'])
        if not math.isfinite(t) or (times and t <= times[-1]):
            raise ValueError('strict finite epoch times required')
        times.append(t)
        if row['role'] == 'training':
            if seen_prediction:
                raise ValueError('later observations cannot enter training')
            training.append(row)
        else:
            seen_prediction = True
            prediction.append(row)
        if any(not math.isfinite(float(row[key])) for key in AXES):
            raise ValueError('finite saved errors required')
    if len(training) < minimum_training_epochs or not prediction:
        raise ValueError('complete earlier/later support required')
    boundary = float(training[-1]['time_s'])
    window = [row for row in training
              if float(row['time_s']) > boundary - training_window_s]
    if len(window) < minimum_training_epochs:
        raise ValueError('fixed earlier window has too few epochs')
    fit_times = [float(row['time_s']) for row in window]
    center_time = statistics.fmean(fit_times)
    spread = math.fsum((time - center_time)**2 for time in fit_times)
    if spread <= 0:
        raise ValueError('nonzero training time span required')
    corrections = {}
    for axis in AXES:
        values = [float(row[axis]) for row in window]
        center = statistics.fmean(values)
        slope = math.fsum((time-center_time)*(value-center)
                          for time,value in zip(fit_times,values)) / spread
        corrections[axis] = dict(mean_m=center,
                                 slope_m_per_s=slope,
                                 center_time_s=center_time)
    error = {'original':{axis:[] for axis in AXES},
             'constant':{axis:[] for axis in AXES},
             'linear':{axis:[] for axis in AXES}}
    for row in prediction:
        t = float(row['time_s'])
        for axis in AXES:
            observed = float(row[axis])
            fit = corrections[axis]
            error['original'][axis].append(observed)
            error['constant'][axis].append(observed-fit['mean_m'])
            error['linear'][axis].append(observed-fit['mean_m']-
                                         fit['slope_m_per_s']*(t-fit['center_time_s']))
    scores = {}
    for method, axes in error.items():
        north,east,up = (axes[axis] for axis in AXES)
        scores[method] = dict(
            north_rms_m=_rms(north), east_rms_m=_rms(east),
            height_rms_m=_rms(up),
            horizontal_rms_m=_rms([math.hypot(n,e) for n,e in zip(north,east)]),
            three_dimensional_rms_m=_rms(
                [math.sqrt(n*n+e*e+u*u)
                 for n,e,u in zip(north,east,up)]))
    return dict(training_epochs=len(training),
                selected_training_epochs=len(window),
                prediction_epochs=len(prediction),
                boundary_time_s=boundary,
                training_window_s=training_window_s,
                correction=corrections, scores=scores,
                scientific_decision='abstain',
                later_values_used_for_fitting=False)
