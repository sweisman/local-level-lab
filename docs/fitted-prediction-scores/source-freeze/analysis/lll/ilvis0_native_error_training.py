# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed-error native training and explicitly limited forecast diagnostics.

No covariance selection, optimizer, original reads or calibrated decisions are
provided. Dense REML controls remain in the separate ilvis0_error_training module.
"""
import math

VERSION='native-structured-error-training-v1'


class ForecastErrorDiagnostic:
    """Declared earlier-only target and local calibration diagnostics.

    This is an explicit protocol provider, not a covariance estimate or a
    calibrated uncertainty interval. The physical-position target omits future
    receiver errors while keeping their effect on earlier conditioning.
    """
    def __init__(self,factory,*,target,receiver_transform_policy,bound_margin,
                 rank_rtol,estimability_rtol,estimability_atol):
        if (not isinstance(factory,ErrorTrainingFactory)
                or target not in ('physical_position','receiver_measurement')
                or receiver_transform_policy!='last-training-transform-v1'
                or not all(math.isfinite(a) for a in (bound_margin,rank_rtol,estimability_rtol,estimability_atol))
                or not 0<bound_margin<1 or not 0<rank_rtol<1
                or not 0<=estimability_rtol<1 or estimability_atol<0):
            raise ValueError('fixed factory, prediction target and complete numerical diagnostic policy required')
        self.factory=factory;self.target=target;self.policy=receiver_transform_policy
        self.bound_margin=bound_margin;self.rank_rtol=rank_rtol
        self.estimability_rtol=estimability_rtol;self.estimability_atol=estimability_atol

    def __call__(self,problem,point,forecast,*,theta,dv,dt,times,reserve):
        import numpy as np
        from .ilvis0_solver_position import physical_metric
        operator,descriptor=self.factory.extend(problem,theta=theta,dv=dv,dt=dt,times=times,
            target=self.target,receiver_transform_policy=self.policy,reserve=reserve)
        future=len(times)-len(problem.gps_times)
        units=physical_metric(np.repeat(problem.gps[-1][None],future,axis=0)).ravel()
        result=diagnose_forecast(problem,point,forecast,operator,bound_margin=self.bound_margin,
            parameter_scales=np.ones(len(problem.bounds.active)),prediction_scales=units,
            rank_rtol=self.rank_rtol,estimability_rtol=self.estimability_rtol,estimability_atol=self.estimability_atol)
        result.update(prediction_target=self.target,error_operator=descriptor,
            parameter_scaling='normalized-unit-v1',prediction_scaling='last-training-receiver-metric-v1')
        return result


class ErrorTrainingFactory:
    """A fixed source-law provider accepting only the protocol's earlier block."""
    def __init__(self,*,noise,noise_kernel,gravity_anchor_height_m,maximum_packets,
                 maximum_queries,maximum_bytes,anchor_policy,disc_radius_m=6371000.):
        from .ilvis0_noise_history import PacketNoise
        from .linear_point_noise import LinearPointNoise
        if (not isinstance(noise,(PacketNoise,LinearPointNoise)) or not callable(noise_kernel)
                or any(type(x) is not int or x<1 for x in (maximum_packets,maximum_queries,maximum_bytes))
                or anchor_policy!='normalized-midpoint-v1' or not math.isfinite(disc_radius_m)
                or disc_radius_m<=0 or (gravity_anchor_height_m is not None and
                    (not math.isfinite(gravity_anchor_height_m) or gravity_anchor_height_m<=-6371000.))):
            raise ValueError('declared source law, native provider, anchor and finite storage/work caps required')
        self.noise=noise;self.noise_kernel=noise_kernel;self.anchor=gravity_anchor_height_m
        self.maximum_packets=maximum_packets;self.maximum_queries=maximum_queries
        self.maximum_bytes=maximum_bytes;self.anchor_policy=anchor_policy;self.radius=disc_radius_m

    @property
    def configuration(self):
        from .studies.artifacts import digest,encoded
        return digest(encoded(dict(noise_type=type(self.noise).__name__,roots=[a.tolist() for a in self.noise.roots],
            taus=list(self.noise.taus),anchor=self.anchor,radius=self.radius,anchor_policy=self.anchor_policy,
            maximum_packets=self.maximum_packets,maximum_queries=self.maximum_queries,maximum_bytes=self.maximum_bytes)))

    def __call__(self,times,gps,*,theta,dv,dt,model,limits,profile,clock,maximum_interval_s,
                 kernel,tangent_kernel,training_weight,time_origin_s,reserve):
        import numpy as np
        from dataclasses import replace
        from .ilvis0_training_forecast import initialize_training
        from .ilvis0_estimator import Bounds
        from .ilvis0_exploratory import ConditionalBounds,MODELS
        from .ilvis0_shape import TangentProblem
        from .ilvis0_wide_tangent import problem as wider
        from .studies.artifacts import digest,encoded
        if model not in MODELS or type(profile) is not bool or not callable(reserve):
            raise ValueError('explicit candidate, processing case and work reservation required')
        times=np.asarray(times,float);gps=np.asarray(gps,float)
        if (not math.isfinite(time_origin_s) or not 0<=time_origin_s<604800
                or not np.array_equal(np.asarray(training_weight.times,float)-time_origin_s,times)
                or gps.shape!=(len(times),3) or not np.all(np.isfinite(gps))):
            raise ValueError('matching earlier receiver rows, epochs and fixed time origin required')
        if self.anchor is not None and self.anchor!=float(gps[0,2]):
            raise ValueError('gravity anchor must equal the first earlier receiver height')
        initial,gravity=initialize_training(times,gps,theta=theta,dv=dv,dt=dt,model=model,
            maximum_interval_s=maximum_interval_s,clock=clock)
        conditional=ConditionalBounds(limits,fit_earth_removal=profile)
        spec=replace(training_weight.spec,drift_origin_s=training_weight.spec.drift_origin_s-time_origin_s)
        def native_charge(**work):
            if set(work)!={'native_calls','packet_steps'}:
                raise ValueError('complete low-level native work charge required')
            reserve(native_calls=work['native_calls'],packet_visits=work['packet_steps'])
        operator,descriptor=build_training_operator(theta=theta,dv=dv,dt=dt,times=times,initial=initial,
            bounds=conditional,model=model,gravity_mps2=gravity,disc_radius_m=self.radius,noise=self.noise,
            receiver_spec=spec,receiver_transforms=training_weight.transforms,noise_kernel=self.noise_kernel,
            gravity_anchor_height_m=self.anchor,maximum_packets=self.maximum_packets,
            maximum_queries=self.maximum_queries,maximum_bytes=self.maximum_bytes,
            anchor_policy=self.anchor_policy,reserve=native_charge)
        descriptor.pop('configuration')
        descriptor.update(initial_state_source='training-only-receiver-and-increments',
            receiver_time_origin_s=float(time_origin_s),receiver_policy=training_weight.descriptor,
            receiver_policy_configuration=training_weight.configuration,
            receiver_source_sha256=training_weight.source_sha256,
            receiver_imu_error_independence_assumed=True)
        descriptor['configuration']=digest(encoded(descriptor))
        base=TangentProblem(theta,dv,dt,times,gps,None,initial,Bounds(limits),
            tangent_kernel=tangent_kernel,kernel=kernel,fit_earth_removal=profile,
            clock_hypothesis=clock,processing_hypothesis='unsubtracted_increment_hypothesis',
            maximum_interval_s=maximum_interval_s,gravity_mps2=gravity,disc_radius_m=self.radius,
            observation_error=operator)
        prepared=wider(base,kernel=tangent_kernel)
        class BoundErrorProblem(type(prepared)):
            def _candidate(self,candidate):
                if candidate!=self.frozen_error_model:
                    raise ValueError('candidate model differs from the frozen covariance model')
            def prediction_tangent(self,point,candidate):
                self._candidate(candidate);return super().prediction_tangent(point,candidate)
            def residual_tangent(self,point,candidate):
                self._candidate(candidate);return super().residual_tangent(point,candidate)
        result=BoundErrorProblem.__new__(BoundErrorProblem);result.__dict__=prepared.__dict__.copy()
        result.frozen_error_model=model;result.error_descriptor=descriptor
        result.requires_extended_training_difference=True
        result.error_factory_configuration=self.configuration
        result.error_receiver_spec=spec
        result.error_receiver_transforms=np.array(training_weight.transforms,dtype=float,copy=True)
        result.error_receiver_transforms.setflags(write=False)
        result.error_maximum_interval_s=maximum_interval_s
        return result

    def extend(self,problem,*,theta,dv,dt,times,target,receiver_transform_policy,reserve):
        """Extend the same anchor without accepting any later receiver fields."""
        import numpy as np
        from .ilvis0_shape import TangentProblem
        from .studies.artifacts import digest,encoded
        if (not isinstance(problem,TangentProblem)
                or getattr(problem,'error_factory_configuration',None)!=self.configuration
                or target not in ('physical_position','receiver_measurement')
                or receiver_transform_policy!='last-training-transform-v1' or not callable(reserve)):
            raise ValueError('matching training factory and explicit prediction target/transform policy required')
        theta,dv,dt,times=(np.array(a,dtype=float,copy=True) for a in (theta,dv,dt,times))
        n=len(dt);m=len(problem.gps_times)
        if (dt.shape!=(n,) or n<len(problem.dt) or theta.shape!=(n,3) or dv.shape!=theta.shape
                or times.ndim!=1 or len(times)<=m or any(not np.all(np.isfinite(a)) for a in (theta,dv,dt,times))
                or np.any(dt<=0) or np.any(dt>problem.error_maximum_interval_s) or np.any(np.diff(times)<=0)
                or not np.array_equal(times[:m],problem.gps_times)
                or any(not np.array_equal(a[:len(b)],b) for a,b in (
                    (theta,problem.theta),(dv,problem.dv),(dt,problem.dt)))
                or (problem.clock_hypothesis=='nominal_200Hz' and not np.all(dt==.005))):
            raise ValueError('complete future IMU/time support and exact earlier prefix required')
        initial=problem.initial
        earlier=dict(theta=problem.theta,dv=problem.dv,dt=problem.dt,times=problem.gps_times,
            receiver_transforms=problem.error_receiver_transforms,
            initial_coordinates=[initial[k] for k in ('latitude_rad','longitude_rad','height_m')],
            initial_velocity=initial['velocity_ned_mps'],initial_rotation=initial['attitude_body_to_ned'])
        if any(digest(np.asarray(a,dtype='<f8').tobytes())!=problem.error_descriptor['input_sha256'][name]
                for name,a in earlier.items()):
            raise ValueError('frozen training inputs, geometry or initial anchor changed')
        transforms=np.empty((len(times),3,3));transforms[:m]=problem.error_receiver_transforms
        transforms[m:]=problem.error_receiver_transforms[-1]
        def charge(**work):reserve(native_calls=work['native_calls'],packet_visits=work['packet_steps'])
        operator,descriptor=build_training_operator(theta=theta,dv=dv,dt=dt,times=times,
            initial=initial,bounds=problem.bounds,model=problem.frozen_error_model,
            gravity_mps2=problem.gravity,disc_radius_m=problem.radius,noise=self.noise,
            receiver_spec=problem.error_receiver_spec,receiver_transforms=transforms,
            noise_kernel=self.noise_kernel,gravity_anchor_height_m=self.anchor,
            maximum_packets=self.maximum_packets,maximum_queries=self.maximum_queries,maximum_bytes=self.maximum_bytes,
            anchor_policy=self.anchor_policy,reserve=charge,
            receiver_epochs=m if target=='physical_position' else None)
        if operator.prefix(m).configuration!=problem.observation_error.prefix(m).configuration:
            raise ValueError('extended error operator changed its training covariance prefix')
        descriptor.pop('configuration')
        descriptor.update(prediction_target=target,receiver_transform_policy=receiver_transform_policy,
            training_epochs=m,training_operator_configuration=problem.observation_error.configuration,
            factory_configuration=self.configuration,later_receiver_fields_used=False)
        descriptor['configuration']=digest(encoded(descriptor))
        return operator,descriptor


