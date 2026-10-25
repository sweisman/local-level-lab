# SPDX-License-Identifier: AGPL-3.0-or-later
"""Construct explicit noisy synthetic inputs before training initialization.

The rates below are frozen development stress settings, not measured archive
noise or hardware defaults. Future truth positions are not generated here.
"""
import math


def noise_settings():
    return dict(version='esa-synthetic-noise-v1',seed=26062413,
        gyro_white_rads_per_sqrt_s=math.radians(.02)/60.,
        accel_white_mps_per_sqrt_s=2e-4,
        gyro_bias_stationary_rads=math.radians(.05)/3600.,
        accel_bias_stationary_mps2=5e-5,
        gyro_bias_tau_s=600.,accel_bias_tau_s=300.,
        values_are_hardware_specifications=False,estimated_from_observed_errors=False)


def rate_point_noise_settings():
    """Explicit synthetic point-error levels; no inferred hardware bandwidth."""
    return dict(version='esa-synthetic-rate-point-noise-v1',seed=26062413,
        input_error_law='linear_rate_points',gyro_point_std_rads=.00010076663134634544,
        accel_point_std_mps2=.0034641016151377548,
        gyro_bias_stationary_rads=math.radians(.05)/3600.,
        accel_bias_stationary_mps2=5e-5,gyro_bias_tau_s=600.,accel_bias_tau_s=300.,
        values_are_hardware_specifications=False,estimated_from_observed_errors=False)


def error_law(settings):
    """Supply exactly the same declared input law to the error propagation."""
    import numpy as np
    square=lambda value:np.eye(3)*value*value
    if settings==noise_settings():
        from .ilvis0_noise_history import PacketNoise
        return PacketNoise(gyro_white_psd=square(settings['gyro_white_rads_per_sqrt_s']),
            accel_white_psd=square(settings['accel_white_mps_per_sqrt_s']),
            **_bias_parameters(settings,square))
    if settings==rate_point_noise_settings():
        from .linear_point_noise import LinearPointNoise
        return LinearPointNoise(gyro_point_covariance=square(settings['gyro_point_std_rads']),
            accel_point_covariance=square(settings['accel_point_std_mps2']),
            **_bias_parameters(settings,square))
    raise ValueError('explicit versioned synthetic input law required')


def _bias_parameters(settings,square):
    return dict(gyro_bias_covariance=square(settings['gyro_bias_stationary_rads']),
        accel_bias_covariance=square(settings['accel_bias_stationary_mps2']),
        gyro_bias_tau_s=settings['gyro_bias_tau_s'],accel_bias_tau_s=settings['accel_bias_tau_s'])


def construction_limits(r):
    n=round(r['duration_s']*r['rate_hz']);cut=2*r['queries']//3
    return dict(constructed_intervals=n,generated_samples=n+1+cut,
        noise_normal_variates=(12*(n+1)+6*cut+6 if r.get('noise')==rate_point_noise_settings()
            else 18*n+6*cut+12))


def construct(spec,r,*,reserve):
    if r.get('noise') not in (noise_settings(),rate_point_noise_settings()):
        raise ValueError('explicit versioned synthetic noise settings required')
    import numpy as np
    from lll.airquantumgrav_training_controls import generated_training
    from lll.airquantumgrav_weighted_controls import fixture_rows
    from lll.airquantumgrav_error_policy import build,policies
    from lll.measurement_noise import perturb_imu,receiver_errors,VERSION
    from lll.studies.artifacts import digest,encoded
    if spec.get('policy_id') not in policies():raise ValueError('declared receiver noise policy required')
    base={k:v for k,v in spec.items() if k!='policy_id'}
    clean=generated_training(base,r,reserve=reserve,height_profile='climb',gravity_model='inverse_square_height')
    n=len(clean['dt']);cut=clean['training_epochs'];settings=r['noise']
    raw_hashes={k:digest(np.asarray(clean[k],dtype='<f8').tobytes()) for k in ('theta','dv','dt')}
    isotropic=lambda std:np.eye(3)*std*std
    if settings==rate_point_noise_settings():
        from .measurement_noise import perturb_linear_rate_points
        # The generator reserves its own point draws; reserve receiver draws
        # separately so none are hidden or charged twice.
        reserve(noise_normal_variates=6*cut+6)
        noisy=perturb_linear_rate_points(**{k:clean[k] for k in ('theta','dv','dt')},
            seed=settings['seed'],maximum_steps=n,reserve=reserve,
            gyro_point_covariance=isotropic(settings['gyro_point_std_rads']),
            accel_point_covariance=isotropic(settings['accel_point_std_mps2']),
            **_bias_parameters(settings,isotropic))
    else:
        reserve(noise_normal_variates=construction_limits(r)['noise_normal_variates'])
        noisy=perturb_imu(**{k:clean[k] for k in ('theta','dv','dt')},seed=settings['seed'],maximum_steps=n,
            gyro_white_psd=isotropic(settings['gyro_white_rads_per_sqrt_s']),
            accel_white_psd=isotropic(settings['accel_white_mps_per_sqrt_s']),
            **_bias_parameters(settings,isotropic))
    rows=fixture_rows(clean['training_gps'],clean['times'][:cut])
    weights=build(rows,policy_id=spec['policy_id'])
    errors=receiver_errors(weights.times,weights.spec,seed=settings['seed'],maximum_epochs=cut,transforms=weights.transforms)
    measured=[dict(row,latitude_deg=row['latitude_deg']+math.degrees(error[0]),
        longitude_deg=row['longitude_deg']+math.degrees(error[1]),height_m=row['height_m']+error[2])
        for row,error in zip(rows,errors,strict=True)]
    binding=dict(noise_version=VERSION,settings=settings,receiver_policy=weights.descriptor,
        receiver_covariance_source_sha256=weights.source_sha256,
        clean_raw_array_sha256=raw_hashes,
        measured_raw_array_sha256={k:digest(np.asarray(noisy[k],dtype='<f8').tobytes()) for k in ('theta','dv','dt')},
        noise_increment_sha256={name:{key:digest(np.asarray(noisy['noise'][name][key],dtype='<f8').tobytes())
            for key in ('white_increments','bias_increments')} for name in ('gyro','accel')},
        noisy_training_receiver_sha256=digest(encoded(measured)),
        receiver_coordinate_noise_sha256=digest(errors.astype('<f8').tobytes()),
        gravity_anchor_height_m=measured[0]['height_m'],gravity_anchor_source='first_noisy_training_receiver_height',
        true_initial_state_supplied=False,true_calibration_supplied=False,
        later_receiver_positions_generated=False,receiver_and_imu_streams_separate=True,
        noise_is_an_assumption_not_measured_archive_error=True)
    if settings==rate_point_noise_settings():binding['input_error_law']='linear_rate_points'
    return dict(**{k:noisy[k] for k in ('theta','dv','dt')},times=clean['times'],
        training_rows=measured,training_epochs=cut,binding=binding)
