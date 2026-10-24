# SPDX-License-Identifier: AGPL-3.0-or-later
"""Observation-free native forecasting; historical prediction helpers stay unchanged."""
import math
import numpy as np


def native_forecast(training,point,model,*,theta,dv,dt,times,maximum_interval_s,reserve,
                    retain_training_difference=False):
    """Continue a training calibration without accepting later GPS or covariance.

    The existing tangent kernel performs all motion/calibration calculations.
    Raw inputs must retain the exact training prefix. The caller freezes source,
    clock and finite resources, and reserves this call before native execution.
    Returned derivatives and start sensitivity are not calibrated uncertainty.
    """
    import ctypes
    from .ilvis0_shape import TangentProblem,PARAMETERS
    from .ilvis0_exploratory import MODELS
    from .ilvis0_training_density import boundary_count
    if (not isinstance(training,TangentProblem) or model not in MODELS or not callable(reserve)
            or training.clock_hypothesis not in ('header_elapsed','nominal_200Hz')
            or training.processing_hypothesis!='unsubtracted_increment_hypothesis'
            or not math.isfinite(maximum_interval_s) or maximum_interval_s<=0):
        raise ValueError('qualified training problem, explicit clock/support and reservation required')
    if getattr(training,'frozen_error_model',model)!=model:
        raise ValueError('forecast model differs from the frozen training error model')
    if (type(retain_training_difference) is not bool or (retain_training_difference
            and not getattr(training,'native_residual_difference_supported',False))):
        raise ValueError('explicit supported native before-cast training residual provider required')
    physical=training.bounds.decode(point)
    theta,dv,dt,times=(np.array(v,dtype=float,copy=True,order='C') for v in (theta,dv,dt,times))
    n=len(dt);m=len(times);nt=len(training.dt);mt=len(training.gps_times)
    if (dt.shape!=(n,) or n<nt or theta.shape!=(n,3) or dv.shape!=(n,3)
            or times.shape!=(m,) or m<=mt or any(not np.all(np.isfinite(v)) for v in (theta,dv,dt,times))
            or np.any(dt<=0) or np.any(dt>maximum_interval_s) or np.any(np.diff(times)<=0)
            or times[:mt].tobytes()!=training.gps_times.tobytes()
            or any(a[:nt].tobytes()!=b.tobytes() for a,b in ((theta,training.theta),(dv,training.dv),(dt,training.dt)))
            or (training.clock_hypothesis=='nominal_200Hz' and not np.all(dt==.005))):
        raise ValueError('complete raw inputs, exact training prefix and fixed increasing queries required')
    offset=training.bounds.limits.get('time_offset',0.)
    if times[0]-offset<0 or times[-1]+offset>np.cumsum(dt)[-1]:
        raise ValueError('forecast queries lack complete timing-bound support')
    active=training.bounds.active;normalized=dict(zip(active,point,strict=True))
    expanded=np.array([normalized.get(name,0.) for name in PARAMETERS])
    limits=np.array([training.bounds.limits.get(name,0.) for name in PARAMETERS])
    initial=training.initial
    coordinates=np.array([initial[k] for k in ('latitude_rad','longitude_rad','height_m')])
    output=np.empty((m,3));jac=np.empty((3*m,27));counter=ctypes.c_int()
    extra={}
    if retain_training_difference:
        observations=np.zeros((m,3));observations[:mt]=training.gps
        difference=np.empty((m,3));extra=dict(observations=observations,difference=difference)
    reserve(native_calls=1,packet_visits=n*m)
    code=training.tangent_kernel(n,theta,dv,dt,m,times,coordinates,
        np.ascontiguousarray(initial['velocity_ned_mps']),np.ascontiguousarray(initial['attitude_body_to_ned']),
        limits,expanded,MODELS.index(model),int(training.bounds.fit_earth_removal),
        training.gravity,training.radius or 6371000.,output,jac,ctypes.byref(counter),**extra)
    classification=boundary_count(status=int(code),counter=counter.value,dt=dt,times=times+physical['time_offset'])
    if not np.all(np.isfinite(output)) or not np.all(np.isfinite(jac)):
        raise ValueError('native forecast returned nonfinite coordinates or derivatives')
    columns=[PARAMETERS.index(name) for name in active]
    result=dict(coordinates=output,jacobian=jac[:,columns],active_parameters=list(active),
        boundary_counter=counter.value,boundary_classification=classification,
        training_epochs=mt,prediction_epochs=m-mt,clock_hypothesis=training.clock_hypothesis,
        continuous_propagation_without_gps_reset=True,prediction_receiver_positions_used=False,
        confidence_calibrated=False,scientific_decision='abstain')
    if retain_training_difference:
        if not np.all(np.isfinite(difference[:mt])):raise ValueError('nonfinite before-cast training difference')
        result['training_coordinate_difference']=difference[:mt].copy()
        result['training_residual_subtraction']='native-before-binary64-cast'
        result['normalized_parameters']=np.asarray(point,dtype=float).tolist()
        result['frozen_error_model']=model
        projection=getattr(training,'observation_error',None)
        result['error_training_configuration']=None if projection is None else projection.configuration
    return result

