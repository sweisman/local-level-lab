# SPDX-License-Identifier: AGPL-3.0-or-later
"""Counted training and observation-free forecast at one fixed calibration."""

import numpy as np


def interpolate(first,second,quarter):
    a,b=(np.asarray(value,float) for value in (first,second))
    if (quarter not in (1,2,3) or a.shape!=(26,) or b.shape!=(26,) or
            not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)) or
            np.any(abs(a)>1) or np.any(abs(b)>1)):
        raise ValueError('two complete feasible 26-coordinate endpoints required')
    return a+(b-a)*(quarter/4)


def calculate(context,problem,model,point,*,packets,cut,common):
    from .ilvis0_forecast import native_forecast
    point=np.asarray(point,float)
    values=np.asarray(common['values'],float)
    times=np.asarray(common['times'],float)
    count=common['layout']['receiver_epochs']
    outer=common['layout']['training_epochs']
    horizon=min(outer-cut,count-outer)
    if (point.shape!=(len(problem.bounds.active),) or
            not np.all(np.isfinite(point)) or np.any(abs(point)>1) or
            values.shape!=(packets,15) or len(times)!=count or
            horizon<1 or cut+horizon>count):
        raise ValueError('complete feasible fixed vector and raw stream required')
    context.charge(native_calls=1,packet_visits=packets*cut)
    residual,_,_=problem.residual_tangent(point,model)
    cost=float(residual@residual)
    if not np.isfinite(cost):
        raise ValueError('finite training cost required')
    forecast=native_forecast(problem,point,model,
        theta=values[:,9:12],dv=values[:,12:15],dt=values[:,2],
        times=times[:cut+horizon],maximum_interval_s=.0075,
        reserve=context.charge)
    if (forecast['prediction_receiver_positions_used'] is not False or
            forecast['training_epochs']!=cut or
            forecast['prediction_epochs']!=horizon):
        raise ValueError('observation-free complete forecast required')
    return dict(cost=cost,normalized_parameters=point.tolist(),
                training_epochs=cut),dict(
        coordinates=forecast['coordinates'].tolist(),
        training_epochs=cut,prediction_epochs=horizon,
        continuous_propagation_without_gps_reset=True,
        prediction_receiver_positions_used=False)
