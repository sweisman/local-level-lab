# SPDX-License-Identifier: AGPL-3.0-or-later
"""Matched generated noise paths; no fits, observed data or coverage claims."""


def draw(data,*,law,seed,reserve):
    import numpy as np
    from .generated_noise_benchmark import VERSION
    from .airquantumgrav_noisy_inputs import noise_settings,rate_point_noise_settings,_bias_parameters
    from .airquantumgrav_weighted_controls import fixture_rows
    from .airquantumgrav_error_policy import build
    from .measurement_noise import perturb_imu,perturb_linear_rate_points,receiver_errors
    from .studies.artifacts import digest
    if (data.get('version')!=VERSION or law not in ('increment','point')
            or type(seed) is not int or not 0<=seed<2**64 or not callable(reserve)):
        raise ValueError('known generated material, explicit input law, uint64 seed and allowance required')
    n=len(data['dt']);cut=data['training_epochs']
    weights=build(fixture_rows(data['nominal_receiver'][:cut],data['times'][:cut]),policy_id='reported-short-v1')
    square=lambda x:np.eye(3)*x*x
    settings=noise_settings() if law=='increment' else rate_point_noise_settings()
    args=dict(theta=data['raw_theta'],dv=data['raw_dv'],dt=data['dt'],seed=seed,
        maximum_steps=n,**_bias_parameters(settings,square))
    # The receiver generator always draws white, offset, drift and OU components,
    # including zero-amplitude components. Pay for every draw before generation.
    reserve(noise_normal_variates=3*cut+6+3*cut*len(weights.spec.components))
    if law=='increment':
        reserve(noise_normal_variates=18*n+6)
        noisy=perturb_imu(**args,gyro_white_psd=square(settings['gyro_white_rads_per_sqrt_s']),
            accel_white_psd=square(settings['accel_white_mps_per_sqrt_s']))
    else:
        noisy=perturb_linear_rate_points(**args,gyro_point_covariance=square(settings['gyro_point_std_rads']),
            accel_point_covariance=square(settings['accel_point_std_mps2']),reserve=reserve)
    receiver=receiver_errors(weights.times,weights.spec,seed=seed,maximum_epochs=cut,transforms=weights.transforms)
    result=dict(theta_error=noisy['theta']-data['raw_theta'],dv_error=noisy['dv']-data['raw_dv'],
        receiver_error=receiver,seed=seed,law=law,future_receiver_errors_generated=False)
    result['array_sha256']={k:digest(np.asarray(result[k],dtype='<f8').tobytes())
        for k in ('theta_error','dv_error','receiver_error')}
    return result


def propagate(data,*,theta,dv,operator,kernel,reserve):
    """Known calibration through the shared scalar equations, not a new solver.

    The oracle clean coordinates fill the scalar API's residual reference. They
    never correct the integrated motion. Its whitened residual is unused here.
    """
    import numpy as np
    from types import SimpleNamespace
    from .generated_noise_benchmark import VERSION
    from .state_space_covariance import LinearInnovations
    from .airquantumgrav_training_controls import parameter_limits
    from .ilvis0_exploratory import ConditionalBounds
    from .ilvis0_precision_value import calculate
    theta=np.asarray(theta,float);dv=np.asarray(dv,float);n=len(data['dt']);m=len(data['times'])
    if (data.get('version')!=VERSION or any(data.get(k) is not True for k in ('initial_state_is_known','calibration_is_known'))
            or theta.shape!=(n,3) or dv.shape!=theta.shape or not np.all(np.isfinite(theta)) or not np.all(np.isfinite(dv))
            or not isinstance(operator,LinearInnovations) or operator.epoch_count!=m
            or operator.observation_dimension!=3 or not callable(kernel) or not callable(reserve)):
        raise ValueError('complete known-calibration inputs, matching operator and finite native allowance required')
    initial=dict(zip(('latitude_rad','longitude_rad','height_m'),data['initial']['coordinates']))
    initial.update(velocity_ned_mps=data['initial']['velocity'],attitude_body_to_ned=data['initial']['rotation'])
    bounds=ConditionalBounds(parameter_limits(),fit_earth_removal=False)
    point=np.array([data['sensor_correction'].get(k,0)/bounds.limits[k] for k in bounds.active])
    problem=SimpleNamespace(theta=theta,dv=dv,dt=data['dt'],gps_times=data['times'],gps=data['nominal_receiver'],
        initial=initial,bounds=bounds,gravity=data['gravity_mps2'],radius=data['radius_m'],
        observation_error=operator,whiten_stacked=operator.whiten)
    reserve(native_calls=1,packet_steps=n,packet_query_visits=n*m)
    result=calculate(problem,point,'sphere_rotating',kernel=kernel,longitude='stable')
    return result['coordinates']