def build_training_operator(*,theta,dv,dt,times,initial,bounds,model,gravity_mps2,
        disc_radius_m,noise,receiver_spec,receiver_transforms,noise_kernel,
        gravity_anchor_height_m,maximum_packets,maximum_queries,maximum_bytes,
        anchor_policy,reserve,receiver_epochs=None):
    """Build a fixed covariance at the declared normalized midpoint only.

    No receiver values, fitted residuals, generating truth or chosen parameter
    solution is an input. The owning factory must obtain initial state, gravity,
    receiver transforms and the height anchor from earlier observations only.
    """
    import numpy as np
    from .ilvis0_exploratory import ConditionalBounds,MODELS
    from .ilvis0_noise_history import NativeNoiseHistory,PacketNoise
    from .linear_point_noise import LinearPointNoise
    from .ilvis0_error_model import Spec,factor
    from .receiver_noise_states import ReceiverAugmentation
    from .state_space_covariance import LinearInnovations
    from .studies.artifacts import digest,encoded
    if anchor_policy!='normalized-midpoint-v1':
        raise ValueError('declared fixed normalized-midpoint anchor policy required')
    if (not isinstance(bounds,ConditionalBounds) or model not in MODELS
            or not isinstance(noise,(PacketNoise,LinearPointNoise)) or not isinstance(receiver_spec,Spec)
            or not callable(reserve) or not math.isfinite(gravity_mps2)
            or gravity_mps2<=bounds.limits.get('gravity_delta',0.)):
        raise ValueError('explicit supported candidate, bounds, noise and receiver law required')
    # Match the original problem's input ABI. Extended precision starts inside
    # mechanization; hashes describe the exact effective binary64 inputs.
    theta=np.asarray(theta,float);dv=np.asarray(dv,float)
    intervals=np.asarray(dt,float);queries=np.asarray(times,float)
    if (intervals.ndim!=1 or not len(intervals) or queries.ndim!=1 or len(queries)<2
            or not np.all(np.isfinite(intervals)) or np.any(intervals<=0)
            or not np.all(np.isfinite(queries)) or np.any(np.diff(queries)<=0)):
        raise ValueError('ordered finite queries and positive raw intervals required')
    if receiver_epochs is not None and (type(receiver_epochs) is not int or not 1<=receiver_epochs<=len(queries)):
        raise ValueError('explicit receiver observation support required')
    offset=bounds.limits.get('time_offset',0.);end=np.cumsum(intervals)[-1]
    if queries[0]-offset<0 or queries[-1]+offset>end:
        raise ValueError('full declared timing-bound support required before covariance construction')
    transforms=np.array(receiver_transforms,dtype=float,copy=True)
    if (transforms.shape!=(len(queries),3,3) or not np.all(np.isfinite(transforms))
            or np.any(np.linalg.slogdet(transforms)[0]==0)):
        raise ValueError('complete invertible receiver-coordinate transforms required')
    white=transforms@factor(receiver_spec.white)
    point=np.zeros(len(bounds.active));physical=bounds.decode(point)
    coordinates=np.array([initial[k] for k in ('latitude_rad','longitude_rad','height_m')],dtype=float)
    velocity=np.asarray(initial['velocity_ned_mps'],float);rotation=np.asarray(initial['attitude_body_to_ned'],float)
    history=NativeNoiseHistory(kernel=noise_kernel,coordinates=coordinates,
        velocity=velocity,rotation=rotation,
        theta=theta,delta_v=dv,dt=intervals,query_times=queries,time_offset_s=0.,model=MODELS.index(model),
        gravity=gravity_mps2,radius=disc_radius_m or 6371000.,removal=physical['earth_removal'],
        anchor_height=gravity_anchor_height_m,lever=np.zeros(3),correction_scales=np.ones(6),
        noise=noise,white_loadings=white,maximum_packets=maximum_packets,
        maximum_epochs=maximum_queries,reserve=reserve)
    augmented=ReceiverAugmentation(history.steps(),times=queries,spec=receiver_spec,
        transforms=transforms,state_dimension=history.state_dimension,
        initial_loading=noise.initial_loading(),maximum_epochs=maximum_queries,receiver_epochs=receiver_epochs)
    operator=LinearInnovations(augmented.steps(),epoch_count=len(queries),
        state_dimension=augmented.state_dimension,observation_dimension=3,
        initial_loading=augmented.initial_loading,maximum_bytes=maximum_bytes,
        design_is_fixed=True,error_distribution='gaussian',
        observation_form='before_transition_shared_noise',
        white_error_may_be_singular=receiver_epochs is not None and receiver_epochs<len(queries))
    source_law='linear_rate_points' if isinstance(noise,LinearPointNoise) else 'recorded_increments'
    arrays=dict(theta=theta,dv=dv,dt=intervals,times=queries,receiver_transforms=transforms,
        initial_coordinates=coordinates,initial_velocity=velocity,initial_rotation=rotation)
    descriptor=dict(version=VERSION,model=model,source_law=source_law,anchor_policy=anchor_policy,
        anchor_normalized_point=point.tolist(),active_parameters=list(bounds.active),
        bounds=dict(bounds.limits),earth_removal_at_anchor=physical['earth_removal'],
        gravity_mps2=float(gravity_mps2),disc_radius_m=float(disc_radius_m or 6371000.),
        gravity_anchor_height_m=None if gravity_anchor_height_m is None else float(gravity_anchor_height_m),
        input_precision='original-binary64-ABI',
        input_sha256={key:digest(np.asarray(value,dtype='<f8').tobytes()) for key,value in arrays.items()},
        noise_roots=[root.tolist() for root in noise.roots],noise_correlation_times_s=list(noise.taus),
        receiver_white=receiver_spec.white.tolist(),receiver_offset=receiver_spec.offset.tolist(),
        receiver_drift=receiver_spec.drift.tolist(),receiver_drift_origin_s=receiver_spec.drift_origin_s,
        receiver_drift_span_s=receiver_spec.drift_span_s,
        receiver_components=[dict(tau_s=tau,covariance=cov.tolist()) for tau,cov in receiver_spec.components],
        observation_chart='receiver WGS84 latitude/longitude/ellipsoidal height',
        weights_depend_on_fitted_residuals=False,weights_frozen_during_optimization=True,
        state_dimension=operator.state_dimension,operator_configuration=operator.configuration,
        error_log_determinant=operator.log_determinant,parameter_uncertainty_included=False,
        confidence_calibrated=False)
    descriptor['configuration']=digest(encoded(descriptor))
    if receiver_epochs is not None:
        descriptor.pop('configuration');descriptor['receiver_observation_epochs']=receiver_epochs
        descriptor['configuration']=digest(encoded(descriptor))
    return operator,descriptor


