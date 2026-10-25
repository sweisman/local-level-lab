# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-trajectory error benchmark, deliberately separate from fitting."""
import math

VERSION='known-calibration-generated-noise-benchmark-v1'


def material(*,duration_s,queries,query_start_s,query_step_s,reserve):
    import numpy as np
    from .airquantumgrav_truth import truth,GRAVITY,DISC_RADIUS
    from .airquantumgrav_observation_truth import observe,receiver_samples,_parameters
    from .airquantumgrav_geographic_controls import construct
    from .ilvis0_solver_position import physical_metric
    if (type(duration_s) not in (int,float) or not math.isfinite(duration_s) or not 2<=duration_s<=1200
            or type(queries) is not int or not 9<=queries<=1200
            or not all(type(v) in (int,float) and math.isfinite(v) for v in (query_start_s,query_step_s))
            or query_start_s<.01 or query_step_s<=0
            or query_start_s+(queries-1)*query_step_s+.001>=duration_s or not callable(reserve)):
        raise ValueError('finite complete generated benchmark support and construction allowance required')
    n=round(duration_s*300)
    if n/300!=duration_s:raise ValueError('complete 300 Hz nominal record required')
    reserve(generated_samples=n+1)
    rate_times=np.arange(n+1)/300.;args=dict(model='sphere_rotating',latitude_deg=55.,pattern='fast',
        removal=0.,height_profile='climb',gravity_model='inverse_square_height')
    geometric=truth(times=rate_times,**args)
    initial=dict(coordinates=np.asarray(geometric['coordinates'][0],float).copy(),
        velocity=np.asarray(geometric['velocity_local_mps'][0],float).copy(),
        rotation=np.asarray(geometric['attitude_body_to_local'][0],float).copy())
    raw=observe(geometric,sign=1);del geometric
    raw['times']=rate_times
    increments=construct(raw,method='linear_points',rate_hz=300,reserve=reserve)
    p=_parameters(1);vector=lambda key:np.array([p[key+'_'+a] for a in 'xyz'])
    corrected_theta=(increments['theta']-increments['dt'][:,None]*vector('gyro_bias'))/(1+vector('gyro_gain'))
    corrected_dv=(increments['dv']-increments['dt'][:,None]*vector('accel_bias'))/(1+vector('accel_gain'))
    times=query_start_s+np.arange(queries)*query_step_s
    reserve(generated_samples=queries)
    receiver=receiver_samples(times=times,sign=1,**args)['coordinates']
    return dict(version=VERSION,theta=corrected_theta,dv=corrected_dv,dt=increments['dt'],times=times,
        raw_theta=increments['theta'],raw_dv=increments['dv'],initial=initial,
        lever=vector('lever'),time_offset_s=p['time_offset'],
        correction_scales=1/np.r_[1+vector('gyro_gain'),1+vector('accel_gain')],
        sensor_correction={k:v for k,v in p.items() if k.startswith(('gyro_','accel_','lever_')) or k=='time_offset'},
        gravity_mps2=GRAVITY,radius_m=DISC_RADIUS,anchor_height_m=float(initial['coordinates'][2]),
        nominal_receiver=receiver,nominal_metric=physical_metric(receiver),training_epochs=2*queries//3,
        oracle_nominal_future_geometry_used=True,initial_state_is_known=True,calibration_is_known=True,
        random_draws=0,original_reads=0,protected_reads=0)


def build_operator(data,*,law,kernel,reserve,maximum_bytes=64*1024**2):
    if law not in ('increment','point'):raise ValueError('one explicit declared source law required')
    import numpy as np
    from .airquantumgrav_noisy_inputs import error_law,noise_settings,rate_point_noise_settings
    from .airquantumgrav_weighted_controls import fixture_rows
    from .airquantumgrav_error_policy import build
    from .ilvis0_error_model import factor
    from .ilvis0_noise_history import NativeNoiseHistory
    from .receiver_noise_states import ReceiverAugmentation
    from .state_space_covariance import LinearInnovations
    from .studies.artifacts import digest
    if (data.get('version')!=VERSION or data.get('oracle_nominal_future_geometry_used') is not True
            or data.get('initial_state_is_known') is not True or data.get('calibration_is_known') is not True
            or not callable(reserve)):
        raise ValueError('explicit known generated trajectory and calibration benchmark required')
    times=data['times'];n=len(data['dt']);m=len(times);cut=data['training_epochs']
    settings=noise_settings() if law=='increment' else rate_point_noise_settings();noise=error_law(settings)
    # These are generated nominal coordinates, not later receiver observations.
    # Their use is an intentional oracle assumption and cannot enter fitting.
    weights=build(fixture_rows(data['nominal_receiver'],times),policy_id='reported-short-v1')
    history=NativeNoiseHistory(kernel=kernel,**data['initial'],theta=data['theta'],delta_v=data['dv'],
        dt=data['dt'],query_times=times,time_offset_s=data['time_offset_s'],model=0,
        gravity=data['gravity_mps2'],radius=data['radius_m'],removal=0.,anchor_height=data['anchor_height_m'],
        lever=data['lever'],correction_scales=data['correction_scales'],noise=noise,
        white_loadings=weights.transforms@factor(weights.spec.white),maximum_packets=n,
        maximum_epochs=m,reserve=reserve)
    augmented=ReceiverAugmentation(history.steps(),times=times,spec=weights.spec,transforms=weights.transforms,
        state_dimension=history.state_dimension,initial_loading=noise.initial_loading(),maximum_epochs=m,
        receiver_epochs=cut)
    operator=LinearInnovations(augmented.steps(),epoch_count=m,state_dimension=augmented.state_dimension,
        observation_dimension=3,initial_loading=augmented.initial_loading,maximum_bytes=maximum_bytes,
        design_is_fixed=True,error_distribution='gaussian',observation_form='before_transition_shared_noise',
        white_error_may_be_singular=True)
    descriptor=dict(version=VERSION,law=law,model='sphere_rotating',source_law=type(noise).__name__,
        noise_settings=settings,receiver_policy=weights.descriptor,receiver_observation_epochs=cut,
        prediction_target='physical_position',oracle_nominal_future_geometry_used=True,
        initial_state_is_known=True,calibration_is_known=True,random_draws=0,optimizer_starts=0,
        original_reads=0,protected_reads=0,confidence_calibrated=False,
        operator_configuration=operator.configuration,state_dimension=operator.state_dimension,
        operator_storage_bytes=operator.storage_bytes,
        input_hashes={k:digest(np.asarray(data[k],dtype='<f8').tobytes()) for k in ('theta','dv','dt','times','nominal_receiver')})
    return operator,np.asarray(history.observations,float),descriptor