def conditional_error(operator,nominal,perturbed,receiver_error,*,training_epochs,metric):
    """True minus predicted position after earlier-only Gaussian conditioning."""
    import numpy as np
    from .state_space_covariance import LinearInnovations
    if (not isinstance(operator,LinearInnovations) or operator.observation_dimension!=3
            or type(training_epochs) is not int or not 1<=training_epochs<operator.epoch_count):
        raise ValueError('matching three-coordinate operator and chronological split required')
    n=operator.epoch_count;cut=training_epochs
    nominal,perturbed,receiver_error,metric=(np.asarray(a,float) for a in (nominal,perturbed,receiver_error,metric))
    if (nominal.shape!=(n,3) or perturbed.shape!=nominal.shape or receiver_error.shape!=(cut,3)
            or metric.shape!=(n-cut,3) or np.any(metric<=0)
            or any(not np.all(np.isfinite(a)) for a in (nominal,perturbed,receiver_error,metric))):
        raise ValueError('complete earlier-only receiver errors and finite positive future metric required')
    delta=perturbed-nominal
    _,checkpoint=operator.apply_block((receiver_error-delta[:cut]).ravel(),first_epoch=0)
    mean=operator.conditional_marginals(state=checkpoint)['mean']
    return (-delta[cut:]-mean)*metric


def summarize_pair(plus,minus,half_plus,half_minus,*,standard_deviation,absolute_limit_m,relative_limit):
    import math
    import numpy as np
    arrays=[np.asarray(v,float) for v in (plus,minus,half_plus,half_minus,standard_deviation)]
    if (arrays[0].ndim!=2 or arrays[0].shape[1:]!=(3,) or not len(arrays[0])
            or any(v.shape!=arrays[0].shape or not np.all(np.isfinite(v)) for v in arrays)
            or np.any(arrays[-1]<0) or not all(type(v) in (int,float) and math.isfinite(v) and v>0
                for v in (absolute_limit_m,relative_limit))):
        raise ValueError('complete matched finite curves, nonnegative deviations and fixed positive limits required')
    a,b,c,d,sigma=arrays;limit=np.maximum(absolute_limit_m,relative_limit*sigma)
    even=(a+b)/2;half_even=(c+d)/2
    response_change=(c-d)-(a-b)/2
    fraction=float(np.max(abs(even)/limit));change=float(np.max(abs(response_change)/limit))
    return dict(passed=fraction<=1 and change<=1,maximum_even_remainder_m=float(np.max(abs(even))),
        maximum_half_amplitude_even_remainder_m=float(np.max(abs(half_even))),
        maximum_half_response_change_m=float(np.max(abs(response_change))),
        maximum_even_remainder_fraction_of_limit=fraction,maximum_half_response_change_fraction_of_limit=change,
        absolute_limit_m=absolute_limit_m,relative_limit=relative_limit,
        plus_rms_neu_m=np.sqrt(np.mean(a*a,axis=0)).tolist(),minus_rms_neu_m=np.sqrt(np.mean(b*b,axis=0)).tolist(),
        independent_realizations=1,finite_sample_check_only=True,global_remainder_bound_established=False,
        confidence_calibrated=False,scientific_decision='abstain')