def gaussian_training_score(problem, *, residual_sum_squares):
    """Keep normalization when declared propagated covariance differs by model."""
    from .ilvis0_estimator import MotionProblem
    if (not isinstance(problem,MotionProblem) or not math.isfinite(residual_sum_squares)
            or residual_sum_squares<0 or not math.isfinite(problem.error_log_determinant)):
        raise ValueError('finite native training cost and fixed covariance normalization required')
    n=problem.gps.size;logdet=problem.error_log_determinant
    score=.5*(residual_sum_squares+logdet+n*math.log(2*math.pi))
    if not math.isfinite(score):raise ValueError('unrepresentable Gaussian training score')
    return dict(residual_sum_squares=float(residual_sum_squares),log_determinant=float(logdet),
        row_count=int(n),negative_log_likelihood=float(score),model_comparison_calibrated=False,
        covariance_parameters_estimated=False,scientific_decision='abstain')


def diagnose_forecast(problem,point,forecast,operator,*,bound_margin,parameter_scales,
                      prediction_scales,rank_rtol,estimability_rtol,estimability_atol):
    """Condition on earlier receiver-minus-model errors, never later positions.

    The fixed-parameter moments are separate from unrestricted linear calibration
    diagnostics. No nonlinear or bounded-calibration confidence is established.
    Active bounds and unidentified prediction directions never obtain finite
    unrestricted-calibration covariance. Raw point forecasts are retained.
    """
    import numpy as np
    from .ilvis0_shape import TangentProblem
    from .state_space_covariance import LinearInnovations,PrefixInnovations
    from .calibrated_linear_prediction import predict
    from .ilvis0_precision_value import longitude_residual
    if (not isinstance(problem,TangentProblem) or not isinstance(operator,LinearInnovations)
            or operator.observation_dimension!=3 or not isinstance(forecast,dict)
            or not math.isfinite(bound_margin) or not 0<bound_margin<1):
        raise ValueError('native problem, full fixed error law, forecast and bound policy required')
    problem.bounds.decode(point);point=np.asarray(point,float);names=list(problem.bounds.active)
    m=len(problem.gps);n=operator.epoch_count;p=len(names)
    coordinates=np.array(forecast.get('coordinates'),dtype=float,copy=True)
    jacobian=np.asarray(forecast.get('jacobian'),dtype=float)
    if (m>=n or coordinates.shape!=(n,3) or jacobian.shape!=(3*n,p)
            or not np.all(np.isfinite(coordinates)) or not np.all(np.isfinite(jacobian))
            or forecast.get('active_parameters')!=names or forecast.get('training_epochs')!=m
            or forecast.get('prediction_epochs')!=n-m
            or forecast.get('continuous_propagation_without_gps_reset') is not True
            or forecast.get('prediction_receiver_positions_used') is not False):
        raise ValueError('complete native forecast, exact earlier split and all calibration columns required')
    projection=getattr(problem,'observation_error',None)
    if not isinstance(projection,(LinearInnovations,PrefixInnovations)):
        raise ValueError('the matching structured training error operator is required')
    configuration=projection.configuration if isinstance(projection,PrefixInnovations) else projection.prefix(m).configuration
    if operator.prefix(m).configuration!=configuration:
        raise ValueError('training and prediction covariance prefixes differ')
    if 'training_coordinate_difference' in forecast:
        difference=np.array(forecast['training_coordinate_difference'],dtype=float,copy=True)
        if difference.shape!=(m,3) or not np.all(np.isfinite(difference)):
            raise ValueError('finite complete before-cast training difference required')
        if getattr(problem,'requires_extended_training_difference',False):
            saved_point=np.asarray(forecast.get('normalized_parameters'),dtype=float)
            if saved_point.shape!=point.shape or not np.array_equal(saved_point,point):
                raise ValueError('forecast fitted point differs from calibration diagnostic point')
            if (forecast.get('frozen_error_model')!=problem.frozen_error_model
                    or forecast.get('error_training_configuration')!=projection.configuration
                    or forecast.get('training_residual_subtraction')!='native-before-binary64-cast'):
                raise ValueError('forecast model, error configuration or residual provenance differs')
        earlier=-difference;precision='native-subtraction-before-binary64-cast'
    else:
        if getattr(problem,'requires_extended_training_difference',False):
            raise ValueError('native before-cast training residuals must be retained')
        earlier=problem.gps-coordinates[:m];precision='binary64-coordinate-difference'
    earlier[:,1]=longitude_residual(earlier[:,1])
    _,checkpoint=operator.apply_block(earlier.ravel(),first_epoch=0)
    fixed=operator.conditional_marginals(state=checkpoint)
    fixed['mean_adjustment']=fixed['mean'].copy()
    fixed['mean']=coordinates[m:]+fixed['mean']
    active=[name for name,value in zip(names,point) if abs(value)>=1-bound_margin]
    unsupported=dict(status='active_bounds_unsupported',active_parameters_at_bounds=active,
        parameter_uncertainty_included=False,nonlinear_coverage_established=False,
        confidence_calibrated=False)
    if active:
        linear=unsupported
    elif not p:
        linear=dict(status='no_active_calibration',parameter_uncertainty_included=False,
            nonlinear_coverage_established=False,confidence_calibrated=False)
    else:
        linear=predict(operator,jacobian,earlier.ravel(),training_epochs=m,
            parameter_scales=parameter_scales,prediction_scales=prediction_scales,
            rank_rtol=rank_rtol,estimability_rtol=estimability_rtol,
            estimability_atol=estimability_atol,maximum_parameters=27)
        if linear['status']=='estimable':
            correction=linear.pop('minimum_norm_parameter_estimate')
            if np.any(abs(point+correction)>1):
                linear=dict(unsupported,status='linear_step_outside_bounds',
                    local_normalized_parameter_correction=correction)
            else:
                linear['local_normalized_parameter_correction']=correction
                linear['mean_adjustment']=linear['mean'].copy()
                linear['mean']=coordinates[m:]+linear['mean']
        linear['confidence_calibrated']=False
    return dict(raw_coordinates=coordinates,fixed_parameters=fixed,linear_calibration=linear,
        training_epochs=m,prediction_epochs=n-m,training_residual_precision=precision,
        later_observations_used=False,confidence_calibrated=False,scientific_decision='abstain')
