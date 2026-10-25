# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate bounded diagnostic; historical native forecasts stay unchanged."""


def diagnose_bounded_forecast(problem,point,forecast,operator,*,scale,training_remainder_radius,
        future_remainder_bounds,alpha_training,alpha_prediction,bound_margin,parameter_scales,
        prediction_scales,rank_rtol,estimability_rtol,estimability_atol):
    import numpy as np
    from .ilvis0_native_error_training import diagnose_forecast
    from .ilvis0_precision_value import longitude_residual
    from .bounded_state_prediction import predict
    # Reuse the qualified forecast/split/prefix/all-column checks, including the
    # original unrestricted diagnostic and all its explicit abstention labels.
    if getattr(problem,'requires_extended_training_difference',False) is not True:
        raise ValueError('before-cast native fitted-point binding required')
    result=diagnose_forecast(problem,point,forecast,operator,bound_margin=bound_margin,
        parameter_scales=parameter_scales,prediction_scales=prediction_scales,
        rank_rtol=rank_rtol,estimability_rtol=estimability_rtol,estimability_atol=estimability_atol)
    difference=np.asarray(forecast['training_coordinate_difference'],float)
    earlier=-difference.copy();earlier[:,1]=longitude_residual(earlier[:,1])
    point=np.asarray(point,float);m=len(problem.gps);p=len(problem.bounds.active)
    bounds=np.column_stack((-np.ones(p)-point,np.ones(p)-point))
    result['bounded_calibration']=predict(operator=operator,design=forecast['jacobian'],
        training_values=earlier.ravel(),training_epochs=m,coefficient_bounds=bounds,
        nominal_future=np.asarray(forecast['coordinates'])[m:].ravel(),scale=scale,
        training_remainder_radius=training_remainder_radius,future_remainder_bounds=future_remainder_bounds,
        alpha_training=alpha_training,alpha_prediction=alpha_prediction,
        mean_design_is_fixed=False,rank_tolerance=rank_rtol,maximum_parameters=27,
        prediction_ids=[f'epoch-{i}-{axis}' for i in range(m,operator.epoch_count) for axis in ('latitude','longitude','height')])
    result['bounded_calibration'].update(normalized_point=point.tolist(),
        coefficient_bounds=bounds.tolist(),calibration_coordinates='normalized displacement from saved fitted point',
        coordinate_chart='receiver latitude/longitude radians and ellipsoidal height metres',
        native_jacobian_is_a_global_linear_model=False)
    return result


class BoundedForecastErrorDiagnostic:
    """Same protocol call shape; extend the fixed error law exactly once.

    The scale and deterministic remainder allowances are caller-owned assumptions,
    never selected from withheld positions or silently supplied as zero.
    """
    def __init__(self,factory,*,target,receiver_transform_policy,bound_margin,rank_rtol,
            estimability_rtol,estimability_atol,scale_value,scale_source_id,training_remainder_radius,
            future_remainder_bounds,alpha_training,alpha_prediction):
        import math
        import numpy as np
        from .ilvis0_native_error_training import ForecastErrorDiagnostic
        # Constructor validation is shared with the existing provider.
        validated=ForecastErrorDiagnostic(factory,target=target,receiver_transform_policy=receiver_transform_policy,
            bound_margin=bound_margin,rank_rtol=rank_rtol,estimability_rtol=estimability_rtol,estimability_atol=estimability_atol)
        if (not isinstance(scale_source_id,str) or not scale_source_id or not math.isfinite(scale_value) or scale_value<0
                or not all(math.isfinite(v) and 0<v<1 for v in (alpha_training,alpha_prediction))
                or alpha_training+alpha_prediction>=1
                or (training_remainder_radius is not None and
                    (not math.isfinite(training_remainder_radius) or training_remainder_radius<0))):
            raise ValueError('explicit scale, error allocation and optional supported remainder allowances required')
        future=None if future_remainder_bounds is None else np.array(future_remainder_bounds,float,copy=True)
        if future is not None:
            if future.ndim!=1 or not len(future) or not np.all(np.isfinite(future)) or np.any(future<0):
                raise ValueError('finite future coordinate remainder bounds required')
            future.setflags(write=False)
        self.reference=validated;self.scale_value=scale_value;self.scale_source_id=scale_source_id
        self.training_remainder=training_remainder_radius;self.future_remainder=future
        self.alpha_training=alpha_training;self.alpha_prediction=alpha_prediction

    def __call__(self,problem,point,forecast,*,theta,dv,dt,times,reserve):
        import numpy as np
        from .ilvis0_solver_position import physical_metric
        from .ilvis0_bounded_prediction import known_scale
        ref=self.reference
        future=len(times)-len(problem.gps_times)
        if future<1 or (self.future_remainder is not None and self.future_remainder.shape!=(3*future,)):
            raise ValueError('complete future remainder layout required before native error extension')
        operator,descriptor=ref.factory.extend(problem,theta=theta,dv=dv,dt=dt,times=times,
            target=ref.target,receiver_transform_policy=ref.policy,reserve=reserve)
        units=physical_metric(np.repeat(problem.gps[-1][None],future,axis=0)).ravel()
        result=diagnose_bounded_forecast(problem,point,forecast,operator,
            scale=known_scale(self.scale_value,source_id=self.scale_source_id,covariance_id=operator.configuration),
            training_remainder_radius=self.training_remainder,future_remainder_bounds=self.future_remainder,
            alpha_training=self.alpha_training,alpha_prediction=self.alpha_prediction,
            bound_margin=ref.bound_margin,parameter_scales=np.ones(len(problem.bounds.active)),
            prediction_scales=units,rank_rtol=ref.rank_rtol,estimability_rtol=ref.estimability_rtol,
            estimability_atol=ref.estimability_atol)
        result.update(prediction_target=ref.target,error_operator=descriptor,
            parameter_scaling='normalized-unit-v1',prediction_scaling='last-training-receiver-metric-v1')
        return result
