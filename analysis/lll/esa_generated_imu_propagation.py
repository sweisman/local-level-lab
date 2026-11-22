# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent local propagation for the known-truth ESA motion control.

This uses the generated IMU's initial state, so it is a software-control
calculation, not an archive fit or an Earth-model test.
"""


def propagate_generated(case):
    """Integrate clean and noisy generated increments on the same time grid."""
    import numpy as np
    from scipy.spatial.transform import Rotation
    from .esa_motion_error_controls import analytic_path

    if not isinstance(case, dict) or case.get('version') != 'esa-motion-error-control-v1':
        raise ValueError('declared generated motion control required')
    dt = case.get('imu_dt_s')
    times = np.asarray(case.get('imu_time_s'), dtype=float)
    receiver_times = np.asarray(case.get('receiver_time_s'), dtype=float)
    clean_angle = np.asarray(case.get('truth_gyro_body_rads'), dtype=float)
    clean_force = np.asarray(case.get('truth_force_body_mps2'), dtype=float)
    noisy_angle = np.asarray(case.get('measured_dtheta_rad'), dtype=float)
    noisy_force = np.asarray(case.get('measured_dv_mps'), dtype=float)
    receiver = np.asarray(case.get('receiver_position_neu_m'), dtype=float)
    receiver_error = np.asarray(case.get('receiver_error_neu_m'), dtype=float)
    if (not isinstance(dt, (int, float)) or not np.isfinite(dt) or dt <= 0 or
            times.ndim != 1 or not len(times) or
            clean_angle.shape != (len(times), 3) or
            clean_force.shape != (len(times), 3) or
            noisy_angle.shape != (len(times), 3) or
            noisy_force.shape != (len(times), 3) or
            receiver.shape != (len(receiver_times), 3) or
            receiver_error.shape != receiver.shape or
            len(receiver_times) < 2 or
            not all(np.all(np.isfinite(value)) for value in (
                times, receiver_times, clean_angle, clean_force,
                noisy_angle, noisy_force, receiver, receiver_error))):
        raise ValueError('complete finite aligned generated IMU and receiver streams required')
    rate = round(1/dt)
    if (rate < 1 or abs(rate*dt-1) > 1e-12 or
            len(times) != (len(receiver_times)-1)*rate or
            not np.allclose(times, (np.arange(len(times))+.5)*dt,
                            rtol=0., atol=1e-10) or
            not np.allclose(receiver_times,
                            np.arange(len(receiver_times)), rtol=0., atol=1e-10)):
        raise ValueError('unsupported generated timing; no resampling or repair')
    start = analytic_path(np.array([0.]))
    yaw, pitch = float(start['yaw_rad'][0]), float(start['pitch_rad'][0])
    orientation = Rotation.from_euler('ZY', [yaw, pitch])
    position_neu = np.asarray(start['position_neu_m'][0], float)
    velocity_neu = np.asarray(start['velocity_neu_mps'][0], float)
    initial_position_ned = position_neu*np.array([1., 1., -1.])
    initial_velocity_ned = velocity_neu*np.array([1., 1., -1.])
    gravity_ned = np.array([0., 0., 9.80665])
    histories = []
    for angular_rate, body_force in ((clean_angle, clean_force),
                                     (noisy_angle/dt, noisy_force/dt)):
        attitude = orientation
        position = initial_position_ned.copy()
        velocity = initial_velocity_ned.copy()
        positions = [position.copy()]
        for index, (rate_body, force_body) in enumerate(
                zip(angular_rate, body_force, strict=True), 1):
            half_turn = Rotation.from_rotvec(.5*rate_body*dt)
            acceleration = (attitude*half_turn).apply(force_body)+gravity_ned
            position = position + velocity*dt + .5*acceleration*dt*dt
            velocity = velocity + acceleration*dt
            attitude = attitude*Rotation.from_rotvec(rate_body*dt)
            if index % rate == 0:
                positions.append(position.copy())
        path = np.asarray(positions)*np.array([1., 1., -1.])
        histories.append(path)
    clean, noisy = histories
    return dict(version='esa-generated-imu-propagation-v1',
                receiver_epochs=len(receiver_times),
                truth_integrated_position_neu_m=clean,
                measured_position_neu_m=noisy,
                sensor_only_position_error_neu_m=noisy-clean,
                receiver_position_neu_m=receiver,
                receiver_error_neu_m=receiver_error,
                true_initial_state_supplied=True,
                local_ned_dynamics_only=True,
                original_reads=0, protected_reads=0,
                observed_error_law_qualified=False,
                scientific_decision='abstain')
