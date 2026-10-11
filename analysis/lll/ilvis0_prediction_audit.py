# SPDX-License-Identifier: AGPL-3.0-or-later
"""Inspect saved prediction errors and calibration; no integration or fitting."""
import math

from . import ilvis0_saved_audit as saved

VERSION='ilvis0-saved-prediction-audit-v1'


def _errors(rows):
    horizontal=[math.hypot(r['north_direct_error_m'],r['east_direct_error_m']) for r in rows]
    up=[r['up_direct_error_m'] for r in rows]
    return dict(epochs=len(rows),horizontal_rms_m=math.sqrt(sum(x*x for x in horizontal)/len(rows)),
        vertical_rms_m=math.sqrt(sum(x*x for x in up)/len(rows)),
        maximum_horizontal_m=max(horizontal),maximum_absolute_up_m=max(abs(x) for x in up),
        endpoint_horizontal_m=horizontal[-1],endpoint_up_m=up[-1])


def error_growth(rows,training_epochs,*,window_seconds=30):
    if (not isinstance(training_epochs,int) or not 0<training_epochs<len(rows) or
        not math.isfinite(window_seconds) or window_seconds<=0):
        raise ValueError('invalid split or window')
    values=[]
    try:
        for i,row in enumerate(rows):
            fields={k:float(row[k]) for k in ('time_s','north_direct_error_m',
                'east_direct_error_m','up_direct_error_m')}
            if (int(row['epoch'])!=i or row['role']!=('training' if i<training_epochs else 'prediction')
                or any(not math.isfinite(v) for v in fields.values())
                or values and fields['time_s']<=values[-1]['time_s']):
                raise ValueError('invalid saved epoch order, role or value')
            values.append(fields)
    except (KeyError,TypeError,OverflowError) as error:
        raise ValueError('invalid saved epoch record') from error
    future=values[training_epochs:]; origin=future[0]['time_s']; groups={}
    for row in future:
        index=math.floor((row['time_s']-origin)/window_seconds)
        groups.setdefault(index,[]).append(row)
    windows=[dict(offset_start_s=i*window_seconds,first_time_s=part[0]['time_s'],
        last_time_s=part[-1]['time_s'],**_errors(part)) for i,part in sorted(groups.items())]
    return dict(training=_errors(values[:training_epochs]),prediction=_errors(future),windows=windows,
        window_seconds=window_seconds,windows_are_independent_trials=False,
        optimizer_starts=0,native_predictions=0)


def conditioning(fit):
    singular=fit.get('singular_values',[])
    if not singular or any(not math.isfinite(x) or x<0 for x in singular):
        raise ValueError('invalid saved singular values')
    gradient=fit.get('exact_projected_gradient_relative')
    tolerance=fit.get('stationarity_tolerance',1e-4)
    if not math.isfinite(tolerance) or tolerance<=0:
        raise ValueError('invalid stationarity tolerance')
    if gradient is not None and (not math.isfinite(gradient) or gradient<0):
        raise ValueError('invalid saved stationarity')
    low,high=min(singular),max(singular)
    return dict(status=saved.fit_status(fit),stationarity_ratio=gradient/tolerance if gradient is not None else None,
        smallest_singular_value=low,largest_singular_value=high,
        jacobian_condition_ratio=high/low if low else None,
        parameter_coupling_identified=False)


def parameter_changes(training,full_window,case):
    if training['active_parameters']!=full_window['active_parameters']:
        raise ValueError('matched active parameter definitions differ')
    before=saved.parameter_rows(full_window,case['limits'],profile=case['profile'])
    after=saved.parameter_rows(training,case['limits'],profile=case['profile'])
    return [dict(parameter=a['parameter'],unit=a['unit'],full_window_value=a['value'],
        training_value=b['value'],change=b['value']-a['value'],
        full_window_boundary=a['boundary'],training_boundary=b['boundary'],
        normalized_change=b['normalized_value']-a['normalized_value'],
        lower_limit=a['lower_limit'],upper_limit=a['upper_limit']) for a,b in zip(before,after)]
