# SPDX-License-Identifier: AGPL-3.0-or-later
"""Common ESA fitting/forecast path with only earlier receiver observations."""
import math


def train_and_forecast(*,theta,dv,dt,times,training_rows,time_origin_s,model,profile,
                       policy_id,start,limits,maximum_evaluations,maximum_interval_s,
                       kernel,tangent_kernel,reserve,save,check_continue,
                       training_error_factory=None,forecast_error_diagnostic=None):
    import numpy as np
    from lll.airquantumgrav_error_policy import build
    from lll.ilvis0_training_forecast import training_problem,fit_training
    from lll.ilvis0_forecast import native_forecast
    from lll.ilvis0_exploratory import MODELS
    from lll.studies.artifacts import digest
    if (model not in MODELS or type(profile) is not bool or type(start) is not int or start not in (0,1)
            or type(maximum_evaluations) is not int or not 8<=maximum_evaluations<=200
            or not math.isfinite(time_origin_s) or not 0<=time_origin_s<604800
            or not math.isfinite(maximum_interval_s) or not 0<maximum_interval_s<=.005
            or (training_error_factory is not None and not callable(training_error_factory))
            or (forecast_error_diagnostic is not None and
                (not callable(forecast_error_diagnostic) or training_error_factory is None))):
        raise ValueError('declared model, processing, start, clock and finite fit allowance required')
    times=np.asarray(times,float);theta,dv,dt=(np.asarray(v,float) for v in (theta,dv,dt))
    rows=list(training_rows);cut=len(rows)
    if (times.ndim!=1 or not 2<=cut<len(times) or cut>1024 or np.any(np.diff(times)<=0)
            or not np.all(np.isfinite(times)) or dt.ndim!=1 or not len(dt) or theta.shape!=(len(dt),3)
            or dv.shape!=theta.shape or any(not np.all(np.isfinite(v)) for v in (theta,dv,dt))
            or np.any(dt<=0) or np.any(dt>maximum_interval_s)):
        raise ValueError('complete finite raw arrays, bounded earlier rows and later query times required')
    weight=build(rows,policy_id=policy_id)
    if not np.array_equal(weight.times-time_origin_s,times[:cut]):
        raise ValueError('training rows must match exact earlier query times')
    offset=limits.get('time_offset',0.);ends=np.cumsum(dt)
    if times[0]-offset<0 or times[-1]+offset>ends[-1]:raise ValueError('whole latency-bound support required')
    count=int(np.searchsorted(ends,times[cut-1]+offset,side='left'))+1
    gps=np.array([[math.radians(row['latitude_deg']),math.radians(row['longitude_deg']),row['height_m']] for row in rows])
    check_continue()
    if training_error_factory is None:
        covariance=weight.dense(maximum_epochs=1024)
        problem=training_problem(times[:cut],gps,theta=theta[:count],dv=dv[:count],dt=dt[:count],covariance=covariance,
            model=model,limits=limits,profile=profile,clock='header_elapsed',maximum_interval_s=maximum_interval_s,
            kernel=kernel,tangent_kernel=tangent_kernel)
    else:
        problem=training_error_factory(times[:cut],gps,theta=theta[:count],dv=dv[:count],dt=dt[:count],
            model=model,limits=limits,profile=profile,clock='header_elapsed',maximum_interval_s=maximum_interval_s,
            kernel=kernel,tangent_kernel=tangent_kernel,training_weight=weight,
            time_origin_s=time_origin_s,reserve=reserve)
        if (getattr(problem,'observation_error',None) is None
                or getattr(problem,'frozen_error_model',None)!=model
                or not np.array_equal(problem.gps_times,times[:cut]) or not np.array_equal(problem.gps,gps)
                or any(not np.array_equal(a,b) for a,b in ((problem.theta,theta[:count]),
                    (problem.dv,dv[:count]),(problem.dt,dt[:count])))
                or not isinstance(getattr(problem,'error_descriptor',None),dict)
                or problem.error_descriptor.get('operator_configuration')!=problem.observation_error.configuration):
            raise ValueError('structured factory must retain exact training inputs, candidate and fixed error binding')
        save('training-error-operator.json',problem.error_descriptor)
    active=list(problem.bounds.active)
    if len(active)!=26+int(profile):raise ValueError('all declared calibration and processing columns required')
    save('training-observations.json',dict(times_s=times[:cut].tolist(),coordinates=gps.tolist(),
        training_epochs=cut,prediction_epochs=len(times)-cut,native_prefix_packets=count,
        weight_configuration=weight.configuration,weight_descriptor=weight.descriptor,
        weight_source_sha256=weight.source_sha256,time_origin_gps_sow_s=time_origin_s,
        true_initial_state_supplied=False,true_calibration_supplied=False,
        prediction_receiver_positions_used=False,training_prefix_sha256={k:digest(np.asarray(v[:count],dtype='<f8').tobytes())
            for k,v in [('theta',theta),('dv',dv),('dt',dt)]}))
    point=np.zeros(len(active)) if start==0 else np.where(np.arange(len(active))%2,.001,-.001)
    def counted(**work):check_continue();reserve(**work)
    fit=fit_training(problem,model,start=point,maximum_evaluations=maximum_evaluations,reserve=counted,stopping='near_zero')
    if training_error_factory is not None:
        from lll.ilvis0_native_error_training import gaussian_training_score
        fit['gaussian_training_score']=gaussian_training_score(problem,residual_sum_squares=fit['residual_sum_squares'])
    save('fit.json',fit);check_continue()
    forecast_arguments=dict(theta=theta,dv=dv,dt=dt,times=times,
        maximum_interval_s=maximum_interval_s,reserve=counted)
    if training_error_factory is not None:forecast_arguments['retain_training_difference']=True
    forecast=native_forecast(problem,fit['normalized_parameters'],model,**forecast_arguments)
    if forecast['active_parameters']!=active or fit['active_parameters']!=active:
        raise ValueError('complete active nuisance columns must survive fitting and forecasting')
    forecast_record=dict(coordinates=forecast['coordinates'].tolist(),times_s=times.tolist(),active_parameters=active,
        training_epochs=cut,prediction_epochs=len(times)-cut,continuous_propagation_without_gps_reset=True,
        prediction_receiver_positions_used=False)
    if training_error_factory is not None:
        difference=np.asarray(forecast.get('training_coordinate_difference'),float)
        if (difference.shape!=(cut,3) or not np.all(np.isfinite(difference))
                or forecast.get('training_residual_subtraction')!='native-before-binary64-cast'):
            raise ValueError('structured forecast must retain native before-cast training residuals')
        saved_point=np.asarray(forecast.get('normalized_parameters'),float)
        if (saved_point.shape!=(len(active),) or not np.array_equal(saved_point,fit['normalized_parameters'])
                or forecast.get('frozen_error_model')!=model
                or forecast.get('error_training_configuration')!=problem.observation_error.configuration):
            raise ValueError('structured forecast must match fitted point, candidate and error configuration')
        forecast_record.update(training_coordinate_difference=difference.tolist(),
            training_residual_subtraction=forecast['training_residual_subtraction'],
            normalized_parameters=saved_point.tolist(),frozen_error_model=model,
            error_training_configuration=forecast['error_training_configuration'])
    save('forecast.json',forecast_record)
    result=dict(fit=fit,forecast=forecast,training_epochs=cut,prediction_epochs=len(times)-cut,
        weight_configuration=weight.configuration,all_columns_retained=True,
        true_initial_state_supplied=False,true_calibration_supplied=False,forecast_saved_before_scoring=True)
    if training_error_factory is not None:result['training_error_configuration']=problem.observation_error.configuration
    if forecast_error_diagnostic is not None:
        check_continue()
        diagnostic=forecast_error_diagnostic(problem,fit['normalized_parameters'],forecast,
            theta=theta,dv=dv,dt=dt,times=times,reserve=reserve)
        if (not isinstance(diagnostic,dict) or diagnostic.get('later_observations_used') is not False
                or diagnostic.get('confidence_calibrated') is not False
                or diagnostic.get('prediction_target') not in ('physical_position','receiver_measurement')
                or diagnostic.get('training_epochs')!=cut or diagnostic.get('prediction_epochs')!=len(times)-cut
                or not np.array_equal(diagnostic.get('raw_coordinates'),forecast['coordinates'])):
            raise ValueError('earlier-only diagnostic, explicit target and unchanged point forecast required')
        import json
        save('forecast-error-diagnostic.json',json.loads(json.dumps(diagnostic,
            default=lambda value:value.tolist(),allow_nan=False)))
        result['forecast_error_diagnostic']=diagnostic
    return result
